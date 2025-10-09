from pathlib import Path
from typing import Dict, List

import numpy as np
import os

from preprocessing import prepare_ingredients_df

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


def _find_ingredient_model_files() -> List[Path]:
    ordered: List[Path] = []
    names_first = [
        'best_models.pkl',
        'best_model.pkl',
        'best_models.joblib',
        'best_model.joblib',
    ]
    for name in names_first:
        p = PARAMETERS_DIR / name
        if p.exists():
            ordered.append(p)
    # Добавляем остальные по маскам (исключая уже добавленные)
    patterns = ['best_model*.pkl', 'best_model*.joblib', 'best_models*.pkl', 'best_models*.joblib']
    extras: List[Path] = []
    for pattern in patterns:
        extras.extend(PARAMETERS_DIR.glob(pattern))
    seen = {p.resolve() for p in ordered}
    extras = [p for p in extras if p.resolve() not in seen]
    extras.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return ordered + extras


def _load_ingredient_model():
    if joblib is None:
        return None
    candidates = _find_ingredient_model_files()
    if not candidates:
        return None
    for model_path in candidates:
        try:
            obj = joblib.load(str(model_path))
            # Возможные структуры: dict с ключом 'XGBoost' или 'model', либо сама модель
            if isinstance(obj, dict):
                if 'XGBoost' in obj:
                    x = obj['XGBoost']
                    return x[0] if isinstance(x, (list, tuple)) and len(x) > 0 else x
                if 'model' in obj:
                    return obj['model']
            return obj
        except Exception:
            continue
    return None


INGR_MODEL = _load_ingredient_model()


def predict_from_ingredients(ingredients_by_name: Dict[str, float]) -> Dict[str, float]:
    """Предсказывает кислоты из состава ингредиентов.
    Если модель не загружена, возвращает нули по целям.
    """
    global INGR_MODEL
    # Готовим DataFrame входов
    X_df = prepare_ingredients_df(ingredients_by_name)
    # Попробуем подогнать порядок и состав фич под модель
    def _align_features(df, model):
        try:
            names = getattr(model, 'feature_names_in_', None)
            if names is None and hasattr(model, 'estimator_'):
                names = getattr(model.estimator_, 'feature_names_in_', None)
            if names is None and hasattr(model, 'regressor_'):
                names = getattr(model.regressor_, 'feature_names_in_', None)
            if names is None:
                # XGBoost sklearn API может хранить имена в booster
                get_booster = getattr(model, 'get_booster', None)
                if callable(get_booster):
                    booster = get_booster()
                    if hasattr(booster, 'feature_names') and booster.feature_names:
                        names = booster.feature_names
            if names is not None:
                names = list(names)
                overlap = len(set(names) & set(df.columns))
                # Выравниваем только если есть заметное пересечение имён
                if overlap >= max(1, int(0.33 * len(names))):
                    for col in names:
                        if col not in df.columns:
                            df[col] = 0.0
                    df = df[names]
        except Exception:
            pass
        return df

    # Если модель не загружена — пробуем подгрузить лениво
    if INGR_MODEL is None:
        INGR_MODEL = _load_ingredient_model()
        if INGR_MODEL is None:
            return {k: 0.0 for k in ['lauric', 'palmitic', 'stearic', 'oleic', 'linoleic', 'linolenic']}

    X_df = _align_features(X_df, INGR_MODEL)

    try:
        y = INGR_MODEL.predict(X_df)
        # Поддержка как для скаляра, так и для массива из 6 таргетов
        if isinstance(y, (list, tuple, np.ndarray)) and len(np.atleast_1d(y)) >= 6:
            arr = np.atleast_2d(y)
            vals = arr[0][:6]
        else:
            vals = [float(y)] * 6
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
