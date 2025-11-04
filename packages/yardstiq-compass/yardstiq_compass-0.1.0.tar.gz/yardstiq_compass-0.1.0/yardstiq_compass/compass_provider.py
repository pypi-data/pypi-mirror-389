# Copyright 2025 Scaleway, Aqora, Quantum Commons
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
from yardstiq.core import (
    provider,
    Backend,
    Benchmark,
    BackendProvider,
    BenchmarkProvider,
)


@provider("compass")
class CompassProvider(BackendProvider, BenchmarkProvider):
    """Compass backend provider for Yardstiq."""

    def get_backend(self, name: str) -> Backend:
        if name == "aer":
            return AerLocalBackend()
        elif name == "qsim":
            return QSimLocalBackend()
        else:
            raise ValueError(f"Unknown backend: {name}")

    def get_benchmark(self, name: str) -> Benchmark:
        if name == "vqe":
            return VQEBenchmark()
        else:
            raise ValueError(f"Unknown benchmark: {name}")
