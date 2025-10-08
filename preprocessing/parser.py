# parser.py
import re
from pathlib import Path
from typing import Dict
from collections import defaultdict
import pandas as pd
try:
    import camelot  # Requires camelot-py (import name: camelot)
    CAMELOT_AVAILABLE = True
    CAMELOT_IMPORT_ERROR = None
except Exception as e:
    CAMELOT_AVAILABLE = False
    CAMELOT_IMPORT_ERROR = e
try:
    from pdf2image import convert_from_path
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

from preprocessing.filtration import (
    feed_types,
    categorize_feed,
    map_ingredients_to_codes,
    aggregate_ratios,
)


def numeric_from_str(s):
    if pd.isna(s):
        return None
    s = str(s).replace('\xa0', ' ').replace('%', '').replace(',', '.').strip()
    m = re.search(r'-?\d+\.\d+|-?\d+', s)
    return float(m.group(0)) if m else None


def find_tables(pdf_path):
    if not CAMELOT_AVAILABLE:
        raise ImportError(
            "Парсер PDF недоступен: не установлен или повреждён camelot-py. "
            "Удалите пакет 'camelot' (не тот) и установите 'camelot-py[cv]'."
        )
    try:
        return camelot.read_pdf(str(pdf_path), pages='all', flavor='lattice', strip_text='\n')
    except Exception as e:
        print(f"PDF read error: {e}")
        return []

def classify_tables(tables):
    recipe_tables = []
    nutrient_tables = []
    for table in tables:
        flat_text = " ".join(table.df.astype(str).values.flatten())
        if re.search(r'Ингредиенты|Рецепт', flat_text, re.I):
            recipe_tables.append(table)
        elif re.search(r'Сводный анализ|Нутриент|Лактирующая корова', flat_text, re.I):
            nutrient_tables.append(table)
    return recipe_tables, nutrient_tables

def parse_ingredients_table(table):
    df = table.df.copy()
    name_col_idx = 0
    percent_sv_col_idx = 5
    ingredients = {}
    for _, row in df.iterrows():
        name = str(row.iloc[name_col_idx]).strip()
        if not name or re.search(r'ингредиент|рецепт|всего|итого|общие', name, re.I) or len(name) < 2:
            continue
        percent_sv_value = numeric_from_str(row.iloc[percent_sv_col_idx])
        if percent_sv_value is not None and 0 <= percent_sv_value <= 100:
            ingredients[name] = percent_sv_value
    return ingredients

def parse_nutrients_table(table):
    df = table.df.copy()
    name_col_idx = 0
    sv_col_idx = 2
    nutrients = {}
    for _, row in df.iterrows():
        name = str(row.iloc[name_col_idx]).strip()
        if not name or re.search(r'нутриент|единица|сводный', name, re.I):
            continue
        sv_value = numeric_from_str(row.iloc[sv_col_idx])
        if sv_value is not None:
            nutrients[name] = sv_value
            
    return nutrients
    
def parse_pdf_diet(pdf_path):
    """
    Парсит PDF рацион и возвращает структуру, ожидаемую GUI:
      {
        'ingredients': {<имя>: %СВ, ...},
        'ingredients_by_code': {<код>: %СВ, ...},
        'nutrients': {<русское имя нутриента>: значение, ...},
        'ratios': {'corn': ..., 'soybean': ..., 'alfalfa': ..., 'other': ...}
      }
    """
    if not CAMELOT_AVAILABLE:
        raise ImportError(
            "Camelot (camelot-py) недоступен. Установите 'camelot-py[cv]' и удалите возможный пакет 'camelot'. "
            f"Исходная ошибка импорта: {CAMELOT_IMPORT_ERROR}"
        )

    tables = find_tables(pdf_path)
    ingredients_by_name = {}
    nutrients_by_name = {}

    if tables:
        recipe_tables, nutrient_tables = classify_tables(tables)
        for table in recipe_tables:
            ingredients_by_name.update(parse_ingredients_table(table))
        for table in nutrient_tables:
            nutrients_by_name.update(parse_nutrients_table(table))

    ingredients_by_code = map_ingredients_to_codes(ingredients_by_name)
    ratios = aggregate_ratios(ingredients_by_name)

    return {
        'ingredients': ingredients_by_name,
        'ingredients_by_code': ingredients_by_code,
        'nutrients': nutrients_by_name,
        'ratios': ratios,
    }