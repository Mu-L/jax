# Copyright 2023 The JAX Authors.
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

# Package for Mosaic-specific Pallas extensions

load("@rules_python//python:defs.bzl", "py_library")
load("//jaxlib:jax.bzl", "py_deps", "pytype_strict_library")

package(
    default_applicable_licenses = [],
    default_visibility = [
        "//jax:internal",
    ],
)

py_library(
    name = "core",
    srcs = [
        "__init__.py",
        "core.py",
    ],
    deps = [
        "//jax",
        "//jax/_src/pallas",
    ],
)

py_library(
    name = "verification",
    srcs = ["verification.py"],
    deps = [
        "//jax",
        "//jax:mlir",
        "//jax/_src/lib",
    ],
)

py_library(
    name = "error_handling",
    srcs = ["error_handling.py"],
    deps = [
        "//jax:compiler",
        "//jax:traceback_util",
        "//jax/_src/lib",
    ],
)

py_library(
    name = "primitives",
    srcs = ["primitives.py"],
    deps = [
        ":core",
        "//jax",
        "//jax:core",
        "//jax:dtypes",
        "//jax:mlir",
        "//jax:pretty_printer",
        "//jax:tree_util",
        "//jax:typing",
        "//jax:util",
        "//jax/_src/pallas",
    ],
)

py_library(
    name = "pallas_call_registration",
    srcs = ["pallas_call_registration.py"],
    deps = [
        ":core",
        ":lowering",
        ":verification",
        "//jax",
        "//jax:config",
        "//jax:core",
        "//jax:mlir",
        "//jax:sharding_impls",
        "//jax:source_info_util",
        "//jax:tpu_custom_call",
        "//jax/_src/lib",
        "//jax/_src/pallas",
        "//jax/experimental:mosaic",
    ] + py_deps("numpy"),
)

pytype_strict_library(
    name = "lowering",
    srcs = ["lowering.py"],
    deps = [
        ":core",
        ":error_handling",
        ":primitives",
        ":random",
        "//jax",
        "//jax:ad_util",
        "//jax:api",
        "//jax:checkify",
        "//jax:cloud_tpu_init",
        "//jax:core",
        "//jax:custom_derivatives",
        "//jax:debugging",
        "//jax:dtypes",
        "//jax:export",
        "//jax:lax",
        "//jax:mesh",
        "//jax:mlir",
        "//jax:partial_eval",
        "//jax:random",
        "//jax:source_info_util",
        "//jax:traceback_util",
        "//jax:typing",
        "//jax:util",
        "//jax:xla",
        "//jax:xla_bridge",
        "//jax/_src/lib",
        "//jax/_src/pallas",
        "//jax/experimental:mosaic",
    ] + py_deps("numpy"),
)

py_library(
    name = "pipeline",
    srcs = ["pipeline.py"],
    deps = [
        ":core",
        ":primitives",
        "//jax",
        "//jax:api_util",
        "//jax:util",
        "//jax/_src/pallas",
        "//jax/experimental:pallas",
        "//jax/extend:backend",
    ] + py_deps("numpy"),
)

py_library(
    name = "random",
    srcs = ["random.py"],
    deps = [
        ":primitives",
        "//jax",
        "//jax:blocked_sampler",
        "//jax:typing",
    ] + py_deps("numpy"),
)

py_library(
    name = "helpers",
    srcs = ["helpers.py"],
    deps = [
        ":core",
        ":primitives",
        "//jax",
        "//jax/_src/pallas",
    ],
)

py_library(
    name = "interpret",
    srcs = ["interpret.py"],
    deps = [
        ":core",
        ":primitives",
        ":verification",
        "//jax",
        "//jax:core",
        "//jax:source_info_util",
        "//jax:util",
        "//jax/_src/lib",
        "//jax/_src/pallas",
    ] + py_deps("numpy"),
)
