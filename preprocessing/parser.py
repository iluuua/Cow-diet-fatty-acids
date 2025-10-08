# parser.py
import re
from pathlib import Path
from typing import Dict

import pandas as pd
import camelot  # Requires camelot-py[cv]
try:
    from pdf2image import convert_from_path
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

from preprocessing.filtration import (
    categorize_feed,
    feed_types,
    map_ingredients_to_codes,
    aggregate_ratios,
)

def numeric_from_str(s):
    if pd.isna(s):
        return None
    s = str(s).replace('\xa0', ' ').replace('%', '').replace(',', '.').strip()
    m = re.search(r'-?\d+\.\d+|-?\d+', s)
    return float(m.group(0)) if m else None

def ocr_pdf(pdf_path: str) -> str:
    if not OCR_AVAILABLE:
        print("OCR dependencies not found. Install pdf2image and pytesseract.")
        return ''
    try:
        images = convert_from_path(pdf_path)
        text = ''
        for image in images:
            text += pytesseract.image_to_string(image, lang='rus+eng') + '\n'
        return text
    except Exception as e:
        print(f"OCR error: {e}. Ensure poppler and tesseract are installed.")
        return ''

def find_tables(pdf_path):
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

def parse_ingredients_from_text(text: str) -> Dict[str, float]:
    lines = text.split('\n')
    in_ingredients = False
    ingredients = {}
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if re.search(r'Ингредиенты|Рецепт', line, re.I):
            in_ingredients = True
            continue
        if re.search(r'Общие значения|Сводный анализ', line, re.I):
            in_ingredients = False
            continue
        if in_ingredients:
            match = re.search(r'(\d+[.,]\d+|\d+)', line)
            if match:
                name = line[:match.start()].strip()
                if not name:
                    continue
                numbers_str = line[match.start():]
                numbers = re.findall(r'[\d.]+', numbers_str)  # Remove commas for float
                if len(numbers) >= 5:
                    percent_sv_str = numbers[4]
                    try:
                        percent_sv = float(percent_sv_str.replace(',', '.'))
                        if 0 <= percent_sv <= 100:
                            ingredients[name] = percent_sv
                    except ValueError:
                        pass
    return ingredients

def parse_nutrients_from_text(text: str) -> Dict[str, float]:
    lines = text.split('\n')
    in_nutrients = False
    nutrients = {}
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if re.search(r'Сводный анализ|Нутриент|Лактирующая корова', line, re.I):
            in_nutrients = True
            continue
        if re.search(r'Сводка CNCPS|Pag\.', line, re.I):
            in_nutrients = False
            continue
        if in_nutrients:
            match = re.search(r'(\d+[.,]\d+|\d+)', line)
            if match:
                name_and_unit = line[:match.start()].strip()
                if not name_and_unit:
                    continue
                # Split to separate name and unit
                parts = name_and_unit.split()
                if len(parts) >= 2:
                    unit = parts[-1]
                    name = ' '.join(parts[:-1])
                else:
                    name = name_and_unit
                    unit = ''
                sv_str = match.group(0).replace(',', '.')
                try:
                    sv = float(sv_str)
                    nutrients[name] = sv
                except ValueError:
                    pass
    return nutrients

def parse_pdf_ingredients(pdf_path: str) -> Dict[str, float]:
    """Парсит только ингредиенты из PDF.
    Возвращает dict: имя ингредиента -> % СВ.
    """
    tables = find_tables(pdf_path)
    ingredients = {}
    if tables:
        recipe_tables, _nutrient_tables = classify_tables(tables)
        for table in recipe_tables:
            ingredients.update(parse_ingredients_table(table))
    else:
        text = ocr_pdf(pdf_path)
        if text:
            ingredients = parse_ingredients_from_text(text)
    return ingredients


def parse_pdf_nutrients(pdf_path: str) -> Dict[str, float]:
    """Парсит только нутриенты из PDF.
    Возвращает dict: название нутриента -> значение (в единицах из отчёта).
    """
    tables = find_tables(pdf_path)
    nutrients = {}
    if tables:
        _recipe_tables, nutrient_tables = classify_tables(tables)
        for table in nutrient_tables:
            nutrients.update(parse_nutrients_table(table))
    else:
        text = ocr_pdf(pdf_path)
        if text:
            nutrients = parse_nutrients_from_text(text)
    return nutrients


def parse_pdf_diet(pdf_path: str) -> Dict:
    """Композитная функция: парсит ингредиенты и нутриенты, агрегирует группы.
    Возвращает dict с ингредиентами, нутриентами, соотношениями и удобными DataFrame.
    """
    all_ingredients = parse_pdf_ingredients(pdf_path)
    all_nutrients = parse_pdf_nutrients(pdf_path)

    # Агрегации
    ingred_by_code = map_ingredients_to_codes(all_ingredients)
    ratios = aggregate_ratios(all_ingredients)

    pdf_name = Path(pdf_path).name
    # Удобный DF с ингредиентами по кодам (колонки — лейблы feed_types)
    ration_row = {'pdf': pdf_name}
    codes = sorted(feed_types.keys(), key=int)
    for code in codes:
        label = feed_types[code]
        ration_row[label + ' % СВ'] = float(ingred_by_code.get(code, 0.0))
    ration_df = pd.DataFrame([ration_row])

    nutrient_row = {'pdf': pdf_name}
    nutrient_row.update(all_nutrients)
    nutrient_df = pd.DataFrame([nutrient_row])

    return {
        'ration_df': ration_df,
        'nutrient_df': nutrient_df,
        'ingredients': all_ingredients,
        'nutrients': all_nutrients,
        'ingredients_by_code': ingred_by_code,
        'ratios': ratios
    }


 

