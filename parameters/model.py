import joblib
import pandas as pd
from typing import Dict, Tuple
from pathlib import Path
import os


class MilkFattyAcidPredictor:
    """
    Обёртка для настоящей ML модели MultiOutputRegressor XGBoost.
    """

    def __init__(self, model_path="best_models.pkl"):
        # Разрешение пути к весам с учётом ENV и локальной папки parameters
        if model_path == "best_models.pkl":
            env_dir = os.getenv("COW_FATTY_PARAMETERS_DIR")
            if env_dir:
                env_candidate = Path(env_dir) / model_path
                if env_candidate.exists():
                    model_path = str(env_candidate)
                else:
                    base_dir = Path(__file__).resolve().parent  # .../parameters
                    model_path = str(base_dir / model_path)
            else:
                base_dir = Path(__file__).resolve().parent  # .../parameters
                model_path = str(base_dir / model_path)
        elif not Path(model_path).is_absolute():
            base_dir = Path(__file__).resolve().parent  # .../parameters
            model_path = str((base_dir / model_path))
        self.model_path = model_path
        self.model = None
        self.model_params = None
        self.load_model()

    def load_model(self):
        """Загрузка сохранённой модели через joblib"""
        if not os.path.exists(self.model_path):
            print(f"⚠️ Файл модели не найден: {self.model_path}")
            # мягкий фолбэк: инициализируем пустую модель, чтобы приложение продолжило работу
            self.model = DummyModel()
            self.model_params = {}
            return
        try:
            best_models = joblib.load(self.model_path)
            self.model, self.model_params = best_models['XGBoost']
        except Exception as e:
            print(f"❌ Ошибка загрузки модели: {e}")
            self.model = DummyModel()
            self.model_params = {}

    def validate_input(self, diet_ratios: Dict[str, float]) -> Tuple[bool, str]:
        """Простейшая валидация входных данных"""
        required_components = ['corn', 'soybean', 'alfalfa', 'other']
        missing = [k for k in required_components if k not in diet_ratios]
        if missing:
            return False, f"Отсутствуют компоненты: {', '.join(missing)}"
        if any(v < 0 for v in diet_ratios.values()):
            return False, "Все значения должны быть >= 0"
        if sum(diet_ratios.values()) > 100:
            return False, "Сумма ингредиентов не должна превышать 100%"
        return True, ""

    def predict_fatty_acids(self, diet_ratios: Dict[str, float]) -> Dict[str, float]:
        """Предсказание жирных кислот с помощью модели-обёртки"""
        df = pd.DataFrame([diet_ratios])
        pred_array = self.model.predict(df)[0]
        fatty_acids = ['lauric_acid', 'palmitic_acid', 'stearic_acid',
                       'oleic_acid', 'linoleic_acid', 'linolenic_acid']
        predictions = dict(zip(fatty_acids, pred_array))
        return predictions


class DummyModel:
    """Простейшая заглушка модели на случай отсутствия файла моделей."""
    def predict(self, df: pd.DataFrame):
        import numpy as np
        # возвращаем нули по шести таргетам, соответствующим порядку в app_desktop
        zeros = np.zeros((len(df), 6), dtype=float)
        return zeros
