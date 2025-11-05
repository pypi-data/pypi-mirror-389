"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

from dataclasses import dataclass
from typing import Any, Mapping
from typing_extensions import Self

import numpy as np


@dataclass
class NamedTensor:
    """
    A simple container for a named NumPy array.

    :param name: The name of the tensor (required).
    :param array: The tensor data (optional, defaults to None).
    """

    name: str
    array: np.ndarray | None = None

    @property
    def shape(self) -> tuple[int, ...] | None:
        return self.array.shape if self.array is not None else None

    @property
    def dtype(self) -> np.dtype | None:
        return self.array.dtype if self.array is not None else None

    def __repr__(self) -> str:
        return (
            f"NamedTensor(name={self.name!r}, shape={self.shape}, dtype={self.dtype})"
        )


class TensorSpecs:
    """
    A simplified class representing the specification of a tensor.

    :ivar name: Name of the tensor.
    :vartype name: str
    :ivar data: Optional NumPy array representing the tensor.
    :vartype data: np.ndarray or None
    :ivar shape: Optional shape of the tensor.
    :vartype shape: list[int] or None
    :ivar dtype: NumPy data type for the tensor (default: np.float32).
    :vartype dtype: np.dtype
    """

    def __init__(
        self,
        /,
        name: str,
        *,
        data: np.ndarray | None = None,
        shape: list[int] | None = None,
        dtype: np.dtype | None = None,
        none_is_undefined: bool = False,
    ) -> None:
        """
        Initialize a TensorSpecs instance.

        :param name: The name of the tensor.
        :type name: str
        :param data: Optional NumPy array. If provided, used as tensor data.
        :type data: np.ndarray or None
        :param shape: Optional list of dimensions.
        :type shape: list[int] or None
        :param dtype: NumPy data type to use. Default is np.float32.
        :type dtype: np.dtype
        """
        self.name = name
        self.dtype = dtype
        self.shape = shape
        self.data = data
        self._none_is_undefined = none_is_undefined

    def generate_array(self) -> np.ndarray | None:
        """
        Return the tensor as a NumPy array.

        If ``data`` is provided, returns it cast to the specified ``dtype``.
        If ``data`` is not provided, generates a random array of the specified ``shape``.

        :raises ValueError: If both ``shape`` and ``data`` mismatch.
        :returns: Tensor data as a NumPy array.
        :rtype: np.ndarray
        """
        if (self.shape is None and self.data is None):
            return None

        if self.shape is not None and self.data is not None:
            if list(self.data.shape) != self.shape:
                raise ValueError(
                    f"Specified shape and data are not compatible: shape {self.shape}, data shape {list(self.data.shape)}."
                )

        res_array: np.ndarray
        if self.data is not None:
            res_array = self.data.astype(self.dtype)
        else:
            if np.issubdtype(self.dtype, np.floating):
                res_array = np.random.rand(*self.shape)  # [0, 1)
            elif np.issubdtype(self.dtype, np.signedinteger):
                low = np.random.randint(-16, 0, size=self.shape)
                high = np.random.randint(1, 17, size=self.shape)
                mask = np.random.rand(*self.shape) < 0.5
                res_array = np.where(mask, low, high)
            elif np.issubdtype(self.dtype, np.unsignedinteger):
                res_array = np.random.randint(1, 17, size=self.shape)  # [0, 100]
            elif self.dtype == np.bool_:
                res_array = np.random.randint(0, 2, size=self.shape)
            else:
                raise TypeError(f"Unsupported dtype: {self.dtype}")
        return np.array(res_array, dtype=self.dtype)

    def is_undefined(self) -> bool:
        """
        Check whether both shape and data are unspecified.

        :return: True if both shape and data are None.
        :rtype: bool
        """
        return self._none_is_undefined and (self.shape is None and self.data is None)

    def is_compatible_with(self, array: np.ndarray | None) -> bool:
        """
        Check if a given array is compatible with this tensor specification.

        Compatibility is defined as:
        - If spec is undefined (no shape and no data), then array must be None.
        - If shape is specified, it must match the array's shape.
        - If data is specified, it must match the array's content (after dtype cast).
        - The array's dtype must match the spec's dtype.

        :param array_: The array to check.
        :type array_: np.ndarray or None
        :return: True if compatible with this spec, False otherwise.
        :rtype: bool
        """
        if (self.shape is None and self.data is None):
            return array is None
        if self.dtype != array.dtype:
            return False
        if self.shape is not None:  # self.data is None
            if self.shape != list(array.shape):
                return False
        else:
            if not np.allclose(self.data.astype(self.dtype), array):
                return False
        return True

    def override_with(self, other: Self) -> Self:
        new_specs = TensorSpecs(other.name)
        if not other.is_undefined():
        # and (
        #     other.shape is not None or other.data is not None
        # ):
            new_specs.shape = other.shape
            new_specs.data = other.data
        else:
            new_specs.shape = self.shape
            new_specs.data = self.data
        new_specs.dtype = other.dtype if other.dtype is not None else self.dtype
        return new_specs

    @staticmethod
    def is_valid_dict(obj: Mapping[str, Any]) -> bool:
        """
        Validate whether a dictionary can represent a valid TensorSpecs instance.

        The dictionary:
          - Must include ``name`` as a string.
          - May optionally include ``data``, ``shape``, and ``dtype``.
          - ``shape`` must be a list of integers or None.
          - ``data`` must be convertible to a NumPy array or None.
          - ``dtype`` must be a valid NumPy dtype or None.

        :param obj: Dictionary to validate.
        :type obj: Mapping[str, Any]
        :returns: True if the dictionary is valid, False otherwise.
        :rtype: bool
        """
        if not isinstance(obj, dict):
            return False

        required_keys = {"name"}
        optional_keys = {"data", "shape", "dtype"}
        if not required_keys.issubset(obj.keys()):
            return False
        if not set(obj.keys()).issubset(required_keys.union(optional_keys)):
            return False

        if not isinstance(obj["name"], str):
            return False

        if "shape" in obj and obj["shape"] is not None:
            if not (
                isinstance(obj["shape"], list)
                and all(isinstance(dim, int) for dim in obj["shape"])
            ):
                return False

        if "data" in obj and obj["data"] is not None:
            try:
                _ = np.array(obj["data"])
            except Exception:
                return False

        if "dtype" in obj and obj["dtype"] is not None:
            try:
                np.dtype(obj["dtype"])
            except TypeError:
                return False

        return True

    @staticmethod
    def from_dict(data: Mapping[str, Any]) -> Self:
        """
        Create a TensorSpecs instance from a dictionary.

        :param data: Dictionary representation of the tensor spec.
        :type data: Mapping[str, Any]
        :raises ValueError: If the dictionary is invalid or if shape and data mismatch.
        :returns: A TensorSpecs instance.
        :rtype: TensorSpecs
        """
        if not TensorSpecs.is_valid_dict(data):
            raise ValueError("Invalid dictionary for TensorSpecs.")

        name = data["name"]
        dtype = np.dtype(data["dtype"]) if "dtype" in data else None
        shape = data.get("shape", None)

        data_array = None
        if "data" in data and data["data"] is not None:
            data_array = np.array(data["data"])
            if shape is not None and list(data_array.shape) != shape:
                raise ValueError(
                    f"Shape mismatch: shape {shape} != data.shape {list(data_array.shape)}"
                )

        return TensorSpecs(
            name=name,
            data=data_array,
            shape=shape,
            dtype=dtype,
            none_is_undefined=("data" not in data and "shape" not in data),
        )

    @staticmethod
    def as_dict(tensor_specs: Self) -> dict:
        """
        Convert the TensorSpecs instance into a dictionary.

        The dictionary includes:
          - ``name`` (str)
          - ``shape`` (list[int] or None)
          - ``data`` (nested list or None)
          - ``dtype`` (string representation of NumPy dtype)

        :returns: Dictionary representation of the instance.
        :rtype: dict
        """
        return {
            "name": tensor_specs.name,
            "shape": tensor_specs.shape,
            "data": (
                tensor_specs.data.tolist() if tensor_specs.data is not None else None
            ),
            "dtype": str(tensor_specs.dtype),
        }
