# recommendations.py
from typing import Dict, List


def generate_recommendations(analysis_results: Dict[str, Dict[str, any]],
                             diet_ratios: Dict[str, float]) -> List[str]:
    recommendations = []
    acid_names = {
        'lauric': 'лауриновой',
        'palmitic': 'пальмитиновой',
        'stearic': 'стеариновой',
        'oleic': 'олеиновой',
        'linoleic': 'линолевой',
        'linolenic': 'линоленовой'
    }
    for acid, data in analysis_results.items():
        if not data['in_range']:
            value = data['value']
            min_target = data['min_target']
            max_target = data['max_target']
            acid_name = acid_names.get(acid, acid)
            if value < min_target:
                recommendations.append(f"Увеличьте содержание {acid_name} кислоты, изменив состав рациона")
            elif value > max_target:
                recommendations.append(f"Снизьте содержание {acid_name} кислоты, изменив состав рациона")
    if diet_ratios.get('corn', 0) > 50:
        recommendations.append("Рассмотрите снижение доли кукурузы - высокое содержание может повлиять на профиль жирных кислот")
    if diet_ratios.get('soybean', 0) > 30:
        recommendations.append("Обнаружено высокое содержание сои - следите за потенциальным влиянием на состав молока")
    if diet_ratios.get('alfalfa', 0) < 10:
        recommendations.append("Рассмотрите увеличение содержания люцерны для лучшего баланса кормов")
    return recommendations