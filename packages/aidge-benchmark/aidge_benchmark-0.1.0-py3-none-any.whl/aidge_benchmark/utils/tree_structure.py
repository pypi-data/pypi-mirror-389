"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

from collections.abc import Iterator
from typing import Any, Generic, TypeVar
from typing_extensions import Self

from rich.tree import Tree as RichTree
from rich.console import Console
from io import StringIO


T = TypeVar("leaf")


class TreeStructure(Generic[T]):
    """
    A utility class to represent and manipulate nested dictionary structures using dot-separated keys.

    This class supports:
    - Deep access and assignment via dot-notation.
    - Recursive merging of trees (`+` operator).
    - Filtering and extracting subtrees.
    - Iteration over leaf nodes.
    - Pretty-printing with `rich`.

    :param tree: An optional dictionary to initialize the tree structure.
    :type tree: dict or None
    """

    def __init__(self, tree: dict = None):
        self._tree: dict = tree or {}

    def __getitem__(self, label: str, /) -> Any:
        """
        Retrieves a value or subtree from the tree using a dot-separated label.

        :param label: Dot-separated path to a node (e.g., "foo.bar.baz").
        :type label: str
        :return: Either a nested TreeStructure or a leaf value.
        :rtype: TreeStructure or Any
        :raises KeyError: If traversal encounters a non-dict before the full path is consumed.
        """
        keys = label.strip().split(".")
        node = self._tree
        for key in keys:
            if not isinstance(node, dict):
                raise KeyError(f"Cannot traverse into non-dict at '{key}'")
            node = node[key]
        if isinstance(node, dict):
            return TreeStructure(node)
        else:
            return node

    def __setitem__(self, label: str, value: Any, /):
        keys = label.strip().split(".")
        node = self._tree
        for key in keys[:-1]:
            if key not in node or not isinstance(node[key], dict):
                node[key] = {}
            node = node[key]

        if isinstance(value, TreeStructure):
            node[keys[-1]] = value._tree
        else:
            node[keys[-1]] = value

    def __add__(self, other: Self, /) -> Self:
        if not isinstance(other, TreeStructure):
            return NotImplemented

        def merge_dicts(a: dict, b: dict, path="") -> dict:
            result = {}
            all_keys = set(a) | set(b)
            for key in all_keys:
                val_a = a.get(key)
                val_b = b.get(key)
                sub_path = f"{path}.{key}" if path else key

                if key in a and key in b:
                    if isinstance(val_a, dict) and isinstance(val_b, dict):
                        result[key] = merge_dicts(val_a, val_b, sub_path)
                    elif val_a == val_b:
                        result[key] = val_a  # Identical leaf value
                    else:
                        raise ValueError(
                            f"Conflict at '{sub_path}': {val_a} != {val_b}"
                        )
                else:
                    result[key] = val_a if key in a else val_b
            return result

        merged = merge_dicts(self._tree, other._tree)
        return TreeStructure(merged)

    # TODO: add more arithmetic functions
    # def __sub__(self) -> Self:

    def __and__(self, other: Self, /) -> Self:
        if not isinstance(other, TreeStructure):
            return NotImplemented

        def intersect_dicts(a: dict, b: dict, path="") -> dict:
            result = {}
            for key in a.keys() & b.keys():
                val_a = a[key]
                val_b = b[key]
                sub_path = f"{path}.{key}" if path else key

                if isinstance(val_a, dict) and isinstance(val_b, dict):
                    child = intersect_dicts(val_a, val_b, sub_path)
                    if child:  # keep only if non-empty
                        result[key] = child
                elif val_a == val_b:
                    result[key] = val_a
                else:
                    raise ValueError(f"Conflict at '{sub_path}': {val_a} != {val_b}")
            return result

        return TreeStructure(intersect_dicts(self._tree, other._tree))

    def __or__(self, other: Self, /) -> Self:
        if not isinstance(other, TreeStructure):
            return NotImplemented

        def union_dicts(a: dict, b: dict, path="") -> dict:
            result = {}
            all_keys = set(a) | set(b)
            for key in all_keys:
                val_a = a.get(key)
                val_b = b.get(key)
                sub_path = f"{path}.{key}" if path else key

                if key in a and key in b:
                    if isinstance(val_a, dict) and isinstance(val_b, dict):
                        result[key] = union_dicts(val_a, val_b, sub_path)
                    elif val_a == val_b:
                        result[key] = val_a
                    else:
                        raise ValueError(f"Conflict at '{sub_path}': {val_a} != {val_b}")
                else:
                    result[key] = val_a if key in a else val_b
            return result

        return TreeStructure(union_dicts(self._tree, other._tree))

    def __xor__(self, other: Self, /) -> Self:
        if not isinstance(other, TreeStructure):
            return NotImplemented

        def xor_dicts(a: dict, b: dict, path="") -> dict:
            result = {}
            all_keys = set(a) | set(b)
            for key in all_keys:
                in_a = key in a
                in_b = key in b
                sub_path = f"{path}.{key}" if path else key

                if in_a and in_b:
                    val_a = a[key]
                    val_b = b[key]
                    if isinstance(val_a, dict) and isinstance(val_b, dict):
                        child = xor_dicts(val_a, val_b, sub_path)
                        if child:  # keep only if non-empty
                            result[key] = child
                    elif val_a == val_b:
                        # same leaf in both trees → exclude
                        continue
                    else:
                        raise ValueError(f"Conflict at '{sub_path}': {val_a} != {val_b}")
                else:
                    result[key] = a.get(key) if in_a else b.get(key)
            return result

        return TreeStructure(xor_dicts(self._tree, other._tree))
    def __iter__(self) -> Iterator[tuple[str, T]]:
        return iter(self.branches_with_leaves())

    def __len__(self) -> int:
        """
        Counts the number of leaf nodes in the tree.

        :return: Number of leaves.
        :rtype: int
        """

        def recurse(tree: dict, count: int):
            for _, v in tree.items():
                if isinstance(v, dict):
                    count += recurse(v, 0)
                else:
                    count += 1
            return count

        return recurse(self._tree, 0)

    def __eq__(self, other: Self, /) -> bool:
        if not isinstance(TreeStructure):
            return NotImplemented

        return self._tree == other._tree

    def __str__(self) -> str:
        """
        Returns a plain (colorless) tree structure string.
        """

        def build_tree(subtree, rich_node):
            if isinstance(subtree, dict):
                for key, value in subtree.items():
                    child = rich_node.add(f"{key}")
                    build_tree(value, child)
            else:
                rich_node.add(type(subtree).__name__)

        tree = RichTree("TreeStructure")
        build_tree(self._tree, tree)

        string_buffer = StringIO()
        console = Console(
            file=string_buffer,
            markup=False,
            color_system=None,
            force_terminal=False,
            width=80,
        )
        console.print(tree)
        return string_buffer.getvalue()

    def __repr__(self):
        return f"{TreeStructure.__name__}(n_elem: {self.__len__()})"

    @property
    def branches(self) -> list[str]:
        """
        Retrieve the complete set of dot-delimited paths to all leaf nodes in the tree.

        This method performs a depth-first traversal of the internal tree representation,
        returning the fully qualified label paths that uniquely identify each leaf node.

        :return: A list of strings representing the hierarchical paths to each leaf.
        :rtype: list[str]
        """
        paths = []

        def recurse(subtree, path):
            if isinstance(subtree, dict):
                for k, v in subtree.items():
                    recurse(v, path + [k])
            else:
                paths.append(".".join(path))

        recurse(self._tree, [])
        return paths

    @property
    def leaves(self) -> list[T]:
        """
        Retrieve the values stored at all leaf nodes in the tree.

        This method performs a depth-first traversal of the internal tree structure,
        collecting the values found at the terminal nodes (leaves), irrespective of
        their associated labels or hierarchical position.

        :return: A list containing the values of all leaf nodes.
        :rtype: list[T]
        """
        leaves_list = []

        def recurse(subtree):
            if isinstance(subtree, dict):
                for _, v in subtree.items():
                    recurse(v)
            else:
                leaves_list.append(subtree)

        recurse(self._tree)
        return leaves_list

    def branches_with_leaves(self) -> list[tuple[str, T]]:
        """
        Retrieve a list of (path, value) pairs corresponding to all leaf nodes.

        This method returns each leaf node in the tree along with its full hierarchical
        path. The path is expressed as a dot-separated string (e.g., ``"root.subkey.leaf"``),
        and the value corresponds to the data stored at the leaf node.

        :return: A list of tuples, each containing a dot-delimited label path and the corresponding leaf value.
        :rtype: list[tuple[str, T]]
        """
        res = []

        def recurse(subtree, path):
            if isinstance(subtree, dict):
                for k, v in subtree.items():
                    recurse(v, path + [k])
            else:
                res.append((".".join(path), subtree))

        recurse(self._tree, [])
        return res

    def _is_valid_label(self, label: str) -> bool:
        """
        Checks whether a given dot-separated label exists in the tree.

        :param label: Path to check.
        :type label: str
        :return: True if valid, False otherwise.
        :rtype: bool
        """
        keys = label.strip().split(".")
        node = self._tree
        for key in keys:
            if not isinstance(node, dict):
                return False
            node = node[key]
        return True

    def to_subtree(self, label: str) -> Self:
        """
        Extracts a subtree rooted at a specific label.

        :param label: Dot-separated path to the root of the desired subtree.
        :type label: str
        :return: A new TreeStructure instance with the subtree.
        :rtype: TreeStructure
        """
        keys = label.strip().split(".")
        return TreeStructure({keys[-1]: self[label].as_dict()})

    def filter(self, substrings: str | list[str]) -> Self:
        """
        Return a new TreeStructure containing only the branches whose labels
        (dot-separated paths) contain at least one of the given substrings.

        :param substrings: Substring or list of substrings to search for.
        :type substrings: str | list[str]
        :return: A new TreeStructure with the filtered branches.
        :rtype: TreeStructure
        """
        if isinstance(substrings, str):
            substrings = [substrings]

        if len(substrings) == 0: # special, return nothing
            return TreeStructure()

        result = {}
        for path, value in self.branches_with_leaves():
            if any(sub in path for sub in substrings):
                keys = path.split(".")
                sub_tree = result
                for key in keys[:-1]:
                    sub_tree = sub_tree.setdefault(key, {})
                sub_tree[keys[-1]] = value

        return TreeStructure(result)

    def filter_out(self, substrings: str | list[str]) -> Self:
        """
        Return a new TreeStructure containing only the branches whose labels
        (dot-separated paths) don't contain any of the given substrings.

        :param substrings: Substring or list of substrings to search for.
        :type substrings: str | list[str]
        :return: A new TreeStructure with the filtered branches.
        :rtype: TreeStructure
        """
        if isinstance(substrings, str):
            substrings = [substrings]

        if len(substrings) == 0: # special, return all
            return TreeStructure(self._tree)

        result = {}
        for path, value in self.branches_with_leaves():
            if any(sub in path for sub in substrings):
                continue
            keys = path.split(".")
            sub_tree = result
            for key in keys[:-1]:
                sub_tree = sub_tree.setdefault(key, {})
            sub_tree[keys[-1]] = value

        return TreeStructure(result)

    def as_dict(self) -> dict:
        return self._tree
