import pandas as pd
from typing import Dict

from preprocessing.filtration import (
    feed_types,
    map_ingredients_to_codes,
    aggregate_ratios,
    NUTRIENT_FEATURES,
    map_nutrients_to_features,
)


def prepare_ingredients(data_x):
    new_data = data_x
    new_data.iloc[:, 1] = new_data.iloc[:, [1, 2, 9, 10, 12, 15, 17, 28, 33, 35, 37, 39, 40, 41]].sum(axis=1)
    cols_drop = new_data.columns[[2, 9, 10, 12, 15, 17, 28, 33, 35, 37, 39, 40, 41]]
    new_data_x = new_data.drop(cols_drop, axis=1)
    new_data = new_data_x
    new_data.iloc[:, 1] = new_data.iloc[:, [4, 17]].sum(axis=1)
    cols_drop = new_data.columns[17]
    new_data_x = new_data.drop(cols_drop, axis=1)
    cols_drop = new_data_x.columns[[13, 14, 16, 18, 19, 21, 23, 25, 27, 26, 28]]
    new_new_data_x = new_data_x.drop(cols_drop, axis=1)

    return new_new_data_x

