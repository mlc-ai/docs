#!groovy
// -*- mode: groovy -*-

// Licensed to the Apache Software Foundation (ASF) under one
// or more contributor license agreements.  See the NOTICE file
// distributed with this work for additional information
// regarding copyright ownership.  The ASF licenses this file
// to you under the Apache License, Version 2.0 (the
// "License"); you may not use this file except in compliance
// with the License.  You may obtain a copy of the License at
//
//   http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing,
// software distributed under the License is distributed on an
// "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
// KIND, either express or implied.  See the License for the
// specific language governing permissions and limitations
// under the License.

// Jenkins pipeline
// See documents at https://jenkins.io/doc/book/pipeline/jenkinsfile/

// ============================= IMPORTANT NOTE =============================
// To keep things simple
// This file is manually updated to maintain unity branch specific builds.
// Please do not send this file to main


import org.jenkinsci.plugins.pipeline.modeldefinition.Utils

// NOTE: these lines are scanned by docker/dev_common.sh. Please update the regex as needed. -->
ci_lint = 'tlcpackstaging/ci_lint:20230504-142417-4d37a0a0'
ci_gpu = 'tlcpackstaging/ci_gpu:20230504-142417-4d37a0a0'
ci_cpu = 'tlcpackstaging/ci_cpu:20230513-200357-e54bbc73'
ci_wasm = 'tlcpack/ci-wasm:v0.72'
ci_i386 = 'tlcpack/ci-i386:v0.75'
ci_qemu = 'tlcpack/ci-qemu:v0.11'
ci_arm = 'tlcpack/ci-arm:v0.08'
ci_hexagon = 'tlcpackstaging/ci_hexagon:20230504-142417-4d37a0a0'
// <--- End of regex-scanned config.

// Parameters to allow overriding (in Jenkins UI), the images
// to be used by a given build. When provided, they take precedence
// over default values above.
properties([
  parameters([
    string(name: 'ci_lint_param', defaultValue: ''),
    string(name: 'ci_cpu_param',  defaultValue: ''),
    string(name: 'ci_gpu_param',  defaultValue: ''),
    string(name: 'ci_wasm_param', defaultValue: ''),
    string(name: 'ci_i386_param', defaultValue: ''),
    string(name: 'ci_qemu_param', defaultValue: ''),
    string(name: 'ci_arm_param',  defaultValue: ''),
    string(name: 'ci_hexagon_param', defaultValue: '')
  ])
])

// tvm libraries
tvm_runtime = 'build/libtvm_runtime.so, build/config.cmake'
tvm_lib = 'build/libtvm.so, ' + tvm_runtime
// LLVM upstream lib
tvm_multilib = 'build/libtvm.so, ' +
               'build/libvta_fsim.so, ' +
               tvm_runtime

tvm_multilib_tsim = 'build/libvta_tsim.so, ' +
               tvm_multilib

// command to start a docker container
docker_run = 'docker/bash.sh'
// timeout in minutes
max_time = 240

