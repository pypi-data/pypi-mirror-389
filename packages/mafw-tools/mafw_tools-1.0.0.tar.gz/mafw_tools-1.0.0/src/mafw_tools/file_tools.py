#  Copyright 2025 European Union
#  Author: Bulgheroni Antonio (antonio.bulgheroni@ec.europa.eu)
#  SPDX-License-Identifier: EUPL-1.2
"""
File tools module.

This module provides utilities for handling file operations, particularly
pickle serialization/deserialization and file name generation.

.. versionadded:: 1.0.0

Functions:
    save_to_pickle: Save dictionary-like objects to a pickle file
    load_from_pickle: Load objects from a pickle file
    generate_new_file_name: Generate a new file name based on an original file name

Example usage::

    >>> from mafw_tools.file_tools import save_to_pickle, load_from_pickle
    >>> data = {'key': 'value'}
    >>> save_to_pickle('data.pkl', zipped=True, my_data=data)
    >>> loaded_data = load_from_pickle('data.pkl')
"""

import pickle
import zipfile
from pathlib import Path
from typing import Any


def save_to_pickle(filepath: str | Path, zipped: bool = True, **kwargs):
    """
    Save a dictionary-like object to a pickle file.

    This function is very helpful when there is the need to save multiple objects
    to the same binary file. The object to be serialized and saved to the file
    must be provided in the form of keyword arguments.

    Here is an example:

    .. code-block:: python

        my_first_object = [1, 2, 3, 4]
        my_second_object = dict(field1='abc', field2='cba')

        save_to_pickle(
            'my_pickle_file.sav',
            zipped=False,
            object1=my_first_object,
            object2=my_second_object,
        )

    A dictionary object in the form of :python:`{object1 : my_first_object, object2 : my_second_object}`
    is saved in the pickle file.

    :param filepath: The output file name
    :type filepath: str | Path
    :param zipped: Flag to select if the output file should be compressed or not. Defaults to True
    :type zipped: bool, optional
    :param kwargs: The objects to the saved.
    """
    objects_dict = kwargs

    if isinstance(filepath, str):
        filepath = Path(filepath)

    if zipped:
        # be sure about the extension
        if filepath.suffix == '.zip':
            filepath = filepath.with_suffix('.sav')

    with open(filepath, 'wb') as f:
        pickle.dump(objects_dict, f)

    if zipped:
        with zipfile.ZipFile(filepath.with_suffix('.zip'), 'w', compression=zipfile.ZIP_LZMA) as zip:
            zip.write(filepath, arcname=filepath.name)
        filepath.unlink()


def load_from_pickle(filepath: str | Path) -> dict[str, Any]:
    """
    Load objects from a pickle file.

    This function loads objects that were previously saved using :func:`save_to_pickle`.
    It handles both compressed and uncompressed pickle files automatically.

    :param filepath: The path to the pickle file to load
    :type filepath: str | Path
    :return: Dictionary containing the loaded objects
    :rtype: dict[str, Any]
    """
    if isinstance(filepath, str):
        filepath = Path(filepath)

    zipped = zipfile.is_zipfile(filepath)

    if zipped:
        with zipfile.ZipFile(filepath) as zip:
            with zip.open(filepath.with_suffix('.sav').name) as file:
                objects_dict = pickle.load(file)
    else:
        with open(filepath, 'rb') as file:
            objects_dict = pickle.load(file)

    return objects_dict


def generate_new_file_name(
    original_file_name: str | Path, new_base_path: str | Path, extra_suffix: str = None, new_extension: str = None
) -> Path:
    """
    Generate a new file name including its full path based on an original file name.

    The generated file name will have the new base path provided, an extra suffix
    (if provided) just before the extension, and if a new extension is provided
    then this is also replaced.

    :param original_file_name: The starting file name. It can be the full file name of an image. It does not need to be the full path. The filename is just fine.
    :type original_file_name: str | Path
    :param new_base_path: The new base path to be appended to the newly generated filename.
    :type new_base_path: str | Path
    :param extra_suffix: A string to be added just before the file extension.
    :type extra_suffix: str, optional, defaults to None
    :param new_extension: A new extension to replace the old one.
    :type new_extension: str, optional, defaults to None
    :return: The newly generated file name
    :rtype: Path
    """

    if isinstance(original_file_name, str):
        original_file_name = Path(original_file_name)

    if isinstance(new_base_path, str):
        new_base_path = Path(new_base_path)

    # be sure that the new path exists.
    new_base_path.mkdir(exist_ok=True, parents=True)

    if new_extension:
        if not new_extension.startswith('.'):
            new_extension = '.' + new_extension
        new_file_name = Path(original_file_name.with_suffix(new_extension).name)
    else:
        new_file_name = Path(original_file_name.name)

    if extra_suffix:
        if not extra_suffix.startswith('_'):
            extra_suffix = '_' + extra_suffix
        new_file_name = Path(new_file_name.stem + extra_suffix + new_file_name.suffix)

    return new_base_path / new_file_name
