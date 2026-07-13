from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
ROOT_DIR = PROJECT_DIR.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from src.analysis import build_analysis
from src.data_loader import load_all_sheets, load_workbook_info
from src.data_quality import data_quality_summary, profile_dataframe
from src.metrics import compute_kpis
from src.report_builder import build_report
from src.transformations import prepare_data


def _log_validation_results(quality_results: list[object], log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    lines = [f'[{timestamp}] Report validation results']
    for item in quality_results:
        issue = getattr(item, 'issue', 'unknown')
        count = getattr(item, 'count', '')
        details = getattr(item, 'details', '')
        line = f'- {issue}: {count} ({details})'
        lines.append(line)
        print(f'Validation | {line}')
    lines.append('')
    with log_path.open('a', encoding='utf-8') as log_file:
        log_file.write('\n'.join(lines))
        log_file.write('\n')


def main() -> None:
    workbook_path = ROOT_DIR / 'Regional_Sales.xlsx'
    output_path = PROJECT_DIR / 'output' / 'regional_sales_report.html'
    validation_log_path = PROJECT_DIR / 'logs' / 'report_validation.log'

    workbook_info = load_workbook_info(workbook_path)
    sheets = load_all_sheets(workbook_path)
    prepared = prepare_data(sheets)

    profile = profile_dataframe(prepared.orders)
    quality = data_quality_summary(prepared.orders, prepared.column_map)
    _log_validation_results(quality, validation_log_path)
    kpis = compute_kpis(prepared.orders)
    analysis = build_analysis(prepared.orders, prepared.has_product)

    build_report(
        project_dir=PROJECT_DIR,
        output_path=output_path,
        kpis=kpis,
        analysis=analysis,
        quality_results=quality,
        workbook_info=workbook_info.__dict__,
        profile=profile,
        filtered_df=prepared.orders,
        has_product=prepared.has_product,
    )
    print(f'Report written to {output_path}')
    print(f'Validation log written to {validation_log_path}')


if __name__ == '__main__':
    main()
