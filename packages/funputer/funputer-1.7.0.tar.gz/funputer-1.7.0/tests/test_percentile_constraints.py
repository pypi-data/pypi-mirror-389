"""
Comprehensive tests for percentile-based constraint inference.

This module tests the new percentile functionality added to metadata inference,
ensuring robust error handling and correct calculation in various scenarios.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch

from funputer.metadata_inference import (
    _infer_constraints,
    _infer_column_metadata,
    infer_metadata_from_dataframe
)
from funputer.models import AnalysisConfig, ColumnMetadata


class TestPercentileConstraints:
    """Test percentile-based constraint inference."""
    
    @pytest.fixture
    def basic_config(self):
        """Basic configuration with percentile ranges enabled."""
        return AnalysisConfig(
            enable_percentile_ranges=True,
            default_percentile_threshold=95.0,
            min_samples_for_percentiles=20
        )
    
    @pytest.fixture
    def disabled_config(self):
        """Configuration with percentile ranges disabled."""
        return AnalysisConfig(
            enable_percentile_ranges=False,
            default_percentile_threshold=95.0,
            min_samples_for_percentiles=20
        )
    
    @pytest.fixture
    def large_sample_data(self):
        """Create numeric data with sufficient samples for percentiles."""
        # Create data with outliers: normal range 10-90, outliers at 1 and 500
        normal_data = list(range(10, 91))  # 81 normal values
        outliers = [1, 500]  # 2 outliers
        return pd.Series(normal_data + outliers)
    
    @pytest.fixture
    def small_sample_data(self):
        """Create numeric data with insufficient samples for percentiles."""
        return pd.Series([10, 20, 30, 40, 50])  # Only 5 values
    
    def test_percentile_calculation_with_sufficient_samples(self, basic_config, large_sample_data):
        """Test percentile calculation when sufficient samples are available."""
        constraints = _infer_constraints(large_sample_data, 'integer', basic_config)
        
        # Should have traditional bounds
        assert constraints['min_value'] == 1.0
        assert constraints['max_value'] == 500.0
        
        # Should have percentile bounds that exclude outliers
        assert constraints['percentile_low'] is not None
        assert constraints['percentile_high'] is not None
        assert constraints['percentile_threshold'] == 95.0
        
        # Percentile bounds should be tighter than absolute bounds
        assert constraints['percentile_low'] > constraints['min_value']
        assert constraints['percentile_high'] < constraints['max_value']
        
        # For 95th percentile, should exclude extreme outliers
        assert constraints['percentile_low'] >= 10  # Should exclude outlier 1
        assert constraints['percentile_high'] <= 90  # Should exclude outlier 500
    
    def test_percentile_calculation_with_insufficient_samples(self, basic_config, small_sample_data):
        """Test percentile calculation when insufficient samples are available."""
        constraints = _infer_constraints(small_sample_data, 'integer', basic_config)
        
        # Should have traditional bounds
        assert constraints['min_value'] == 10.0
        assert constraints['max_value'] == 50.0
        
        # Should NOT have percentile bounds due to insufficient samples
        assert constraints['percentile_low'] is None
        assert constraints['percentile_high'] is None
        assert constraints['percentile_threshold'] is None
    
    def test_percentile_disabled_config(self, disabled_config, large_sample_data):
        """Test that percentiles are not calculated when disabled in config."""
        constraints = _infer_constraints(large_sample_data, 'integer', disabled_config)
        
        # Should have traditional bounds
        assert constraints['min_value'] == 1.0
        assert constraints['max_value'] == 500.0
        
        # Should NOT have percentile bounds due to disabled config
        assert constraints['percentile_low'] is None
        assert constraints['percentile_high'] is None
        assert constraints['percentile_threshold'] is None
    
    def test_percentile_no_config_provided(self, large_sample_data):
        """Test backward compatibility when no config is provided."""
        constraints = _infer_constraints(large_sample_data, 'integer', None)
        
        # Should have traditional bounds
        assert constraints['min_value'] == 1.0
        assert constraints['max_value'] == 500.0
        
        # Should NOT have percentile bounds when no config provided
        assert constraints['percentile_low'] is None
        assert constraints['percentile_high'] is None
        assert constraints['percentile_threshold'] is None
    
    def test_different_percentile_thresholds(self, large_sample_data):
        """Test different percentile threshold configurations."""
        # Test 90th percentile
        config_90 = AnalysisConfig(
            enable_percentile_ranges=True,
            default_percentile_threshold=90.0,
            min_samples_for_percentiles=20
        )
        constraints_90 = _infer_constraints(large_sample_data, 'integer', config_90)
        
        # Test 99th percentile
        config_99 = AnalysisConfig(
            enable_percentile_ranges=True,
            default_percentile_threshold=99.0,
            min_samples_for_percentiles=20
        )
        constraints_99 = _infer_constraints(large_sample_data, 'integer', config_99)
        
        # 99th percentile should have wider range than 90th percentile
        assert constraints_99['percentile_low'] <= constraints_90['percentile_low']
        assert constraints_99['percentile_high'] >= constraints_90['percentile_high']
        
        # Thresholds should be correctly set
        assert constraints_90['percentile_threshold'] == 90.0
        assert constraints_99['percentile_threshold'] == 99.0
    
    def test_non_numeric_data_types(self, basic_config):
        """Test that percentiles are only calculated for numeric data types."""
        string_data = pd.Series(['a', 'b', 'c'] * 10)  # 30 string values
        categorical_data = pd.Series(['X', 'Y', 'Z'] * 10)  # 30 categorical values
        
        string_constraints = _infer_constraints(string_data, 'string', basic_config)
        categorical_constraints = _infer_constraints(categorical_data, 'categorical', basic_config)
        
        # Non-numeric types should not have percentile fields
        assert 'percentile_low' not in string_constraints
        assert 'percentile_high' not in string_constraints
        assert 'percentile_threshold' not in string_constraints
        
        assert 'percentile_low' not in categorical_constraints
        assert 'percentile_high' not in categorical_constraints
        assert 'percentile_threshold' not in categorical_constraints
    
    def test_float_data_percentiles(self, basic_config):
        """Test percentile calculation with float data."""
        float_data = pd.Series([1.5, 2.7, 3.1] + list(np.random.normal(50, 10, 25)) + [999.9])
        constraints = _infer_constraints(float_data, 'float', basic_config)
        
        # Should calculate percentiles for float data
        assert constraints['percentile_low'] is not None
        assert constraints['percentile_high'] is not None
        assert constraints['percentile_threshold'] == 95.0
        
        # Should be float values
        assert isinstance(constraints['percentile_low'], float)
        assert isinstance(constraints['percentile_high'], float)
    
    def test_edge_case_all_same_values(self, basic_config):
        """Test percentile calculation when all values are the same."""
        same_values = pd.Series([42] * 30)
        constraints = _infer_constraints(same_values, 'integer', basic_config)
        
        # Should still calculate percentiles even if they're all the same
        assert constraints['percentile_low'] == 42.0
        assert constraints['percentile_high'] == 42.0
        assert constraints['percentile_threshold'] == 95.0
    
    def test_edge_case_with_nan_values(self, basic_config):
        """Test percentile calculation with NaN values in the data."""
        data_with_nan = pd.Series([1, 2, 3, np.nan, 4, 5] + list(range(6, 26)) + [np.nan, 100])
        constraints = _infer_constraints(data_with_nan, 'integer', basic_config)
        
        # Should calculate percentiles ignoring NaN values
        assert constraints['percentile_low'] is not None
        assert constraints['percentile_high'] is not None
        
        # Should not include NaN in calculations
        assert not np.isnan(constraints['percentile_low'])
        assert not np.isnan(constraints['percentile_high'])
    
    def test_percentile_calculation_error_handling(self, basic_config):
        """Test error handling during percentile calculation."""
        # Create data that might cause quantile calculation issues
        problematic_data = pd.Series([np.inf, -np.inf] + list(range(20, 40)))
        
        with patch('pandas.Series.quantile', side_effect=ValueError("Quantile calculation failed")):
            constraints = _infer_constraints(problematic_data, 'float', basic_config)
            
            # Should have traditional bounds
            assert 'min_value' in constraints
            assert 'max_value' in constraints
            
            # Should gracefully handle percentile calculation failure
            assert constraints['percentile_low'] is None
            assert constraints['percentile_high'] is None
            assert constraints['percentile_threshold'] is None


class TestPercentileIntegration:
    """Test percentile functionality integrated through the full pipeline."""
    
    def test_column_metadata_integration(self):
        """Test that percentile fields are properly integrated into ColumnMetadata."""
        df = pd.DataFrame({
            'numeric_col': list(range(1, 31)) + [100]  # 30 normal + 1 outlier
        })
        
        config = AnalysisConfig(enable_percentile_ranges=True, min_samples_for_percentiles=20)
        metadata = _infer_column_metadata(df, 'numeric_col', config)
        
        # Should be ColumnMetadata object with percentile fields
        assert isinstance(metadata, ColumnMetadata)
        assert metadata.percentile_low is not None
        assert metadata.percentile_high is not None
        assert metadata.percentile_threshold == 95.0
        
        # Traditional bounds should also be present
        assert metadata.min_value is not None
        assert metadata.max_value is not None
    
    def test_dataframe_inference_integration(self):
        """Test percentile functionality through full dataframe inference."""
        df = pd.DataFrame({
            'large_numeric': list(range(1, 26)) + [500],  # Sufficient samples
            'small_numeric': [1, 2, 3, 4, 5],  # Insufficient samples
            'text_col': ['a', 'b', 'c'] * 10  # Non-numeric
        })
        
        config = AnalysisConfig(enable_percentile_ranges=True, min_samples_for_percentiles=20)
        metadata_list = infer_metadata_from_dataframe(df, warn_user=False, config=config)
        
        metadata_dict = {m.column_name: m for m in metadata_list}
        
        # Large numeric column should have percentiles
        large_meta = metadata_dict['large_numeric']
        assert large_meta.percentile_low is not None
        assert large_meta.percentile_high is not None
        
        # Small numeric column should not have percentiles
        small_meta = metadata_dict['small_numeric']
        assert small_meta.percentile_low is None
        assert small_meta.percentile_high is None
        
        # Text column should not have percentile fields
        text_meta = metadata_dict['text_col']
        assert text_meta.percentile_low is None
        assert text_meta.percentile_high is None
    
    def test_backward_compatibility_no_config(self):
        """Test that existing code works without providing config."""
        df = pd.DataFrame({
            'numeric_col': list(range(1, 31))
        })
        
        # Should work without config (backward compatibility)
        metadata_list = infer_metadata_from_dataframe(df, warn_user=False)
        metadata = metadata_list[0]
        
        # Should have traditional fields
        assert metadata.min_value is not None
        assert metadata.max_value is not None
        
        # Should not have percentile fields when no config provided
        assert metadata.percentile_low is None
        assert metadata.percentile_high is None
        assert metadata.percentile_threshold is None


class TestConfigValidation:
    """Test configuration validation for percentile functionality."""
    
    def test_valid_percentile_threshold(self):
        """Test valid percentile threshold values."""
        # Valid thresholds
        valid_configs = [
            AnalysisConfig(default_percentile_threshold=50.0),
            AnalysisConfig(default_percentile_threshold=95.0),
            AnalysisConfig(default_percentile_threshold=99.9)
        ]
        
        for config in valid_configs:
            assert config.default_percentile_threshold >= 50.0
            assert config.default_percentile_threshold <= 99.9
    
    def test_invalid_percentile_threshold(self):
        """Test invalid percentile threshold values raise errors."""
        with pytest.raises(ValueError, match="Percentile threshold must be between 50.0 and 99.9"):
            AnalysisConfig(default_percentile_threshold=49.9)
        
        with pytest.raises(ValueError, match="Percentile threshold must be between 50.0 and 99.9"):
            AnalysisConfig(default_percentile_threshold=100.0)
    
    def test_valid_min_samples(self):
        """Test valid minimum samples values."""
        valid_configs = [
            AnalysisConfig(min_samples_for_percentiles=5),
            AnalysisConfig(min_samples_for_percentiles=20),
            AnalysisConfig(min_samples_for_percentiles=100)
        ]
        
        for config in valid_configs:
            assert config.min_samples_for_percentiles >= 5
    
    def test_invalid_min_samples(self):
        """Test invalid minimum samples values raise errors."""
        with pytest.raises(ValueError, match="Minimum samples for percentiles must be at least 5"):
            AnalysisConfig(min_samples_for_percentiles=4)
        
        with pytest.raises(ValueError, match="Minimum samples for percentiles must be at least 5"):
            AnalysisConfig(min_samples_for_percentiles=0)