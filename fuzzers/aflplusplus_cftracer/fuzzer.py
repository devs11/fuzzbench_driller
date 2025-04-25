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
"""Integration code for AFLplusplus fuzzer."""

import subprocess
import time
import os

from fuzzers.aflplusplus import fuzzer as aflplusplus_fuzzer


def build():
    """Build benchmark."""
    aflplusplus_fuzzer.build('qemu')



def _launch_cce(target_binary):
    
    log_path = os.path.join("/tmp/experiment-data/", "cce.log")

    cmd = ["python", "/cftracer/control_engine/dispatch_task.py", "--redis-host", "redis", "--stdin-input", target_binary]
    # cmd = ["python", "/cftracer/control_engine/dispatch_task.py", "--redis-host", "redis", "--input-file", target_binary]
    subprocess.Popen(["ls", "-l", "/"], close_fds=True)
    return subprocess.Popen(cmd, close_fds=True)
    # with open(log_path, "w") as log_fh:
    #     return subprocess.Popen(cmd, stdout=log_fh, stderr=log_fh, close_fds=True)
    
def _launch_cfe(target_binary):
    log_path = os.path.join("/tmp/experiment-data/", "cfe.log")
    TAKS_NAME_FILE = "/out/cftracer_task"
    with open(TAKS_NAME_FILE, "r") as f:
        task_name = f.read()

    cmd = ["python", "/cftracer/fuzzing_engine/launch_fuzzer.py", "--output-dir", "/out/corpus/default/queue", "--corpus-dir", "/out/seeds", "--external-fuzzer", "--redis-host", "redis", "--task", task_name]
    return subprocess.Popen(cmd, close_fds=True)
    # with open(log_path, "w") as log_fh:
    #     return subprocess.Popen(cmd, stdout=log_fh, stderr=log_fh, close_fds=True)
    

def fuzz(input_corpus, output_corpus, target_binary):
    """Run fuzzer."""
    # Get LLVMFuzzerTestOneInput address.
    nm_proc = subprocess.run([
        'sh', '-c',
        'nm \'' + target_binary + '\' | grep -i \'T afl_qemu_driver_stdin\''
    ],
                             stdout=subprocess.PIPE,
                             check=True)
    target_func = '0x' + nm_proc.stdout.split()[0].decode('utf-8')
    print('[fuzz] afl_qemu_driver_stdin_input() address =', target_func)

    # Fuzzer options for qemu_mode.
    flags = ['-Q', '-c0']

    os.environ['AFL_QEMU_PERSISTENT_ADDR'] = target_func
    os.environ['AFL_ENTRYPOINT'] = target_func
    os.environ['AFL_QEMU_PERSISTENT_CNT'] = '1000000'
    os.environ['AFL_QEMU_DRIVER_NO_HOOK'] = '1'

    # removing huge init corpus and replacing it with one file for better incremental coverage demonstration
    # os.system("rm -rf /out/seeds/*")
    # os.system("rm -rf /out/corpus/*")
    # os.system("cp /src/benchmarks/libxml2_xml/seeds/seed.xml /out/seeds/")
    # os.system("ls -la /out && ls -la /out/seeds && ls -la /out/corpus")
    
    print("dispatching cce...")
    _launch_cce(target_binary=target_binary)
    time.sleep(5)
    print("dispatching cfe...")
    _launch_cfe(target_binary=target_binary)

    print("dispatching fuzzer....")
    aflplusplus_fuzzer.fuzz(input_corpus,
                            output_corpus,
                            target_binary,
                            flags=flags)