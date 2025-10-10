from pathlib import Path
from typing import Dict, List
from sklearn.multioutput import MultiOutputRegressor
from xgboost import XGBRegressor
import joblib

# загружаем модель
model = joblib.load('parameters/ingredient_model.pkl')

import numpy as np
import os

from preprocessing import prepare_ingredients

try:
    import joblib
except Exception:
    joblib = None
try:
    import warnings
    from sklearn.exceptions import InconsistentVersionWarning

    warnings.filterwarnings("ignore", category=InconsistentVersionWarning)
except Exception:
    pass

PARAMETERS_DIR = Path(os.getenv('COW_FATTY_PARAMETERS_DIR') or (Path(__file__).resolve().parent.parent / 'parameters'))


def _load_ingredient_model():
    models = []
    for i in range(16):
        model = XGBRegressor()
        model.load_model(f"parameters/xgb_output_{i}.json")
        models.append(model)
    return models


INGR_MODEL = MultiOutputRegressor(XGBRegressor(n_estimators=100, random_state=42))
# Загружаем кортеж (модель, параметры)
INGR_MODEL = _load_ingredient_model()  # параметры


def align_features(X_df, model):
    train_features = model.get_booster().feature_names

    for f in train_features:
        if f not in X_df.columns:
            X_df[f] = 0

    X_df = X_df[train_features]
    return X_df


def predict_from_ingredients(ingredients_by_name):
    """Предсказывает кислоты из состава ингредиентов."""
    X_df = prepare_ingredients(ingredients_by_name)
    preds = []
    for model in INGR_MODEL:
        y_pred = model.predict(X_df.to_numpy())
        preds.append(y_pred)
    Y_pred = ['Масляная', 'Капроновая', 'Каприловая', 'Каприновая', 'Деценовая', 'Лауриновая', 'Миристиновая',
              'Миристолеиновая', 'Пальмитиновая', 'Пальмитолеиновая', 'Стеариновая', 'Олеиновая', 'Линолевая',
              'Линоленовая', 'Арахиновая', 'Бегеновая']
    # Объединяем в матрицу [n_samples, n_targets]
    Y_pred = np.column_stack(preds)

    return Y_pred
