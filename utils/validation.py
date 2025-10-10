# validation.py
from typing import Dict, Tuple
from .constants import GOST

def validate_diet_ratios(ratios: Dict[str, float]) -> Tuple[bool, str]:
    # Разрешаем любую сумму процентов; проверяем только на неотрицательность
    if any(ratio < 0 for ratio in ratios.values()):
        return False, "Все соотношения должны быть положительными"
    return True, "Соотношения рациона корректны"


def check_fatty_acid_ranges(values):
    res = []

    for i in range(len(GOST)):
        if values[i] < GOST[i][0]:
            res.append(f'Ниже на {round(GOST[i][0] - values[i], 2)}')
        elif GOST[i][0] <= values[i] <= GOST[i][1]:
            res.append(f'В пределах нормы')
        else:
            res.append(f'Выше на {round(values[i] - GOST[i][1], 2)}')

    return res
