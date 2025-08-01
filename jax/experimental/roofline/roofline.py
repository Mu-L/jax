# Copyright 2024 The JAX Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol
from collections.abc import Callable, Sequence
import numpy as np

import jax.numpy as jnp
from jax.sharding import NamedSharding
from jax._src import api
from jax._src import core
from jax._src import prng
from jax._src import source_info_util
from jax._src import traceback_util
from jax._src import util
from jax._src.api import make_jaxpr
from jax._src.interpreters.partial_eval import dce_jaxpr
from jax._src.mesh import AbstractMesh, Mesh
from jax._src.tree_util import broadcast_prefix, tree_flatten, tree_unflatten, tree_map
from jax._src.util import foreach
from jax._src.shard_map import shard_map, shard_map_p


ShapeDtypeStructTree = Any
Specs = Any
ValidRooflineDtype = np.dtype | prng.KeyTy

map = util.safe_map


@dataclass(frozen=True, slots=True, kw_only=True)
class RooflineRuleContext:
  name_stack: source_info_util.NameStack
  primitive: core.Primitive
  avals_in: Sequence[core.AbstractValue]
  avals_out: Sequence[core.AbstractValue]
  jaxpr_eqn_ctx: core.JaxprEqnContext
  mesh: Mesh | AbstractMesh | None
  pin_lhs_in_vmem: bool
  pin_rhs_in_vmem: bool


@dataclass(frozen=True, slots=True, kw_only=True)
class RooflineShape:
  shape: tuple[int, ...]
  dtype: ValidRooflineDtype

  @classmethod
  def from_aval(cls, aval: core.AbstractValue) -> RooflineShape:
    if not isinstance(aval, core.ShapedArray):
      raise TypeError(f"Expected ShapedArray, got {type(aval)}.")
    if not isinstance(aval.dtype, ValidRooflineDtype):
      raise TypeError(
          f"Expected numpy or prng.KeyTy dtype, got {type(aval.dtype)}."
      )
    return cls(shape=aval.shape, dtype=aval.dtype)

  @property
  def size(self) -> int:
    return int(np.prod(self.shape))

  @property
  def bytes(self) -> int:
    return int(self.size * self.dtype.itemsize)

  @classmethod
  def total_bytes(cls, avals: Sequence[core.AbstractValue]) -> int:
    return sum(cls.from_aval(aval).bytes for aval in avals)


@dataclass(frozen=True, slots=True, kw_only=True)
class RooflineResult:
  flops: int = 0
  unfused_flops: int = 0
  ici_bytes: dict[str, int] = field(default_factory=dict)
  ici_latency: dict[str, int] = field(default_factory=dict)
  hbm_bytes: int = 0
  peak_hbm_bytes: int = 0
  unfused_hbm_bytes: int = 0

  @classmethod
  def zeros(cls) -> RooflineResult:
    return cls()

  def __add__(self, other: RooflineResult) -> RooflineResult:
    def merge_ici_dicts(d1: dict[str, int], d2: dict[str, int]) -> dict[str, int]:
      return {k: d1.get(k, 0) + d2.get(k, 0) for k in set(d1) | set(d2)}

    return RooflineResult(
        flops=self.flops + other.flops,
        unfused_flops=self.unfused_flops + other.unfused_flops,
        ici_bytes=merge_ici_dicts(self.ici_bytes, other.ici_bytes),
        ici_latency=merge_ici_dicts(self.ici_latency, other.ici_latency),
        hbm_bytes=self.hbm_bytes + other.hbm_bytes,
        peak_hbm_bytes=max(self.peak_hbm_bytes, other.peak_hbm_bytes),
        unfused_hbm_bytes=self.unfused_hbm_bytes + other.unfused_hbm_bytes,
    )

  def __mul__(self, constant: int | float) -> RooflineResult:
    return RooflineResult(
        flops=int(self.flops * constant),
        unfused_flops=int(self.unfused_flops * constant),
        ici_bytes={k: int(v * constant) for k, v in self.ici_bytes.items()},
        ici_latency={k: int(v * constant) for k, v in self.ici_latency.items()},
        hbm_bytes=int(self.hbm_bytes * constant),
        peak_hbm_bytes=int(self.peak_hbm_bytes * constant),
        unfused_hbm_bytes=int(self.unfused_hbm_bytes * constant),
    )

  def __rmul__(self, constant: int | float) -> RooflineResult:
    return self.__mul__(constant)


class _RooflineRule(Protocol):
  def __call__(
    self, ctx: RooflineRuleContext, *args: RooflineShape, **kw
  ) -> RooflineResult: ...


_rooflines: dict[core.Primitive, _RooflineRule] = {}


def _roofline_interpreter(
  f_name: str,
  jaxpr: core.Jaxpr,
  mesh: Mesh | AbstractMesh,
  *,
  pin_lhs_in_vmem: bool = False,
  pin_rhs_in_vmem: bool = False,
) -> RooflineResult:
  name_stack = source_info_util.new_name_stack(util.wrap_name("roofline", f_name))

  result = RooflineResult.zeros()

  env: dict[core.Var, RooflineShape] = {}

  def write(v: core.Var, node: RooflineShape):
    assert node is not None
    env[v] = node

  def read(v: core.Atom) -> RooflineShape:
    if type(v) is core.Literal:
      return RooflineShape.from_aval(core.abstractify(v.val))
    else:
      assert isinstance(v, core.Var)
      return env[v]

  def aval(v: core.Atom) -> core.AbstractValue:
    if type(v) is core.Literal:
      return core.abstractify(v.val)
    else:
      return v.aval

  def sum_bytes(shapes: Sequence[RooflineShape]) -> int:
    return sum(shape.bytes for shape in shapes)

  jaxpr = jaxpr.jaxpr if isinstance(jaxpr, core.ClosedJaxpr) else jaxpr
  make_roofline_shape = lambda x: RooflineShape.from_aval(aval(x))
  foreach(
    write,
    jaxpr.constvars,
    map(make_roofline_shape, jaxpr.constvars),
  )
  foreach(write, jaxpr.invars, map(make_roofline_shape, jaxpr.invars))
  last_used = core.last_used(jaxpr)

  current_hbm_bytes = sum_bytes(list(env.values()))
  peak_hbm_bytes = current_hbm_bytes

  for eqn in jaxpr.eqns:
    source_info = eqn.source_info.replace(
      name_stack=name_stack + eqn.source_info.name_stack
    )
    with source_info_util.user_context(
      eqn.source_info.traceback, name_stack=source_info.name_stack
    ):
      if "jaxpr" in eqn.params:
        result += _roofline_interpreter(
          util.wrap_name(eqn.primitive.name, f_name),
          eqn.params["jaxpr"],
          mesh,
          pin_lhs_in_vmem=pin_lhs_in_vmem,
          pin_rhs_in_vmem=pin_rhs_in_vmem,
        )
      elif "call_jaxpr" in eqn.params:
        # Used for custom_jvp_call_p. Recursively calculates roofline result for
        # all primitives in the custom function.
        result += _roofline_interpreter(
          util.wrap_name(eqn.primitive.name, f_name),
          eqn.params['call_jaxpr'],
          mesh,
          pin_lhs_in_vmem=pin_lhs_in_vmem,
          pin_rhs_in_vmem=pin_rhs_in_vmem,
        )
      else:
        if eqn.primitive not in _rooflines:
          msg = f"No roofline rule for {eqn.primitive}."
          for attr in dir(eqn):
            if not attr.startswith("_"):
              msg += f"\n{attr}: {getattr(eqn, attr)}"
          raise NotImplementedError(msg)
        rule = _rooflines[eqn.primitive]
        result += rule(
          RooflineRuleContext(
            name_stack=source_info.name_stack,
            primitive=eqn.primitive,
            avals_in=map(aval, eqn.invars),
            avals_out=map(aval, eqn.outvars),
            jaxpr_eqn_ctx=eqn.ctx,
            mesh=mesh,
            pin_lhs_in_vmem=pin_lhs_in_vmem,
            pin_rhs_in_vmem=pin_rhs_in_vmem,
          ),
          *map(read, eqn.invars),
          **eqn.params,
        )

      # Add bytes for the newly-created output variables.
      outvar_shapes = map(make_roofline_shape, eqn.outvars)
      current_hbm_bytes += sum_bytes(outvar_shapes)
      foreach(write, eqn.outvars, outvar_shapes)

      # Remove bytes for the no-longer-needed input variables.
      removed_shapes = [
          env[v] for v in eqn.invars
          if not isinstance(v, core.Literal) and last_used[v] is eqn
      ]
      current_hbm_bytes -= sum_bytes(removed_shapes)
      core.clean_up_dead_vars(eqn, env, last_used)

      peak_hbm_bytes = max(peak_hbm_bytes, current_hbm_bytes)

  result += RooflineResult(peak_hbm_bytes=peak_hbm_bytes)
  return result


def _f_with_vjp(f: Callable):
  @util.wraps(f)
  def wrapped(*args):
    primals, f_vjp = api.vjp(f, *args)
    return f_vjp(tree_map(jnp.bfloat16, primals))

  return wrapped


def roofline(
    f: Callable,
    mesh: Mesh | AbstractMesh | None = None,
    in_specs: Specs | None = None,
    out_specs: Specs | None = None,
    *,
    pin_lhs_in_vmem: bool = False,
    pin_rhs_in_vmem: bool = False,
    vjp: bool = False,
    print_jaxpr: bool = False,
) -> Callable[..., tuple[ShapeDtypeStructTree, RooflineResult]]:
  @util.wraps(f)
  @traceback_util.api_boundary
  def wrapped(*args):
    wrapped_f = f
    if in_specs is not None and out_specs is not None and mesh is not None:
      wrapped_f = shard_map(wrapped_f, mesh=mesh, in_specs=in_specs,
                            out_specs=out_specs)
    if vjp:
      wrapped_f = _f_with_vjp(wrapped_f)

    jaxpr, out_shapes = make_jaxpr(wrapped_f, return_shape=True)(*args)

    def make_sharded_shape_dtype_struct(
      shape: api.ShapeDtypeStruct, out_spec: Specs
    ) -> api.ShapeDtypeStruct:
      return api.ShapeDtypeStruct(
        shape.shape, shape.dtype, sharding=NamedSharding(mesh, out_spec)  # type: ignore
      )

    if out_specs is not None and mesh is not None:
      out_specs_flat = broadcast_prefix(out_specs, out_shapes)
      flat_out_shapes, treedef = tree_flatten(out_shapes)
      flat_out_shapes = map(
          make_sharded_shape_dtype_struct, flat_out_shapes, out_specs_flat
      )
      out_shapes = tree_unflatten(treedef, flat_out_shapes)

    used_outputs = (True,) * len(jaxpr.jaxpr.outvars)
    jaxpr, _ = dce_jaxpr(jaxpr.jaxpr, used_outputs)
    shard_map_eqns = [
        e for e in jaxpr.eqns if e.primitive == shard_map_p
    ]
    if shard_map_eqns:
      try:
        jaxpr = shard_map_eqns[-1].params["jaxpr"]
      except KeyError:
        raise ValueError(f"Missing shard_map jaxpr in {jaxpr}.")

    if print_jaxpr:
      print(jaxpr)

    return out_shapes, _roofline_interpreter(
        util.fun_qual_name(f),
        jaxpr,
        mesh,
        pin_lhs_in_vmem=pin_lhs_in_vmem,
        pin_rhs_in_vmem=pin_rhs_in_vmem,
    )

  return wrapped


def register_roofline(prim: core.Primitive):
  def register(rule: _RooflineRule):
    _rooflines[prim] = rule
    return rule

  return register


def register_standard_roofline(prim: core.Primitive):
  def standard_rule(ctx: RooflineRuleContext, *args, **kwargs):
    return RooflineResult.zeros()

  _rooflines[prim] = standard_rule


def roofline_and_grad(
  f: Callable,
  mesh: Mesh | AbstractMesh,
  in_specs: Specs,
  out_specs: Specs,
  *,
  pin_lhs_in_vmem: bool = False,
  pin_rhs_in_vmem: bool = False,
  print_jaxpr: bool = False,
) -> Callable[..., tuple[ShapeDtypeStructTree, RooflineResult, RooflineResult]]:
  @util.wraps(f)
  @traceback_util.api_boundary
  def wrapped(*args):
    primal_shapes, fwd_result = roofline(
      f,
      mesh,
      in_specs,
      out_specs,
      pin_lhs_in_vmem=pin_lhs_in_vmem,
      pin_rhs_in_vmem=pin_rhs_in_vmem,
      print_jaxpr=print_jaxpr,
    )(*args)

    return (
      primal_shapes,
      fwd_result,
      roofline(
        f,
        mesh,
        in_specs,
        out_specs,
        pin_lhs_in_vmem=pin_lhs_in_vmem,
        pin_rhs_in_vmem=pin_rhs_in_vmem,
        vjp=True,
        print_jaxpr=print_jaxpr,
      )(
        *tree_map(
          lambda x: api.ShapeDtypeStruct(
            x.shape,
            jnp.int32 if x.dtype == jnp.int32 else jnp.bfloat16,
            sharding=x.sharding,
          ),
          args,
        )
      )[1],
    )

  return wrapped
