import numpy as np
import pandas as pd
from typing import Dict
from pathlib import Path

try:
    import joblib
except Exception:
    joblib = None

from preprocessing import prepare_nutrients_df
from preprocessing.filtration import NUTRIENT_FEATURES


def load_model_assets(path_prefix: str | None = None):
    if path_prefix is None:
        # файл модели лежит в папке parameters рядом с корнем проекта
        path_prefix = str((Path(__file__).resolve().parent.parent / 'parameters' / 'nutrients-_acids_03941_400_MLP.pkl'))
    if joblib is None:
        return None, None, None
    try:
        bundle = joblib.load(path_prefix)
        model = bundle.get('model') if isinstance(bundle, dict) else bundle
        scaler_X = bundle.get('scaler_X') if isinstance(bundle, dict) else None
        scaler_y = bundle.get('scaler_y') if isinstance(bundle, dict) else None
        return model, scaler_X, scaler_y
    except Exception:
        return None, None, None


model, scaler_X, scaler_y = load_model_assets()


def predict_from_nutrients(nutrients_by_name: Dict[str, float]) -> Dict[str, float]:
    """Предсказывает кислоты из набора нутриентов (Value_i фичи).
    Если модель или скейлеры не загружены — вернём нули.
    """
    X_df = prepare_nutrients_df(nutrients_by_name)
    X_df = X_df[[c for c in NUTRIENT_FEATURES if c in X_df.columns]]

    if model is None:
        return {k: 0.0 for k in ['lauric', 'palmitic', 'stearic', 'oleic', 'linoleic', 'linolenic']}

    try:
        X = X_df.values
        if scaler_X is not None:
            X = scaler_X.transform(X)
        y_pred = model.predict(X)
        if scaler_y is not None:
            y_pred = scaler_y.inverse_transform(np.atleast_2d(y_pred))
        arr = np.atleast_2d(y_pred)
        vals = arr[0]
        # Если модель возвращает больше выходов, берём первые 6
        if len(vals) < 6:
            vals = list(vals) + [0.0] * (6 - len(vals))
        return {
            'lauric': float(vals[0]),
            'palmitic': float(vals[1]),
            'stearic': float(vals[2]),
            'oleic': float(vals[3]),
            'linoleic': float(vals[4]),
            'linolenic': float(vals[5]),
        }
    except Exception:
        return {k: 0.0 for k in ['lauric', 'palmitic', 'stearic', 'oleic', 'linoleic', 'linolenic']}

