#  Copyright 2025 European Union
#  Author: Bulgheroni Antonio (antonio.bulgheroni@ec.europa.eu)
#  SPDX-License-Identifier: EUPL-1.2
"""
Unit tests for plotting_tools module
"""

from unittest.mock import MagicMock, patch

import numpy as np
from matplotlib.image import AxesImage

# Import the function to be tested
from mafw_tools.plotting_tools import plot_image


class TestPlotImage:
    """Test class for plot_image function"""

    def test_basic_functionality(self):
        """Test basic image plotting functionality"""
        # Create mock data and axis
        img = np.random.rand(10, 10)
        ax = MagicMock()

        # Mock the return value of imshow to be an AxesImage
        mock_image = MagicMock(spec=AxesImage)
        ax.imshow.return_value = mock_image

        # Call the function
        result = plot_image(img, ax)

        # Verify the result is an AxesImage
        assert isinstance(result, AxesImage)

        # Verify that imshow was called with correct parameters
        ax.imshow.assert_called_once_with(img)

        # Verify that title was set
        ax.set_title.assert_called_once_with('')

        # Verify that ticks were cleared
        ax.set_xticks.assert_called_once_with([])
        ax.set_yticks.assert_called_once_with([])

    def test_with_title(self):
        """Test plotting with custom title"""
        img = np.random.rand(5, 5)
        ax = MagicMock()
        mock_image = MagicMock(spec=AxesImage)
        ax.imshow.return_value = mock_image

        result = plot_image(img, ax, title='Test Title')

        # Verify the result is an AxesImage
        assert isinstance(result, AxesImage)

        ax.set_title.assert_called_once_with('Test Title')

    def test_preserve_axis_limits_false(self):
        """Test behavior when preserve_axis_limits is False"""
        img = np.random.rand(5, 5)
        ax = MagicMock()
        mock_image = MagicMock(spec=AxesImage)
        ax.imshow.return_value = mock_image

        result = plot_image(img, ax, preserve_axis_limits=False)

        # Verify the result is an AxesImage
        assert isinstance(result, AxesImage)

        # Should not call cla() since preserve_axis_limits is False
        ax.cla.assert_not_called()

    def test_preserve_axis_limits_true(self):
        """Test behavior when preserve_axis_limits is True"""
        img = np.random.rand(5, 5)
        ax = MagicMock()
        ax.get_xlim.return_value = (0, 10)
        ax.get_ylim.return_value = (0, 10)
        mock_image = MagicMock(spec=AxesImage)
        ax.imshow.return_value = mock_image

        result = plot_image(img, ax, preserve_axis_limits=True)

        # Verify the result is an AxesImage
        assert isinstance(result, AxesImage)

        # Should call cla() and restore limits
        ax.cla.assert_called_once()
        ax.set_xlim.assert_called_once_with(0, 10)
        ax.set_ylim.assert_called_once_with(0, 10)

    def test_axis_off(self):
        """Test turning off axis"""
        img = np.random.rand(5, 5)
        ax = MagicMock()
        mock_image = MagicMock(spec=AxesImage)
        ax.imshow.return_value = mock_image

        result = plot_image(img, ax, axis_off=True)

        # Verify the result is an AxesImage
        assert isinstance(result, AxesImage)

        ax.axis.assert_called_once_with('off')

    @patch('matplotlib.pyplot.colorbar')
    @patch('mafw_tools.plotting_tools.make_axes_locatable')
    def test_attach_colorbar_no_ticks(self, mock_divider, mock_colorbar):
        """Test attaching colorbar without custom ticks"""
        img = np.random.rand(5, 5)
        ax = MagicMock()
        mock_image = MagicMock(spec=AxesImage)
        ax.imshow.return_value = mock_image

        # Create a proper mock for the divider instance that doesn't try to spec mock objects
        # The key fix: make sure we don't create complex specs that conflict with matplotlib internals
        mock_divider_instance = MagicMock()
        mock_divider.return_value = mock_divider_instance

        # Mock the append_axes method to return a simple mock that won't cause conflicts
        mock_cax = MagicMock()
        # Make sure the mock_cax behaves like a proper axes object for the test
        mock_cax.set_position = MagicMock()
        mock_cax.get_position = MagicMock()

        mock_divider_instance.append_axes.return_value = mock_cax

        # Mock the colorbar function to return a mock
        mock_colorbar_instance = MagicMock()
        mock_colorbar.return_value = mock_colorbar_instance

        result = plot_image(img, ax, attach_colorbar=True)

        # Verify the result is an AxesImage
        assert isinstance(result, AxesImage)

        # Verify colorbar creation
        mock_divider.assert_called_once_with(ax)
        mock_divider_instance.append_axes.assert_called_once_with('right', size='5%', pad=0.05)
        mock_colorbar.assert_called_once_with(result, cax=mock_cax)
        mock_colorbar_instance.set_ticks.assert_not_called()
        mock_colorbar_instance.set_ticklabels.assert_not_called()

    @patch('matplotlib.pyplot.colorbar')
    @patch('mafw_tools.plotting_tools.make_axes_locatable')
    def test_attach_colorbar_with_ticks(self, mock_divider, mock_colorbar):
        """Test attaching colorbar with custom ticks"""
        img = np.random.rand(5, 5)
        ax = MagicMock()
        mock_image = MagicMock(spec=AxesImage)
        ax.imshow.return_value = mock_image

        # Create a proper mock for the divider instance that doesn't try to spec mock objects
        # The key fix: make sure we don't create complex specs that conflict with matplotlib internals
        mock_divider_instance = MagicMock()
        mock_divider.return_value = mock_divider_instance

        # Mock the append_axes method to return a simple mock that won't cause conflicts
        mock_cax = MagicMock()
        # Make sure the mock_cax behaves like a proper axes object for the test
        mock_cax.set_position = MagicMock()
        mock_cax.get_position = MagicMock()

        mock_divider_instance.append_axes.return_value = mock_cax

        # Mock the colorbar function to return a mock
        mock_colorbar_instance = MagicMock()
        mock_colorbar.return_value = mock_colorbar_instance

        result = plot_image(img, ax, attach_colorbar=True, cbar_ticks=[0, 0.5, 1])
        assert isinstance(result, AxesImage)

        # Verify colorbar creation with ticks
        mock_colorbar_instance.set_ticks.assert_called_once_with([0, 0.5, 1])
        mock_colorbar_instance.set_ticklabels.assert_called_once_with(['0', '0.5', '1'])

    def test_kwargs_passed_to_imshow(self):
        """Test that additional kwargs are passed to imshow"""
        img = np.random.rand(5, 5)
        ax = MagicMock()
        mock_image = MagicMock(spec=AxesImage)
        ax.imshow.return_value = mock_image

        result = plot_image(img, ax, cmap='viridis', alpha=0.7)
        assert isinstance(result, AxesImage)

        # Verify imshow was called with kwargs
        ax.imshow.assert_called_once_with(img, cmap='viridis', alpha=0.7)

    def test_edge_case_empty_image(self):
        """Test with empty image array"""
        img = np.array([]).reshape(0, 0)
        ax = MagicMock()
        mock_image = MagicMock(spec=AxesImage)
        ax.imshow.return_value = mock_image

        result = plot_image(img, ax)

        assert isinstance(result, AxesImage)

    def test_edge_case_single_pixel(self):
        """Test with single pixel image"""
        img = np.array([[1.0]])
        ax = MagicMock()
        mock_image = MagicMock(spec=AxesImage)
        ax.imshow.return_value = mock_image

        result = plot_image(img, ax)

        assert isinstance(result, AxesImage)
        ax.imshow.assert_called_once_with(img)

    def test_return_value(self):
        """Test that the function returns the correct type"""
        img = np.random.rand(5, 5)
        ax = MagicMock()
        mock_image = MagicMock(spec=AxesImage)
        ax.imshow.return_value = mock_image

        result = plot_image(img, ax)

        assert isinstance(result, AxesImage)

    @patch('matplotlib.pyplot.colorbar')
    @patch('mafw_tools.plotting_tools.make_axes_locatable')
    def test_integration_colorbar_creation(self, mock_divider, mock_colorbar):
        """Integration test for colorbar creation"""
        # Setup mocks
        img = np.random.rand(5, 5)
        ax = MagicMock()

        # Create a proper mock for the divider instance that doesn't try to spec mock objects
        # The key fix: make sure we don't create complex specs that conflict with matplotlib internals
        mock_divider_instance = MagicMock()
        mock_divider.return_value = mock_divider_instance

        # Mock the append_axes method to return a simple mock that won't cause conflicts
        mock_cax = MagicMock()
        # Make sure the mock_cax behaves like a proper axes object for the test
        mock_cax.set_position = MagicMock()
        mock_cax.get_position = MagicMock()

        mock_divider_instance.append_axes.return_value = mock_cax

        # Mock the colorbar function to return a mock
        mock_colorbar_instance = MagicMock()
        mock_colorbar.return_value = mock_colorbar_instance

        # Call function
        result = plot_image(img, ax, attach_colorbar=True)
        #
        # Verify calls
        mock_divider.assert_called_once_with(ax)
        mock_divider_instance.append_axes.assert_called_once_with('right', size='5%', pad=0.05)
        mock_colorbar.assert_called_once_with(result, cax=mock_cax)

    def test_preserve_axis_limits_with_default_values(self):
        """Test preserve_axis_limits with default axis limits"""
        img = np.random.rand(5, 5)
        ax = MagicMock()
        ax.get_xlim.return_value = (0, 1)
        ax.get_ylim.return_value = (0, 1)
        mock_image = MagicMock(spec=AxesImage)
        ax.imshow.return_value = mock_image

        result = plot_image(img, ax, preserve_axis_limits=True)
        assert isinstance(result, AxesImage)

        # Should not restore limits since they're default
        ax.set_xlim.assert_not_called()
        ax.set_ylim.assert_not_called()

    def test_multiple_calls(self):
        """Test multiple calls to the function don't interfere"""
        img1 = np.random.rand(5, 5)
        img2 = np.random.rand(5, 5)
        ax = MagicMock()
        mock_image1 = MagicMock(spec=AxesImage)
        mock_image2 = MagicMock(spec=AxesImage)
        ax.imshow.side_effect = [mock_image1, mock_image2]

        result1 = plot_image(img1, ax)
        result2 = plot_image(img2, ax)

        # Both should return AxesImage objects
        assert isinstance(result1, AxesImage)
        assert isinstance(result2, AxesImage)

        # imshow should be called twice
        assert ax.imshow.call_count == 2
