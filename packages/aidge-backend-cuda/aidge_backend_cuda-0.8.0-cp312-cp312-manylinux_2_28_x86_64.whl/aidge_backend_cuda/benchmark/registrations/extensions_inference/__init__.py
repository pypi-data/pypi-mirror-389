"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

from .aidge_backend_cuda import compute_output, measure_inference_time

try:
    from aidge_benchmark.registrations import (
        register_backend_inference,
        register_backend_time,
    )

    register_backend_inference("aidge_backend_cuda", compute_output)
    register_backend_time("aidge_backend_cuda", measure_inference_time)
except ImportError:
    # print("could not register")
    # Optional: fail silently if running in isolation
    pass
