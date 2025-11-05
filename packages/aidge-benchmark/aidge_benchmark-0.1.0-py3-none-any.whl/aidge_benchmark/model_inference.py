"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

from importlib import import_module
from importlib.util import find_spec
from typing import Any

from numpy import ndarray

from aidge_benchmark import NamedTensor
from aidge_benchmark.registrations import _BACKEND_INFERENCE_REGISTRY, _BACKEND_TIME_REGISTRY


def compute_output(
    backend: str, /, model: Any, inputs: list[NamedTensor]
) -> list[ndarray]:
    """
    Execute model inference using the specified backend and input tensors.

    This function dispatches model execution to a backend-specific inference function
    registered in the internal backend registry. It supports dynamic loading of backends
    via Python's import system and ensures that the provided input tensor specifications
    are properly initialized before execution.

    The backend must be:
      - Importable as a Python module, and
      - Registered in ``_BACKEND_INFERENCE_REGISTRY`` with a callable accepting a model and inputs.

    .. note::
       Input tensors must have their ``array`` field initialized prior to inference.
       Otherwise, a ``RuntimeError`` is raised.

    :param backend: The name of the backend module (e.g., ``'onnxruntime'``, ``'torch'``, or a custom backend).
    :type backend: str

    :param model: The model object to be executed. The required format depends on the backend.
    :type model: Any

    :param inputs: A list of input specifications. Each must be an instance of :class:`TensorSpecs` with its ``array`` populated.
    :type inputs: list[TensorSpecs]

    :raises ImportError: If the backend module cannot be found in the Python environment.
    :raises RuntimeError: If inputs are not properly initialized or if no inference function is registered for the backend.

    :return: A list of output tensors resulting from model execution.
    :rtype: list[numpy.ndarray]
    """
    if find_spec(backend) is None:
        raise ImportError(
            "'{lib}' package not found in your Python environment. Cannot run the model."
        )
    if backend in _BACKEND_INFERENCE_REGISTRY:
        # check each input has a value array
        # for spec in inputs:
        #     if spec.array is None:
        #         raise RuntimeError("Each input should be filled for inference")
        import_module(backend)
        return _BACKEND_INFERENCE_REGISTRY[backend](model, inputs)
    else:
        raise RuntimeError(
            f"No 'compute_output' function registered for '{backend}' backend"
        )

def measure_inference_time(
        backend: str, /, model: Any, inputs: list[NamedTensor], nb_warmup: int = 10, nb_iterations: int = 50
) -> list[float]:
    if find_spec(backend) is None:
        raise ImportError(
            "'{lib}' package not found in your Python environment. Cannot run the model."
        )
    if backend in _BACKEND_TIME_REGISTRY:
        # check each input has a value array
        for spec in inputs:
            if spec.array is None:
                raise RuntimeError("Each input should be filled for inference")
        import_module(backend)
        return _BACKEND_TIME_REGISTRY[backend](model, inputs, nb_warmup, nb_iterations)
    else:
        raise RuntimeError(
            f"No 'measure_inference_time' function registered for '{backend}' backend"
        )