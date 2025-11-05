"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

from copy import deepcopy
from typing import Any, Mapping
from typing_extensions import Self

from numpy import ndarray

from aidge_benchmark.format_descriptor import FormatDescriptor
from aidge_benchmark.tensor_specs import TensorSpecs, NamedTensor
from aidge_benchmark.registrations import _MODEL_GENERATORS_REGISTRY


class SingleOperationConfig:
    """
    Defines the configuration for testing a single operation.

    Attributes:
        operation (str): Name of the operation.
        format (FormatDescriptor | None): Description of the format the operation is described in.
        attributes (dict[str, Any]): Attributes of the operation being tested (e.g., kernel size, strides, padding).
        input_specs (list[TensorSpecs]): A list of input tensor specifications required for the test.
    """

    def __init__(
        self,
        operation: str,
        format: FormatDescriptor | None = None,
        attributes: dict[str, Any] | None = None,
        input_specs: list[TensorSpecs] | None = None
    ) -> None:
        self._operation = operation
        self.format = format
        self.attributes: dict[str, Any] = attributes if attributes is not None else {}
        self.input_specs: list[TensorSpecs] = (
            input_specs if input_specs is not None else []
        )

    def __str__(self) -> str:
        return (
            f"SingleOperationConfig(\n"
            f"  operation: {self.operation}\n"
            f"  format: {self.format}\n"
            f"  attributes: {self.attributes}\n"
            f"  input_specs:\n    {self.input_specs}\n"
            f")"
        )

    def __repr__(self) -> str:
        return f"{SingleOperationConfig.__name__}('{self.operation}', attr: {'None' if self.attributes is None else 'dict[n='+str(len(self.attributes))+']'}, input_specs: {'None' if self.input_specs is None else 'list[n='+str(len(self.input_specs))+']'}, format='{'None' if self.format is None else self.format.name}')"

    def generate_inputs(self) -> list[NamedTensor]:
        return [NamedTensor(specs.name, specs.generate_array()) for specs in self.input_specs]

    @property
    def operation(self) -> str:
        return self._operation

    # Maybe another way to handle combination of test config from different operation types
    # For now, operation type need to be the same so allowing property setter
    @operation.setter
    def operation(self, value: str, /) -> None:
        self._operation = value

    def override_with(self, override: Self) -> Self:
        """
        Merges this config (as base) with an overriding config.

        - Preserves the input order from `self`.
        - Uses values from `override` when present.
        - Falls back to `self` for missing input properties or attributes.
        - Ensures a uniquely determined merged input order; otherwise raises a ValueError.

        Args:
            override (SingleOperationConfig): The overriding config (e.g., test-specific).

        Returns:
            SingleOperationConfig: A merged configuration with complete attributes and inputs.

        Raises:
            ValueError: If input specs from the two configs cannot be merged due to ambiguous order.
        """

        def merge_attributes(
            override_attrs: Mapping[str, Any], base_attrs: Mapping[str, Any]
        ) -> Mapping[str, Any]:
            merged = deepcopy(base_attrs)
            merged.update(override_attrs)
            return merged

        def merge_tensor_specs(
            base_specs: list[TensorSpecs], override_specs: list[TensorSpecs]
        ) -> list[TensorSpecs]:
            i, j = 0, 0
            I, J = len(base_specs), len(override_specs)
            merged_specs: list[TensorSpecs] = []

            while i < I and j < J:
                k = j
                while k < J and base_specs[i].name != override_specs[k].name:
                    k += 1
                if k == J:
                    k = i
                    while k < I and override_specs[j].name != base_specs[k].name:
                        k += 1
                    if k == I:
                        raise ValueError(
                            "Updated input list order cannot be deduced: "
                            "no common elements between base and override input specs."
                        )
                    else:
                        merged_specs += base_specs[i:k]
                        merged_specs.append(base_specs[k].override_with(override_specs[j]))
                        j += 1
                        i = k + 1
                else:
                    merged_specs += override_specs[j : k]
                    merged_specs.append(base_specs[i].override_with(override_specs[k]))
                    j = k + 1
                    i += 1

            if i < I and j == J:
                merged_specs += base_specs[i:]
            elif i == I and j < J:
                merged_specs += override_specs[j:]
            elif i < I and j < J:
                raise ValueError("Ill-formed updated tensor specification.")

            return merged_specs

        if (override.format != self.format) or (override.operation != self.operation):
            raise ValueError(
                "Override and base config must describe the same operation with the same format"
            )

        merged = SingleOperationConfig(operation=self.operation, format=self.format)

        if not self.input_specs:
            merged.input_specs = override.input_specs
        elif not override.input_specs:
            merged.input_specs = self.input_specs
        else:
            merged.input_specs = merge_tensor_specs(
                self.input_specs, override.input_specs
            )

        merged.attributes = merge_attributes(override.attributes, self.attributes)

        return merged

    def as_model(self, input_arrays: list[NamedTensor | None]) -> Any:
        if len(input_arrays) > len(self.input_specs):
            raise ValueError("Providing more input arrays than the current onfiguration specifies.")
        else:
            # complete arrays to be the same size as input_specs
            input_arrays += [None]*(len(self.input_specs) - len(input_arrays))
        for i in range(len(input_arrays)):
            assert(self.input_specs[i].is_compatible_with(input_arrays[i].array))
        format_lower = self.format.name.lower()
        if format_lower not in _MODEL_GENERATORS_REGISTRY.keys():
            raise NotImplementedError(
                f"Unknown model format: {format_lower}. You may need to manually convert your {SingleOperationConfig.__name__} object to a model."
            )
        return _MODEL_GENERATORS_REGISTRY[format_lower](self, input_arrays)

    @staticmethod
    def from_dict(data: Mapping[str, Any]) -> Self:
        if not SingleOperationConfig.is_valid_dict(data):
            raise ValueError("Invalid data for SingleOperatorConfig")
        attr = data.get("attributes", {})
        attr = {k: v for k, v in attr.items() if v is not None}
        return SingleOperationConfig(
            operation=data["operation"],
            format=(
                FormatDescriptor.from_dict(data["format"])
                if data.get("format")
                else None
            ),
            attributes=attr,
            input_specs=[
                TensorSpecs.from_dict(spec) for spec in data.get("input_specs", [])
            ],
        )

    @staticmethod
    def is_valid_dict(obj: Mapping[str, Any]) -> bool:
        """
        Check if the given object is a valid dictionary representation of a SingleOperationConfig.
        """
        if not isinstance(obj, dict):
            return False

        required_keys = {"operation"}
        # optional_keys = {"attributes", "input_specs", "format"}
        if not required_keys.issubset(obj.keys()):
            return False
        # required_keys.union(optional_keys)
        if not set(obj.keys()).issubset(
            {"operation", "attributes", "input_specs", "format"}
        ):
            return False

        attributes = obj.get("attributes", {})
        input_specs = obj.get("input_specs", [])

        if not isinstance(obj["operation"], str):
            return False

        if not isinstance(attributes, dict):
            return False

        if not isinstance(input_specs, list):
            return False

        if "format" in obj and obj["format"] is not None:
            if not FormatDescriptor.is_valid_dict(obj["format"]):
                return False

        for item in input_specs:
            if not TensorSpecs.is_valid_dict(item):
                return False

        return True
