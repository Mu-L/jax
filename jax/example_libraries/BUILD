# Copyright 2025 The JAX Authors.
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

load("//jaxlib:jax.bzl", "py_deps", "pytype_strict_library")

package(
    default_applicable_licenses = [],
    default_visibility = ["//jax:internal"],
)

pytype_strict_library(
    name = "stax",
    srcs = [
        "stax.py",
    ],
    visibility = ["//visibility:public"],
    deps = ["//jax"],
)

pytype_strict_library(
    name = "optimizers",
    srcs = [
        "optimizers.py",
    ],
    visibility = ["//visibility:public"],
    deps = [
        "//jax",
        "//jax/_src:util",
    ] + py_deps("numpy"),
)

# TODO(dsuo): Remove this filegroup once experimental aliases from jax/BUILD are
# removed.
filegroup(
    name = "jax_example_libraries",
    srcs = glob(["*.py"]),
    visibility = ["//jax:internal"],
)
