"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

import time
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from onnx import ModelProto

from aidge_benchmark import NamedTensor
from aidge_benchmark.registrations import register_backend_inference, register_backend_time
from ..dynamic_lib_import import load_package


def _measure_inference_time(
    model: "ModelProto",
    inputs: list[NamedTensor],
    nb_warmup: int = 10,
    nb_iterations: int = 50,
) -> list[float]:
    """
        Run the provided ONNX model using ONNXRuntime.
        Performs 10 warm-up runs followed by 50 timed runs (using CPU process time).
    s
        Args:
            model: The ONNX model (ModelProto).
            input_data: Dictionary mapping all input names to NumPy arrays.

        Returns:
            List of CPU times (in seconds) for the 50 timed runs.
    """
    if len(inputs) > len(model.graph.input):
        raise RuntimeError(
            f"More inputs provided than expected for the model. It may be that you are also providing input parameters such as weights while the model expects only inpud data. This can be fixed by manually reducing the number of provided inputs or increasing the `initializer_rank` parameter when generating the ONNX model."
        )
    ort = load_package("onnxruntime")

    inputs_map = {i.name: i.array for i in inputs}

    sess_opt = ort.SessionOptions()
    sess_opt.intra_op_num_threads = 1
    sess = ort.InferenceSession(model.SerializeToString(), sess_opt)

    timings = []
    # Warm-up runs.
    for i in range(nb_warmup + nb_iterations):
        if i < nb_warmup:
            sess.run(None, inputs_map)
        else:
            start = time.process_time()
            sess.run(None, inputs_map)
            end = time.process_time()
            timings.append((end - start))
    return timings


def _compute_output(
    model: "ModelProto", inputs: list[NamedTensor]
) -> list[np.ndarray]:
    if len(inputs) > len(model.graph.input):
        raise RuntimeError(
            f"More inputs provided than expected for the model. It may be that you are also providing input parameters such as weights while the model expects only inpud data. This can be fixed by manually reducing the number of provided inputs or increasing the `initializer_rank` parameter when generating the ONNX model."
        )
    ort = load_package("onnxruntime")

    inputs_map = {i.name: i.array for i in inputs}

    sess = ort.InferenceSession(model.SerializeToString())
    # Run the session with the provided inputs_map.
    outputs = sess.run(None, inputs_map)
    # Return all outputs.
    return outputs

register_backend_time("onnxruntime", _measure_inference_time)
register_backend_inference("onnxruntime", _compute_output)
