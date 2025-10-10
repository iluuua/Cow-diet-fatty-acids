# parser.py
import re
import pandas as pd

try:
    import camelot  # Requires camelot-py (import name: camelot)

    CAMELOT_AVAILABLE = True
    CAMELOT_IMPORT_ERROR = None
except Exception as e:
    CAMELOT_AVAILABLE = False
    CAMELOT_IMPORT_ERROR = e
# OCR не используется в текущей реализации, удалён

from preprocessing.filtration import (
    categorize_feeds_bulk,
)

from typing import List

# Обновлённый список all_columns
all_columns = [
    'Нутриент', 'Фураж', 'Концентрат', 'ЧЭЛ 3x NRC', 'ОЭ', 'СП', 'ПНР 3x Уровень 1', 'Сол. КП', 'Крахмал', 'aNDFom',
    'aNDFom фуража', 'CHO C uNDF', 'Растворимая', 'КДК', 'Сахар (ВРУ)', 'НСУ', 'НВУ', 'СЖ', 'ОЖК', 'СВ', 'Влага',
    'Зола', 'Ca', 'P', 'Mg', 'K', 'Na', 'Cl', 'S', 'НРП', 'peNDF', 'Растворимая клетчатка', 'СК', 'Азот', 'NaCl',
    'Fe - всего', 'Cu - всего', 'Zn - всего', 'НДНП', 'RD Крахмал', 'RD CHO 3x', 'LYS', 'MET', 'RD Крахмал 3xУровень 1',
    'Масляная', 'КДЛ', 'СУ', 'Уксусная', 'Пропионовая', 'Молочная', 'CHO C uNDF Lig*2.4', 'TRUE PROTEIN',
    'Аммиак (Прот. А1)',
    'I - всего', 'ПРР 3x Уровень 1', 'Монензин', 'Растворимый', 'CHO B3 pdNDF', 'VAL', 'LEU'
]

# Словарь синонимов для объединения схожих полей
synonyms_map = {
    'RD Крахмал': 'Крахмал',
    'RD Крахмал 3xУровень 1': 'Крахмал',
    'RD CHO 3x': 'CHO C uNDF',
    # добавь другие синонимы при необходимости
}


def postprocess_table_data(df: pd.DataFrame) -> List:
    """
    Сопоставляет данные из df с all_columns, объединяет схожие поля.
    Возвращает список значений по порядку all_columns.
    """
    # Извлекаем имена колонок и значения
    columns = list(df[0].iloc[1:])  # например, 'Нутриент', 'Крахмал' и т.д.
    values = list(df[2].iloc[1:])  # соответствующие значения

    # Сопоставляем колонки с их значениями
    column_to_value = {}
    for col, val in zip(columns, values):
        col_clean = col.strip()
        # Проверяем, есть ли синоним
        col_mapped = synonyms_map.get(col_clean, col_clean)
        if col_mapped not in column_to_value:
            column_to_value[col_mapped] = val  # берём первое значение, если несколько синонимов

    # Создаём итоговый список значений по порядку all_columns
    result = []
    for col in all_columns:
        value = column_to_value.get(col, 0)  # если нет, то 0
        result.append(value)

    return result


def parse_pdf(pdf_path):
    try:
        tables = camelot.read_pdf(pdf_path, pages="all", flavor="lattice")
        all_df = []
        if tables:
            print(f"Найдено {len(tables)} таблиц Camelot")
            for i, table in enumerate(tables):
                df = table.df
                all_df.append(df)
            return all_df
        else:
            raise ValueError("Camelot не нашёл таблицы")
    except Exception as e:
        print("Camelot не справился:", e)
        return []


def get_nutrients_data(full_path):
    """
    Возвращает pd.DataFrame с одной строкой, содержащей все значения из "Сводного анализа".
    """
    all_tables = parse_pdf(full_path)
    analysis = None
    for j in range(len(all_tables)):
        first_cell = str(all_tables[j].iloc[0, 0])
        if "Сводный анализ" in first_cell:
            analysis = all_tables[j]
            break

    if analysis is None:
        print("Таблица 'Сводный анализ' не найдена.")
        # Возвращаем пустую строку с нужными колонками
        return pd.DataFrame(columns=[f'Value_{i}' for i in range(len(all_columns))])

    # Обрабатываем таблицу
    values = postprocess_table_data(analysis)

    # Создаём DataFrame с одной строкой и колонками Value_0, Value_1, ...
    result_df = pd.DataFrame([values], columns=[f'Value_{i}' for i in range(len(values))])
    return result_df


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


def parse_pdf_diet(pdf_path):
    if not CAMELOT_AVAILABLE:
        raise ImportError(
            "Camelot (camelot-py) недоступен. Установите 'camelot-py[cv]' и удалите возможный пакет 'camelot'. "
            f"Исходная ошибка импорта: {CAMELOT_IMPORT_ERROR}"
        )

    tables = find_tables(pdf_path)
    ingredients_by_name = {}

    if tables:
        recipe_tables, nutrient_tables = classify_tables(tables)
        for table in recipe_tables:
            ingredients_by_name.update(parse_ingredients_table(table))
            df_ingredients = categorize_feeds_bulk(ingredients_by_name)
        df_nutrients = get_nutrients_data(pdf_path)
    return df_ingredients, df_nutrients
