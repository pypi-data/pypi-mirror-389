"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""


def convert_bytes_to_str(obj):
    """
    Recursively converts bytes in a nested data structure to UTF-8 strings.

    Args:
        obj: A dictionary, list, or value possibly containing bytes.

    Returns:
        A structure with bytes converted to strings.
    """
    if isinstance(obj, dict):
        return {k: convert_bytes_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_bytes_to_str(item) for item in obj]
    elif isinstance(obj, bytes):
        return obj.decode('utf-8')
    else:
        return obj

def build_onnx_template_config(operator_name: str, opset_version: int, initializer_rank: int) -> dict:
    """
    Generate a configuration template for testing an ONNX operator.

    :param operator_name: The name of the ONNX operator (e.g., "Add", "Relu").
    :type operator_name: str
    :param opset_version: The ONNX opset version to target.
    :type opset_version: int
    :param initializer_rank: Index of the first initializer input among all inputs.
                             Inputs before this index are dynamic inputs (e.g., tensors).
    :type initializer_rank: int

    :return: A dictionary containing operator name, opset, test metadata, and base configuration
             derived from the ONNX schema.
    :rtype: dict
    """
    config: dict = {
        "operation": operator_name,
        "format": {
            "name": "ONNX",
            "metadata": {
                "opset_version": opset_version,
                "initializer_rank": initializer_rank,
            }
        }
    }

    def build_base_configuration_from_onnx_schema(operator_name: str, opset_version: int) -> dict:
        """
        Build a base configuration from the ONNX operator schema.

        This includes:
            - default attribute values (if any),
            - input specifications with placeholder shape and values.

        :param operator_name: Name of the ONNX operator (e.g., "Add", "Relu").
        :type operator_name: str
        :param opset_version: The ONNX opset version to target.
        :type opset_version: int

        :raises RuntimeError: If the ONNX schema cannot be retrieved.

        :return: A dictionary containing default attributes and input specifications.
        :rtype: dict
        """
        from onnx.helper import get_attribute_value
        from onnx.defs import get_schema

        try:
            schema = get_schema(operator_name, opset_version)
        except Exception as e:
            raise RuntimeError(f"Failed to get schema for operator '{operator_name}': {e}")

        base_config = {
            "attributes": {},
            "input_specs": []
        }

        # Handle attributes with default values
        for attr_name, attr_proto in schema.attributes.items():
            if attr_proto.default_value is not None:
                base_config["attributes"][attr_name] = get_attribute_value(attr_proto.default_value)

        # Handle inputs
        for input_param in schema.inputs:
            # No value for 'shape' or 'values' specified
            # This will cause an error if required inputs are not set
            # Optional inputs will not be linked if not set
            base_config["input_specs"].append({
                "name": input_param.name,
                "shape": None,
                "data": None
            })

        return base_config
    config["base_configuration"] = build_base_configuration_from_onnx_schema(operator_name, opset_version)
    config["test_configurations"] = {}
    return convert_bytes_to_str(config)