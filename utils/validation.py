# validation.py
from typing import Dict, Tuple


def validate_diet_ratios(ratios: Dict[str, float]) -> Tuple[bool, str]:
    total = sum(ratios.values())
    if abs(total - 100.0) > 5.0:
        return False, f"Соотношения рациона суммируются до {total:.1f}%, должны быть близки к 100%"
    if any(ratio < 0 for ratio in ratios.values()):
        return False, "Все соотношения должны быть положительными"
    return True, "Соотношения рациона корректны"


def get_target_ranges() -> Dict[str, Tuple[float, float]]:
    return {
        'lauric': (2.0, 4.0),
        'palmitic': (25.0, 35.0),
        'stearic': (8.0, 15.0),
        'oleic': (20.0, 30.0),
        'linoleic': (2.0, 5.0),
        'linolenic': (0.5, 2.0)
    }


def check_fatty_acid_ranges(values: Dict[str, float]) -> Dict[str, Dict[str, any]]:
    target_ranges = get_target_ranges()
    results = {}
    for acid, value in values.items():
        if acid in target_ranges:
            min_val, max_val = target_ranges[acid]
            is_in_range = min_val <= value <= max_val
            results[acid] = {
                'value': value,
                'min_target': min_val,
                'max_target': max_val,
                'in_range': is_in_range,
                'status': 'good' if is_in_range else 'warning'
            }
        else:
            results[acid] = {
                'value': value,
                'in_range': True,
                'status': 'info'
            }
    return results