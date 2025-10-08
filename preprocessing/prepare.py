import pandas as pd
from typing import Dict

from preprocessing.filtration import (
    feed_types,
    map_ingredients_to_codes,
    aggregate_ratios,
    NUTRIENT_FEATURES,
    map_nutrients_to_features,
)


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

