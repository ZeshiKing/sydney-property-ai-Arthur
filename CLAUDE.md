# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
This is a Python-based data analysis project focused on Sydney real estate properties. The project processes CSV data from Domain.com.au listings and performs exploratory data analysis using pandas and scikit-learn.

## Commands
Since this is a simple Python script project without formal build tools:
- **Run main script**: `python Data_process.py`
- **Install dependencies**: `pip install pandas scikit-learn` (no requirements.txt exists)

## Data Architecture
The project works with multiple CSV datasets that have been consolidated:
- `sydney_properties_working.csv` (5,980 rows)
- `sydney_properties_working_2.csv` (2,318 rows) 
- `sydney_properties_working_3.csv` (2,915 rows)
- `sydney_properties_working_final.csv` (17,938 rows) - **Main dataset**

### Data Schema
Key columns in the datasets:
- `price`: String format (e.g., "$695,000" or "Contact Agent")
- `price_numeric`: Float format for calculations (null for "Contact Agent" entries)
- `address`, `suburb`: Location information
- `bedrooms`, `bathrooms`, `parking`: Property features (integers)
- `property_type`: Category (e.g., "Apartment / Unit / Flat")
- `link`: Domain.com.au listing URL

## Code Structure
- **Single-file implementation**: All processing logic in `Data_process.py`
- **Data pipeline pattern**: Load → Clean → Process → Analyze
- **ML preprocessing imports**: StandardScaler and cosine_similarity available but not actively used
- **Mixed language comments**: Some comments in Chinese

## Current State
The project is in exploratory phase with:
- Basic data loading and filtering (removes null price_numeric entries)
- Commented-out data exploration code
- No formal project structure or dependency management
- No testing or linting configuration

## Development Notes
- The script filters out properties with "Contact Agent" pricing (null price_numeric values)
- Previous data merging operations are commented out, suggesting completed consolidation
- Machine learning preprocessing capabilities imported but not implemented