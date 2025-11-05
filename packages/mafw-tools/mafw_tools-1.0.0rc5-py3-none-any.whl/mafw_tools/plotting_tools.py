#  Copyright 2025 European Union
#  Author: Bulgheroni Antonio (antonio.bulgheroni@ec.europa.eu)
#  SPDX-License-Identifier: EUPL-1.2
"""
Plotting tools module

This module provides utility functions for creating plots and visualizations
using matplotlib. It includes functionality for plotting images with various
customization options such as colorbars, axis control, and title management.

.. versionadded:: 1.0.0
"""

import matplotlib
from matplotlib import pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable


def plot_image(
    img,
    ax: plt.Axes,
    title: str = '',
    preserve_axis_limits: bool = False,
    axis_off: bool = False,
    attach_colorbar: bool = False,
    cbar_ticks: list = None,
    **kwargs,
) -> matplotlib.image.AxesImage:
    """
    Plot an image on a matplotlib axis with various customization options.

    This function provides a flexible way to display images with options for
    controlling axis appearance, adding colorbars, and preserving axis limits.

    :param img: The image data to be plotted
    :type img: numpy.ndarray
    :param ax: The matplotlib axis object where the image will be displayed
    :type ax: matplotlib.pyplot.Axes
    :param title: Title to be displayed on the axis. Defaults to empty string
    :type title: str
    :param preserve_axis_limits: If True, preserves the current axis limits. Defaults to False
    :type preserve_axis_limits: bool
    :param axis_off: If True, turns off the axis ticks and labels. Defaults to False
    :type axis_off: bool
    :param attach_colorbar: If True, attaches a colorbar to the plot. Defaults to False
    :type attach_colorbar: bool
    :param cbar_ticks: List of tick locations for the colorbar. Defaults to None
    :type cbar_ticks: list
    :param kwargs: Additional keyword arguments passed to matplotlib's imshow function
    :return: The matplotlib image object created
    :rtype: matplotlib.image.AxesImage
    :example:

        >>> import matplotlib.pyplot as plt
        >>> import numpy as np
        >>> fig, ax = plt.subplots()
        >>> data = np.random.rand(10, 10)
        >>> plot_image(
        ...     data, ax, title='Sample Image', attach_colorbar=True
        ... )
        >>> plt.show()
    """
    if preserve_axis_limits:
        x_lim, y_lim = ax.get_xlim(), ax.get_ylim()
        ax.cla()
    else:
        x_lim = y_lim = (0, 1)
    ax.set_xticks([])
    ax.set_yticks([])
    if axis_off:
        ax.axis('off')
    ax.set_title(title)
    map = ax.imshow(img, **kwargs)
    if preserve_axis_limits and x_lim != (0, 1) and y_lim != (0, 1):
        ax.set_xlim(*x_lim)
        ax.set_ylim(*y_lim)

    if attach_colorbar:
        # Use the make_axes_locatable to create a new axes for the colorbar
        divider = make_axes_locatable(ax)
        cax = divider.append_axes('right', size='5%', pad=0.05)

        # Add the colorbar to the new axes
        cbar = plt.colorbar(map, cax=cax)
        if cbar_ticks is not None:
            cbar.set_ticks(cbar_ticks)
            cbar.set_ticklabels([f'{i}' for i in cbar_ticks])

    return map
