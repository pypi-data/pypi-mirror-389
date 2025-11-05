"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

from importlib import resources
import json
import os
from pathlib import Path
import sys

from aidge_benchmark.operation_config import SingleOperationConfig
from aidge_benchmark.utils.tree_structure import TreeStructure


class BenchmarkScheme:
    """
    Set of operation configurations stored in a label tree structure.
    """
    def __init__(self, tree: TreeStructure) -> None:
        self._tree: TreeStructure[SingleOperationConfig] = tree

        # Validation: all leaf nodes must be SingleOperationConfig
        for label, value in self._tree:
            if not isinstance(value, SingleOperationConfig):
                raise TypeError(
                    f"Leaf node at '{label}' is not a SingleOperationConfig"
                )

    def __getitem__(self, label: str):
        item = self._tree[label]
        if isinstance(item, TreeStructure):
            return BenchmarkScheme(item)
        return item

    def __setitem__(self, label: str, value):
        if isinstance(value, BenchmarkScheme):
            self._tree[label] = value._tree
        elif isinstance(value, SingleOperationConfig):
            self._tree[label] = value
        else:
            raise TypeError("Only SingleOperationConfig or BenchmarkScheme can be set")

    def __and__(self, other: "BenchmarkScheme") -> "BenchmarkScheme":
        if not isinstance(other, BenchmarkScheme):
            return NotImplemented
        merged_tree = self._tree & other._tree
        return BenchmarkScheme(merged_tree)

    def __or__(self, other: "BenchmarkScheme") -> "BenchmarkScheme":
        if not isinstance(other, BenchmarkScheme):
            return NotImplemented
        merged_tree = self._tree | other._tree
        return BenchmarkScheme(merged_tree)

    def __xor__(self, other: "BenchmarkScheme") -> "BenchmarkScheme":
        if not isinstance(other, BenchmarkScheme):
            return NotImplemented
        merged_tree = self._tree ^ other._tree
        return BenchmarkScheme(merged_tree)

    def __iter__(self):
        return iter(self._tree)

    def __len__(self) -> int:
        return len(self._tree)

    def __str__(self) -> str:
        return str(self._tree)

    def __repr__(self) -> str:
        return f"{BenchmarkScheme.__name__}(n_config: {len(self._tree)})"

    @property
    def labels(self) -> list[str]:
        return self._tree.branches

    @property
    def configs(self) -> list[SingleOperationConfig]:
        return self._tree.leaves

    def as_dict(self) -> dict:
        return self._tree.as_dict()

    @staticmethod
    def from_dict(config_dict: dict) -> "BenchmarkScheme":
        def process_tree(tree: dict) -> dict:
            result = {}
            for key, value in tree.items():
                if not isinstance(key, str):
                    raise TypeError("Labels must be strings")
                if isinstance(value, dict) and not SingleOperationConfig.is_valid_dict(
                    value
                ):
                    result[key] = process_tree(value)
                else:
                    result[key] = SingleOperationConfig(value)
            return result

        tree = TreeStructure(process_tree(config_dict))
        return BenchmarkScheme(tree)

    @staticmethod
    def from_json(json_path: str) -> tuple["BenchmarkScheme", "SingleOperationConfig"]:
        test_json = _load_json(json_path)

        other_params = {
            "operation": test_json["operation"],
            "format": {
                "name": test_json["format"]["name"],
                "metadata": test_json["format"]["metadata"],
            },
        }

        default_config_dict = test_json.get("base_configuration", {})
        default_config_dict.update(other_params)
        default_config = SingleOperationConfig.from_dict(default_config_dict)

        def is_json_operation_config(obj: dict) -> bool:
            if not isinstance(obj, dict):
                return False
            if not set(obj.keys()).issubset({"attributes", "input_specs"}):
                return False
            if not isinstance(obj.get("attributes", {}), dict):
                return False
            if not isinstance(obj.get("input_specs", []), list):
                return False
            return True

        def process_tree(tree: dict) -> dict:
            result = {}
            for key, value in tree.items():
                if isinstance(value, dict) and not is_json_operation_config(value):
                    result[key] = process_tree(value)
                else:
                    merged_config = {**value, **other_params}
                    result[key] = SingleOperationConfig.from_dict(merged_config)
            return result

        tree = TreeStructure(process_tree(test_json["test_configurations"]))
        return BenchmarkScheme(tree), default_config



def create_benchmark_from_dict(config_dict: dict) -> BenchmarkScheme:
    return BenchmarkScheme.from_dict(config_dict)


def create_benchmark_from_json(
    json_path: str,
) -> tuple[BenchmarkScheme, "SingleOperationConfig"]:
    return BenchmarkScheme.from_json(json_path)

def _find_file_in_package(file_path: str) -> str | None:
    """Try to locate the given config file either in current directory or in package data."""
    # Try loading from packaged resources
    try:
        config_file = resources.files("aidge_benchmark.operations_config").joinpath(file_path)
        if config_file.is_file():
            return config_file
    except ModuleNotFoundError:
        pass  # if resources can't find the package

    # Not found
    return None

def _load_json(file_path: str, search_dir: str = '.') -> dict:
    """
    Loads and returns the JSON configuration from the given file.
    Searches in the given directory, current working directory, and package resources.
    """
    config_path = None

    file_path_obj = Path(file_path)
    search_dir_path = Path(os.path.expanduser(search_dir))

    # Check if file_path is directly usable
    if file_path_obj.is_file():
        config_path = file_path_obj
    # Check inside the search_dir
    elif (search_dir_path / file_path_obj).is_file():
        config_path = search_dir_path / file_path_obj
    # Fallback to package search
    elif _find_file_in_package(file_path):
        config_path = _find_file_in_package(file_path)

    if not config_path:
        print(file_path, search_dir, file_path_obj, search_dir_path)
        print("Cannot find JSON file.")
        sys.exit(1)

    with open(config_path, "r") as f:
        return json.load(f)