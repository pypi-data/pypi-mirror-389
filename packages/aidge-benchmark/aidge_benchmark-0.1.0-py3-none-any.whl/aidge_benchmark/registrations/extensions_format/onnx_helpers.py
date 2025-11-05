"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from onnx import ModelProto, TensorProto
    from onnx.defs import OpSchema

import numpy as np

from aidge_benchmark import NamedTensor
from ..dynamic_lib_import import load_package

def create_onnx_model(operator_type: str, opset_version: int, input_arrays: list[NamedTensor], intializer_rank: int = 1, **kwargs) -> "ModelProto":
    """
    Create an ONNX model with a single operator using ONNX shape inference

    Args:
        operator_type (str): Type of operator (e.g., 'Conv')
        opset_version (int): opset version
        input_specs (list): List of dict (name, shapes, data) for each input tensor. Data format is NCHW. (e.g ['name'='input', 'shape'=[1,2,3,4], 'data'=None])
        intializer_rank: value above which inputs should be linked to initializers
        **kwargs: Operator-specific attributes (e.g conv_params = {'kernel_shape': (3, 3), 'strides': (2, 2),'pads': (0, 0, 0, 0)})

    Returns:
        onnx.ModelProto: Generated ONNX model
    """
    onnx = load_package("onnx")

    def _to_tensor_proto_enum(type_str: str) -> "TensorProto.DataType":
        """
        Map an ONNX type string like 'tensor(float16)' or 'tensor(int64)'
        to the corresponding TensorProto enum value
        FLOAT16 and INT64.
        """
        # strip the 'tensor('  and ')'  → 'float16'
        base = type_str[len("tensor("):-1]
        return getattr(onnx.TensorProto, base.upper())

    def _schema_required_outputs(op_type: str, opset_version: int, domain: str = "") -> "OpSchema":
        """
        Return a list of (name, TensorProtoEnum) for every *required*
        output of `op_type` in the given opset.
        """
        schema = onnx.defs.get_schema(op_type, opset_version, domain)
        type_dict = {tc.type_param_str: tc.allowed_type_strs for tc in schema.type_constraints}
        required = []
        for output in schema.outputs:
            # Skip optional outputs
            if output.option == onnx.defs.OpSchema.FormalParameterOption.Optional:
                continue

            # Choose dtype: float if available, else first allowed type
            allowed = type_dict[output.type_str]
            chosen_type = "tensor(float)" if "tensor(float)" in allowed else allowed[0]
            proto_enum = _to_tensor_proto_enum(chosen_type)
            required.append((output.name, proto_enum))
        return required

    def _remove_initializers_from_inputs(model: "ModelProto") -> None:
        """Remove graph inputs that are also initializers."""
        initializer_names = {init.name for init in model.graph.initializer}
        # Create a new list excluding any input whose name is in initializer_names.
        new_inputs = [inp for inp in model.graph.input if inp.name not in initializer_names]
        # Clear the existing inputs and extend with the new list.
        del model.graph.input[:]
        model.graph.input.extend(new_inputs)


    # Create input tensors info
    input_value_infos = []
    initializers = []
    input_names = [val.name for val in input_arrays]

    for i, named_array in enumerate(input_arrays):
        tensor_type: "TensorProto.DataType" = onnx.TensorProto.FLOAT
        if named_array.dtype == np.bool_:
            tensor_type = onnx.TensorProto.BOOL
        elif np.issubdtype(named_array.dtype, np.integer):
            tensor_type = onnx.TensorProto.INT64
        elif np.issubdtype(named_array.dtype, np.floating):
            assert(named_array.dtype == np.float32)
            tensor_type = onnx.TensorProto.FLOAT
        else:
            raise TypeError(f"Unsupported data type in input specifications. Cannot create an initializer for the onnx.")
        if i < intializer_rank:  # First input is always the actual input
            input_value_infos.append(onnx.helper.make_tensor_value_info(named_array.name, tensor_type, named_array.shape))
        else:  # Other inputs are typically weights/parameters
            if named_array.array is None:
                input_names[i] = ''
                continue
            # array should not be None at this point
            initializers.append(onnx.numpy_helper.from_array(named_array.array, name=named_array.name))
            input_value_infos.append(onnx.helper.make_tensor_value_info(named_array.name, tensor_type,  named_array.shape))

    output_specs = _schema_required_outputs(operator_type, opset_version)
    # Build the name list for the node and the corresponding ValueInfos
    output_names = [name for name, _ in output_specs]
    output_value_infos = [
        onnx.helper.make_tensor_value_info(name, dtype, None)  # scalar placeholder
        for name, dtype in output_specs
    ]

    # Create node
    node = onnx.helper.make_node(
        operator_type,
        inputs=input_names,
        outputs=output_names,
        **kwargs
    )

    # Create graph with empty output shape - will be inferred
    graph = onnx.helper.make_graph(
        [node],
        'single-operator-model',
        input_value_infos,
        output_value_infos,
        initializers
    )

    model = onnx.helper.make_model(graph)
    model.opset_import[0].version = opset_version
    model.ir_version = 10
    # Remove constant weights from the graph inputs.
    _remove_initializers_from_inputs(model)
    # Use ONNX shape inference to propagate shapes
    model = onnx.shape_inference.infer_shapes(model)

    # Validate the model
    onnx.checker.check_model(model)

    return model

# Example usage
# if __name__ == '__main__':
#     TYPE = 'Concat'

#     # Define shapes for three input tensors with same spatial dimensions but different channels
#     input_specs = [
#         TensorSpec.from_dict({'name': 'input_0', 'shape': [1, 16, 32, 32]}),  # 16 channels
#         TensorSpec.from_dict({'name': 'input_1', 'shape': [1, 32, 32, 32]}),  # 32 channels
#         TensorSpec.from_dict({'name': 'input_2', 'shape': [1, 16, 32, 32]})   # 16 channels
#     ]

#     # Concatenate along channel axis (axis=1 in NCHW format)
#     attributes = {
#         'axis': 1  # Concatenate along channel dimension
#     }

#     model = create_onnx_model(TYPE, 12, input_specs, 3, **attributes)

#     single_operator_model_name: str = TYPE + '_model.onnx'
#     onnx.save(model, single_operator_model_name)
#     print("Model created successfully!")
#     print("Output shape:", [dim.dim_value for dim in model.graph.output[0].type.tensor_type.shape.dim])