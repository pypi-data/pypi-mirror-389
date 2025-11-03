"""
Simplified command-line interface with only essential commands.
"""

import click
import logging
import sys
import json
import pandas as pd
from pathlib import Path

from .analyzer import analyze_imputation_requirements
from .models import AnalysisConfig
from .io import save_suggestions


@click.group()
def cli():
    """FunPuter - Intelligent Imputation Analysis"""
    pass


@cli.command()
@click.option("--data", "-d", required=True, help="Path to data CSV file to analyze")
@click.option("--metadata", "-m", help="Path to metadata file (CSV or JSON). If not provided, auto-infers metadata")
@click.option("--output", "-o", help="Output path for analysis results (JSON format)")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--percentile-threshold", type=float, default=95.0, help="Percentile threshold for outlier-resistant ranges (50.0-99.9, default: 95.0)")
@click.option("--min-samples-percentiles", type=int, default=20, help="Minimum samples required for percentile calculation (default: 20)")
@click.option("--disable-percentile-ranges", is_flag=True, help="Disable percentile-based range calculation")
def analyze(data, metadata, output, verbose, percentile_threshold, min_samples_percentiles, disable_percentile_ranges):
    """
    Analyze dataset for missing data imputation recommendations.

    This is the main command that analyzes your data and provides intelligent
    imputation method suggestions based on data patterns and constraints.

    Examples:

    # Auto-infer metadata and analyze
    funputer analyze -d data.csv

    # Use explicit metadata file
    funputer analyze -d data.csv -m metadata.csv

    # Save results to file
    funputer analyze -d data.csv -o results.json
    
    # Use 99th percentile for outlier-resistant ranges
    funputer analyze -d data.csv --percentile-threshold 99.0
    
    # Disable percentile ranges (use only traditional min/max)
    funputer analyze -d data.csv --disable-percentile-ranges
    
    # Require fewer samples for percentile calculation
    funputer analyze -d data.csv --min-samples-percentiles 10
    """
    if verbose:
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
        logger = logging.getLogger(__name__)

    try:
        # Basic data validation
        data_path = Path(data)
        if not data_path.exists():
            click.echo(f"❌ Error: Data file not found: {data}", err=True)
            sys.exit(1)

        if verbose:
            click.echo(f"📊 Analyzing dataset: {data}")

        # Validate percentile options
        if not (50.0 <= percentile_threshold <= 99.9):
            click.echo(f"❌ Error: Percentile threshold must be between 50.0 and 99.9, got {percentile_threshold}", err=True)
            sys.exit(1)
        
        if min_samples_percentiles < 5:
            click.echo(f"❌ Error: Minimum samples for percentiles must be at least 5, got {min_samples_percentiles}", err=True)
            sys.exit(1)
        
        # Create analysis configuration
        from .models import AnalysisConfig
        config = AnalysisConfig(
            enable_percentile_ranges=not disable_percentile_ranges,
            default_percentile_threshold=percentile_threshold,
            min_samples_for_percentiles=min_samples_percentiles
        )
        
        if verbose:
            if config.enable_percentile_ranges:
                click.echo(f"📈 Percentile ranges enabled: {percentile_threshold}% threshold, min {min_samples_percentiles} samples")
            else:
                click.echo("📈 Percentile ranges disabled")

        # Run analysis
        if metadata:
            # Use explicit metadata file
            metadata_path = Path(metadata)
            if not metadata_path.exists():
                click.echo(f"❌ Error: Metadata file not found: {metadata}", err=True)
                sys.exit(1)
            
            if verbose:
                click.echo(f"📋 Using metadata file: {metadata}")
            
            suggestions = analyze_imputation_requirements(
                data_path=str(data_path),
                metadata_path=str(metadata_path),
                config=config
            )
        else:
            # Auto-infer metadata
            if verbose:
                click.echo("🤖 Auto-inferring metadata from data...")
            
            suggestions = analyze_imputation_requirements(data_path=str(data_path), config=config)

        if not suggestions:
            click.echo("⚠️  No imputation suggestions generated. Check your data file.")
            sys.exit(1)

        # Display results
        click.echo(f"\n📈 Analysis Results ({len(suggestions)} columns):")
        click.echo("=" * 60)

        columns_with_missing = 0
        total_missing = 0
        confidence_scores = []

        for suggestion in suggestions:
            if suggestion.missing_count > 0:
                columns_with_missing += 1
                total_missing += suggestion.missing_count
                
                click.echo(f"\n🔍 {suggestion.column_name}")
                click.echo(f"   Missing: {suggestion.missing_count} ({suggestion.missing_percentage:.1%})")
                click.echo(f"   Method: {suggestion.proposed_method}")
                click.echo(f"   Confidence: {suggestion.confidence_score:.2f}")
                click.echo(f"   Rationale: {suggestion.rationale}")
                
                if suggestion.outlier_count > 0:
                    click.echo(f"   Outliers: {suggestion.outlier_count} ({suggestion.outlier_percentage:.1%})")
            
            confidence_scores.append(suggestion.confidence_score)

        # Summary
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        click.echo(f"\n📋 Summary:")
        click.echo(f"   Columns with missing data: {columns_with_missing}")
        click.echo(f"   Total missing values: {total_missing}")
        click.echo(f"   Average confidence: {avg_confidence:.2f}")

        # Save results if requested
        if output:
            save_suggestions(suggestions, output)
            click.echo(f"\n💾 Results saved to: {output}")

        click.echo("\n✅ Analysis complete!")

    except Exception as e:
        click.echo(f"❌ Error during analysis: {str(e)}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option("--data", "-d", required=True, help="Path to data CSV file to validate")
@click.option("--json-out", help="Save validation report to JSON file")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def validate(data, json_out, verbose):
    """
    Run basic data validation checks before analysis.

    This command performs quick validation to check if your data file
    is ready for analysis and provides recommendations for next steps.

    Examples:

    # Basic validation
    funputer validate -d data.csv

    # Save validation report
    funputer validate -d data.csv --json-out report.json
    """
    if verbose:
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    try:
        # Import preflight functionality
        from .preflight import run_preflight, format_preflight_report

        data_path = Path(data)
        if not data_path.exists():
            click.echo(f"❌ Error: Data file not found: {data}", err=True)
            sys.exit(1)

        if verbose:
            click.echo(f"🔍 Validating dataset: {data}")

        # Run validation
        report = run_preflight(str(data_path))
        
        # Format and display results
        formatted_report = format_preflight_report(report)
        click.echo(formatted_report)

        # Save JSON report if requested
        if json_out:
            with open(json_out, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            click.echo(f"\n💾 Validation report saved to: {json_out}")

        # Exit with appropriate code
        exit_code = report.get('exit_code', 0)
        if exit_code == 0:
            click.echo("\n✅ Data validation passed!")
        elif exit_code == 2:
            click.echo("\n⚠️  Data validation passed with warnings.")
        else:
            click.echo(f"\n❌ Data validation failed (code: {exit_code})")
        
        sys.exit(exit_code)

    except Exception as e:
        click.echo(f"❌ Error during validation: {str(e)}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    cli()