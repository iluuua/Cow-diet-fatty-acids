# utils.py
from typing import Dict

import pandas as pd
import numpy as np


def format_percentage(value: float, decimals: int = 1) -> str:
    return f"{value:.{decimals}f}%"


def create_summary_statistics(values: Dict[str, float]) -> Dict[str, any]:
    if not values:
        return {}
    numeric_values = [v for v in values.values() if isinstance(v, (int, float))]
    if not numeric_values:
        return {}
    return {
        'mean': np.mean(numeric_values),
        'std': np.std(numeric_values),
        'min': np.min(numeric_values),
        'max': np.max(numeric_values),
        'count': len(numeric_values)
    }