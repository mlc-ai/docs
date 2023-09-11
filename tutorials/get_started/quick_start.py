# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""
.. _quick_start:

Quick Start
===========
**Authors**:
`Siyuan Feng <https://github.com/hzfengsy>`_

This tutorial is for people who are new to Apache TVM Unity. Taking an simple example
to show how to use Apache TVM Unity to compile a simple neural network.
"""

################################################################################
# Prepare the Neural Network Model
# --------------------------------
# Before we get started, let's prepare a neural network model first.
# In this tutorial, to make things simple, we will defined a two-layer MLP networks
# directly in this script. For people who are trying to run real models, please jump
# to the next section.
#

import torch
from torch import nn


class MLPModel(nn.Module):
    def __init__(self):
        super(MLPModel, self).__init__()
        self.fc1 = nn.Linear(784, 256)
        self.relu1 = nn.ReLU()
        self.fc2 = nn.Linear(256, 10)

    def forward(self, x):
        x = self.fc1(x)
        x = self.relu1(x)
        x = self.fc2(x)
        return x


torch_model = MLPModel()

################################################################################
# Import Model into Apache TVM Unity
# ------------------------------------------
# We choose `PyTorch FX <https://pytorch.org/docs/stable/fx.html>`_ as our frontend.
# PyTorch FX is a toolkit for tracing PyTorch programs into a intermediate
# representation (IR) with symbolic shape support.
#
# .. note::
#     Original PyTorch FX may not be compatible with HuggingFace Model. Please use
#     `HuggingFace self-defined FX <https://huggingface.co/docs/optimum/torch_fx/overview>`_
#     to trace the model.

from tvm import relax
from tvm.relax.frontend.torch import from_fx
from torch import fx

torch_fx_model = fx.symbolic_trace(torch_model)

################################################################################
# As the PyTorch model does not contain input information like in ONNX, we need
# to provide the input information ourselves. This includes the shape and data
# type of the input tensors, which are represented as a list of tuples.
# Each tuple contains the shape and data type of one input tensor.
#
# In this particular example, the shape of the input tensor is ``(1, 784)`` and
# the data type is ``"float32"``. We combine the shape and data type in a tuple
# like ``((1, 784), "float32")``. Then we gather all the input tuples into a list,
# which looks like ``[((1, 784), "float32")]``.

input_info = [((1, 784), "float32")]

################################################################################
# Use the Apache TVM Unity API to convert the PyTorch FX model into Relax Model.
# And print it out to in the TVMScript Syntax

with torch.no_grad():
    mod = from_fx(torch_fx_model, input_info)
mod.show()

################################################################################
# Up to this point, we have successfully transformed the PyTorch FX model into a
# TVM IRModule. It is important to mention that the IRModule is the central
# abstraction of Apache TVM Unity, and it is utilized for subsequent transformations
# and optimization processes. The IRModule has the ability to hold both high-level
# graph IR (Relax) and low-level tensor IR (TensorIR). Currently, the IRModule
# solely consists of Relax functions, which are marked with the `@R.function`
# decorator.

################################################################################
# Transform The Model
# -------------------
# Apply Optimization Transforms
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# We can apply a variety of optimization transforms to the IRModule. We have predefined
# a set of optimization transforms to simplify their usage. By using the `get_pipeline`
# function, we can apply the default optimization flow. By following the default path,
# the following transformations will be applied in order:
#
# - **LegalizeOps**: This transform converts the Relax operators into `call_tir` functions
#   with the corresponding TensorIR Functions. After this transform, the IRModule will
#   contain both Relax functions and TensorIR functions.
# - **AnnotateTIROpPattern**: This transform annotates the pattern of the TensorIR functions,
#   preparing them for subsequent operator fusion.
# - **FoldConstant**: This pass performs constant folding, optimizing operations
#   involving constants.
# - **FuseOps and FuseTIR**: These two passes work together to fuse operators based on the
#   patterns annotated in the previous step (AnnotateTIROpPattern). These passes transform
#   both Relax functions and TensorIR functions.

mod = relax.get_pipeline()(mod)
mod.show()

################################################################################
# If you are only interested in the changes of the Relax functions and omit the
# TensorIR functions, print the ``main`` function of the IRModule.

mod["main"].show()

################################################################################
# Tensor Function Optimization
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Usually we apply Tensor Function Optimization after the Relax Function Optimization,
# as graph transformations will changes the TIR functions.
# There are different ways to apply Tensor Function Optimization, we choose ``DLight`` on
# ``cuda`` target in this tutorial. Note that ``DLight`` is not the only way to optimize
# the Tensor Function, for other optimizations, please refer to corresponding tutorials.
#

import tvm
from tvm import dlight as dl

target = tvm.target.Target("cuda")

with target:
    mod = dl.ApplyDefaultSchedule(
        dl.gpu.Matmul(),
        dl.gpu.GEMV(),
        dl.gpu.Reduction(),
        dl.gpu.GeneralReduction(),
        dl.gpu.Fallback(),
    )(mod)
mod.show()

################################################################################
# .. note::
#     The ``DLight`` framework is still under development, and currently only supports
#     GPU backends with limited operators, to be specific, common operators used in LLMs.
#     We would improve the framework in the future to support more operators and backends.
#

################################################################################
# Compile and Run
# ---------------
# After the optimization, we can compile the model into a TVM runtime module.
# Apache TVM Unity use Relax Virtual Machine to run the model. The following code
# shows how to compile the model

exec = relax.build(mod, target=target)
dev = tvm.device(str(target.kind), 0)
vm = relax.VirtualMachine(exec, dev)

################################################################################
# Now we can run the model on the TVM runtime module. We first prepare the input
# data and then invoke the TVM runtime module to get the output.

import numpy as np

data = np.random.rand(1, 784).astype("float32")
vm.set_input("main", data)
vm.invoke_stateful("main")
tvm_out = vm.get_outputs("main").numpy()

################################################################################
# We can also compare the output with the PyTorch model to verify the correctness.

with torch.no_grad():
    torch_out = torch_model(torch.Tensor(data)).numpy()

np.testing.assert_allclose(tvm_out, torch_out, rtol=1e-5, atol=1e-5)

################################################################################
# Relax VM supports timing evaluation. We can use the following code to get the
# timing result.

timing_res = vm.time_evaluator("invoke_stateful", dev)("main")
print(timing_res)
