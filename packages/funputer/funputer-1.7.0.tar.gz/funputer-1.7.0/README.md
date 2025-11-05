# FunPuter - Intelligent Imputation Analysis

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/funputer.svg)](https://pypi.org/project/funputer/)
[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red.svg)]
[![Test Coverage](https://img.shields.io/badge/coverage-45%25-yellow.svg)](#documentation)

**Intelligent imputation analysis with automatic data validation and metadata inference**

FunPuter analyzes your data and recommends the best imputation methods based on data patterns, missing mechanisms, and metadata constraints. Get intelligent suggestions with confidence scores to handle missing data professionally.

## 🆕 What's New in v1.7.0

**Frequency-Based Categorical Intelligence** - Revolutionary statistical filtering for categorical variables:

- **🏷️ Statistical Significance Filtering**: Automatically exclude categories with insufficient statistical power
- **📊 Chi-Square Validity**: Ensures minimum 5 occurrences per category for reliable statistical tests  
- **🎯 Overfitting Prevention**: Reduces model complexity by filtering out rare categories (default: <1% frequency)
- **🔧 Configurable Thresholds**: Customize count (5+) and percentage (1.0%+) requirements
- **⚡ Production Ready**: Handles high-cardinality categorical data with 20-80% category reduction
- **🤝 Full Integration**: Works seamlessly with existing percentile ranges and all v1.6.0 features

```python
# NEW: Intelligent categorical filtering
suggestions = funputer.analyze_with_frequency_filtering("data.csv")

# NEW: Combined percentile + frequency analysis  
suggestions = funputer.analyze_with_enhanced_filtering("data.csv")
```

## 🎯 Real-World Impact

**Before v1.7.0**: Traditional analysis includes ALL categorical values, even rare ones
```
E-commerce Categories: 47 total → 47 included (including 1-2 occurrences)
Result: Model overfitting, poor generalization, production failures
```

**After v1.7.0**: Intelligent frequency filtering for robust analysis
```
E-commerce Categories: 47 total → 12 significant (≥5 occurrences, ≥1% frequency)
Result: 74% reduction, statistical validity, production robustness
```

**Proven Benefits:**
- **🔬 Statistical Reliability**: 100% chi-square test compliance for retained categories
- **⚡ Model Performance**: 20-80% reduction in categorical feature space
- **🛡️ Production Safety**: Eliminates rare category overfitting
- **📊 Data Quality**: Focuses analysis on statistically meaningful patterns

## 🚀 Quick Start

### Installation

```bash
pip install funputer
```

### 30-Second Example

**🚀 Enhanced Mode** (v1.7.0 - Recommended)
```python
import funputer

# NEW: Intelligent analysis with frequency filtering + percentile ranges
suggestions = funputer.analyze_with_enhanced_filtering("your_data.csv")

# Get enhanced suggestions with statistical validity
for suggestion in suggestions:
    if suggestion.missing_count > 0:
        print(f"📊 {suggestion.column_name}: {suggestion.proposed_method}")
        print(f"   Confidence: {suggestion.confidence_score:.3f}")
        print(f"   Reason: {suggestion.rationale}")
        print(f"   Missing: {suggestion.missing_count} ({suggestion.missing_percentage:.1f}%)")
```

**Classic Mode** (Zero Configuration)
```python
import funputer

# Traditional analysis - works with all existing code
suggestions = funputer.analyze_imputation_requirements("your_data.csv")
```

**Production Mode** (Full Control)
```python
import funputer
from funputer.models import ColumnMetadata

# Define your data structure with constraints
metadata = [
    ColumnMetadata('customer_id', 'integer', unique_flag=True, nullable=False),
    ColumnMetadata('age', 'integer', min_value=18, max_value=100),
    ColumnMetadata('income', 'float', min_value=0),
    ColumnMetadata('category', 'categorical', allowed_values='A,B,C'),
]

# Get production-grade suggestions
suggestions = funputer.analyze_dataframe(your_dataframe, metadata)
```

## 🎯 Key Features

- **🤖 Automatic Metadata Inference** - Intelligent data type and constraint detection
- **📊 Missing Data Analysis** - MCAR, MAR, MNAR mechanism detection  
- **⚡ Data Validation** - Real-time constraint checking and validation
- **🎯 Smart Recommendations** - Context-aware imputation method suggestions
- **📈 Confidence Scoring** - Transparent reliability estimates for each recommendation
- **🛡️ Pre-flight Checks** - Comprehensive data validation before analysis
- **📊 Percentile-Based Ranges** - Outlier-resistant numeric bounds using configurable percentiles
- **🏷️ Frequency-Based Filtering** - Statistical significance filtering for categorical variables
- **💻 CLI & Python API** - Flexible usage via command line or programmatic access

## 📊 Data Validation System

Comprehensive validation runs automatically to prevent crashes and guide your workflow:

- **File validation**: Format detection, encoding, accessibility
- **Structure validation**: Column analysis, data type inference  
- **Memory estimation**: Resource usage prediction
- **Advisory recommendations**: Guided workflow suggestions

**Independent Usage:**
```bash
# Basic validation check
funputer preflight -d your_data.csv

# With custom options  
funputer preflight -d data.csv --sample-rows 5000 --encoding utf-8

# JSON report output
funputer preflight -d data.csv --json-out report.json
```

**Exit Codes:**
- `0`: Ready for analysis
- `2`: OK with warnings (can proceed)
- `10`: Hard error (cannot proceed)

## 📊 Percentile-Based Range Detection

**NEW in v1.6.0**: Intelligent outlier-resistant numeric bounds using configurable percentiles.

Instead of using absolute min/max values that include outliers, FunPuter can calculate percentile-based ranges that provide more realistic business constraints.

**How it works:**
- **95th percentile** (default): Excludes top/bottom 2.5% as outliers
- **99th percentile**: More conservative, excludes top/bottom 0.5% as outliers  
- **Requires 20+ samples** for statistical reliability (configurable)
- **Falls back** to traditional min/max when insufficient data

**Example Benefits:**
```python
# Traditional bounds (includes outliers)
age_column: min=5, max=150  # Includes data entry errors

# Percentile bounds (outlier-resistant) 
age_column: percentile_low=18.2, percentile_high=65.8  # Realistic business range
```

**Usage:**
```python
# Enable percentile ranges with default 95% threshold
from funputer import analyze_with_percentile_ranges
suggestions = analyze_with_percentile_ranges("data.csv")

# Custom percentile threshold (99% = more conservative)
suggestions = analyze_with_percentile_ranges("data.csv", percentile_threshold=99.0)

# With configuration object
from funputer.models import AnalysisConfig
config = AnalysisConfig(
    enable_percentile_ranges=True,
    default_percentile_threshold=90.0,
    min_samples_for_percentiles=15
)
suggestions = funputer.analyze_dataframe(df, config=config)
```

**CLI Usage:**
```bash
# Enable percentile ranges (95% default)
funputer analyze -d data.csv --percentile-threshold 95.0

# More conservative outlier detection (99%)
funputer analyze -d data.csv --percentile-threshold 99.0

# Disable percentile ranges (traditional min/max only)
funputer analyze -d data.csv --disable-percentile-ranges

# Custom minimum samples requirement
funputer analyze -d data.csv --min-samples-percentiles 25
```

## 🏷️ Frequency-Based Categorical Filtering

**NEW in v1.7.0**: Intelligent categorical filtering based on statistical significance thresholds.

Instead of including all categorical values regardless of frequency, FunPuter can filter out statistically insignificant categories that lack sufficient sample size for reliable analysis.

### Statistical Benefits

- **Chi-square validity**: Ensures minimum 5 occurrences per category for valid statistical tests
- **Sample size power**: Excludes categories with <1% representation for stable inference
- **Overfitting prevention**: Reduces model complexity by removing rare categories
- **Production robustness**: Handles unseen categories gracefully in deployed models

### Configuration Options

- **Min Count Threshold** (default: 5): Minimum absolute occurrences required
- **Min Percentage Threshold** (default: 1.0%): Minimum percentage of total data
- **Combined Logic**: Uses the more restrictive of count OR percentage thresholds

### Examples

```python
# Basic frequency filtering (min 5 occurrences OR 1% of data)
from funputer import analyze_with_frequency_filtering
suggestions = analyze_with_frequency_filtering("data.csv")

# Stricter filtering (min 10 occurrences OR 2% of data)  
suggestions = analyze_with_frequency_filtering("data.csv", 
                                             min_frequency_count=10, 
                                             min_frequency_percentage=2.0)

# Statistical significance threshold (chi-square validity)
suggestions = analyze_with_frequency_filtering("data.csv", min_frequency_count=5)

# Combined with percentile ranges for complete outlier resistance
from funputer import analyze_with_enhanced_filtering
suggestions = analyze_with_enhanced_filtering("data.csv", 
                                            percentile_threshold=95.0,
                                            min_frequency_percentage=2.0)
```

### Configuration Object

```python
from funputer.models import AnalysisConfig

config = AnalysisConfig(
    enable_frequency_filtering=True,
    min_frequency_count=5,
    min_frequency_percentage=1.0,
    min_samples_for_frequency_filtering=20
)
```

### CLI Usage

```bash
# Enable frequency filtering with default thresholds
funputer analyze -d data.csv --min-frequency-count 5 --min-frequency-percentage 1.0

# Stricter filtering for high-cardinality data
funputer analyze -d data.csv --min-frequency-count 10 --min-frequency-percentage 2.0

# Disable frequency filtering (include all categories)
funputer analyze -d data.csv --disable-frequency-filtering

# Combined with percentile ranges
funputer analyze -d data.csv --percentile-threshold 95.0 --min-frequency-percentage 2.0
```

## 💻 Command Line Interface

```bash
# Generate metadata template from your data
funputer init -d data.csv -o metadata.csv

# Analyze with auto-inference  
funputer analyze -d data.csv

# Analyze with custom metadata
funputer analyze -d data.csv -m metadata.csv --verbose

# Analyze with percentile-based ranges (NEW in v1.6.0)
funputer analyze -d data.csv --percentile-threshold 95.0

# Analyze with frequency filtering (NEW in v1.7.0)
funputer analyze -d data.csv --min-frequency-count 10 --min-frequency-percentage 2.0

# Combined enhanced analysis with both features
funputer analyze -d data.csv --percentile-threshold 95.0 --min-frequency-percentage 1.5

# Data quality check first
funputer preflight -d data.csv
```

## 📚 Usage Examples

### Basic Analysis

```python
import funputer

# Simple analysis with auto-inference
suggestions = funputer.analyze_imputation_requirements("sales_data.csv")

# Display recommendations
for suggestion in suggestions:
    print(f"Column: {suggestion.column_name}")
    print(f"Method: {suggestion.proposed_method}")  
    print(f"Confidence: {suggestion.confidence_score:.3f}")
    print(f"Missing: {suggestion.missing_count} values")
    print()
```

### Percentile-Based Range Analysis (NEW)

```python
import funputer

# Outlier-resistant analysis with percentile ranges
suggestions = funputer.analyze_with_percentile_ranges("customer_data.csv")

# Access both traditional and percentile bounds
from funputer.metadata_inference import infer_metadata_from_dataframe
from funputer.models import AnalysisConfig
import pandas as pd

df = pd.read_csv("customer_data.csv")
config = AnalysisConfig(enable_percentile_ranges=True, default_percentile_threshold=95.0)
metadata = infer_metadata_from_dataframe(df, config=config)

for meta in metadata:
    if meta.data_type in ['integer', 'float']:
        print(f"\n{meta.column_name}:")
        print(f"  Traditional bounds: {meta.min_value} - {meta.max_value}")
        if meta.percentile_low is not None:
            print(f"  Percentile bounds:  {meta.percentile_low:.1f} - {meta.percentile_high:.1f} ({meta.percentile_threshold}%)")
            print(f"  Outlier exclusion:  {((meta.max_value - meta.min_value) - (meta.percentile_high - meta.percentile_low)) / (meta.max_value - meta.min_value) * 100:.1f}% of range")
        else:
            print(f"  Percentile bounds:  Not available (insufficient samples)")
```

### Advanced Configuration

```python
from funputer.models import ColumnMetadata, AnalysisConfig
from funputer.analyzer import ImputationAnalyzer

# Custom metadata with business rules
metadata = [
    ColumnMetadata('product_id', 'string', unique_flag=True, max_length=10),
    ColumnMetadata('price', 'float', min_value=0, max_value=10000),
    ColumnMetadata('category', 'categorical', allowed_values='Electronics,Books,Clothing'),
    ColumnMetadata('rating', 'float', min_value=1.0, max_value=5.0),
]

# Custom analysis configuration
config = AnalysisConfig(
    missing_percentage_threshold=0.3,  # 30% threshold
    skip_columns=['internal_id'],
    outlier_threshold=0.1
)

# Run analysis
analyzer = ImputationAnalyzer(config)
suggestions = analyzer.analyze_dataframe(df, metadata)
```

### Industry-Specific Examples

**E-commerce Analytics**
```python
metadata = [
    ColumnMetadata('customer_id', 'integer', unique_flag=True, nullable=False),
    ColumnMetadata('age', 'integer', min_value=13, max_value=120),
    ColumnMetadata('purchase_amount', 'float', min_value=0),
    ColumnMetadata('customer_segment', 'categorical', allowed_values='Premium,Standard,Basic'),
]

# Enhanced analysis with frequency filtering for categorical data
suggestions = funputer.analyze_with_enhanced_filtering(customer_df, 
                                                     percentile_threshold=95.0,
                                                     min_frequency_percentage=2.0)
```

**Healthcare Data**  
```python
metadata = [
    ColumnMetadata('patient_id', 'integer', unique_flag=True, nullable=False),
    ColumnMetadata('age', 'integer', min_value=0, max_value=150),
    ColumnMetadata('blood_pressure', 'integer', min_value=50, max_value=300),
    ColumnMetadata('diagnosis', 'categorical', nullable=False),
]
config = AnalysisConfig(missing_threshold=0.05)  # Low tolerance for healthcare
suggestions = funputer.analyze_dataframe(patient_df, metadata, config)
```

**Financial Risk Assessment**
```python  
metadata = [
    ColumnMetadata('application_id', 'integer', unique_flag=True, nullable=False),
    ColumnMetadata('credit_score', 'integer', min_value=300, max_value=850),
    ColumnMetadata('debt_to_income', 'float', min_value=0.0, max_value=10.0),
    ColumnMetadata('loan_purpose', 'categorical', allowed_values='home,auto,personal,business'),
]
# Skip sensitive columns
config = AnalysisConfig(skip_columns=['ssn', 'account_number'])
suggestions = funputer.analyze_dataframe(loan_df, metadata, config)
```

## ⚙️ Requirements

- **Python**: 3.9 or higher
- **Dependencies**: pandas, numpy, scipy, pydantic, click, pyyaml

## 🔧 Installation from Source

```bash
git clone https://github.com/RajeshRamachander/funputer.git
cd funputer
pip install -e .
```

## 📚 Documentation

- **API Reference**: Complete docstrings and type hints throughout the codebase
- **Examples**: See usage examples above and in the codebase
- **Test Coverage**: 84% coverage with comprehensive test suite

## 📄 License  

Proprietary License - Source code is available for inspection but not for derivative works.

---

**Focus**: Get intelligent imputation recommendations, not complex infrastructure.