"""
Comprehensive tests for frequency-based categorical filtering functionality.

Tests cover:
- Frequency threshold validation and configuration
- Categorical value filtering based on count and percentage thresholds
- Integration with existing percentile features
- Edge cases and error handling
- Statistical validation of filtered results
- CLI integration
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

from funputer.models import AnalysisConfig, ColumnMetadata
from funputer.metadata_inference import infer_metadata_from_dataframe, _filter_categorical_by_frequency
from funputer.analyzer import analyze_with_frequency_filtering, analyze_with_enhanced_filtering
from funputer import analyze_dataframe


class TestAnalysisConfigFrequencyValidation:
    """Test AnalysisConfig validation for frequency filtering parameters."""
    
    def test_valid_frequency_config(self):
        """Test valid frequency filtering configuration."""
        config = AnalysisConfig(
            enable_frequency_filtering=True,
            min_frequency_count=5,
            min_frequency_percentage=1.0,
            min_samples_for_frequency_filtering=20
        )
        
        assert config.enable_frequency_filtering is True
        assert config.min_frequency_count == 5
        assert config.min_frequency_percentage == 1.0
        assert config.min_samples_for_frequency_filtering == 20
    
    def test_min_frequency_count_validation(self):
        """Test validation of minimum frequency count."""
        # Valid ranges
        config = AnalysisConfig(min_frequency_count=1)
        assert config.min_frequency_count == 1
        
        config = AnalysisConfig(min_frequency_count=1000)
        assert config.min_frequency_count == 1000
        
        # Invalid ranges
        with pytest.raises(ValueError, match="Minimum frequency count must be at least 1"):
            AnalysisConfig(min_frequency_count=0)
        
        with pytest.raises(ValueError, match="Minimum frequency count cannot exceed 1,000"):
            AnalysisConfig(min_frequency_count=1001)
    
    def test_min_frequency_percentage_validation(self):
        """Test validation of minimum frequency percentage."""
        # Valid ranges
        config = AnalysisConfig(min_frequency_percentage=0.1)
        assert config.min_frequency_percentage == 0.1
        
        config = AnalysisConfig(min_frequency_percentage=50.0)
        assert config.min_frequency_percentage == 50.0
        
        # Invalid ranges
        with pytest.raises(ValueError, match="Minimum frequency percentage must be between 0.1 and 50.0"):
            AnalysisConfig(min_frequency_percentage=0.05)
        
        with pytest.raises(ValueError, match="Minimum frequency percentage must be between 0.1 and 50.0"):
            AnalysisConfig(min_frequency_percentage=51.0)
    
    def test_min_samples_frequency_validation(self):
        """Test validation of minimum samples for frequency filtering."""
        # Valid ranges
        config = AnalysisConfig(min_samples_for_frequency_filtering=10)
        assert config.min_samples_for_frequency_filtering == 10
        
        config = AnalysisConfig(min_samples_for_frequency_filtering=10000)
        assert config.min_samples_for_frequency_filtering == 10000
        
        # Invalid ranges
        with pytest.raises(ValueError, match="Minimum samples for frequency filtering must be at least 10"):
            AnalysisConfig(min_samples_for_frequency_filtering=9)
        
        with pytest.raises(ValueError, match="Minimum samples for frequency filtering cannot exceed 10,000"):
            AnalysisConfig(min_samples_for_frequency_filtering=10001)


class TestCategoricalFrequencyFiltering:
    """Test core frequency filtering functionality."""
    
    def test_filter_categorical_by_frequency_basic(self):
        """Test basic frequency filtering functionality."""
        # Create test data with clear frequency distribution
        data = pd.Series(['A'] * 50 + ['B'] * 30 + ['C'] * 15 + ['D'] * 4 + ['E'] * 1)
        
        config = AnalysisConfig(
            enable_frequency_filtering=True,
            min_frequency_count=5,
            min_frequency_percentage=5.0,  # 5% of 100 = 5
            min_samples_for_frequency_filtering=20
        )
        
        result = _filter_categorical_by_frequency(data, config)
        
        # Should include A, B, C (>=5 occurrences) but exclude D, E
        expected_values = set(['A', 'B', 'C'])
        actual_values = set(result['allowed_values'].split(','))
        
        assert actual_values == expected_values
        assert result['total_categories'] == 5
        assert result['filtered_categories'] == 3
        assert result['frequency_threshold_used'] == 5.0  # max(5, 5% of 100)
    
    def test_filter_categorical_percentage_threshold(self):
        """Test percentage-based threshold filtering."""
        # Create data where percentage threshold is more restrictive than count
        data = pd.Series(['A'] * 20 + ['B'] * 10 + ['C'] * 6 + ['D'] * 4)  # 40 total
        
        config = AnalysisConfig(
            enable_frequency_filtering=True,
            min_frequency_count=3,          # Would allow all
            min_frequency_percentage=15.0,  # 15% of 40 = 6, more restrictive
            min_samples_for_frequency_filtering=20
        )
        
        result = _filter_categorical_by_frequency(data, config)
        
        # Should include A, B, C (>=6 occurrences) but exclude D
        expected_values = set(['A', 'B', 'C'])
        actual_values = set(result['allowed_values'].split(','))
        
        assert actual_values == expected_values
        assert result['frequency_threshold_used'] == 6.0  # 15% of 40
    
    def test_filter_categorical_insufficient_samples(self):
        """Test behavior with insufficient samples for filtering."""
        data = pd.Series(['A'] * 5 + ['B'] * 3 + ['C'] * 2)  # 10 total, below min_samples
        
        config = AnalysisConfig(
            enable_frequency_filtering=True,
            min_frequency_count=5,
            min_frequency_percentage=20.0,
            min_samples_for_frequency_filtering=20  # More than available
        )
        
        result = _filter_categorical_by_frequency(data, config)
        
        # Should fall back to traditional approach (all values included)
        expected_values = set(['A', 'B', 'C'])
        actual_values = set(result['allowed_values'].split(','))
        
        assert actual_values == expected_values
        assert result['total_categories'] == 3
        assert result['filtered_categories'] == 3
        assert result['frequency_threshold_used'] == 0  # No filtering applied
    
    def test_filter_categorical_disabled(self):
        """Test behavior when frequency filtering is disabled."""
        data = pd.Series(['A'] * 50 + ['B'] * 2 + ['C'] * 1)
        
        config = AnalysisConfig(enable_frequency_filtering=False)
        
        result = _filter_categorical_by_frequency(data, config)
        
        # Should include all values when filtering is disabled
        expected_values = set(['A', 'B', 'C'])
        actual_values = set(result['allowed_values'].split(','))
        
        assert actual_values == expected_values
        assert result['frequency_threshold_used'] == 0
    
    def test_filter_categorical_empty_data(self):
        """Test handling of empty or all-null data."""
        data = pd.Series([np.nan, np.nan, np.nan])
        
        config = AnalysisConfig(enable_frequency_filtering=True)
        
        result = _filter_categorical_by_frequency(data, config)
        
        assert result['allowed_values'] is None
        assert result['total_categories'] is None
        assert result['filtered_categories'] is None
        assert result['frequency_threshold_used'] is None
    
    def test_filter_categorical_no_values_meet_threshold(self):
        """Test when no values meet the frequency threshold."""
        data = pd.Series(['A', 'B', 'C', 'D'])  # All values appear only once
        
        config = AnalysisConfig(
            enable_frequency_filtering=True,
            min_frequency_count=5,
            min_frequency_percentage=50.0,
            min_samples_for_frequency_filtering=1
        )
        
        result = _filter_categorical_by_frequency(data, config)
        
        # Should fall back to including all values
        expected_values = set(['A', 'B', 'C', 'D'])
        actual_values = set(result['allowed_values'].split(','))
        
        assert actual_values == expected_values
        assert result['total_categories'] == 4
        assert result['filtered_categories'] == 4
        assert result['frequency_threshold_used'] == 0


class TestMetadataInferenceWithFrequencyFiltering:
    """Test metadata inference integration with frequency filtering."""
    
    def test_categorical_metadata_with_frequency_filtering(self):
        """Test categorical column metadata inference with frequency filtering."""
        # Create data with mixed frequency categories
        df = pd.DataFrame({
            'category': ['A'] * 40 + ['B'] * 30 + ['C'] * 20 + ['D'] * 8 + ['E'] * 2,
            'numeric': range(100)
        })
        
        config = AnalysisConfig(
            enable_frequency_filtering=True,
            min_frequency_count=10,
            min_frequency_percentage=5.0
        )
        
        metadata = infer_metadata_from_dataframe(df, warn_user=False, config=config)
        
        # Find the categorical column metadata
        cat_meta = next(m for m in metadata if m.column_name == 'category')
        
        assert cat_meta.data_type == 'categorical'
        assert cat_meta.total_categories == 5
        assert cat_meta.filtered_categories == 3  # A, B, C meet threshold
        assert cat_meta.frequency_threshold_used == 10.0  # max(10, 5% of 100)
        
        # Check allowed values
        allowed = set(cat_meta.allowed_values.split(','))
        expected = set(['A', 'B', 'C'])
        assert allowed == expected
    
    def test_string_metadata_with_categorical_behavior(self):
        """Test string column that behaves like categorical gets frequency filtering."""
        # Create string data that should be treated as categorical
        df = pd.DataFrame({
            'status': ['active'] * 60 + ['inactive'] * 30 + ['pending'] * 8 + ['error'] * 2
        })
        
        config = AnalysisConfig(
            enable_frequency_filtering=True,
            min_frequency_count=10,
            min_frequency_percentage=5.0
        )
        
        metadata = infer_metadata_from_dataframe(df, warn_user=False, config=config)
        
        # Should be detected as categorical due to low unique ratio
        status_meta = metadata[0]
        assert status_meta.data_type == 'categorical'
        assert status_meta.total_categories == 4
        assert status_meta.filtered_categories == 2  # Only 'active' and 'inactive' meet threshold
        
        allowed = set(status_meta.allowed_values.split(','))
        expected = set(['active', 'inactive'])
        assert allowed == expected
    
    def test_metadata_frequency_filtering_disabled(self):
        """Test metadata inference with frequency filtering disabled."""
        df = pd.DataFrame({
            'category': ['A'] * 40 + ['B'] * 5 + ['C'] * 1
        })
        
        config = AnalysisConfig(enable_frequency_filtering=False)
        
        metadata = infer_metadata_from_dataframe(df, warn_user=False, config=config)
        
        cat_meta = metadata[0]
        assert cat_meta.frequency_threshold_used == 0
        assert cat_meta.total_categories == 3
        assert cat_meta.filtered_categories == 3  # All categories included
        
        allowed = set(cat_meta.allowed_values.split(','))
        expected = set(['A', 'B', 'C'])
        assert allowed == expected


class TestAPIIntegration:
    """Test API functions with frequency filtering."""
    
    def test_analyze_with_frequency_filtering_function(self):
        """Test the analyze_with_frequency_filtering convenience function."""
        df = pd.DataFrame({
            'category': ['Premium'] * 50 + ['Standard'] * 30 + ['Basic'] * 15 + ['Trial'] * 4 + ['Test'] * 1,
            'value': np.random.normal(100, 15, 100)
        })
        
        suggestions = analyze_with_frequency_filtering(
            df,
            min_frequency_count=10,
            min_frequency_percentage=5.0
        )
        
        assert len(suggestions) == 2
        
        # Check that frequency filtering was applied
        cat_suggestion = next(s for s in suggestions if s.column_name == 'category')
        assert cat_suggestion.column_name == 'category'
    
    def test_analyze_with_enhanced_filtering_function(self):
        """Test the combined percentile + frequency filtering function."""
        df = pd.DataFrame({
            'category': ['A'] * 40 + ['B'] * 30 + ['C'] * 20 + ['D'] * 8 + ['E'] * 2,
            'numeric': [1, 2, 3] * 30 + [100, 200]  # Has outliers
        })
        
        suggestions = analyze_with_enhanced_filtering(
            df,
            percentile_threshold=95.0,
            min_frequency_count=10,
            min_frequency_percentage=5.0
        )
        
        assert len(suggestions) == 2
        
        # Both columns should be analyzed
        column_names = {s.column_name for s in suggestions}
        assert column_names == {'category', 'numeric'}
    
    def test_backward_compatibility_with_existing_functions(self):
        """Test that existing functions still work without frequency filtering."""
        df = pd.DataFrame({
            'category': ['A'] * 5 + ['B'] * 1,  # Very unbalanced
            'numeric': [1, 2, 3, 4, 5, 6]
        })
        
        # Should work without errors, using default config
        suggestions = analyze_dataframe(df)
        
        assert len(suggestions) == 2


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling."""
    
    def test_high_cardinality_categorical_data(self):
        """Test frequency filtering with high cardinality data."""
        # Create data with 100 categories, mostly rare
        categories = [f'cat_{i}' for i in range(100)]
        data = []
        
        # Few common categories
        data.extend(['common1'] * 50)
        data.extend(['common2'] * 30)
        data.extend(['common3'] * 10)
        
        # Many rare categories (1-2 occurrences each)
        for cat in categories[:97]:
            data.extend([cat] * np.random.randint(1, 3))
        
        df = pd.DataFrame({'high_cardinality': data})
        
        config = AnalysisConfig(
            enable_frequency_filtering=True,
            min_frequency_count=5,
            min_frequency_percentage=2.0
        )
        
        metadata = infer_metadata_from_dataframe(df, warn_user=False, config=config)
        cat_meta = metadata[0]
        
        # Should significantly reduce the number of categories
        assert cat_meta.total_categories > 90  # Many categories originally
        assert cat_meta.filtered_categories <= 10  # Drastically reduced
        assert cat_meta.filtered_categories < cat_meta.total_categories
        
        # Check that common categories are preserved
        allowed = set(cat_meta.allowed_values.split(','))
        assert 'common1' in allowed
        assert 'common2' in allowed
    
    def test_single_category_data(self):
        """Test handling of data with only one category."""
        df = pd.DataFrame({'single_cat': ['A'] * 100})
        
        config = AnalysisConfig(enable_frequency_filtering=True)
        
        metadata = infer_metadata_from_dataframe(df, warn_user=False, config=config)
        cat_meta = metadata[0]
        
        assert cat_meta.total_categories == 1
        assert cat_meta.filtered_categories == 1
        assert cat_meta.allowed_values == 'A'
    
    def test_all_categories_meet_threshold(self):
        """Test when all categories meet the frequency threshold."""
        df = pd.DataFrame({
            'balanced': ['A'] * 25 + ['B'] * 25 + ['C'] * 25 + ['D'] * 25
        })
        
        config = AnalysisConfig(
            enable_frequency_filtering=True,
            min_frequency_count=20,
            min_frequency_percentage=20.0
        )
        
        metadata = infer_metadata_from_dataframe(df, warn_user=False, config=config)
        cat_meta = metadata[0]
        
        assert cat_meta.total_categories == 4
        assert cat_meta.filtered_categories == 4  # All categories preserved
        
        allowed = set(cat_meta.allowed_values.split(','))
        expected = set(['A', 'B', 'C', 'D'])
        assert allowed == expected
    
    def test_frequency_filtering_with_missing_values(self):
        """Test frequency filtering behavior with missing values."""
        df = pd.DataFrame({
            'with_nulls': ['A'] * 40 + ['B'] * 20 + ['C'] * 5 + [np.nan] * 35
        })
        
        config = AnalysisConfig(
            enable_frequency_filtering=True,
            min_frequency_count=10,
            min_frequency_percentage=5.0
        )
        
        metadata = infer_metadata_from_dataframe(df, warn_user=False, config=config)
        cat_meta = metadata[0]
        
        # Missing values should not be counted in frequency calculation
        assert cat_meta.total_categories == 3  # A, B, C (nulls excluded)
        assert cat_meta.filtered_categories == 2  # A, B meet threshold
        
        allowed = set(cat_meta.allowed_values.split(','))
        expected = set(['A', 'B'])
        assert allowed == expected


class TestStatisticalValidation:
    """Test statistical validity of frequency filtering results."""
    
    def test_chi_square_threshold_compliance(self):
        """Test that default threshold meets chi-square test requirements."""
        # Create data that tests chi-square validity
        df = pd.DataFrame({
            'category': ['Valid1'] * 10 + ['Valid2'] * 8 + ['Valid3'] * 6 + ['Invalid'] * 2
        })
        
        # Default config should use min_frequency_count=5 for chi-square validity
        config = AnalysisConfig(enable_frequency_filtering=True)
        
        metadata = infer_metadata_from_dataframe(df, warn_user=False, config=config)
        cat_meta = metadata[0]
        
        # Should exclude 'Invalid' (only 2 occurrences < 5)
        allowed = set(cat_meta.allowed_values.split(','))
        expected = set(['Valid1', 'Valid2', 'Valid3'])
        assert allowed == expected
        
        # All retained categories should have >= 5 occurrences for chi-square validity
        assert cat_meta.frequency_threshold_used >= 5
    
    def test_statistical_power_preservation(self):
        """Test that filtering preserves categories with statistical power."""
        # Create dataset with clear signal vs noise categories
        df = pd.DataFrame({
            'signal_category': (
                ['Strong_Signal'] * 50 +    # Clear signal
                ['Medium_Signal'] * 25 +    # Moderate signal  
                ['Weak_Signal'] * 10 +      # Weak but valid signal
                ['Noise1'] * 3 +            # Statistical noise
                ['Noise2'] * 2              # Statistical noise
            )
        })
        
        config = AnalysisConfig(
            enable_frequency_filtering=True,
            min_frequency_count=5,
            min_frequency_percentage=5.0
        )
        
        metadata = infer_metadata_from_dataframe(df, warn_user=False, config=config)
        cat_meta = metadata[0]
        
        # Should preserve signal categories, exclude noise
        allowed = set(cat_meta.allowed_values.split(','))
        expected_signal = set(['Strong_Signal', 'Medium_Signal', 'Weak_Signal'])
        noise_categories = set(['Noise1', 'Noise2'])
        
        assert allowed == expected_signal
        assert len(allowed.intersection(noise_categories)) == 0


class TestPerformanceAndIntegration:
    """Test performance characteristics and integration scenarios."""
    
    def test_integration_with_percentile_ranges(self):
        """Test that frequency filtering works alongside percentile ranges."""
        df = pd.DataFrame({
            'category': ['A'] * 40 + ['B'] * 30 + ['C'] * 20 + ['D'] * 5 + ['E'] * 5,
            'numeric': list(range(90)) + [1000] * 10  # Has outliers
        })
        
        config = AnalysisConfig(
            enable_frequency_filtering=True,
            min_frequency_count=10,
            enable_percentile_ranges=True,
            default_percentile_threshold=95.0
        )
        
        metadata = infer_metadata_from_dataframe(df, warn_user=False, config=config)
        
        # Check categorical filtering
        cat_meta = next(m for m in metadata if m.column_name == 'category')
        assert cat_meta.filtered_categories == 3  # A, B, C
        
        # Check percentile ranges for numeric
        num_meta = next(m for m in metadata if m.column_name == 'numeric')
        assert num_meta.percentile_low is not None
        assert num_meta.percentile_high is not None
    
    def test_large_dataset_performance(self):
        """Test frequency filtering performance with larger datasets."""
        # Create a larger dataset
        np.random.seed(42)
        n_samples = 10000
        
        # Create categories with realistic distribution
        categories = ['Common'] * 5000 + ['Frequent'] * 2000 + ['Regular'] * 1500 + ['Rare'] * 1000 + ['VeryRare'] * 500
        np.random.shuffle(categories)
        
        df = pd.DataFrame({'large_category': categories})
        
        config = AnalysisConfig(
            enable_frequency_filtering=True,
            min_frequency_count=100,  # 1% of data
            min_frequency_percentage=1.0
        )
        
        # Should complete without performance issues
        import time
        start_time = time.time()
        metadata = infer_metadata_from_dataframe(df, warn_user=False, config=config)
        end_time = time.time()
        
        # Should be reasonably fast (< 1 second for 10k rows)
        assert end_time - start_time < 1.0
        
        cat_meta = metadata[0]
        assert cat_meta.total_categories == 5
        assert cat_meta.filtered_categories >= 3  # Common, Frequent, Regular should pass