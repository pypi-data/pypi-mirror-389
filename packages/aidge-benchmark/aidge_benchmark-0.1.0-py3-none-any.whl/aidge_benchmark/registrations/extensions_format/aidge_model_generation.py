"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

from typing import TYPE_CHECKING

from numpy import ndarray

import aidge_core

if TYPE_CHECKING:
    from aidge_benchmark import SingleOperationConfig, NamedTensor


def _generate_aidge_model(
    config: "SingleOperationConfig", input_arrays: list["NamedTensor"]
) -> aidge_core.GraphView:
    op = aidge_core.__getattribute__(config.operation)(**config.attributes)
    node = aidge_core.Node(op)
    model = aidge_core.GraphView()
    model.add(node)
    for idx, (node, node_idx) in enumerate(model.get_ordered_inputs()):
        if (idx < len(input_arrays)) and (input_arrays[idx].array is not None):
            if node.get_operator().input_category(node_idx) in [
                aidge_core.InputCategory.OptionalParam,
                aidge_core.InputCategory.Param,
            ]:
                p = aidge_core.Producer(
                    aidge_core.Tensor(input_arrays[idx].array),
                    name=input_arrays[idx].name,
                )
                p.add_child(node, 0, node_idx)
                model.add(p)
            else:
                t = aidge_core.Tensor(dims=list(input_arrays[idx].shape)) if (input_arrays[idx].array is None) else aidge_core.Tensor(input_arrays[idx].array)
                t.to_dtype(aidge_core.numpy_to_aidge_dtype(input_arrays[idx].dtype))
                node.get_operator().associate_input(node_idx, t)
                # needed for Resize or Pad
                node.input_name(node_idx, f"{node.get_operator().type()}_{node.id()}_{input_arrays[idx].name}")
    model.set_dataformat(aidge_core.dformat.nchw)
    model.forward_dims(allow_data_dependency=True)
    model.forward_dtype()
    type_id: dict[str, int] = {}
    for node in model.get_nodes():
        if node.name() == "":
            type: str = node.get_operator().type()
            id = type_id.setdefault(type, 0)
            node.set_name(f"{type}_{id}")
            type_id[type] = id + 1
    return model
