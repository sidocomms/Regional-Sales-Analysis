# Regional Sales Report

This project builds an interactive HTML business intelligence report from `Regional_Sales.xlsx`.

## Installation

Use the existing virtual environment or install the required packages from `requirements.txt`.

## Requirements

- Python
- pandas
- numpy
- plotly
- jinja2
- openpyxl

## How to Run

From the project root, run:

```bash
python regional_sales_report/generate_report.py
```

The report is generated at:

`regional_sales_report/output/regional_sales_report.html`

## Folder Structure

- `generate_report.py` - main entry point
- `requirements.txt` - Python dependencies
- `README.md` - usage notes
- `assets/` - report styling
- `output/` - generated HTML report
- `templates/` - Jinja2 HTML template
- `src/` - data loading, transformation, KPI, analysis, and report code
- `logs/` - run logs

## Known Limitations

- The workbook uses IDs for several dimensions, so the report relies on supporting sheets to map customers, teams, categories, stores, and regions.
- Product-level analysis is shown at category level because the workbook does not provide a separate product name column in the sales order sheet.
- The HTML report is standalone, but cross-filtering is limited compared with a live BI server.
