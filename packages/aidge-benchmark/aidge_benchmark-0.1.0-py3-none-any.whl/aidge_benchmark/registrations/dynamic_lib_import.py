"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

import sys
import importlib

def load_package(package_name: str):
    """
    Ensures that a package is available and imported.

    If the package is already imported, it does nothing.
    If the package is available but not yet imported, it imports it.
    If the package is not available, raises an ImportError with a clear message.

    Args:
        package_name: The name of the package to check and import.

    Returns:
        The imported module object.

    Raises:
        ImportError: If the package is not installed.
    """
    if package_name in sys.modules:
        return sys.modules[package_name]

    spec = importlib.util.find_spec(package_name)
    if spec is None:
        raise ImportError(
            f"The package '{package_name}' is required for this functionality but is not installed. "
            f"Please install it with `pip install {package_name}`."
        )

    return importlib.import_module(package_name)