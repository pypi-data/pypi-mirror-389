"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

import numpy as np


def compare_tensors(
    actual: np.ndarray,
    expected: np.ndarray,
    rtol=1e-3,
    atol=1e-5,
    verbose: bool = False,
) -> bool:
    """
    Compares two tensors element-wise using relative and absolute tolerance.

    Args:
        actual (np.ndarray): The computed or observed tensor values.
        expected (np.ndarray): The reference or expected tensor values.
        rtol (float): Relative tolerance. Defaults to 1e-3.
        atol (float): Absolute tolerance. Defaults to 1e-5.
        verbose (bool): If True, prints detailed mismatch information, including indices and error values.

    Returns:
        bool: True if all elements are equal within the specified tolerances, False otherwise.
    """
    equality: np.ndarray = np.isclose(actual, expected, rtol=rtol, atol=atol)
    is_equal = bool(np.all(equality))
    if verbose:
        print(f"Equal: {is_equal}")
        if not is_equal:
            mismatches = ~equality
            n_mismatches = np.count_nonzero(mismatches)
            print(f"Mismatch:\t{n_mismatches}/{actual.size}")
            print(
                "Average diff: " \
                    f"rtol = {np.sum(np.abs((actual-expected)/expected))/actual.size}, " \
                    f"atol = {np.sum(np.abs(actual-expected))/actual.size}"
            )

            mismatch_indices = np.argwhere(mismatches)
            for idx in mismatch_indices[:10]:
                actual_val = actual[tuple(idx)]
                expected_val = expected[tuple(idx)]
                print(
                    f"  at index {idx}: " \
                        f"\t| actual={actual_val:.3E}, " \
                        f"\t| expected={expected_val:.3E}, " \
                        f"\t| adiff={np.abs(actual_val - expected_val):.5E}" \
                        f"\t| rdiff={np.abs((actual_val - expected_val)/expected_val):.5E}"
                )
    return is_equal
