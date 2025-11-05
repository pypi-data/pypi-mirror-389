"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

from typing import TYPE_CHECKING, Any, Callable

from numpy import ndarray

from aidge_benchmark.tensor_specs import NamedTensor
if TYPE_CHECKING:
    from aidge_benchmark.operation_config import SingleOperationConfig


_MODEL_GENERATORS_REGISTRY: dict[
    str, Callable[["SingleOperationConfig", list[ndarray]], Any]
] = {}
_BACKEND_INFERENCE_REGISTRY: dict[
    str, Callable[[str, Any, list[NamedTensor]], list[ndarray]]
] = {}
_BACKEND_TIME_REGISTRY: dict[
    str, Callable[[str, Any, list[NamedTensor], int, int], list[ndarray]]
] = {}


def register_model_generator(
    name: str, fn: Callable[["SingleOperationConfig", list[ndarray]], Any]
) -> None:
    _MODEL_GENERATORS_REGISTRY[name.lower()] = fn

def register_backend_inference(
    name: str, fn: Callable[[str, Any, list[NamedTensor]], list[ndarray]]
) -> None:
    _BACKEND_INFERENCE_REGISTRY[name.lower()] = fn

def register_backend_time(
    name: str, fn: Callable[[str, Any, list[NamedTensor], int, int], list[ndarray]]
) -> None:
    _BACKEND_TIME_REGISTRY[name.lower()] = fn
