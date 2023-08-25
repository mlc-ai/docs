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

// command to start a docker container
docker_run = 'ci/docker_bash.sh'
// timeout in minutes
max_time = 30

def per_exec_ws(folder) {
  return "workspace/exec_${env.EXECUTOR_NUMBER}/" + folder
}

// initialize source codes
def init_git() {
  checkout scm
  // Add more info about job node
  sh (
   script: "echo NODE_NAME=${env.NODE_NAME}",
   label: 'Show executor node info',
  )
  retry(5) {
    timeout(time: 2, unit: 'MINUTES') {
      sh (script: 'git submodule update --init --recursive -f', label: 'Update git submodules')
    }
  }
}


def deploy() {
  withCredentials([string(
    credentialsId: 'MLC_ACCESS_TOKEN',
    variable: 'GITHUB_TOKEN',
  )]) {
    sh ("git remote remove origin")
    sh ("git remote add origin https://$GITHUB_TOKEN@github.com/mlc-ai/docs")
    sh ("git config user.name mlc-bot")
    sh ("git config user.email 106439794+mlc-bot@users.noreply.github.com")
    sh ("git config --get user.name")
    sh ("python ci/update_site.py --site-path docs-gh-pages --source-path _build/html")
  }
}

stage('Prepare') {
  node('CPU-SMALL') {
    // When something is provided in ci_*_param, use it, otherwise default with ci_*
    ci_lint = params.ci_lint_param ?: ci_lint
    ci_cpu = params.ci_cpu_param ?: ci_cpu
    ci_gpu = params.ci_gpu_param ?: ci_gpu
    ci_wasm = params.ci_wasm_param ?: ci_wasm
    ci_i386 = params.ci_i386_param ?: ci_i386
    ci_qemu = params.ci_qemu_param ?: ci_qemu
    ci_arm = params.ci_arm_param ?: ci_arm
    ci_hexagon = params.ci_hexagon_param ?: ci_hexagon

    sh (script: """
      echo "Docker images being used in this build:"
      echo " ci_lint = ${ci_lint}"
      echo " ci_cpu  = ${ci_cpu}"
      echo " ci_gpu  = ${ci_gpu}"
      echo " ci_wasm = ${ci_wasm}"
      echo " ci_i386 = ${ci_i386}"
      echo " ci_qemu = ${ci_qemu}"
      echo " ci_arm  = ${ci_arm}"
      echo " ci_hexagon  = ${ci_hexagon}"
    """, label: 'Docker image names')
  }
}

stage('Build') {
  timeout(time: max_time, unit: 'MINUTES') {
    node('GPU') {
      ws(per_exec_ws('mlc-docs/build')) {
        init_git()
        sh (script: "${docker_run} ${ci_gpu} nvidia-smi", label: 'Check GPU info')
        sh (script: "${docker_run} ${ci_gpu} ./ci/build_docs.sh", label: 'Build docs')
        if (env.BRANCH_NAME == 'main' || env.BRANCH_NAME == 'PR-4') {
          deploy()
        }
      }
    }
  }
}
