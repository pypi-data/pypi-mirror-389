"""
Tests for Sceptic utility modules (evaluation and plotting).
"""

import numpy as np
import pytest
from sceptic import evaluation, plotting


class TestEvaluationMetrics:
    """Test suite for evaluation.py module."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        np.random.seed(42)
        n_samples = 100
        n_classes = 5

        # Create sample predictions and labels
        y_true = np.random.randint(0, n_classes, n_samples)
        y_pred = y_true.copy()
        # Add some errors (80% accuracy)
        error_indices = np.random.choice(n_samples, size=20, replace=False)
        y_pred[error_indices] = np.random.randint(0, n_classes, 20)

        # Create sample pseudotime and true time
        true_time = np.linspace(0, 100, n_samples)
        pseudotime = true_time + np.random.normal(0, 10, n_samples)

        # Create confusion matrix
        cm = np.zeros((n_classes, n_classes))
        for t, p in zip(y_true, y_pred):
            cm[t, p] += 1

        return {
            'y_true': y_true,
            'y_pred': y_pred,
            'true_time': true_time,
            'pseudotime': pseudotime,
            'cm': cm
        }

    def test_compute_classification_metrics(self, sample_data):
        """Test classification metrics computation."""
        metrics = evaluation.compute_classification_metrics(
            y_true=sample_data['y_true'],
            y_pred=sample_data['y_pred']
        )

        # Check that all expected keys are present
        assert 'accuracy' in metrics
        assert 'balanced_accuracy' in metrics
        assert 'classification_report' in metrics

        # Check that accuracy is between 0 and 1
        assert 0 <= metrics['accuracy'] <= 1
        assert 0 <= metrics['balanced_accuracy'] <= 1

        # Check that classification report is a string
        assert isinstance(metrics['classification_report'], str)

    def test_compute_correlation_metrics(self, sample_data):
        """Test correlation metrics computation."""
        metrics = evaluation.compute_correlation_metrics(
            pseudotime=sample_data['pseudotime'],
            true_time=sample_data['true_time']
        )

        # Check that all expected keys are present
        assert 'spearman' in metrics
        assert 'pearson' in metrics
        assert 'kendall' in metrics

        # Each should be a tuple of (correlation, p-value)
        for key in ['spearman', 'pearson', 'kendall']:
            assert len(metrics[key]) == 2
            corr, p_val = metrics[key]
            # Correlation should be between -1 and 1
            assert -1 <= corr <= 1
            # P-value should be between 0 and 1
            assert 0 <= p_val <= 1

    def test_compute_regression_metrics(self, sample_data):
        """Test regression metrics computation."""
        metrics = evaluation.compute_regression_metrics(
            pseudotime=sample_data['pseudotime'],
            true_time=sample_data['true_time']
        )

        # Check that all expected keys are present
        assert 'mae' in metrics
        assert 'mse' in metrics
        assert 'rmse' in metrics

        # All should be non-negative
        assert metrics['mae'] >= 0
        assert metrics['mse'] >= 0
        assert metrics['rmse'] >= 0

        # RMSE should be sqrt(MSE)
        assert np.isclose(metrics['rmse'], np.sqrt(metrics['mse']))

    def test_evaluate_sceptic_results(self, sample_data):
        """Test comprehensive evaluation function."""
        results = evaluation.evaluate_sceptic_results(
            confusion_matrix=sample_data['cm'],
            y_true=sample_data['y_true'],
            y_pred=sample_data['y_pred'],
            pseudotime=sample_data['pseudotime'],
            true_time=sample_data['true_time'],
            include_regression=True,
            verbose=False  # Don't print during tests
        )

        # Check that all expected metrics are present
        expected_keys = [
            'cm_accuracy', 'accuracy', 'balanced_accuracy',
            'classification_report', 'spearman', 'pearson', 'kendall',
            'mae', 'mse', 'rmse'
        ]
        for key in expected_keys:
            assert key in results

    def test_correlation_with_nan(self):
        """Test correlation handling with NaN values."""
        pseudotime = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        true_time = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        # Should handle NaN values gracefully
        metrics = evaluation.compute_correlation_metrics(pseudotime, true_time)

        # Should still return valid correlations
        assert 'spearman' in metrics
        assert not np.isnan(metrics['spearman'][0])

    def test_empty_arrays_raise_error(self):
        """Test that empty arrays raise appropriate errors."""
        with pytest.raises(ValueError):
            evaluation.compute_correlation_metrics(
                pseudotime=np.array([]),
                true_time=np.array([])
            )


class TestPlottingUtilities:
    """Test suite for plotting.py module."""

    @pytest.fixture
    def plot_data(self):
        """Create sample data for plotting tests."""
        np.random.seed(42)
        n_samples = 50
        n_classes = 4

        # Create confusion matrix
        cm = np.random.randint(5, 20, (n_classes, n_classes))

        # Create labels
        label_list = np.array([10, 20, 30, 40])

        # Create pseudotime and true labels
        pseudotime = np.random.rand(n_samples)
        true_labels = np.random.choice(label_list, n_samples)

        # Create group labels
        group_labels = np.random.choice(['TypeA', 'TypeB', 'TypeC'], n_samples)

        return {
            'cm': cm,
            'label_list': label_list,
            'pseudotime': pseudotime,
            'true_labels': true_labels,
            'group_labels': group_labels
        }

    def test_set_publication_style(self):
        """Test setting publication style."""
        # Should run without errors
        plotting.set_publication_style()
        plotting.set_publication_style(small_size=14, medium_size=16, bigger_size=20)

    def test_plot_confusion_matrix(self, plot_data, tmp_path):
        """Test confusion matrix plotting."""
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend for testing

        output_path = tmp_path / "test_cm.png"

        fig = plotting.plot_confusion_matrix(
            confusion_matrix=plot_data['cm'],
            label_list=plot_data['label_list'],
            output_path=str(output_path),
            normalize=True
        )

        # Check that figure was created
        assert fig is not None

        # Check that file was saved
        assert output_path.exists()

        # Close figure
        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_plot_pseudotime_violin(self, plot_data, tmp_path):
        """Test violin plot creation."""
        import matplotlib
        matplotlib.use('Agg')

        output_path = tmp_path / "test_violin.png"

        fig = plotting.plot_pseudotime_violin(
            pseudotime=plot_data['pseudotime'],
            true_labels=plot_data['true_labels'],
            output_path=str(output_path)
        )

        # Check that figure was created
        assert fig is not None

        # Check that file was saved
        assert output_path.exists()

        # Close figure
        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_plot_pseudotime_by_group(self, plot_data, tmp_path):
        """Test stratified plotting by groups."""
        import matplotlib
        matplotlib.use('Agg')

        output_dir = tmp_path / "violin_by_group"

        plotting.plot_pseudotime_by_group(
            pseudotime=plot_data['pseudotime'],
            true_labels=plot_data['true_labels'],
            group_labels=plot_data['group_labels'],
            output_dir=str(output_dir),
            top_k=3
        )

        # Check that directory was created
        assert output_dir.exists()

        # Check that some files were created
        files = list(output_dir.glob("*.png"))
        assert len(files) > 0

        # Close all figures
        plotting.close_all_figures()

    def test_close_all_figures(self):
        """Test closing all figures."""
        # Should run without errors
        plotting.close_all_figures()


def run_tests():
    """Run all tests."""
    pytest.main([__file__, '-v'])


if __name__ == '__main__':
    run_tests()
