"""
Константы для приложения
"""

# Нормы кислот по ГОСТу
GOST = [
    (2.4, 4.2),
    (1.5, 3.),
    (1., 2.),
    (2., 3.8),
    (0.2, 0.4),
    (2., 4.4),
    (8., 13.),
    (0.6, 1.5),
    (21., 32.),
    (1.3, 2.4),
    (8., 13.5),
    (20., 28.),
    (2.2, 5.),
    (0, 1.5),
    (0, 0.3),
    (0, 0.1)
]


# Полный список жирных кислот
FATTY_ACIDS = [
    ('butyric', 'Масляная'),
    ('caproic', 'Капроновая'),
    ('caprylic', 'Каприловая'),
    ('capric', 'Каприновая'),
    ('decenoic', 'Деценовая'),
    ('lauric', 'Лауриновая'),
    ('myristic', 'Миристиновая'),
    ('myristoleic', 'Миристолеиновая'),
    ('palmitic', 'Пальмитиновая'),
    ('palmitoleic', 'Пальмитолеиновая'),
    ('stearic', 'Стеариновая'),
    ('oleic', 'Олеиновая'),
    ('linoleic', 'Линолевая'),
    ('linolenic', 'Линоленовая'),
    ('arachidic', 'Арахиновая'),
    ('behenic', 'Бегеновая')
]

# Словарь жирных кислот (ключ -> название)
FATTY_ACID_NAMES = {key: name for key, name in FATTY_ACIDS}

# Читаемые лейблы для UI (ингредиенты и нутриенты)
try:
    # Ингредиенты: код -> человекочитаемое название из filtration.feed_types
    from preprocessing.filtration import feed_types as _feed_types, NUTRIENT_FEATURES as _NUTRIENT_FEATURES
    ingredient_names = dict(_feed_types)

    # Нутриенты: соответствие Value_i -> человекочитаемое название
    _NUTRIENT_LABELS = {
        'Value_0': 'ЧЭЛ 3x NRC',
        'Value_2': 'СП',
        'Value_3': 'Крахмал',
        'Value_4': 'RD Крахмал 3x Уровень 1',
        'Value_5': 'Сахар',
        'Value_6': 'НСУ',
        'Value_8': 'НВУ',
        'Value_9': 'aNDFom',
        'Value_10': 'CHO B3 pdNDF',
        'Value_11': 'Растворимая клетчатка',
        'Value_13': 'aNDFom фуража',
        'Value_15': 'peNDF',
        'Value_16': 'CHO B3 медленная фракция',
        'Value_17': 'CHO C uNDF',
    }
    nutrient_names = {k: _NUTRIENT_LABELS.get(k, k) for k in _NUTRIENT_FEATURES}
except Exception:
    # Fallback, если импорт недоступен
    ingredient_names = {}
    nutrient_names = {}
