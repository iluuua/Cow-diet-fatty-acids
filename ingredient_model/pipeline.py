from pathlib import Path
from typing import Dict, List

import numpy as np

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


PARAMETERS_DIR = Path(__file__).resolve().parent.parent / 'parameters'


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
        print(f"⚠️ Файл модели ингредиентов не найден в: {PARAMETERS_DIR}")
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
    print(f"❌ Не удалось загрузить ни один файл модели ингредиентов из: {PARAMETERS_DIR}")
    return None


INGR_MODEL = _load_ingredient_model()


def predict_from_ingredients(ingredients_by_name: Dict[str, float]) -> Dict[str, float]:
    """Предсказывает кислоты из состава ингредиентов.
    Если модель не загружена, возвращает нули по целям.
    """
    # Готовим DataFrame входов
    X_df = prepare_ingredients_df(ingredients_by_name)

    # Если модель не загружена — пробуем подгрузить лениво
    global INGR_MODEL
    if INGR_MODEL is None:
        INGR_MODEL = _load_ingredient_model()
        if INGR_MODEL is None:
            return {k: 0.0 for k in ['lauric', 'palmitic', 'stearic', 'oleic', 'linoleic', 'linolenic']}

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
