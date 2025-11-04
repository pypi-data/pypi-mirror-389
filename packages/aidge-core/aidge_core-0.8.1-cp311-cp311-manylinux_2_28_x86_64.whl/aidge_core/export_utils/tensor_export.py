"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

import os
from pathlib import Path

from aidge_core.export_utils.code_generation import generate_file
from aidge_core.export_utils.data_conversion import aidge2c
from aidge_core import Tensor


def tensor_to_c(tensor: Tensor) -> str:
    """Given a :py:class:``aigd_core.Tensor``, return a C description of the tensor.
    For example:
    {
        {1, 2},
        {3, 4}
    }

    :param tensor: Tensor to transform to a string
    :type tensor: Tensor
    :return: String representation of a C array
    :rtype: str
    """
    return str(tensor)

def generate_input_file(export_folder:str,
                        array_name:str,
                        tensor:Tensor,
                        template_path:str = None):

    # If directory doesn't exist, create it
    if not os.path.exists(export_folder):
        os.makedirs(export_folder)
    print(f"gen : {export_folder}/{array_name}.h")
    ROOT = Path(__file__).resolve().parents[0]

    if tensor.impl:
        fallback_tensor = Tensor()
        tensor_host = tensor.ref_from(fallback_tensor, "cpu")
        generate_file(
            file_path=f"{export_folder}/{array_name}.h",
            template_path=str(ROOT / "templates" / "c_data.jinja") if template_path is None else template_path,
            dims = tensor.dims,
            data_t = aidge2c(tensor.dtype),
            name = array_name,
            values = list(tensor_host)
        )
    else:
        generate_file(
            file_path=f"{export_folder}/{array_name}.h",
            template_path=str(ROOT / "templates" / "c_data.jinja") if template_path is None else template_path,
            dims = tensor.dims,
            data_t = aidge2c(tensor.dtype),
            name = array_name,
            values = []
        )
