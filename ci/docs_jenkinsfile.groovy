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
ci_gpu = 'tlcpackstaging/ci_gpu:20240428-060115-0b09ed018'
// <--- End of regex-scanned config.

// Parameters to allow overriding (in Jenkins UI), the images
// to be used by a given build. When provided, they take precedence
// over default values above.
properties([
  parameters([
    string(name: 'ci_gpu_param',  defaultValue: ''),
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

stage('Prepare') {
  node('CPU-SMALL') {
    // When something is provided in ci_*_param, use it, otherwise default with ci_*
    ci_gpu = params.ci_gpu_param ?: ci_gpu

    sh (script: """
      echo "Docker images being used in this build:"
      echo " ci_gpu  = ${ci_gpu}"
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
        if (env.BRANCH_NAME == 'main') {
            withCredentials([string(
              credentialsId: 'MLC_ACCESS_TOKEN',
              variable: 'GITHUB_TOKEN',
            )]) {
              sh (script: 'if [ ! -d docs-site ]; then git clone https://$GITHUB_TOKEN@github.com/mlc-ai/docs docs-site; fi')
              sh (script: 'python ci/update_site.py --site-path docs-site --source-path _build/html', label: 'Depoly')
            }
        }
      }
    }
  }
}
