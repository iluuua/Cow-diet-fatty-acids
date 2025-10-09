import pandas as pd
from typing import Dict, List

# Берём справочник кодов -> лейблов и список целевых лейблов ингредиентов для UI
from preprocessing.filtration import (
    feed_types,
    ingredient_cols,
    categorize_feed,
)

# -------------------------
# Маппинг нутриентов: русское имя -> Value_i
# (Синхронизирован с utils.constants._NUTRIENT_LABELS)
# -------------------------
NUTRIENT_LABEL_TO_FEATURE = {
    'ЧЭЛ 3x NRC': 'Value_0',
    'СП': 'Value_2',
    'Крахмал': 'Value_3',
    'RD Крахмал 3x Уровень 1': 'Value_4',
    'Сахар': 'Value_5',
    'НСУ': 'Value_6',
    'НВУ': 'Value_8',
    'aNDFom': 'Value_9',
    'CHO B3 pdNDF': 'Value_10',
    'Растворимая клетчатка': 'Value_11',
    'aNDFom фуража': 'Value_13',
    'peNDF': 'Value_15',
    'CHO B3 медленная фракция': 'Value_16',
    'CHO C uNDF': 'Value_17',
}

# Порядок показа фич нутриентов в UI
NUTRIENT_FEATURES: List[str] = list(NUTRIENT_LABEL_TO_FEATURE.values())


def map_nutrients_to_features(nutrients_by_name: Dict[str, float]) -> Dict[str, float]:
    """Конвертирует русские названия нутриентов -> Value_i фичи модели."""
    mapped: Dict[str, float] = {}
    for name, val in nutrients_by_name.items():
        key = NUTRIENT_LABEL_TO_FEATURE.get(name)
        if key:
            mapped[key] = float(val)
    return mapped


# -------------------------
# Маппинг ингредиентов: человекочитаемый лейбл -> код из feed_types
# Основан на filtration.ingredient_cols
# -------------------------
LABEL_TO_CODE = {
    'Кукуруза плющеная': '01',
    'Тритикале сенаж': '02',
    'Патока свекловичная': '04',
    'Шрот соевый': '05',
    'Кукуруза силос': '06',
    'Жир защищенный': '07',
    'Солома': '08',
    'Ячмень сухой': '09',
    'Кукуруза сухая': '12',
    'Сено': '14',
    'Жом свекловичный': '15',
    'Комбикорм': '17',
    'Кукуруза корнаж': '19',
    'Кукуруза влажная': '22',
    'Пшеница': '25',
    'Соевая оболочка': '27',
    'Жмых рапсовый': '30',
    'Сода': '32',
    'Л.Е.Д. ЖНАПКХ добавка': '35',
    'Кальций пропионат': '45',
}

CODE_TO_UI_LABEL = {code: label for label, code in LABEL_TO_CODE.items()}


def map_ingredients_to_codes(ingredients_by_name: Dict[str, float]) -> Dict[str, float]:
    """Преобразует {читаемый лейбл: %СВ} -> {код: %СВ}.
    Предполагается, что ключи приходят из filtration.ingredient_cols.
    Неизвестные ключи игнорируются.
    """
    by_code: Dict[str, float] = {}
    for label, val in ingredients_by_name.items():
        code = LABEL_TO_CODE.get(label)
        if code:
            by_code[code] = float(val)
    return by_code


def aggregate_ratios(ingredients_by_name: Dict[str, float]) -> Dict[str, float]:
    """Грубая агрегация по 4 группам для БД: corn/soybean/alfalfa/other.
    Использует коды из feed_types.
    """
    by_code = map_ingredients_to_codes(ingredients_by_name)

    # Группы определяем через наборы кодов
    corn_codes = {'01', '06', '12', '19', '22', '42'}
    soybean_codes = {'05', '27'}
    alfalfa_codes = {'11'}

    corn = sum(v for c, v in by_code.items() if c in corn_codes or 'кукуруза' in feed_types.get(c, '').lower())
    soybean = sum(v for c, v in by_code.items() if c in soybean_codes or 'соев' in feed_types.get(c, '').lower())
    alfalfa = sum(v for c, v in by_code.items() if c in alfalfa_codes or 'люцерна' in feed_types.get(c, '').lower())

    other = max(0.0, sum(by_code.values()) - (corn + soybean + alfalfa))
    return {
        'corn': float(corn),
        'soybean': float(soybean),
        'alfalfa': float(alfalfa),
        'other': float(other),
    }


def aggregate_ratios_from_codes(ingredients_by_code: Dict[str, float]) -> Dict[str, float]:
    """Агрегация по группам, если на входе коды ингредиентов ("01", "05", ...)."""
    corn_codes = {'01', '06', '12', '19', '22', '42'}
    soybean_codes = {'05', '27'}
    alfalfa_codes = {'11'}

    corn = sum(v for c, v in ingredients_by_code.items() if c in corn_codes or 'кукуруза' in feed_types.get(c, '').lower())
    soybean = sum(v for c, v in ingredients_by_code.items() if c in soybean_codes or 'соев' in feed_types.get(c, '').lower())
    alfalfa = sum(v for c, v in ingredients_by_code.items() if c in alfalfa_codes or 'люцерна' in feed_types.get(c, '').lower())
    other = max(0.0, sum(ingredients_by_code.values()) - (corn + soybean + alfalfa))
    return {
        'corn': float(corn),
        'soybean': float(soybean),
        'alfalfa': float(alfalfa),
        'other': float(other),
    }


def map_parsed_names_to_codes(ingredients_by_name: Dict[str, float]) -> Dict[str, float]:
    """Маппинг произвольных имён из PDF -> коды через filtration.categorize_feed."""
    df = categorize_feed(ingredients_by_name)
    reverse_map = {v: k for k, v in feed_types.items()}
    by_code: Dict[str, float] = {}
    if not df.empty:
        row = df.iloc[0]
        for label, value in row.items():
            if value and float(value) > 0:
                code = reverse_map.get(label)
                if code:
                    by_code[code] = float(value)
    return by_code


def prepare_ingredients_df(ingredients_by_name: Dict[str, float]) -> pd.DataFrame:
    """Формирует DataFrame с колонками по лейблам feed_types + '% СВ'."""
    ingred_by_code = map_ingredients_to_codes(ingredients_by_name)
    row = {}
    for code in sorted(feed_types.keys(), key=int):
        label = feed_types[code]
        row[label + ' % СВ'] = float(ingred_by_code.get(code, 0.0))
    return pd.DataFrame([row])


def prepare_nutrients_df(nutrients_by_name: Dict[str, float]) -> pd.DataFrame:
    """Формирует DataFrame с колонками из NUTRIENT_FEATURES (Value_i)."""
    feat = map_nutrients_to_features(nutrients_by_name)
    row = {k: 0.0 for k in NUTRIENT_FEATURES}
    row.update(feat)
    return pd.DataFrame([row])


def prepare_ratios(ingredients_by_name: Dict[str, float]) -> Dict[str, float]:
    """Возвращает агрегированные доли по группам corn/soybean/alfalfa/other."""
    return aggregate_ratios(ingredients_by_name)

