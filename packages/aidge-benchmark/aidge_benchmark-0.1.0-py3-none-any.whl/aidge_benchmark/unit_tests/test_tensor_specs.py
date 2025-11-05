"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

import numpy as np
import pytest

from aidge_benchmark.tensor_specs import TensorSpecs

def test_from_dict_with_shape_only():
    data = {
        "name": "input_tensor",
        "shape": [2, 3]
    }
    spec = TensorSpecs.from_dict(data)
    assert spec.name == "input_tensor"
    assert spec.shape == [2, 3]
    assert spec.data is None
