"""
Константы для приложения
"""

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

# Ингредиенты рациона
INGREDIENTS = [
    ('forage', 'Фураж'),
    ('flax_meal', 'Жмых льняной'),
    ('yeast', 'Дрожжи'),
    ('dry_grains', 'Дробина сухая'),
    ('concentrates', 'Концентраты'),
    ('premix_milk', 'Премикс дойный'),
    ('chalk', 'Мел'),
    ('salt', 'Соль'),
    ('potash', 'Поташ')
]

# Словарь ингредиентов (ключ -> название)
INGREDIENT_NAMES = {key: name for key, name in INGREDIENTS}

