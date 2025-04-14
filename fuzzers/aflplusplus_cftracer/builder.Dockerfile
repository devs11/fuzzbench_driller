# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# FROM base-image-jammy

ARG parent_image
FROM $parent_image

# Install the necessary packages.
RUN apt-get update && \
    apt-get install -y \
        build-essential \
        git \
        flex \
        bison \
        libglib2.0-dev \
        libpixman-1-dev \
        ninja-build \
        libstdc++-$(gcc --version|head -n1|sed 's/\..*//'|sed 's/.* //')-dev


# Download afl++
RUN git clone https://github.com/AFLplusplus/AFLplusplus.git /afl && \
    cd /afl && git checkout 56d5aa3101945e81519a3fac8783d0d8fad82779 || true
    
# Build afl++ without Python support as we don't need it.
# Set AFL_NO_X86 to skip flaky tests.
RUN cd /afl && \
    unset CFLAGS && unset CXXFLAGS && \
    AFL_NO_X86=1 CC=clang PYTHON_INCLUDE=/ make && \
    cd qemu_mode && ./build_qemu_support.sh && cd .. && \
    make -C utils/aflpp_driver && \
    cp utils/aflpp_driver/libAFLQemuDriver.a /libAFLDriver.a && \
    cp utils/aflpp_driver/aflpp_qemu_driver_hook.so /

# fetch CFTracer for fuzzbench
RUN git clone -b fuzzbench https://git.breadslice.de/sim/cftracer.git && \
    cd cftracer && \
    # git checkout TODO-tag || true
    pip install -r requirements.txt

# install SymQEMU (template from https://github.com/eurecom-s3/symqemu/blob/master/Dockerfile)

RUN apt update && apt install -y \
    ninja-build \
    libglib2.0-dev \
    llvm \
    git \
    python3 \
    python3-pip \
    cmake \
    wget \
    lsb-release \
    software-properties-common \
    gnupg \
    z3 \
    libz3-dev \
    libz3-dev \
    libzstd-dev \
    colordiff \
    xxd \
    wdiff

RUN pip install --user meson tomli
ARG LLVM_VERSION=15
RUN apt install -y llvm-${LLVM_VERSION} clang-${LLVM_VERSION}

RUN git clone -b master https://github.com/eurecom-s3/symqemu.git && \
    cd symqemu && \
    # git checkout e09c3d597e3ac9ed7b7820971999773449eb896b || true && \
    git submodule update --init --recursive subprojects/symcc-rt && \
    mkdir build && cd build && \
    ../configure                                                    \
    --audio-drv-list=                                         \
    --disable-sdl                                             \
    --disable-gtk                                             \
    --disable-vte                                             \
    --disable-opengl                                          \
    --disable-virglrenderer                                   \
    --target-list=x86_64-linux-user,riscv64-linux-user        \
    --enable-debug                                            \
    --enable-debug-tcg                                        \
    --symcc-rt-llvm-version="$LLVM_VERSION"                   \
    --disable-werror && \
    make -j && \
    cd ../..

