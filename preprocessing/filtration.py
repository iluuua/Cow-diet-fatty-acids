import re

# Справочник (может дополняться)
acid_cols = [
    'Масляная', 'Капроновая', 'Каприловая', 'Каприновая', 'Деценовая',
    'Лауриновая', 'Миристиновая', 'Миристолеиновая', 'Пальмитиновая',
    'Пальмитолеиновая', 'Стеариновая', 'Олеиновая', 'Линолевая',
    'Линоленовая', 'Арахиновая', 'Бегеновая'
]

ingredient_names = [
    'Кукуруза плющеная',
    'Однолетние травы сенаж',
    "Шрот соевый",
    "Жир защищенный",
    "Ячмень сухой",
    "Люцерна сенаж",
    "Суданка сенаж",
    "Жом свекловичный",
    "Комбикорм",
    "Кукуруза корнаж",
    "Фураж",
    "Жмых льняной",
    "Пшеница",
    "Соевая оболочка",
    "Сенаж",
    "Премикс дойный",
    "Мел",
    "Л.Е.Д.ЖНАПКХ добавка",
    "Шрот подсолнечный",
    "Соль",
    "Клевер сенаж",
    "Поташ",
    "Кальций пропионат"
]

# Ожидаемые названия нутриентов в PDF (человеческие)
nutrient_cols = [  # первоначальные лейблы нутриентов
    'ЧЭЛ 3x NRC',
    'СП',
    'Крахмал',
    'RD Крахмал 3xУровень 1',
    'Сахар',
    'НСУ',
    'НВУ',
    'aNDFom',
    'CHO B3 pdNDF',
    'Растворимая клетчатка',
    'aNDFom фуража',
    'peNDF',
    'CHO B3 медленная фракция',
    'CHO C uNDF',
    'СЖ',
    'ОЖК',
    'K'
]

# Финальные фичи для подачи в модель (как описано в модуле)
NUTRIENT_FEATURES = [
    'Value_0', 'Value_2', 'Value_3', 'Value_4',
    'Value_5', 'Value_6', 'Value_8', 'Value_9', 'Value_10',
    'Value_11', 'Value_13', 'Value_15', 'Value_16', 'Value_17'
]

# Маппинг понятных имен нутриентов -> Value_i (в порядке, указанном выше)
NUTRIENT_TO_FEATURE = {
    'чэл 3x nrc': 'Value_0',
    'сп': 'Value_2',
    'крахмал': 'Value_3',
    'rd крахмал 3xуровень 1': 'Value_4',
    'сахар': 'Value_5',
    'нсу': 'Value_6',
    'нву': 'Value_8',
    'andfom': 'Value_9',
    'cho b3 pdndf': 'Value_10',
    'растворимая клетчатка': 'Value_11',
    'andfom фуража': 'Value_13',
    'pendf': 'Value_15',
    'cho b3 медленная фракция': 'Value_16',
    'cho c undf': 'Value_17',
}

# основной справочник feed_types — дополняйте как нужно
feed_types = {
    '01': '05.06 зерно(кукуруза) плющенное',
    '02': '12.01 тритикале сенаж',
    '03': '10.01 однолетние травы сенаж',
    '04': 'патока свекловичная',
    '05': 'шрот соевый',
    '06': '05.02 зерно(кукуруза) силос',
    '07': 'жир защищенный',
    '08': '**.04 солома',
    '09': 'ячмень сухой',
    '10': '08.01 сенаж',
    '11': '01.01 люцерна сенаж',
    '12': 'кукуруза сухая',
    '13': '06.01 суданка сенаж',
    '14': 'сено',
    '15': 'жом свекловичный',
    '16': '03.01 сенаж',
    '17': 'комбикорм',
    '18': '16.01 сенаж',
    '19': '05.07 зерно(кукуруза) корнаж',
    '20': 'шрот рапсовый',
    '21': 'фураж',
    '22': '05.** кукуруза влажная',
    '23': 'жмых льняной',
    '24': '06.02 суданка силос',
    '25': 'пшеница',
    '26': 'дрожжи',
    '27': 'соевая оболочка',
    '28': 'дробина сухая',
    '29': '04.01 сенаж',
    '30': 'жмых рапсовый',
    '31': 'премикс дойный',
    '32': 'сода',
    '33': 'мел',
    '34': '13.01 рожь сенаж',
    '35': 'лед жнапкх добавка',
    '36': '02.01 сенаж',
    '37': 'шрот подсолнечный',
    '38': '07.01 сенаж',
    '39': 'соль',
    '40': '18.01 зерносмесь сенаж',
    '41': '09.01 клевер сенаж',
    '42': '05.01 зерно(кукуруза) сенаж',
    '43': 'поташ',
    '44': 'концентраты',
    '45': 'кальций пропионат',
}

# Лейблы ингредиентов для UI: (код, название)
INGREDIENT_FEATURES = sorted(feed_types.items(), key=lambda kv: int(kv[0]))


def normalize(s: str) -> str:
    s = (s or '')
    s = str(s).lower()
    s = s.replace('\\', '/')
    s = re.sub(r'[^\S\r\n]+', ' ', s).strip()
    return s


def categorize_feed(feed_name: str):
    """
    Определяет (group, code, label) по имени ингредиента/ярлыку.
    """
    s = normalize(feed_name)
    if not s:
        return 'other', None, 'Не определено'

    # Ключевые слова -> коды
    keywords = {
        'патока': '04', 'меласса': '04',
        'шрот соев': '05', 'шрот рапсов': '20', 'шрот подсолнеч': '37',
        'жом свеклов': '15',
        'кукуруза': '12', 'плющ': '01', 'плющенное': '01',
        'корнаж': '19', 'силос': '06', 'сенаж': '10',
        'ячмень': '09', 'люцерна': '11', 'клевер': '41',
        'сено': '14', 'солома': '08', 'комбикорм': '17', 'кк': '17',
        'мел': '33', 'соль': '39', 'жир защищ': '07',
        'премикс': '31', 'поташ': '43', 'концентраты': '44',
        'жмых льнян': '23', 'жмых рапсов': '30', 'фураж': '21'
    }
    matched_code = None
    for k, code in keywords.items():
        if k in s:
            matched_code = code
            break

    # номер-префикс NN.NN внутри строки -> попытка сопоставить по feed_types
    if not matched_code:
        m = re.search(r'(\d{2}\.\d{2})', s)
        if m:
            pref = m.group(1)
            for code, label in feed_types.items():
                if pref in label:
                    matched_code = code
                    break

    label = feed_types.get(matched_code, 'Не определено') if matched_code else 'Не определено'

    # Группировка для модельных 4-х компонент
    group = 'other'
    norm_label = normalize(label)
    if 'кукуруз' in s or 'кукуруз' in norm_label:
        group = 'corn'
    elif 'соев' in s or 'соев' in norm_label:
        group = 'soybean'
    elif 'люцерн' in s or 'люцерн' in norm_label:
        group = 'alfalfa'

    return group, matched_code, label


def map_ingredients_to_codes(ingredients_by_name):
    """Агрегирует проценты по кодам feed_types из произвольных имен ингредиентов."""
    result = {code: 0.0 for code in feed_types.keys()}
    for name, percent in (ingredients_by_name or {}).items():
        group, code, _label = categorize_feed(name)
        if code:
            result[code] = result.get(code, 0.0) + float(percent or 0.0)
    # удаляем пустые
    return {code: v for code, v in result.items() if v > 0}


def aggregate_ratios(ingredients_by_name):
    """Суммирует проценты в 4 группы (corn/soybean/alfalfa/other) по исходным именам."""
    ratios = {'corn': 0.0, 'soybean': 0.0, 'alfalfa': 0.0, 'other': 0.0}
    for name, percent in (ingredients_by_name or {}).items():
        group, _code, _label = categorize_feed(name)
        ratios[group] += float(percent or 0.0)
    return ratios


def aggregate_ratios_from_codes(ingredients_by_code):
    """Суммирует проценты в 4 группы по кодам feed_types."""
    ratios = {'corn': 0.0, 'soybean': 0.0, 'alfalfa': 0.0, 'other': 0.0}
    for code, percent in (ingredients_by_code or {}).items():
        label = feed_types.get(code)
        if not label:
            ratios['other'] += float(percent or 0.0)
            continue
        group, _resolved_code, _label = categorize_feed(label)
        ratios[group] += float(percent or 0.0)
    return ratios


def map_nutrients_to_features(nutrients_by_name):
    """Маппит нутриенты из PDF к финальным Value_i фичам.
    Неизвестные — игнорируются.
    """
    features = {}
    for name, value in (nutrients_by_name or {}).items():
        key = normalize(name)
        # точное совпадение по словарю
        if key in NUTRIENT_TO_FEATURE:
            features[NUTRIENT_TO_FEATURE[key]] = float(value)
            continue
        # частичное совпадение по подстроке
        for pat, feat in NUTRIENT_TO_FEATURE.items():
            if pat in key:
                features[feat] = float(value)
                break
    return features
