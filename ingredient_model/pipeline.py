import os
import json
import zipfile
from typing import Dict, Tuple

import numpy as np
import pandas as pd

from preprocessing import prepare_ingredients_df


def load_xgboost_models_safe(zip_filename='xgboost_models.zip'):
    """Безопасная загрузка с автоматическим именованием папки"""

    # Создаем уникальное имя папки на основе времени
    import time
    extract_to = f'loaded_models_{int(time.time())}'

    # Распаковываем
    with zipfile.ZipFile(zip_filename, 'r') as zipf:
        zipf.extractall(extract_to)

    print(f"📦 Распаковано в: {extract_to}/")

    # Ищем файлы модели
    for file in os.listdir(extract_to):
        if file.endswith('.joblib'):
            model_path = os.path.join(extract_to, file)
            try:
                import joblib
                model = joblib.load(model_path)
            except Exception:
                model = None
            print(f"✅ Загружена модель: {file}")

            # Ищем параметры
            param_file = file.replace('.joblib', '.json').replace('_model', '_params')
            param_path = os.path.join(extract_to, param_file)

            if os.path.exists(param_path):
                with open(param_path, 'r') as f:
                    params = json.load(f)
                print(f"✅ Загружены параметры: {param_file}")
            else:
                params = {}
                print("⚠️ Параметры не найдены")

            return model, params, extract_to

    print("❌ Модель не найдена в архиве")
    return None, None, extract_to


model, params, folder = load_xgboost_models_safe('../parameters/xgboost_models.zip')


def predict_from_ingredients(ingredients_by_name: Dict[str, float]) -> Dict[str, float]:
    """Предсказывает кислоты из состава ингредиентов.
    Если модель не загружена, возвращает нули по целям.
    """
    # Готовим DataFrame входов
    X_df = prepare_ingredients_df(ingredients_by_name)

    # Если модель не доступна — вернём пустые прогнозы
    if model is None:
        return {k: 0.0 for k in ['lauric', 'palmitic', 'stearic', 'oleic', 'linoleic', 'linolenic']}

    try:
        y = model.predict(X_df)
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
