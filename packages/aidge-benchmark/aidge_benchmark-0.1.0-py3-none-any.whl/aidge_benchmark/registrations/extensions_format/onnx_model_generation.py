"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

from importlib.util import find_spec
from typing import TYPE_CHECKING

from numpy import ndarray

from .onnx_helpers import create_onnx_model

if TYPE_CHECKING:
    from aidge_benchmark import SingleOperationConfig, NamedTensor
    from onnx import ModelProto


def _generate_onnx_model(config: "SingleOperationConfig", input_arrays: list["NamedTensor"]) -> "ModelProto":
    if find_spec('onnx') is None:
        raise ImportError("ONNX generation requires 'onnx'. Please install it.")

    return create_onnx_model(
        config.operation,
        config.format.metadata.get("opset_version", 21),
        input_arrays,
        config.format.metadata.get("initializer_rank", len(config.input_specs)),
        **config.attributes
    )