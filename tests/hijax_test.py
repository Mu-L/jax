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

from dataclasses import dataclass
from functools import partial
import unittest

from absl.testing import absltest, parameterized

import jax
import jax.numpy as jnp

from jax._src import config
from jax._src import core
from jax._src.interpreters import ad
from jax._src import test_util as jtu
from jax._src.util import safe_zip, safe_map

from jax._src.hijax import (HiPrimitive, HiType, Box, new_box, box_set, box_get,
                            box_effect)

config.parse_flags_with_absl()

map, unsafe_map = safe_map, map
zip, unsafe_zip = safe_zip, zip


class HijaxTest(jtu.JaxTestCase):

  def test_custom_types_and_primitive(self):
    if config.enable_x64.value: raise unittest.SkipTest("no x64")

    @dataclass(frozen=True)
    class MyArray:
      arr: jax.Array  # always f32

    @dataclass(frozen=True)
    class MyTy(HiType):
      def to_tangent_aval(self):
        return MyTy()
      def str_short(self, short_dtypes=False):
        return 'MyTy'
      def lo_ty(self):
        return [core.ShapedArray((), jnp.dtype('float32'))]
      def lower_val(self, hi_val: MyArray) -> list[jax.Array]:
        return [hi_val.arr]
      def raise_val(self, val) -> MyArray:
        return MyArray(val)

      def __eq__(self, other): return isinstance(other, MyTy)

      def vspace_zero(self):
        return MyArray(jnp.zeros((), 'float32'))
      def vspace_add(self, x, y):
        return add(x, y)
    core.pytype_aval_mappings[MyArray] = lambda _: MyTy()

    class ToMy(HiPrimitive):
      def is_high(self): return True

      def abstract_eval(_, lo_aval):
        return MyTy(), set()

      def to_lojax(_, lo):
        return MyArray(lo)

      def jvp(_, primals, tangents):
        x, x_dot = *primals, *tangents
        return to(x), to(x_dot)

      def transpose(self, out_bar, _):
        return from_(out_bar),

    class FromMy(HiPrimitive):
      def is_high(self): return True

      def abstract_eval(_, hi_aval):
        return hi_aval.lo_ty()[0], set()

      def to_lojax(_, hi):
        return hi.arr

      def jvp(_, primals, tangents):
        x, x_dot = *primals, *tangents
        return from_(x), from_(x_dot)

      def transpose(self, out_bar, _):
        return to(out_bar),

    def to(x): return to_p.bind(x)
    to_p = ToMy('to_my')

    def from_(x): return from_p.bind(x)
    from_p = FromMy('from_my')

    def mul(x, y): return mul_p.bind(x, y)
    def add(x, y): return add_p.bind(x, y)

    class MyMul(HiPrimitive):
      def is_high(self): return True

      def abstract_eval(_, hi_x, hi_y):
        if hi_x != hi_y: raise Exception
        return hi_x, set()

      def to_lojax(_, hi_x, hi_y):
        return MyArray(hi_x.arr * hi_y.arr)

      def jvp(_, primals, tangents):
        (x, y), (x_dot, y_dot) = primals, tangents
        return mul(x, y), add(mul(x, y_dot), mul(x_dot, y))

      def transpose(self, out_bar, x, y):
        assert ad.is_undefined_primal(x) ^ ad.is_undefined_primal(y)
        if ad.is_undefined_primal(x):
          return mul(out_bar, y), None
        else:
          return None, mul(x, out_bar)

    class MyAdd(HiPrimitive):
      def is_high(self): return True

      def abstract_eval(_, hi_x, hi_y):
        if hi_x != hi_y: raise Exception
        return hi_x, set()

      def to_lojax(_, hi_x, hi_y):
        return MyArray(hi_x.arr + hi_y.arr)

      def jvp(_, primals, tangents):
        assert False  # TODO

      def transpose(self, out_bar, x, y):
        return out_bar, out_bar

    mul_p = MyMul('my_mul')
    add_p = MyAdd('my_add')


    @jax.jit
    def f(x):
      return to(from_(x))

    # test basic to/from jit
    a = MyArray(jnp.ones(()))
    b = f(a)  # don't crash
    self.assertIsInstance(b, MyArray)
    self.assertAllClose(b.arr, jnp.ones(()))

    # test basic to/from autodiff
    b, b_dot = jax.jvp(f, (a,), (a,))
    self.assertIsInstance(b, MyArray)
    self.assertIsInstance(b_dot, MyArray)

    # test mul jit and backward pass

    @jax.jit
    def f(x):
      return mul(x, x)

    b, f_vjp = jax.vjp(f, a)
    self.assertIn('MyTy', str(f_vjp))
    a_grad, = f_vjp(b)
    self.assertIsInstance(a_grad, MyArray)
    self.assertAllClose(a_grad.arr, 2.0, check_dtypes=False)


class BoxTest(jtu.JaxTestCase):

  @parameterized.parameters([False, True])
  def test_qdd(self, jit):

    val1 = 1.0
    val2 = jnp.arange(3)

    box1 = Box(val1)

    def f(box2):
      assert core.cur_qdd(box2).leaf_avals == (core.typeof(val1),)
      box2.set(val2)
      assert core.cur_qdd(box2).leaf_avals == (core.typeof(val2),)

      box3 = new_box()
      box3.set(val2)
      assert core.cur_qdd(box3).leaf_avals == (core.typeof(val2),)
      box3.set(val1)
      assert core.cur_qdd(box3).leaf_avals == (core.typeof(val1),)

      assert core.cur_qdd(box1).leaf_avals == (core.typeof(val1),)
      box1.set(val2)
      assert core.cur_qdd(box1).leaf_avals == (core.typeof(val2),)

      return

    if jit:
      f = jax.jit(f)

    f(Box(val1))

  def test_jit_arg(self):
    @jax.jit
    def f(box, x):
      assert tracing_ok
      box.set(box.get() + x)

    tracing_ok = True
    box1 = Box(1.0)
    f(box1, 1.)
    self.assertAllClose(box1.get(), 2.0)

    tracing_ok = False
    box2 = Box(2.0)
    f(box2, 2.)
    self.assertAllClose(box2.get(), 4.0)

  def test_jit_arg2(self):
    # set without get

    @jax.jit
    def f(box, x):
      box_set(box, x)

    box = Box(0.0)
    f(box, 1.)
    self.assertAllClose(box_get(box), 1.0, check_dtypes=False)

  def test_jit_arg_in_pytree(self):
    @jax.jit
    def f(dct, x):
      assert tracing_ok
      box = dct['box']
      box.set(box.get() + x)

    tracing_ok = True
    box1 = Box(1.0)
    f({'box': box1, 'a': 1.0}, 1.)
    self.assertAllClose(box1.get(), 2.0)

    tracing_ok = False
    box2 = Box(2.0)
    f({'box': box2, 'a': 2.0}, 2.)
    self.assertAllClose(box2.get(), 4.0)

    tracing_ok = True
    box3 = Box(3)  # int, dtype changed
    f({'box': box3, 'a': 2.0}, 2.)
    self.assertAllClose(box3.get(), 5.0)

  def test_jit_closure(self):
    box = Box(1.0)

    @jax.jit
    def f(x):
      assert tracing_ok
      box.set(box.get() + x)

    tracing_ok = True
    f(2.0)
    self.assertAllClose(box.get(), 3.0)
    tracing_ok = False
    f(5.0)
    self.assertAllClose(box.get(), 8.0)

  def test_jit_closure_nested(self):
    box = Box(5.0)

    @jax.jit
    def f(x):
      box.set(box.get() + x)

    @jax.jit
    def g(x):
      f(x)

    g(3.0)
    self.assertAllClose(box.get(), 8.0)

  def test_jit_closure_nested2(self):
    @jax.jit
    def h(x):
      box = new_box()
      box.set(x)

      @jax.jit
      def k(x):
        box.set(box.get() + x)

      k(1.0)
      k(1.0)
      return box.get()

    ans = h(2.0)
    self.assertAllClose(ans, 4.0)

  def test_jit_closure_nested3(self):
    box = new_box()

    @jax.jit
    def h(x):
      box.set(x)

      @jax.jit
      def k(x):
        box.set(box.get() + x)

      k(1.0)
      k(1.0)
      return box.get()

    ans = h(2.0)
    self.assertAllClose(ans, 4.0)

  @parameterized.parameters([False, True])
  def test_jvp_closure_stop_gradient(self, jit):
    box = Box(1.0)

    def f(x):
      y = 2 * x
      box.set(box.get() + jax.lax.stop_gradient(y))
      return y

    if jit:
      f = jax.jit(f)

    y, y_dot = jax.jvp(f, (1.0,), (1.0,))
    self.assertAllClose(y, 2.0)
    self.assertAllClose(y_dot, 2.0)
    self.assertAllClose(box.get(), 3.0)

  @parameterized.parameters([False, True])
  def test_jvp_arg(self, jit):
    def f(box, x):
      box.set(box.get() + x)
      return x

    if jit:
      f = jax.jit(f)

    box = Box(5.0)
    box_dot = Box(1.0)
    y, y_dot = jax.jvp(f, (box, 2.), (box_dot, 1.))
    self.assertAllClose(y, 2.0)
    self.assertAllClose(y_dot, 1.0)
    self.assertAllClose(box.get(), 7.0)
    self.assertAllClose(box_dot.get(), 2.0)

  @parameterized.parameters([False, True])
  def test_custom_vjp_plumbing(self, jit):
    box = Box(0.0)

    @jax.custom_vjp
    def foo(x):
      return x
    def foo_fwd(x):
      return foo(x), None
    def foo_bwd(_, g):
      box.set(g)
      return g,
    foo.defvjp(foo_fwd, foo_bwd)

    def f(x):
      x = 2 * x
      x = foo(x)
      x = 2 * x
      return x

    if jit:
      f = jax.jit(f)

    jax.grad(f)(1.0)

    self.assertAllClose(box.get(), 2.0)

  # TODO(mattjj,dougalm): make this work...
  # @parameterized.parameters([False, True])
  # def test_custom_vjp_plumbing_abstracted(self, jit):
  #   box = Box(0.0)

  #   @jax.custom_vjp
  #   def foo(box, x):
  #     return x
  #   def foo_fwd(box, x):
  #     return x, box
  #   def foo_bwd(box, g):
  #     box.set(g)
  #     return None, g
  #   foo.defvjp(foo_fwd, foo_bwd)

  #   def f(box, x):
  #     x = 2 * x
  #     x = foo(box, x)
  #     x = 2 * x
  #     return x

  #   if jit:
  #     f = jax.jit(f)

  #   jax.grad(partial(f, box))(1.0)
  #   self.assertAllClose(box.get(), 2.0)

  @parameterized.parameters([False, True])
  def test_grad_closure_stop_gradient(self, jit):
    box = Box(0.0)

    def f(x):
      y = x * 2
      box.set(box.get() + jax.lax.stop_gradient(y))
      return y

    if jit:
      f = jax.jit(f)

    g = jax.grad(f)(1.0)
    self.assertAllClose(g, 2.0)
    self.assertAllClose(box.get(), 2.0)

  @unittest.skip('Need to figure out effects and scan')
  @parameterized.parameters([False, True])
  def test_scan_basic(self, jit):
    box = Box(1.0)

    def double_it_10():
      def body(_, __):
        box.set(box.get() * 2)
        return None, None
      _, _ = jax.lax.scan(body, None, None, length=10)

    if jit:
      double_it_10 = jax.jit(double_it_10)

    double_it_10()

    self.assertAllClose(box.get(), 1024., check_dtypes=False)

  # TODO error-checking tests from attrs_test.py

  ###

  def test_box_autodiff(self):
    if config.enable_x64.value: raise unittest.SkipTest("no x64")

    class StashTangents(HiPrimitive):
      def is_high(self):
        return True

      def abstract_eval(_, box_aval, x_aval):
        del box_aval
        return x_aval, {box_effect}

      def to_lojax(_, box, x):
        return x

      def jvp(_, primals, tangents):
        box, x = primals
        _, x_dot = tangents
        box_set(box, x_dot)
        return x, x_dot

      def transpose(self, *args):
        assert False  # TODO
    stash_tangents_p = StashTangents('stash_tangents')

    def stash_tangents(box, x):
      return stash_tangents_p.bind(box, x)

    @jax.jit
    def f(box, x):
      x = stash_tangents(box, x)
      return x

    box = Box(0.0)
    jax.jvp(partial(f, box), (3.,), (5.,))
    self.assertAllClose(box_get(box), 5.0, check_dtypes=False)

  def test_type_changing_box(self):
    box = Box(jnp.arange(1))
    box_set(box, jnp.arange(2))
    self.assertLen(box._val, 2)

    @jax.jit
    def f(box, x):
      box_set(box, x)

    f(box, jnp.arange(3))
    self.assertLen(box._val, 3)
    f(box, jnp.arange(4))
    self.assertLen(box._val, 4)

  def test_pytree_box(self):
    box = Box(None)

    @jax.jit
    def f(box, x):
      assert tracing_ok
      val = box_get(box)
      if val is None:
        box_set(box, x)
      else:
        box_set(box, [x, x])

    tracing_ok = True
    f(box, 1.0)
    self.assertAllClose(box_get(box), 1.0, check_dtypes=False)
    f(box, 2.0)
    self.assertAllClose(box_get(box), [2.0, 2.0], check_dtypes=False)
    f(box, 3.0)
    self.assertAllClose(box_get(box), [3.0, 3.0], check_dtypes=False)
    tracing_ok = False
    f(box, 4.0)
    self.assertAllClose(box_get(box), [4.0, 4.0], check_dtypes=False)

  def test_pytree_of_hijaxtypes_box(self):

    @dataclass(frozen=True)
    class MyArray:
      arr: jax.Array  # always f32

    @dataclass(frozen=True)
    class MyTy(HiType):
      has_qdd = False

      def to_tangent_aval(self):
        return MyTy()
      def str_short(self, short_dtypes=False):
        return 'MyTy'
      def lo_ty(self):
        return [core.ShapedArray((), jnp.dtype('float32'))]
      def lower_val(self, hi_val: MyArray) -> list[jax.Array]:
        return [hi_val.arr]
      def raise_val(self, val) -> MyArray:
        return MyArray(val)

      def __eq__(self, other): return isinstance(other, MyTy)

    core.pytype_aval_mappings[MyArray] = lambda _: MyTy()

    box = Box([MyArray(jnp.float32(1)),
               MyArray(jnp.float32(2))])

    @jax.jit
    def f(box):
      a, b = box_get(box)
      box_set(box, [b, a])

    f(box)
    val = box_get(box)
    self.assertIsInstance(val, list)
    self.assertLen(val, 2)
    b_, a_ = val
    self.assertIsInstance(a_, MyArray)
    self.assertIsInstance(b_, MyArray)
    self.assertAllClose(a_.arr, 1, check_dtypes=False)
    self.assertAllClose(b_.arr, 2, check_dtypes=False)


if __name__ == '__main__':
  absltest.main(testLoader=jtu.JaxTestLoader())
