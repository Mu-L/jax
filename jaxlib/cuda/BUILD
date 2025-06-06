# Copyright 2018 The JAX Authors.
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

# NVIDIA CUDA kernels

load("@rules_python//python:defs.bzl", "py_library")
load(
    "//jaxlib:jax.bzl",
    "cuda_library",
    "if_cuda_is_configured",
    "nanobind_extension",
)

licenses(["notice"])

package(
    default_applicable_licenses = [],
    default_visibility = ["//jax:internal"],
)

cc_library(
    name = "cuda_vendor",
    hdrs = [
        "//jaxlib/gpu:vendor.h",
    ],
    defines = ["JAX_GPU_CUDA=1"],
    visibility = ["//visibility:public"],
    deps = [
        "@local_config_cuda//cuda:cuda_headers",
        "@local_config_cuda//cuda:cudnn_header",
        "@xla//xla/tsl/cuda:cupti",
    ],
)

cc_library(
    name = "cuda_gpu_kernel_helpers",
    srcs = [
        "//jaxlib/gpu:gpu_kernel_helpers.cc",
    ],
    hdrs = [
        "//jaxlib/gpu:gpu_kernel_helpers.h",
    ],
    copts = [
        "-fexceptions",
    ],
    features = ["-use_header_modules"],
    deps = [
        ":cuda_vendor",
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/memory",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:str_format",
        "@local_config_cuda//cuda:cuda_headers",
        "@xla//xla/tsl/cuda:cupti",
        "@xla//xla/tsl/cuda:cusolver",
        "@xla//xla/tsl/cuda:cusparse",
    ],
)

cuda_library(
    name = "cuda_make_batch_pointers",
    srcs = ["//jaxlib/gpu:make_batch_pointers.cu.cc"],
    hdrs = ["//jaxlib/gpu:make_batch_pointers.h"],
    deps = [
        ":cuda_vendor",
        "@local_config_cuda//cuda:cuda_headers",
    ],
)

cc_library(
    name = "cuda_blas_handle_pool",
    srcs = ["//jaxlib/gpu:blas_handle_pool.cc"],
    hdrs = ["//jaxlib/gpu:blas_handle_pool.h"],
    deps = [
        ":cuda_gpu_kernel_helpers",
        ":cuda_vendor",
        "//jaxlib/gpu:handle_pool",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/synchronization",
        "@local_config_cuda//cuda:cuda_headers",
        "@xla//xla/tsl/cuda:cublas",
        "@xla//xla/tsl/cuda:cudart",
    ],
)

cc_library(
    name = "cudnn_rnn_kernels",
    srcs = ["//jaxlib/gpu:rnn_kernels.cc"],
    hdrs = ["//jaxlib/gpu:rnn_kernels.h"],
    deps = [
        ":cuda_gpu_kernel_helpers",
        ":cuda_vendor",
        ":ffi_wrapper",
        "//jaxlib:kernel_helpers",
        "//jaxlib/gpu:handle_pool",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings:str_format",
        "@com_google_absl//absl/synchronization",
        "@local_config_cuda//cuda:cuda_headers",
        "@xla//xla/ffi/api:ffi",
        "@xla//xla/tsl/cuda:cudart",
        "@xla//xla/tsl/cuda:cudnn",
    ],
)

nanobind_extension(
    name = "_rnn",
    srcs = ["//jaxlib/gpu:rnn.cc"],
    copts = [
        "-fexceptions",
        "-fno-strict-aliasing",
    ],
    features = ["-use_header_modules"],
    module_name = "_rnn",
    deps = [
        ":cuda_vendor",
        ":cudnn_rnn_kernels",
        "//jaxlib:absl_status_casters",
        "//jaxlib:kernel_nanobind_helpers",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/strings:str_format",
        "@nanobind",
    ],
)

cc_library(
    name = "cuda_solver_handle_pool",
    srcs = ["//jaxlib/gpu:solver_handle_pool.cc"],
    hdrs = ["//jaxlib/gpu:solver_handle_pool.h"],
    deps = [
        ":cuda_gpu_kernel_helpers",
        ":cuda_vendor",
        "//jaxlib/gpu:handle_pool",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/synchronization",
        "@local_config_cuda//cuda:cuda_headers",
        "@xla//xla/tsl/cuda:cudart",
        "@xla//xla/tsl/cuda:cusolver",
    ],
)

cc_library(
    name = "cusolver_interface",
    srcs = ["//jaxlib/gpu:solver_interface.cc"],
    hdrs = ["//jaxlib/gpu:solver_interface.h"],
    deps = [
        ":cuda_gpu_kernel_helpers",
        ":cuda_vendor",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings:str_format",
        "@local_config_cuda//cuda:cuda_headers",
        "@xla//xla/tsl/cuda:cublas",
        "@xla//xla/tsl/cuda:cudart",
        "@xla//xla/tsl/cuda:cusolver",
    ],
)

cc_library(
    name = "cusolver_kernels_ffi",
    srcs = ["//jaxlib/gpu:solver_kernels_ffi.cc"],
    hdrs = ["//jaxlib/gpu:solver_kernels_ffi.h"],
    deps = [
        ":cuda_blas_handle_pool",
        ":cuda_gpu_kernel_helpers",
        ":cuda_make_batch_pointers",
        ":cuda_solver_handle_pool",
        ":cuda_vendor",
        ":cusolver_interface",
        "//jaxlib:ffi_helpers",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings:str_format",
        "@local_config_cuda//cuda:cuda_headers",
        "@xla//xla/ffi/api:ffi",
        "@xla//xla/tsl/cuda:cublas",
        "@xla//xla/tsl/cuda:cudart",
        "@xla//xla/tsl/cuda:cusolver",
    ],
)

nanobind_extension(
    name = "_solver",
    srcs = ["//jaxlib/gpu:solver.cc"],
    copts = [
        "-fexceptions",
        "-fno-strict-aliasing",
    ],
    features = ["-use_header_modules"],
    module_name = "_solver",
    deps = [
        ":cuda_vendor",
        ":cusolver_kernels_ffi",
        "//jaxlib:kernel_nanobind_helpers",
        "@local_config_cuda//cuda:cuda_headers",
        "@nanobind",
        "@xla//xla/tsl/cuda:cublas",
        "@xla//xla/tsl/cuda:cudart",
        "@xla//xla/tsl/cuda:cusolver",
    ],
)

cc_library(
    name = "ffi_wrapper",
    hdrs = ["//jaxlib/gpu:ffi_wrapper.h"],
    deps = [
        ":cuda_vendor",
        "//jaxlib:ffi_helpers",
        "@xla//xla/ffi/api:ffi",
    ],
)

cc_library(
    name = "cusparse_kernels",
    srcs = ["//jaxlib/gpu:sparse_kernels.cc"],
    hdrs = ["//jaxlib/gpu:sparse_kernels.h"],
    deps = [
        ":cuda_gpu_kernel_helpers",
        ":cuda_vendor",
        ":ffi_wrapper",
        "//jaxlib:ffi_helpers",
        "//jaxlib:kernel_helpers",
        "//jaxlib/gpu:handle_pool",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:str_format",
        "@com_google_absl//absl/synchronization",
        "@local_config_cuda//cuda:cuda_headers",
        "@xla//xla/ffi/api:ffi",
        "@xla//xla/tsl/cuda:cudart",
        "@xla//xla/tsl/cuda:cusparse",
    ],
)

nanobind_extension(
    name = "_sparse",
    srcs = ["//jaxlib/gpu:sparse.cc"],
    copts = [
        "-fexceptions",
        "-fno-strict-aliasing",
    ],
    features = ["-use_header_modules"],
    module_name = "_sparse",
    deps = [
        ":cuda_gpu_kernel_helpers",
        ":cuda_vendor",
        ":cusparse_kernels",
        "//jaxlib:absl_status_casters",
        "//jaxlib:kernel_nanobind_helpers",
        "@com_google_absl//absl/algorithm:container",
        "@com_google_absl//absl/base",
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/hash",
        "@com_google_absl//absl/memory",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:str_format",
        "@com_google_absl//absl/synchronization",
        "@local_config_cuda//cuda:cuda_headers",
        "@nanobind",
        "@xla//xla/tsl/cuda:cudart",
        "@xla//xla/tsl/cuda:cusparse",
        "@xla//xla/tsl/python/lib/core:numpy",
    ],
)

cc_library(
    name = "cuda_linalg_kernels",
    srcs = [
        "//jaxlib/gpu:linalg_kernels.cc",
    ],
    hdrs = ["//jaxlib/gpu:linalg_kernels.h"],
    features = ["-use_header_modules"],
    deps = [
        ":cuda_blas_handle_pool",
        ":cuda_gpu_kernel_helpers",
        ":cuda_linalg_kernels_impl",
        ":cuda_vendor",
        "//jaxlib:ffi_helpers",
        "//jaxlib:kernel_helpers",
        "@com_google_absl//absl/strings:str_format",
        "@local_config_cuda//cuda:cuda_headers",
        "@xla//xla/ffi/api:ffi",
    ],
)

cuda_library(
    name = "cuda_linalg_kernels_impl",
    srcs = ["//jaxlib/gpu:linalg_kernels.cu.cc"],
    hdrs = ["//jaxlib/gpu:linalg_kernels.h"],
    deps = [
        ":cuda_gpu_kernel_helpers",
        ":cuda_vendor",
        "@local_config_cuda//cuda:cuda_headers",
        "@xla//xla/ffi/api:ffi",
    ],
)

nanobind_extension(
    name = "_linalg",
    srcs = ["//jaxlib/gpu:linalg.cc"],
    copts = [
        "-fexceptions",
        "-fno-strict-aliasing",
    ],
    features = ["-use_header_modules"],
    module_name = "_linalg",
    deps = [
        ":cuda_gpu_kernel_helpers",
        ":cuda_linalg_kernels",
        ":cuda_vendor",
        "//jaxlib:kernel_nanobind_helpers",
        "@local_config_cuda//cuda:cuda_headers",
        "@nanobind",
        "@xla//xla/tsl/cuda:cudart",
    ],
)

cc_library(
    name = "cuda_prng_kernels",
    srcs = [
        "//jaxlib/gpu:prng_kernels.cc",
    ],
    hdrs = ["//jaxlib/gpu:prng_kernels.h"],
    deps = [
        ":cuda_gpu_kernel_helpers",
        ":cuda_prng_kernels_impl",
        ":cuda_vendor",
        "//jaxlib:ffi_helpers",
        "//jaxlib:kernel_helpers",
        "@com_google_absl//absl/algorithm:container",
        "@com_google_absl//absl/status",
        "@local_config_cuda//cuda:cuda_headers",
        "@xla//xla/ffi/api:c_api",
        "@xla//xla/ffi/api:ffi",
    ],
)

cuda_library(
    name = "cuda_prng_kernels_impl",
    srcs = [
        "//jaxlib/gpu:prng_kernels.cu.cc",
    ],
    hdrs = ["//jaxlib/gpu:prng_kernels.h"],
    deps = [
        ":cuda_gpu_kernel_helpers",
        ":cuda_vendor",
        "//jaxlib:kernel_helpers",
        "@local_config_cuda//cuda:cuda_headers",
        "@xla//xla/ffi/api:ffi",
    ],
)

nanobind_extension(
    name = "_prng",
    srcs = ["//jaxlib/gpu:prng.cc"],
    copts = [
        "-fexceptions",
        "-fno-strict-aliasing",
    ],
    features = ["-use_header_modules"],
    module_name = "_prng",
    deps = [
        ":cuda_gpu_kernel_helpers",
        ":cuda_prng_kernels",
        ":cuda_vendor",
        "//jaxlib:kernel_nanobind_helpers",
        "@local_config_cuda//cuda:cuda_headers",
        "@nanobind",
        "@xla//xla/tsl/cuda:cudart",
    ],
)

cc_library(
    name = "cuda_hybrid_kernels",
    srcs = ["//jaxlib/gpu:hybrid_kernels.cc"],
    hdrs = ["//jaxlib/gpu:hybrid_kernels.h"],
    deps = [
        ":cuda_gpu_kernel_helpers",
        ":cuda_vendor",
        "//jaxlib:ffi_helpers",
        "//jaxlib/cpu:lapack_kernels",
        "@com_google_absl//absl/algorithm:container",
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings:str_format",
        "@com_google_absl//absl/synchronization",
        "@com_google_absl//absl/types:span",
        "@xla//xla/ffi/api:ffi",
    ],
)

nanobind_extension(
    name = "_hybrid",
    srcs = ["//jaxlib/gpu:hybrid.cc"],
    copts = [
        "-fexceptions",
        "-fno-strict-aliasing",
    ],
    features = ["-use_header_modules"],
    module_name = "_hybrid",
    deps = [
        ":cuda_gpu_kernel_helpers",
        ":cuda_hybrid_kernels",
        ":cuda_vendor",
        "//jaxlib:kernel_nanobind_helpers",
        "//jaxlib/cpu:lapack_kernels",
        "@com_google_absl//absl/base",
        "@local_config_cuda//cuda:cuda_headers",
        "@nanobind",
        "@xla//xla/ffi/api:ffi",
        "@xla//xla/tsl/cuda:cudart",
    ],
)

cc_library(
    name = "cuda_gpu_kernels",
    srcs = ["//jaxlib/gpu:gpu_kernels.cc"],
    visibility = ["//visibility:public"],
    deps = [
        ":cuda_linalg_kernels",
        ":cuda_prng_kernels",
        ":cuda_vendor",
        ":cudnn_rnn_kernels",
        ":cusolver_kernels_ffi",
        ":cusparse_kernels",
        ":triton_kernels",
        "//jaxlib/mosaic/gpu:mosaic_gpu_support",
        "@xla//xla/ffi/api:c_api",
        "@xla//xla/ffi/api:ffi",
        "@xla//xla/service:custom_call_target_registry",
    ],
    alwayslink = 1,
)

cc_library(
    name = "triton_kernels",
    srcs = ["//jaxlib/gpu:triton_kernels.cc"],
    hdrs = ["//jaxlib/gpu:triton_kernels.h"],
    deps = [
        ":cuda_gpu_kernel_helpers",
        ":cuda_vendor",
        ":triton_utils",
        "//jaxlib/gpu:triton_cc_proto",
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/cleanup",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/container:flat_hash_set",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings:str_format",
        "@com_google_absl//absl/strings:string_view",
        "@com_google_absl//absl/synchronization",
        "@xla//xla/service:custom_call_status",
        "@xla//xla/stream_executor/cuda:cuda_asm_compiler",
        "@xla//xla/tsl/cuda:cudart",
    ],
)

cc_library(
    name = "triton_utils",
    srcs = ["//jaxlib/gpu:triton_utils.cc"],
    hdrs = ["//jaxlib/gpu:triton_utils.h"],
    visibility = ["//visibility:public"],
    deps = [
        ":cuda_gpu_kernel_helpers",
        ":cuda_vendor",
        "//jaxlib/gpu:triton_cc_proto",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@zlib",
    ],
)

nanobind_extension(
    name = "_triton",
    srcs = ["//jaxlib/gpu:triton.cc"],
    copts = [
        "-fexceptions",
        "-fno-strict-aliasing",
    ],
    features = ["-use_header_modules"],
    module_name = "_triton",
    deps = [
        ":cuda_gpu_kernel_helpers",
        ":cuda_vendor",
        ":triton_kernels",
        ":triton_utils",
        "//jaxlib:absl_status_casters",
        "//jaxlib:kernel_nanobind_helpers",
        "//jaxlib/gpu:triton_cc_proto",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings:string_view",
        "@nanobind",
    ],
)

cc_library(
    name = "versions_helpers",
    srcs = ["versions_helpers.cc"],
    hdrs = ["versions_helpers.h"],
    copts = [
        "-fexceptions",
        "-fno-strict-aliasing",
    ],
    features = ["-use_header_modules"],
    deps = [
        ":cuda_gpu_kernel_helpers",
        ":cuda_vendor",
        "@com_google_absl//absl/base:dynamic_annotations",
        "@xla//xla/tsl/cuda:cublas",
        "@xla//xla/tsl/cuda:cudart",
        "@xla//xla/tsl/cuda:cudnn",
        "@xla//xla/tsl/cuda:cufft",
        "@xla//xla/tsl/cuda:cupti",
        "@xla//xla/tsl/cuda:cusolver",
        "@xla//xla/tsl/cuda:cusparse",
    ],
)

nanobind_extension(
    name = "_versions",
    srcs = ["versions.cc"],
    copts = [
        "-fexceptions",
        "-fno-strict-aliasing",
    ],
    features = ["-use_header_modules"],
    module_name = "_versions",
    deps = [
        ":cuda_gpu_kernel_helpers",
        ":cuda_vendor",
        ":versions_helpers",
        "//jaxlib:absl_status_casters",
        "//jaxlib:kernel_nanobind_helpers",
        "@com_google_absl//absl/status:statusor",
        "@nanobind",
        "@xla//xla/tsl/cuda:cublas",
        "@xla//xla/tsl/cuda:cudart",
        "@xla//xla/tsl/cuda:cudnn",
        "@xla//xla/tsl/cuda:cufft",
        "@xla//xla/tsl/cuda:cupti",
        "@xla//xla/tsl/cuda:cusolver",
        "@xla//xla/tsl/cuda:cusparse",
    ],
)

py_library(
    name = "cuda_gpu_support",
    deps = [
        ":_hybrid",
        ":_linalg",
        ":_prng",
        ":_rnn",
        ":_solver",
        ":_sparse",
        ":_triton",
        ":_versions",
        "//jaxlib/mosaic/gpu:mosaic_gpu",
    ],
)

cc_library(
    name = "py_client_gpu",
    srcs = ["//jaxlib/gpu:py_client_gpu.cc"],
    hdrs = ["//jaxlib/gpu:py_client_gpu.h"],
    copts = [
        "-fexceptions",
        "-fno-strict-aliasing",
    ],
    features = ["-use_header_modules"],
    deps = [
        ":cuda_vendor",
        "//jaxlib:ffi",
        "@com_google_absl//absl/algorithm:container",
        "@com_google_absl//absl/base",
        "@com_google_absl//absl/container:inlined_vector",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:str_format",
        "@com_google_absl//absl/strings:string_view",
        "@com_google_absl//absl/types:span",
        "@dlpack",
        "@nanobind",
        "@xla//third_party/python_runtime:headers",  # buildcleaner: keep
        "@xla//xla:comparison_util",
        "@xla//xla:shape_util",
        "@xla//xla:util",
        "@xla//xla:xla_data_proto_cc",
        "@xla//xla/ffi:ffi_api",
        "@xla//xla/ffi/api:ffi",
        "@xla//xla/pjrt:host_callback",
        "@xla//xla/pjrt:transpose",
        "@xla//xla/python:nb_numpy",
        "@xla//xla/python:types",
        "@xla//xla/service:platform_util",
    ],
)

nanobind_extension(
    name = "cuda_plugin_extension",
    srcs = ["cuda_plugin_extension.cc"],
    module_name = "cuda_plugin_extension",
    deps = [
        ":py_client_gpu",
        "//jaxlib:kernel_nanobind_helpers",
        "//jaxlib/gpu:gpu_plugin_extension",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
        "@local_config_cuda//cuda:cuda_headers",
        "@nanobind",
        "@xla//xla/pjrt:status_casters",
        "@xla//xla/tsl/cuda:cublas",
        "@xla//xla/tsl/cuda:cudart",
    ],
)

# We cannot nest select and if_cuda_is_configured so we introduce
# a standalone py_library target.
py_library(
    name = "gpu_only_test_deps",
    # `if_cuda_is_configured` will default to `[]`.
    deps = if_cuda_is_configured([
        ":cuda_gpu_support",
        ":cuda_plugin_extension",
    ]),
)
