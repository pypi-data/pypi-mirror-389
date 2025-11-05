"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

from dataclasses import dataclass
from typing import Any
from typing_extensions import Self


@dataclass
class FormatDescriptor:
    """
    Description of the representation format with associated metadata required to generate or interpret a machine learning model.
    """

    name: str  # e.g., "onnx", "aidge"
    metadata: dict | None = None  # e.g., {'op_set': 13, 'n_initializer': 5}

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Self:
        """
        Create a FormatDescriptor from a dictionary.
        """
        if not FormatDescriptor.is_valid_dict(data):
            raise ValueError("Invalid data for FormatDescriptor")
        return FormatDescriptor(name=data["name"], metadata=data.get("metadata"))

    @staticmethod
    def is_valid_dict(obj: dict) -> bool:
        """
        Check if the given object is a valid dictionary representation of a FormatDescriptor.
        """
        if not isinstance(obj, dict):
            return False

        if "name" not in obj or not isinstance(obj["name"], str):
            return False

        if (
            "metadata" in obj
            and obj["metadata"] is not None
            and not isinstance(obj["metadata"], dict)
        ):
            return False

        return True