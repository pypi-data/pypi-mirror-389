"""
Visualization utilities for Sceptic pseudotime analysis.

This module provides publication-quality plotting functions for visualizing
Sceptic results, including confusion matrices and pseudotime distributions.
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import re
from typing import Optional, List, Union
import pandas as pd


def set_publication_style(
    small_size: int = 18,
    medium_size: int = 20,
    bigger_size: int = 24
) -> None:
    """
    Set matplotlib style parameters for publication-quality figures.

    Parameters
    ----------
    small_size : int, default=18
        Font size for small text elements.
    medium_size : int, default=20
        Font size for medium text elements (ticks, legend).
    bigger_size : int, default=24
        Font size for large text elements (titles, axis labels).

    Examples
    --------
    >>> set_publication_style()
    >>> # Now all subsequent plots will use these settings
    """
    plt.rc('font', size=small_size)
    plt.rc('axes', titlesize=bigger_size)
    plt.rc('axes', labelsize=bigger_size)
    plt.rc('xtick', labelsize=medium_size)
    plt.rc('ytick', labelsize=medium_size)
    plt.rc('legend', fontsize=medium_size)
    plt.rc('figure', titlesize=bigger_size)
    # Use Type 42 fonts for PDF compatibility
    plt.rcParams['pdf.fonttype'] = 42
    plt.rcParams['ps.fonttype'] = 42


def plot_confusion_matrix(
    confusion_matrix: np.ndarray,
    label_list: np.ndarray,
    output_path: Optional[str] = None,
    normalize: bool = True,
    cmap: str = "YlGnBu",
    figsize: tuple = (20, 18),
    xlabel: str = "Sceptic predicted time",
    ylabel: str = "Observed time",
    colorbar_label: str = "Normalized Counts",
    annot_fontsize: Optional[int] = None,
    tick_fontsize: Optional[int] = None,
    label_fontsize: Optional[int] = None,
    dpi: int = 300
) -> plt.Figure:
    """
    Create a publication-quality confusion matrix heatmap.

    Parameters
    ----------
    confusion_matrix : np.ndarray
        Confusion matrix from Sceptic (n_classes x n_classes).
    label_list : np.ndarray
        List of unique time labels for axis tick labels.
    output_path : str, optional
        Path to save the figure. If None, figure is not saved.
    normalize : bool, default=True
        If True, normalize by row (true labels).
    cmap : str, default="YlGnBu"
        Colormap for the heatmap.
    figsize : tuple, default=(20, 18)
        Figure size (width, height) in inches.
    xlabel : str, default="Sceptic predicted time"
        X-axis label.
    ylabel : str, default="Observed time"
        Y-axis label.
    colorbar_label : str, default="Normalized Counts"
        Colorbar label.
    annot_fontsize : int, optional
        Font size for annotations. If None, uses default (18).
    tick_fontsize : int, optional
        Font size for tick labels. If None, uses default (20).
    label_fontsize : int, optional
        Font size for axis labels. If None, uses default (24).
    dpi : int, default=300
        Resolution for saved figure.

    Returns
    -------
    matplotlib.figure.Figure
        The created figure object.

    Examples
    --------
    >>> fig = plot_confusion_matrix(
    ...     confusion_matrix=cm,
    ...     label_list=np.array([20, 25, 30, 35, 40]),
    ...     output_path="confusion_matrix.png"
    ... )
    """
    # Set default font sizes if not provided
    if annot_fontsize is None:
        annot_fontsize = 18
    if tick_fontsize is None:
        tick_fontsize = 20
    if label_fontsize is None:
        label_fontsize = 24

    # Normalize if requested
    if normalize:
        cm_normalized = confusion_matrix / confusion_matrix.sum(axis=1, keepdims=True)
    else:
        cm_normalized = confusion_matrix

    # Create figure with custom gridspec for colorbar
    fig, axs = plt.subplots(
        ncols=2,
        gridspec_kw=dict(width_ratios=[4.5, 0.05]),
        figsize=figsize
    )

    # Plot heatmap
    ax = sns.heatmap(
        cm_normalized,
        cmap=cmap,
        cbar=False,
        ax=axs[0],
        xticklabels=label_list,
        yticklabels=label_list,
        fmt='.1f',
        annot_kws={"fontsize": annot_fontsize}
    )

    # Set tick label sizes
    ax.set_xticklabels(ax.get_xticklabels(), fontsize=tick_fontsize)
    ax.set_yticklabels(ax.get_yticklabels(), fontsize=tick_fontsize)

    # Set axis labels
    ax.set_xlabel(xlabel, fontsize=label_fontsize)
    ax.set_ylabel(ylabel, fontsize=label_fontsize)

    # Create colorbar
    cbar = fig.colorbar(axs[0].collections[0], cax=axs[1])
    cbar.ax.tick_params(labelsize=tick_fontsize)
    cbar.ax.yaxis.set_label_position('left')
    cbar.ax.set_ylabel(colorbar_label, size=label_fontsize)

    # Save if path provided
    if output_path:
        plt.savefig(output_path, bbox_inches='tight', dpi=dpi)

    return fig


def plot_pseudotime_violin(
    pseudotime: np.ndarray,
    true_labels: np.ndarray,
    output_path: Optional[str] = None,
    figsize: tuple = (18, 10),
    palette: str = 'YlGnBu',
    xlabel: str = "True time labels",
    ylabel: str = "Sceptic pseudotime",
    title: str = "Pseudotime distribution across time labels",
    rotation: int = 45,
    label_fontsize: Optional[int] = None,
    title_fontsize: Optional[int] = None,
    dpi: int = 300
) -> plt.Figure:
    """
    Create violin plot showing pseudotime distribution across true time labels.

    Parameters
    ----------
    pseudotime : np.ndarray
        Predicted continuous pseudotime values.
    true_labels : np.ndarray
        True time labels (can be numeric or categorical).
    output_path : str, optional
        Path to save the figure. If None, figure is not saved.
    figsize : tuple, default=(18, 10)
        Figure size (width, height) in inches.
    palette : str, default='YlGnBu'
        Color palette for violins.
    xlabel : str, default="True time labels"
        X-axis label.
    ylabel : str, default="Sceptic pseudotime"
        Y-axis label.
    title : str, default="Pseudotime distribution across time labels"
        Plot title.
    rotation : int, default=45
        Rotation angle for x-axis tick labels.
    label_fontsize : int, optional
        Font size for axis labels. If None, uses default (24).
    title_fontsize : int, optional
        Font size for title. If None, uses label_fontsize + 2.
    dpi : int, default=300
        Resolution for saved figure.

    Returns
    -------
    matplotlib.figure.Figure
        The created figure object.

    Examples
    --------
    >>> fig = plot_pseudotime_violin(
    ...     pseudotime=pseudotime,
    ...     true_labels=donor_ages,
    ...     output_path="violin_plot.png"
    ... )
    """
    # Set default font sizes
    if label_fontsize is None:
        label_fontsize = 24
    if title_fontsize is None:
        title_fontsize = label_fontsize + 2

    # Prepare data
    df = pd.DataFrame({
        'true_labels': true_labels,
        'pseudotime': pseudotime
    })
    df = df.dropna()

    # Convert to string for categorical x-axis, but sort numerically if possible
    try:
        # Try to sort numerically
        df['true_labels_str'] = df['true_labels'].astype(float).astype(int).astype(str)
        order = sorted(df['true_labels_str'].unique(), key=lambda x: float(x))
    except (ValueError, TypeError):
        # If not numeric, sort alphabetically
        df['true_labels_str'] = df['true_labels'].astype(str)
        order = sorted(df['true_labels_str'].unique())

    # Create plot
    fig, ax = plt.subplots(figsize=figsize)

    sns.violinplot(
        x='true_labels_str',
        y='pseudotime',
        data=df,
        inner='box',
        cut=0,
        hue='true_labels_str',
        palette=palette,
        order=order,
        legend=False,
        ax=ax
    )

    # Aesthetics
    ax.set_xlabel(xlabel, fontsize=label_fontsize)
    ax.set_ylabel(ylabel, fontsize=label_fontsize)
    ax.set_title(title, fontsize=title_fontsize)
    ax.tick_params(axis='x', labelrotation=rotation)
    sns.despine()

    plt.tight_layout()

    # Save if path provided
    if output_path:
        plt.savefig(output_path, bbox_inches='tight', dpi=dpi)

    return fig


def plot_pseudotime_by_group(
    pseudotime: np.ndarray,
    true_labels: np.ndarray,
    group_labels: np.ndarray,
    output_dir: str,
    group_column_name: str = "group",
    time_column_name: str = "time",
    top_k: Optional[int] = None,
    figsize: tuple = (18, 10),
    palette: str = 'YlGnBu',
    xlabel: str = "True time labels",
    ylabel: str = "Sceptic pseudotime",
    title_template: str = "Pseudotime by time\nGroup: {group}",
    rotation: int = 45,
    label_fontsize: Optional[int] = None,
    title_fontsize: Optional[int] = None,
    dpi: int = 300
) -> None:
    """
    Create separate violin plots for each group (e.g., cell type).

    This function generates one violin plot per group showing how pseudotime
    varies across true time labels within that group. Useful for stratified analysis.

    Parameters
    ----------
    pseudotime : np.ndarray
        Predicted continuous pseudotime values.
    true_labels : np.ndarray
        True time labels (can be numeric or categorical).
    group_labels : np.ndarray
        Group labels (e.g., cell types, conditions).
    output_dir : str
        Directory to save the individual plots.
    group_column_name : str, default="group"
        Name for the group column in data preparation.
    time_column_name : str, default="time"
        Name for the time column in data preparation.
    top_k : int, optional
        Number of top groups (by frequency) to plot. If None, plot all groups.
    figsize : tuple, default=(18, 10)
        Figure size (width, height) in inches for each plot.
    palette : str, default='YlGnBu'
        Color palette for violins.
    xlabel : str, default="True time labels"
        X-axis label.
    ylabel : str, default="Sceptic pseudotime"
        Y-axis label.
    title_template : str, default="Pseudotime by time\\nGroup: {group}"
        Title template with {group} placeholder.
    rotation : int, default=45
        Rotation angle for x-axis tick labels.
    label_fontsize : int, optional
        Font size for axis labels. If None, uses default (24).
    title_fontsize : int, optional
        Font size for title. If None, uses label_fontsize + 2.
    dpi : int, default=300
        Resolution for saved figures.

    Returns
    -------
    None
        Plots are saved to output_dir.

    Examples
    --------
    >>> plot_pseudotime_by_group(
    ...     pseudotime=pseudotime,
    ...     true_labels=ages,
    ...     group_labels=cell_types,
    ...     output_dir="results/violin_by_cell_type"
    ... )
    """
    # Set default font sizes
    if label_fontsize is None:
        label_fontsize = 24
    if title_fontsize is None:
        title_fontsize = label_fontsize + 2

    # Prepare data
    df = pd.DataFrame({
        time_column_name: true_labels,
        'pseudotime': pseudotime,
        group_column_name: group_labels
    })
    df = df.dropna()

    # Convert time to numeric if possible for proper ordering
    try:
        df[f'{time_column_name}_num'] = df[time_column_name].astype(float).astype(int)
        time_order = sorted(df[f'{time_column_name}_num'].unique().tolist())
        time_order_str = [str(t) for t in time_order]
        df[f'{time_column_name}_str'] = df[f'{time_column_name}_num'].astype(str)
    except (ValueError, TypeError):
        df[f'{time_column_name}_str'] = df[time_column_name].astype(str)
        time_order_str = sorted(df[f'{time_column_name}_str'].unique())

    # Determine which groups to plot
    group_counts = df[group_column_name].value_counts()
    if top_k is not None:
        groups_to_plot = group_counts.head(top_k).index.tolist()
    else:
        groups_to_plot = group_counts.index.tolist()

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Helper function to sanitize filenames
    def sanitize_filename(name: str) -> str:
        """Replace problematic characters with underscores."""
        return re.sub(r'[^A-Za-z0-9_.-]+', '_', name)

    # Plot for each group
    for group in groups_to_plot:
        subset = df[df[group_column_name] == group]
        if subset.empty:
            continue

        fig, ax = plt.subplots(figsize=figsize)

        sns.violinplot(
            x=f'{time_column_name}_str',
            y='pseudotime',
            data=subset,
            order=time_order_str,
            inner='box',
            cut=0,
            hue=f'{time_column_name}_str',
            palette=palette,
            density_norm='width',
            legend=False,
            ax=ax
        )

        # Aesthetics
        ax.set_xlabel(xlabel, fontsize=label_fontsize)
        ax.set_ylabel(ylabel, fontsize=label_fontsize)
        ax.set_title(title_template.format(group=group), fontsize=title_fontsize)
        ax.tick_params(axis='x', labelrotation=rotation)
        sns.despine()

        plt.tight_layout()

        # Save
        filename = f"{sanitize_filename(str(group))}.png"
        filepath = os.path.join(output_dir, filename)
        plt.savefig(filepath, bbox_inches='tight', dpi=dpi)
        plt.close(fig)

    print(f"Saved {len(groups_to_plot)} violin plots to: {output_dir}")


def close_all_figures() -> None:
    """
    Close all open matplotlib figures to free memory.

    Useful when generating many plots in a loop.

    Examples
    --------
    >>> close_all_figures()
    """
    plt.close('all')
