"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

from .registration_helpers import (
    _MODEL_GENERATORS_REGISTRY,
    _BACKEND_INFERENCE_REGISTRY,
    _BACKEND_TIME_REGISTRY,
    register_model_generator,
    register_backend_inference,
    register_backend_time,
)

from .extensions_inference.onnxruntime import _compute_output, _measure_inference_time
from .extensions_inference.torch import _compute_output, _measure_inference_time

from .extensions_format.aidge_model_generation import _generate_aidge_model
from .extensions_format.onnx_model_generation import _generate_onnx_model

register_model_generator("aidge", _generate_aidge_model)
register_model_generator("onnx", _generate_onnx_model)

__all__ = [
    "_MODEL_GENERATORS_REGISTRY",
    "_BACKEND_INFERENCE_REGISTRY",
    "_BACKEND_TIME_REGISTRY",
    "register_model_generator",
    "register_backend_inference",
    "register_backend_time"
]