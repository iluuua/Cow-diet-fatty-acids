# export.py
from typing import Dict
import pandas as pd


def export_analysis_to_excel(analysis_data: Dict, diet_data: Dict,
                             predictions: Dict, filename: str = "milk_analysis_export.xlsx"):
    try:
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            if analysis_data:
                analysis_df = pd.DataFrame([analysis_data])
                analysis_df.to_excel(writer, sheet_name='Fatty Acid Analysis', index=False)
            if diet_data:
                diet_df = pd.DataFrame([diet_data])
                diet_df.to_excel(writer, sheet_name='Diet Information', index=False)
            if predictions:
                pred_df = pd.DataFrame([predictions])
                pred_df.to_excel(writer, sheet_name='Predictions', index=False)
        return True, f"Данные успешно экспортированы в {filename}"
    except Exception as e:
        return False, f"Ошибка экспорта данных: {str(e)}"
