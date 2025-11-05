"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

import time
from typing import TYPE_CHECKING

from numpy import ndarray

if TYPE_CHECKING:
    from onnx import ModelProto

from aidge_benchmark import NamedTensor
from aidge_benchmark.registrations import register_backend_inference, register_backend_time
from ..dynamic_lib_import import load_package


def _measure_inference_time(
    model_onnx: "ModelProto",
    inputs: list[NamedTensor],
    nb_warmup: int = 10,
    nb_iterations: int = 50,
) -> list[float]:
    """
    Run the provided PyTorch model.
    Performs 10 warm-up runs followed by 50 timed runs (using CPU process time).

    Args:
        model_onnx: The ONNX model.
        input_data: Dictionary mapping all input names to NumPy arrays.

    Returns:
        List of CPU times (in seconds) for the 50 timed runs.
    """
    torch = load_package("torch")
    onnx2torch = load_package("onnx2torch")

    model_torch = onnx2torch.convert(model_onnx)

    device = torch.device("cpu")
    model_torch.to(device)
    model_torch.eval()

    torch.set_num_threads(1)

    inputs = [torch.tensor(i.array, device=device) for i in inputs]
    timings = []
    with torch.no_grad():
        # Warm-up runs
        for i in range(nb_warmup + nb_iterations):
            if i < nb_warmup:
                model_torch(*inputs)
            else:
                start = time.process_time()
                model_torch(*inputs)
                end = time.process_time()
                timings.append(end - start)
    return timings


def _compute_output(
    model_onnx: "ModelProto", inputs: dict[NamedTensor]
) -> list[ndarray]:
    """
    Run the PyTorch model inference.

    Args:
        model: The PyTorch model.
        input_data: Dictionary mapping all input names to NumPy arrays.

    Returns:
        The first output tensor if there is only one, else a list of output tensors.
    """
    torch = load_package("torch")
    onnx2torch = load_package("onnx2torch")

    model_torch = onnx2torch.convert(model_onnx)

    device = torch.device("cpu")
    model_torch.to(device)
    model_torch.eval()

    inputs = [torch.tensor(i.array, device=device) for i in inputs]

    with torch.no_grad():
        # Warning: not tested for multiple outputs case
        output = model_torch(*inputs)

    return [o.numpy() for o in output]

register_backend_time("torch", _measure_inference_time)
register_backend_inference("torch", _compute_output)