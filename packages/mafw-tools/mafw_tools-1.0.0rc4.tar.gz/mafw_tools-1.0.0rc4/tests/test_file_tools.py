#  Copyright 2025 European Union
#  Author: Bulgheroni Antonio (antonio.bulgheroni@ec.europa.eu)
#  SPDX-License-Identifier: EUPL-1.2
"""
Unit tests for file_tools module.
"""

import pickle
from pathlib import Path

import pytest

from mafw_tools.file_tools import generate_new_file_name, load_from_pickle, save_to_pickle


class TestSaveToPickle:
    """Test cases for save_to_pickle function."""

    def test_save_to_pickle_uncompressed(self, tmp_path):
        """Test saving objects to uncompressed pickle file."""
        test_file = tmp_path / 'test_uncompressed.pkl'

        test_data = {'obj1': [1, 2, 3], 'obj2': {'key': 'value'}}

        save_to_pickle(test_file, zipped=False, **test_data)

        # Verify file was created
        assert test_file.exists()

        # Verify content by loading it back
        loaded_data = load_from_pickle(test_file)
        assert loaded_data == test_data

    def test_save_to_pickle_compressed(self, tmp_path):
        """Test saving objects to compressed pickle file."""
        test_file = tmp_path / 'test_compressed.sav'

        test_data = {'obj1': [1, 2, 3], 'obj2': {'key': 'value'}}

        save_to_pickle(test_file, zipped=True, **test_data)

        # Verify zip file was created
        zip_file = test_file.with_suffix('.zip')
        assert zip_file.exists()

        # Verify original file was removed
        assert not test_file.exists()

        # Verify content by loading it back
        loaded_data = load_from_pickle(zip_file)
        assert loaded_data == test_data

    def test_save_to_pickle_compressed_nozip(self, tmp_path):
        """Test saving objects to compressed pickle file."""
        test_file = tmp_path / 'test_compressed.zip'

        test_data = {'obj1': [1, 2, 3], 'obj2': {'key': 'value'}}

        save_to_pickle(test_file, zipped=True, **test_data)

        # Verify zip file was created
        zip_file = test_file.with_suffix('.zip')
        assert zip_file.exists()

        # Verify original file was removed
        assert not test_file.with_suffix('.sav').exists()

        # Verify content by loading it back
        loaded_data = load_from_pickle(zip_file)
        assert loaded_data == test_data

    def test_save_to_pickle_with_string_filepath(self, tmp_path):
        """Test saving with string filepath instead of Path object."""
        test_file = str(tmp_path / 'test_string.pkl')

        test_data = {'obj1': [1, 2, 3]}

        save_to_pickle(test_file, zipped=False, **test_data)

        # Verify file was created
        assert Path(test_file).exists()

        # Verify content
        loaded_data = load_from_pickle(test_file)
        assert loaded_data == test_data

    def test_save_to_pickle_empty_objects(self, tmp_path):
        """Test saving empty objects."""
        test_file = tmp_path / 'test_empty.pkl'

        save_to_pickle(test_file, zipped=False)

        # Verify file was created
        assert test_file.exists()

        # Verify content
        loaded_data = load_from_pickle(test_file)
        assert loaded_data == {}

    def test_save_to_pickle_with_special_characters(self, tmp_path):
        """Test saving objects with special characters."""
        test_file = tmp_path / 'test_special.pkl'

        test_data = {'unicode': 'café', 'emoji': '😀🎉', 'list': [1, 'a', {'nested': True}]}

        save_to_pickle(test_file, zipped=False, **test_data)

        # Verify content
        loaded_data = load_from_pickle(test_file)
        assert loaded_data == test_data


class TestLoadFromPickle:
    """Test cases for load_from_pickle function."""

    def test_load_from_pickle_uncompressed(self, tmp_path):
        """Test loading from uncompressed pickle file."""
        test_file = tmp_path / 'test_load.pkl'

        test_data = {'obj1': [1, 2, 3], 'obj2': {'key': 'value'}}

        # Save first
        save_to_pickle(test_file, zipped=False, **test_data)

        # Load and verify
        loaded_data = load_from_pickle(test_file)
        assert loaded_data == test_data

    def test_load_from_pickle_compressed(self, tmp_path):
        """Test loading from compressed pickle file."""
        test_file = tmp_path / 'test_load_compressed.sav'

        test_data = {'obj1': [1, 2, 3], 'obj2': {'key': 'value'}}

        # Save first
        save_to_pickle(test_file, zipped=True, **test_data)

        # Load and verify
        zip_file = test_file.with_suffix('.zip')
        loaded_data = load_from_pickle(zip_file)
        assert loaded_data == test_data

    def test_load_from_pickle_nonexistent_file(self, tmp_path):
        """Test loading from non-existent file raises FileNotFoundError."""
        nonexistent_file = tmp_path / 'nonexistent.pkl'

        with pytest.raises(FileNotFoundError):
            load_from_pickle(nonexistent_file)

    def test_load_from_pickle_invalid_pickle(self, tmp_path):
        """Test loading from invalid pickle file raises pickle.UnpicklingError."""
        test_file = tmp_path / 'invalid.pkl'

        # Create an invalid pickle file
        test_file.write_text('not a pickle file')

        with pytest.raises(pickle.UnpicklingError):
            load_from_pickle(test_file)

    def test_load_from_pickle_with_string_filepath(self, tmp_path):
        """Test loading with string filepath instead of Path object."""
        test_file = str(tmp_path / 'test_string.pkl')

        test_data = {'obj1': [1, 2, 3]}

        # Save first
        save_to_pickle(test_file, zipped=False, **test_data)

        # Load and verify
        loaded_data = load_from_pickle(test_file)
        assert loaded_data == test_data


class TestGenerateNewFileName:
    """Test cases for generate_new_file_name function."""

    def test_generate_new_file_name_basic(self, tmp_path):
        """Test basic file name generation."""
        original_file = 'original.txt'
        new_base = tmp_path / 'new_folder'

        result = generate_new_file_name(original_file, new_base)

        expected = new_base / 'original.txt'
        assert result == expected
        assert expected.parent.exists()

    def test_generate_new_file_name_with_extra_suffix(self, tmp_path):
        """Test file name generation with extra suffix."""
        original_file = 'original.txt'
        new_base = tmp_path / 'new_folder'

        result = generate_new_file_name(original_file, new_base, extra_suffix='_backup')

        expected = new_base / 'original_backup.txt'
        assert result == expected

    def test_generate_new_file_name_with_extra_suffix_no_underscore(self, tmp_path):
        """Test file name generation with extra suffix that doesn't start with underscore."""
        original_file = 'original.txt'
        new_base = tmp_path / 'new_folder'

        result = generate_new_file_name(original_file, new_base, extra_suffix='backup')

        expected = new_base / 'original_backup.txt'
        assert result == expected

    def test_generate_new_file_name_with_new_extension(self, tmp_path):
        """Test file name generation with new extension."""
        original_file = 'original.txt'
        new_base = tmp_path / 'new_folder'

        result = generate_new_file_name(original_file, new_base, new_extension='.dat')

        expected = new_base / 'original.dat'
        assert result == expected

    def test_generate_new_file_name_with_new_extension_no_dot(self, tmp_path):
        """Test file name generation with new extension that doesn't start with dot."""
        original_file = 'original.txt'
        new_base = tmp_path / 'new_folder'

        result = generate_new_file_name(original_file, new_base, new_extension='dat')

        expected = new_base / 'original.dat'
        assert result == expected

    def test_generate_new_file_name_both_modifications(self, tmp_path):
        """Test file name generation with both extra suffix and new extension."""
        original_file = 'original.txt'
        new_base = tmp_path / 'new_folder'

        result = generate_new_file_name(original_file, new_base, extra_suffix='backup', new_extension='.dat')

        expected = new_base / 'original_backup.dat'
        assert result == expected

    def test_generate_new_file_name_with_full_path_original(self, tmp_path):
        """Test file name generation with full path original file."""
        original_file = tmp_path / 'original.txt'
        new_base = tmp_path / 'new_folder'

        result = generate_new_file_name(original_file, new_base)

        expected = new_base / 'original.txt'
        assert result == expected

    def test_generate_new_file_name_with_string_paths(self, tmp_path):
        """Test file name generation with string paths."""
        original_file = 'original.txt'
        new_base = str(tmp_path / 'new_folder')

        result = generate_new_file_name(original_file, new_base)

        expected = Path(new_base) / 'original.txt'
        assert result == expected

    def test_generate_new_file_name_no_extension(self, tmp_path):
        """Test file name generation with no extension."""
        original_file = 'original'
        new_base = tmp_path / 'new_folder'

        result = generate_new_file_name(original_file, new_base)

        expected = new_base / 'original'
        assert result == expected

    def test_generate_new_file_name_no_extension_with_suffix(self, tmp_path):
        """Test file name generation with no extension and extra suffix."""
        original_file = 'original'
        new_base = tmp_path / 'new_folder'

        result = generate_new_file_name(original_file, new_base, extra_suffix='backup')

        expected = new_base / 'original_backup'
        assert result == expected


class TestIntegration:
    """Integration tests for file_tools module."""

    @pytest.mark.integration_test
    def test_save_and_load_roundtrip(self, tmp_path):
        """Test complete roundtrip save/load cycle."""
        test_file = tmp_path / 'roundtrip.pkl'

        # Original data
        original_data = {
            'string': 'hello world',
            'number': 42,
            'list': [1, 2, 3],
            'dict': {'nested': 'value'},
            'none': None,
        }

        # Save
        save_to_pickle(test_file, zipped=False, **original_data)

        # Load
        loaded_data = load_from_pickle(test_file)

        # Verify
        assert loaded_data == original_data

    @pytest.mark.integration_test
    def test_save_and_load_compressed_roundtrip(self, tmp_path):
        """Test complete roundtrip save/load cycle with compression."""
        test_file = tmp_path / 'roundtrip_compressed.sav'

        # Original data
        original_data = {
            'string': 'hello world',
            'number': 42,
            'list': [1, 2, 3],
            'dict': {'nested': 'value'},
            'none': None,
        }

        # Save
        save_to_pickle(test_file, zipped=True, **original_data)

        # Load
        zip_file = test_file.with_suffix('.zip')
        loaded_data = load_from_pickle(zip_file)

        # Verify
        assert loaded_data == original_data


class TestEdgeCases:
    """Test edge cases for all functions."""

    def test_save_to_pickle_with_zipped_false_and_zip_suffix(self, tmp_path):
        """Test save_to_pickle with zipped=False but .zip suffix."""
        test_file = tmp_path / 'test.zip'  # Should remain as .zip since zipped=False

        save_to_pickle(test_file, zipped=False, obj=[1, 2, 3])

        # With zipped=False, the file should keep its .zip extension
        assert test_file.exists()
        assert not test_file.with_suffix('.sav').exists()

        # Verify content can still be loaded
        loaded_data = load_from_pickle(test_file)
        assert loaded_data == {'obj': [1, 2, 3]}

    def test_generate_new_file_name_empty_strings(self, tmp_path):
        """Test generate_new_file_name with empty strings."""
        result = generate_new_file_name('', tmp_path, extra_suffix='', new_extension='')
        expected = tmp_path / ''
        assert result == expected

    def test_generate_new_file_name_none_values(self, tmp_path):
        """Test generate_new_file_name with None values."""
        result = generate_new_file_name('test.txt', tmp_path, extra_suffix=None, new_extension=None)
        expected = tmp_path / 'test.txt'
        assert result == expected

    def test_generate_new_file_name_special_chars_in_filename(self, tmp_path):
        """Test generate_new_file_name with special characters in filename."""
        original_file = 'test-file_name.txt'
        new_base = tmp_path / 'new_folder'

        result = generate_new_file_name(original_file, new_base, extra_suffix='backup')

        expected = new_base / 'test-file_name_backup.txt'
        assert result == expected
