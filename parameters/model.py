import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import random

class MilkFattyAcidPredictor:
    """
    Заглушка модели для предсказания жирнокислотного состава молока на основе параметров рациона.
    Это заглушка, которая будет заменена на настоящую ML модель позже.
    """
    
    def __init__(self):
        self.model_name = "Модель предсказания жирных кислот v1.0"
        self.is_trained = False
        
        # Базовые коэффициенты для разных компонентов рациона
        self.base_coefficients = {
            'corn': {
                'lauric': 0.02,
                'palmitic': 0.15,
                'stearic': 0.05,
                'oleic': 0.20,
                'linoleic': 0.03,
                'linolenic': 0.01
            },
            'soybean': {
                'lauric': 0.01,
                'palmitic': 0.12,
                'stearic': 0.04,
                'oleic': 0.25,
                'linoleic': 0.08,
                'linolenic': 0.02
            },
            'alfalfa': {
                'lauric': 0.03,
                'palmitic': 0.18,
                'stearic': 0.08,
                'oleic': 0.15,
                'linoleic': 0.02,
                'linolenic': 0.01
            },
            'other': {
                'lauric': 0.02,
                'palmitic': 0.16,
                'stearic': 0.06,
                'oleic': 0.18,
                'linoleic': 0.04,
                'linolenic': 0.01
            }
        }
    
    def predict_fatty_acids(self, diet_ratios: Dict[str, float]) -> Dict[str, float]:
        """
        Предсказание жирнокислотного состава на основе соотношений рациона
        
        Args:
            diet_ratios: Словарь с соотношениями компонентов рациона (кукуруза, соя, люцерна, прочее)
            
        Returns:
            Словарь с предсказанными процентами жирных кислот
        """
        # Убедиться, что соотношения суммируются до 100%
        total_ratio = sum(diet_ratios.values())
        if total_ratio > 0:
            normalized_ratios = {k: v/total_ratio * 100 for k, v in diet_ratios.items()}
        else:
            normalized_ratios = diet_ratios
        
        predictions = {}
        
        # Calculate weighted average of base coefficients
        for acid in ['lauric', 'palmitic', 'stearic', 'oleic', 'linoleic', 'linolenic']:
            weighted_sum = 0.0
            total_weight = 0.0
            
            for component, ratio in normalized_ratios.items():
                if component in self.base_coefficients:
                    weight = ratio / 100.0
                    weighted_sum += self.base_coefficients[component][acid] * weight
                    total_weight += weight
            
            if total_weight > 0:
                base_prediction = weighted_sum / total_weight
            else:
                base_prediction = 0.0
            
            # Добавить некоторую реалистичную вариацию и ограничения
            variation = np.random.normal(0, 0.02)  # 2% стандартное отклонение
            prediction = base_prediction + variation
            
            # Применить реалистичные границы
            prediction = max(0.1, min(50.0, prediction))
            
            predictions[acid] = round(prediction, 2)
        
        return predictions
    
    def predict_with_uncertainty(self, diet_ratios: Dict[str, float], 
                                num_samples: int = 100) -> Dict[str, Dict[str, float]]:
        """
        Предсказание жирных кислот с оценками неопределенности с использованием симуляции Монте-Карло
        
        Args:
            diet_ratios: Словарь с соотношениями компонентов рациона
            num_samples: Количество выборок Монте-Карло
            
        Returns:
            Словарь со средним, стд. отклонением, мин, макс для каждой жирной кислоты
        """
        predictions_list = []
        
        for _ in range(num_samples):
            pred = self.predict_fatty_acids(diet_ratios)
            predictions_list.append(pred)
        
        # Вычисление статистики
        results = {}
        for acid in ['lauric', 'palmitic', 'stearic', 'oleic', 'linoleic', 'linolenic']:
            values = [pred[acid] for pred in predictions_list]
            results[acid] = {
                'mean': np.mean(values),
                'std': np.std(values),
                'min': np.min(values),
                'max': np.max(values),
                'median': np.median(values)
            }
        
        return results
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Возвращает оценки важности признаков (заглушка)
        """
        return {
            'corn_ratio': 0.35,
            'soybean_ratio': 0.30,
            'alfalfa_ratio': 0.25,
            'other_ratio': 0.10
        }
    
    def validate_input(self, diet_ratios: Dict[str, float]) -> Tuple[bool, str]:
        """
        Валидация входных соотношений рациона
        """
        if not diet_ratios:
            return False, "Не предоставлены соотношения рациона"
        
        required_components = ['corn', 'soybean', 'alfalfa', 'other']
        missing_components = [comp for comp in required_components if comp not in diet_ratios]
        
        if missing_components:
            return False, f"Отсутствуют компоненты рациона: {', '.join(missing_components)}"
        
        # Проверка на отрицательные значения
        negative_components = [comp for comp, ratio in diet_ratios.items() if ratio < 0]
        if negative_components:
            return False, f"Отрицательные соотношения не допускаются: {', '.join(negative_components)}"
        
        # Проверка, что соотношения суммируются примерно до 100%
        total = sum(diet_ratios.values())
        if abs(total - 100.0) > 10.0:
            return False, f"Соотношения рациона суммируются до {total:.1f}%, должны быть близки к 100%"
        
        return True, "Валидация входных данных прошла успешно"
    
    def get_model_info(self) -> Dict[str, any]:
        """
        Возвращает информацию о модели
        """
        return {
            'name': self.model_name,
            'version': '1.0.0',
            'type': 'Заглушка модели (Placeholder)',
            'description': 'Простая модель на основе правил для предсказания жирных кислот',
            'features': ['corn_ratio', 'soybean_ratio', 'alfalfa_ratio', 'other_ratio'],
            'targets': ['lauric', 'palmitic', 'stearic', 'oleic', 'linoleic', 'linolenic'],
            'is_trained': self.is_trained,
            'created_date': '2024-01-01'
        }

def create_sample_data() -> Dict[str, any]:
    """
    Создание тестовых данных для тестирования и демонстрации
    """
    sample_diets = [
        {
            'name': 'Высококукурузный рацион',
            'corn_ratio': 60.0,
            'soybean_ratio': 20.0,
            'alfalfa_ratio': 15.0,
            'other_ratio': 5.0
        },
        {
            'name': 'Сбалансированный рацион',
            'corn_ratio': 40.0,
            'soybean_ratio': 25.0,
            'alfalfa_ratio': 25.0,
            'other_ratio': 10.0
        },
        {
            'name': 'Высококормовой рацион',
            'corn_ratio': 30.0,
            'soybean_ratio': 15.0,
            'alfalfa_ratio': 40.0,
            'other_ratio': 15.0
        }
    ]
    
    sample_analyses = [
        {
            'lauric': 3.2,
            'palmitic': 28.5,
            'stearic': 12.1,
            'oleic': 24.8,
            'linoleic': 3.8,
            'linolenic': 1.2
        },
        {
            'lauric': 2.8,
            'palmitic': 31.2,
            'stearic': 10.5,
            'oleic': 26.3,
            'linoleic': 4.1,
            'linolenic': 1.1
        }
    ]
    
    return {
        'diets': sample_diets,
        'analyses': sample_analyses
    }
