"""
Evaluation utilities for Sceptic pseudotime analysis.

This module provides comprehensive evaluation metrics for assessing the quality
of pseudotime predictions, including both classification metrics (for discrete
time labels) and regression metrics (for continuous pseudotime values).
"""

import numpy as np
from typing import Tuple, Dict, Optional, Union
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    mean_absolute_error,
    mean_squared_error
)
from scipy import stats


def compute_classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    zero_division: int = 0
) -> Dict[str, Union[float, str]]:
    """
    Compute classification metrics for discrete time label predictions.

    Parameters
    ----------
    y_true : np.ndarray
        True encoded labels (integers from 0 to n_classes-1).
    y_pred : np.ndarray
        Predicted encoded labels (integers from 0 to n_classes-1).
    zero_division : int, default=0
        Value to return for metrics when there is a zero division.

    Returns
    -------
    dict
        Dictionary containing:
        - 'accuracy': Overall accuracy
        - 'balanced_accuracy': Balanced accuracy (accounts for class imbalance)
        - 'classification_report': Detailed per-class metrics as string

    Examples
    --------
    >>> y_true = np.array([0, 0, 1, 1, 2, 2])
    >>> y_pred = np.array([0, 1, 1, 1, 2, 2])
    >>> metrics = compute_classification_metrics(y_true, y_pred)
    >>> print(f"Accuracy: {metrics['accuracy']:.3f}")
    """
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)

    acc = accuracy_score(y_true, y_pred)
    bacc = balanced_accuracy_score(y_true, y_pred)
    report = classification_report(y_true, y_pred, zero_division=zero_division)

    return {
        'accuracy': acc,
        'balanced_accuracy': bacc,
        'classification_report': report
    }


def compute_correlation_metrics(
    pseudotime: np.ndarray,
    true_time: np.ndarray,
    nan_policy: str = 'omit'
) -> Dict[str, Tuple[float, float]]:
    """
    Compute correlation metrics between predicted pseudotime and true time values.

    This function computes three types of correlations:
    - Spearman: Rank-based correlation (monotonic relationship)
    - Pearson: Linear correlation
    - Kendall: Rank-based, more robust to ties

    Parameters
    ----------
    pseudotime : np.ndarray
        Predicted continuous pseudotime values.
    true_time : np.ndarray
        True continuous time values (e.g., hours, ages).
    nan_policy : str, default='omit'
        How to handle NaN values. Options: 'omit', 'propagate', 'raise'.

    Returns
    -------
    dict
        Dictionary containing:
        - 'spearman': (correlation coefficient, p-value)
        - 'pearson': (correlation coefficient, p-value)
        - 'kendall': (correlation coefficient, p-value)

    Examples
    --------
    >>> pseudotime = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
    >>> true_time = np.array([20, 30, 40, 50, 60])
    >>> corr = compute_correlation_metrics(pseudotime, true_time)
    >>> print(f"Spearman r={corr['spearman'][0]:.3f}")
    """
    # Ensure arrays are float and 1-D
    pseudotime = np.asarray(pseudotime, dtype=float).flatten()
    true_time = np.asarray(true_time, dtype=float).flatten()

    # Remove NaN values
    mask = np.isfinite(pseudotime) & np.isfinite(true_time)
    pseudotime_clean = pseudotime[mask]
    true_time_clean = true_time[mask]

    if len(pseudotime_clean) == 0:
        raise ValueError("No valid (non-NaN) paired values found for correlation.")

    # Compute correlations
    spearman_r, spearman_p = stats.spearmanr(pseudotime_clean, true_time_clean)
    pearson_r, pearson_p = stats.pearsonr(pseudotime_clean, true_time_clean)
    kendall_tau, kendall_p = stats.kendalltau(
        pseudotime_clean,
        true_time_clean,
        nan_policy=nan_policy
    )

    return {
        'spearman': (spearman_r, spearman_p),
        'pearson': (pearson_r, pearson_p),
        'kendall': (kendall_tau, kendall_p)
    }


def compute_regression_metrics(
    pseudotime: np.ndarray,
    true_time: np.ndarray
) -> Dict[str, float]:
    """
    Compute regression metrics (MAE and MSE) for pseudotime predictions.

    These metrics are useful when treating pseudotime estimation as a regression
    problem, measuring the absolute and squared errors between predicted and true values.

    Parameters
    ----------
    pseudotime : np.ndarray
        Predicted continuous pseudotime values.
    true_time : np.ndarray
        True continuous time values (e.g., hours, ages).

    Returns
    -------
    dict
        Dictionary containing:
        - 'mae': Mean Absolute Error
        - 'mse': Mean Squared Error
        - 'rmse': Root Mean Squared Error

    Examples
    --------
    >>> pseudotime = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
    >>> true_time = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
    >>> metrics = compute_regression_metrics(pseudotime, true_time)
    >>> print(f"MAE: {metrics['mae']:.3f}")
    """
    # Ensure arrays are float and 1-D
    pseudotime = np.asarray(pseudotime, dtype=float).flatten()
    true_time = np.asarray(true_time, dtype=float).flatten()

    # Remove NaN values
    mask = np.isfinite(pseudotime) & np.isfinite(true_time)
    pseudotime_clean = pseudotime[mask]
    true_time_clean = true_time[mask]

    if len(pseudotime_clean) == 0:
        raise ValueError("No valid (non-NaN) paired values found for regression metrics.")

    mae = mean_absolute_error(true_time_clean, pseudotime_clean)
    mse = mean_squared_error(true_time_clean, pseudotime_clean)
    rmse = np.sqrt(mse)

    return {
        'mae': mae,
        'mse': mse,
        'rmse': rmse
    }


def evaluate_sceptic_results(
    confusion_matrix: np.ndarray,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    pseudotime: np.ndarray,
    true_time: np.ndarray,
    include_regression: bool = False,
    verbose: bool = True
) -> Dict[str, Union[float, str, Tuple[float, float]]]:
    """
    Comprehensive evaluation of Sceptic results.

    This function combines all evaluation metrics into a single comprehensive report,
    including classification metrics, correlation metrics, and optionally regression metrics.

    Parameters
    ----------
    confusion_matrix : np.ndarray
        Confusion matrix from Sceptic (n_classes x n_classes).
    y_true : np.ndarray
        True encoded labels (integers from 0 to n_classes-1).
    y_pred : np.ndarray
        Predicted encoded labels (integers from 0 to n_classes-1).
    pseudotime : np.ndarray
        Predicted continuous pseudotime values.
    true_time : np.ndarray
        True continuous time values (e.g., hours, ages, developmental stages).
    include_regression : bool, default=False
        Whether to include MAE/MSE regression metrics.
    verbose : bool, default=True
        If True, print results to console.

    Returns
    -------
    dict
        Comprehensive dictionary containing all metrics.

    Examples
    --------
    >>> # After running Sceptic:
    >>> results = evaluate_sceptic_results(
    ...     confusion_matrix=cm,
    ...     y_true=label,
    ...     y_pred=label_predicted,
    ...     pseudotime=pseudotime,
    ...     true_time=label_real,
    ...     include_regression=True
    ... )
    >>> print(f"Accuracy: {results['accuracy']:.3f}")
    >>> print(f"Spearman r: {results['spearman'][0]:.3f}")
    """
    results = {}

    # 1. Basic accuracy from confusion matrix
    cm_accuracy = np.sum(np.diag(confusion_matrix)) / np.sum(confusion_matrix)
    results['cm_accuracy'] = cm_accuracy

    # 2. Classification metrics
    classification = compute_classification_metrics(y_true, y_pred)
    results.update(classification)

    # 3. Correlation metrics
    correlations = compute_correlation_metrics(pseudotime, true_time)
    results.update(correlations)

    # 4. Optional regression metrics
    if include_regression:
        regression = compute_regression_metrics(pseudotime, true_time)
        results.update(regression)

    # 5. Print if verbose
    if verbose:
        print("=" * 60)
        print("SCEPTIC EVALUATION RESULTS")
        print("=" * 60)
        print(f"\nConfusion Matrix Accuracy: {cm_accuracy:.4f}")
        print(f"Accuracy: {classification['accuracy']:.4f}")
        print(f"Balanced Accuracy: {classification['balanced_accuracy']:.4f}")

        print("\nClassification Report:")
        print(classification['classification_report'])

        print("\nCorrelation Metrics:")
        spear_r, spear_p = correlations['spearman']
        pear_r, pear_p = correlations['pearson']
        kend_tau, kend_p = correlations['kendall']
        print(f"  Spearman  r = {spear_r:.4f} (p = {spear_p:.2e})")
        print(f"  Pearson   r = {pear_r:.4f} (p = {pear_p:.2e})")
        print(f"  Kendall   τ = {kend_tau:.4f} (p = {kend_p:.2e})")

        if include_regression:
            print("\nRegression Metrics:")
            print(f"  MAE  = {regression['mae']:.4f}")
            print(f"  MSE  = {regression['mse']:.4f}")
            print(f"  RMSE = {regression['rmse']:.4f}")

        print("=" * 60)

    return results
