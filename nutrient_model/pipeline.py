import numpy as np
from typing import Dict, List
from pathlib import Path
import os

try:
    import joblib
except Exception:
    joblib = None
try:
    from skops.io import load as skops_load
except Exception:
    skops_load = None
try:
    import warnings
    from sklearn.exceptions import InconsistentVersionWarning
    warnings.filterwarnings("ignore", category=InconsistentVersionWarning)
except Exception:
    pass
try:
    import sklearn  # для логирования версии
except Exception:
    sklearn = None

from preprocessing import prepare_nutrients_df, NUTRIENT_FEATURES


PARAMETERS_DIR = Path(os.getenv('COW_FATTY_PARAMETERS_DIR') or (Path(__file__).resolve().parent.parent / 'parameters'))


def _find_nutrient_bundle_files() -> List[Path]:
    patterns = ['nutrients-_acids*.pkl', 'nutrients-_acids*.joblib', 'nutrients-_acids*.skops', 'nutrients*.skops']
    found: List[Path] = []
    for pattern in patterns:
        found.extend(PARAMETERS_DIR.glob(pattern))
    found.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    # Тихий режим: не печатаем в консоль
    return found


def _load_nutrient_assets():
    if joblib is None:
        return None, None, None
    for file_path in _find_nutrient_bundle_files():
        try:
            if file_path.suffix == '.skops':
                if skops_load is None:
                    continue
                bundle = skops_load(str(file_path), trusted=True)
            else:
                bundle = joblib.load(str(file_path))
            if isinstance(bundle, dict):
                model = bundle.get('model', None)
                scaler_X = bundle.get('scaler_X', None)
                scaler_y = bundle.get('scaler_y', None)
                return model, scaler_X, scaler_y
            return bundle, None, None
        except Exception as e:
            continue
    return None, None, None


N_MODEL, N_SCALER_X, N_SCALER_Y = _load_nutrient_assets()


def predict_from_nutrients(nutrients_by_name: Dict[str, float]) -> Dict[str, float]:
    """Предсказывает кислоты из набора нутриентов (Value_i фичи).
    Если модель или скейлеры не загружены — вернём нули.
    """
    X_df = prepare_nutrients_df(nutrients_by_name)
    # Выравнивание набора фич под модель, если она ожидает строгий порядок
    def _align_features(df, model):
        try:
            names = getattr(model, 'feature_names_in_', None)
            if names is None and hasattr(model, 'estimator_'):
                names = getattr(model.estimator_, 'feature_names_in_', None)
            if names is None and hasattr(model, 'regressor_'):
                names = getattr(model.regressor_, 'feature_names_in_', None)
            if names is not None:
                names = list(names)
                for col in names:
                    if col not in df.columns:
                        df[col] = 0.0
                df = df[names]
            else:
                df = df[[c for c in NUTRIENT_FEATURES if c in df.columns]]
        except Exception:
            df = df[[c for c in NUTRIENT_FEATURES if c in df.columns]]
        return df

    X_df = _align_features(X_df, N_MODEL)

    if N_MODEL is None:
        return {k: 0.0 for k in ['lauric', 'palmitic', 'stearic', 'oleic', 'linoleic', 'linolenic']}

    try:
        X = X_df.values
        if N_SCALER_X is not None:
            X = N_SCALER_X.transform(X)
        y_pred = N_MODEL.predict(X)
        if N_SCALER_Y is not None:
            y_pred = N_SCALER_Y.inverse_transform(np.atleast_2d(y_pred))
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

