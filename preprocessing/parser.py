# parser.py
import re
from pathlib import Path
from typing import Dict

import pandas as pd
import camelot  # Requires camelot-py[cv]

from preprocessing.filtration import categorize_feed, feed_types


def numeric_from_str(s):
    if pd.isna(s):
        return None
    s = str(s).replace('\xa0', ' ').replace('%', '').replace(',', '.').strip()
    m = re.search(r'-?\d+\.\d+|-?\d+', s)
    return float(m.group(0)) if m else None


def find_tables(pdf_path):
    try:
        return camelot.read_pdf(str(pdf_path), pages='all', flavor='lattice', strip_text='\n')
    except Exception as e:
        print(f"Error reading PDF: {e}")
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
        if not name or re.search(r'гистриент|единица|сводный', name, re.I):
            continue
        sv_value = numeric_from_str(row.iloc[sv_col_idx])
        if sv_value is not None:
            nutrients[name] = sv_value
    return nutrients


def parse_pdf_diet(pdf_path: str) -> Dict:
    tables = find_tables(pdf_path)
    recipe_tables, nutrient_tables = classify_tables(tables)

    all_ingredients = {}
    for table in recipe_tables:
        ingredients = parse_ingredients_table(table)
        all_ingredients.update(ingredients)

    all_nutrients = {}
    for table in nutrient_tables:
        nutrients = parse_nutrients_table(table)
        all_nutrients.update(nutrients)

    ingred_by_code = {code: 0.0 for code in feed_types.keys()}
    ratios = {'corn': 0.0, 'soybean': 0.0, 'alfalfa': 0.0, 'other': 0.0}
    for name, percent in all_ingredients.items():
        group, code, label = categorize_feed(name)
        if code:
            ingred_by_code[code] += percent
        ratios[group] += percent

    pdf_name = Path(pdf_path).name
    ration_row = {'pdf': pdf_name}
    codes = sorted(feed_types.keys(), key=int)
    for code in codes:
        label = feed_types[code]
        ration_row[label + ' % СВ'] = ingred_by_code.get(code, 0.0)

    ration_df = pd.DataFrame([ration_row])

    nutrient_row = {'pdf': pdf_name}
    nutrient_row.update(all_nutrients)
    nutrient_df = pd.DataFrame([nutrient_row])

    return {
        'ration_df': ration_df,
        'nutrient_df': nutrient_df,
        'ingredients': all_ingredients,
        'nutrients': all_nutrients,
        'ratios': ratios
    }


def parse_excel_fatty_acids(file_path: str) -> Dict[str, float]:
    try:
        df = pd.read_excel(file_path)
        fatty_acid_columns = {
            'lauric': ['lauric', 'lauric acid', 'C12:0', 'C12', 'лауриновая', 'лауриновая кислота'],
            'palmitic': ['palmitic', 'palmitic acid', 'C16:0', 'C16', 'пальмитиновая', 'пальмитиновая кислота'],
            'stearic': ['stearic', 'stearic acid', 'C18:0', 'C18', 'стеариновая', 'стеариновая кислота'],
            'oleic': ['oleic', 'oleic acid', 'C18:1', 'C18:1n9', 'олеиновая', 'олеиновая кислота'],
            'linoleic': ['linoleic', 'linoleic acid', 'C18:2', 'C18:2n6', 'линолевая', 'линолевая кислота'],
            'linolenic': ['linolenic', 'linolenic acid', 'C18:3', 'C18:3n3', 'линоленовая', 'линоленовая кислота']
        }
        result = {}
        for acid_name, possible_names in fatty_acid_columns.items():
            found_value = None
            for col in df.columns:
                col_lower = str(col).lower()
                for name in possible_names:
                    if name.lower() in col_lower:
                        for idx, row in df.iterrows():
                            value = row[col]
                            if pd.notna(value) and isinstance(value, (int, float)):
                                found_value = float(value)
                                break
                        if found_value is not None:
                            break
                if found_value is not None:
                    break
            result[acid_name] = found_value if found_value is not None else 0.0
        return result
    except Exception as e:
        print(f"Excel parsing error: {str(e)}")
        return {}