import joblib
import pandas as pd
from typing import Dict, Tuple


class MilkFattyAcidPredictor:
    """
    Обёртка для настоящей ML модели MultiOutputRegressor XGBoost.
    """

    def __init__(self, model_path="best_models.pkl"):
        self.model_path = model_path
        self.model = None
        self.model_params = None
        self.load_model()

    def load_model(self):
        """Загрузка сохранённой модели через joblib"""
        import os
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Модель не найдена: {self.model_path}")
        
        best_models = joblib.load(self.model_path)
        self.model, self.model_params = best_models['XGBoost']

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
        """Предсказание жирных кислот с помощью модели"""
        df = pd.DataFrame([diet_ratios])
        pred_array = self.model.predict(df)[0]
        
        fatty_acids = ['lauric_acid', 'palmitic_acid', 'stearic_acid',
                       'oleic_acid', 'linoleic_acid', 'linolenic_acid']
        predictions = dict(zip(fatty_acids, pred_array))
        return predictions
