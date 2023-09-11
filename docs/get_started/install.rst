.. _install:

Installing Apache TVM Unity
===========================

.. contents:: Table of Contents
    :local:
    :depth: 2

Option 1. Prebuilt Package
---------------------------------------
To help our community to use Apache TVM Unity, a nightly prebuilt developer package is provided by
`MLC community <https://github.com/mlc-ai>`_

Please visit the installation page for installation instructions: https://mlc.ai/package/.

Option 2. Build from Source
---------------------------
While it is generally recommended to always use the prebuilt TVM Unity, if you require more customization,
you may need to build it from source.

Step 1. Install Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TVM Unity requires the following dependencies:

- CMake (>= 3.24.0)
- LLVM (recommended >= 15)
- Git
- A recent C++ compiler supporting C++ 17, at the minimum
    - GCC 7.1
    - Clang 5.0
    - Apple Clang 9.3
    - Visual Studio 2019 (v16.7)
- Python (>= 3.8)
- (Optional) Conda (Strongly Recommended)


For Ubuntu/Debian users, the following APT Repository may help:

- CMake: https://apt.kitware.com
- LLVM: https://apt.llvm.org

Step 2. Get Source from Github
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
First, You can also choose to clone the source repo from Github. The code of Apache TVM Unity is hosted
under the `Apache TVM <https://github.com/apache/tvm>`_ but with a different ``unity`` branch.

.. code:: bash

    git clone https://github.com/apache/tvm -b unity tvm-unity --recursive


.. note::
    Need to use ``-b unity`` to checkout the ``unity`` branch. Or you can use ``git switch unity`` after
    cloning the repository.

.. note::
    It's important to use the ``--recursive`` flag when cloning the TVM Unity repository, which will
    automatically clone the submodules. If you forget to use this flag, you can manually clone the submodules
    by running ``git submodule update --init --recursive`` in the root directory of the TVM Unity repository.


Step 3. Configure and Build
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Create a build directory and run CMake to configure the build. The following example shows how to build

.. code:: bash

    cd tvm-unity
    rm -rf build && mkdir build && cd build
    # Specify the build configuration via CMake options
    cp ../cmake/config.cmake .

Then you can configure the build by running CMake:

.. code:: bash

    # controls default compilation flags (Candidates: Release, Debug, RelWithDebInfo)
    echo "set(CMAKE_BUILD_TYPE RelWithDebInfo)" >> config.cmake

    # LLVM is a must dependency
    echo "set(USE_LLVM \"llvm-config --ignore-libllvm --link-static\")" >> config.cmake
    echo "set(HIDE_PRIVATE_SYMBOLS ON)" >> config.cmake

    # GPU SDKs, turn on if needed
    echo "set(USE_CUDA   OFF)" >> config.cmake
    echo "set(USE_METAL  OFF)" >> config.cmake
    echo "set(USE_VULKAN OFF)" >> config.cmake
    echo "set(USE_OPENCL OFF)" >> config.cmake

    # cuBLAS, cuDNN, cutlass support, turn on if needed
    echo "set(USE_CUBLAS OFF)" >> config.cmake
    echo "set(USE_CUDNN  OFF)" >> config.cmake
    echo "set(USE_CUTLASS OFF)" >> config.cmake

.. note::

    ``HIDE_PRIVATE_SYMBOLS`` is a configuration option that enables the ``-fvisibility=hidden`` flag.
    This flag helps prevent potential symbol conflicts between TVM and PyTorch. These conflicts arise
    due to the frameworks shipping LLVMs of different versions.

Once config.cmake is edited accordingly, kick off build with the commands below:

.. code:: bash

    cmake .. && cmake --build . --parallel $(nproc)

A success build should produce ``libtvm`` and ``libtvm_runtime`` under ``build/`` directory.

.. tabs ::

    .. code-tab :: bash Install via environment variable

        export TVM_HOME=/path/to/tvm
        export PYTHONPATH=$TVM_HOME/python:$PYTHONPATH

    .. code-tab :: bash Install via pip local project

        cd /path-to-tvm-unity/python
        pip install -e .

Step 4. Validate Installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Please the following code to validate the TVM installation:

.. code:: bash

    python -c "import tvm; print(tvm.__file__)"

If the installation is successful, you should see the path to the TVM Python package printed out.

Also, please verify you installed the Unity versions

.. code:: bash

    python -c "import tvm.relax; print(\"OK\")"

If the installation is successful, you should see ``OK`` printed out.