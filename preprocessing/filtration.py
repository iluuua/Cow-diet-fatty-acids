# filtration.py
import re
from collections import defaultdict
import csv
import pandas as pd

acid_cols = [
    'Масляная', 'Капроновая', 'Каприловая', 'Каприновая', 'Деценовая',
    'Лауриновая', 'Миристиновая', 'Миристолеиновая', 'Пальмитиновая',
    'Пальмитолеиновая', 'Стеариновая', 'Олеиновая', 'Линолевая',
    'Линоленовая', 'Арахиновая', 'Бегеновая'
]

nutrient_cols = [
    'ЧЭЛ 3x NRC',
    'СП',
    'Крахмал'
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
    'K',
]

ingredient_cols = [
    'Кукуруза плющеная', 'Тритикале сенаж',
    'Патока свекловичная', 'Шрот соевый',
    'Кукуруза силос', 'Жир защищенный',
    'Солома', 'Ячмень сухой', 'Кукуруза сухая',
    'Сено', 'Жом свекловичный', 'Комбикорм',
    'Кукуруза корнаж', 'Кукуруза влажная',
    'Пшеница', 'Соевая оболочка', 'Жмых рапсовый',
    'Сода', 'Л.Е.Д. ЖНАПКХ добавка', 'Кальций пропионат'
]

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
# === Построим обратную карту префиксов (на основе feed_types) ===
# Ищем в label префиксы вида 'DD.DD' (например '05.06') и мапим -> код
reverse_prefix_map = {}
for code, label in feed_types.items():
    m = re.search(r'(\d{2}\.\d{2})', label)
    if m:
        reverse_prefix_map[m.group(1)] = code
# Теперь reverse_prefix_map содержит ожидаемые префиксы, например {'05.06':'01', '05.02':'06', ...}

# === Маска, которую попросил пользователь (строго) ===
STRICT_MASK = re.compile(r'\d{4}\.\d{2}\.(\d{2})\.(\d{2})\.\d{1}\.\d{2}')


def normalize(s: str) -> str:
    s = s or ''
    s = s.lower()
    s = s.replace('\\', '/')
    s = re.sub(r'[^\S\r\n]+', ' ', s).strip()  # normalize whitespace
    return s


def extract_prefix_by_strict_mask(s: str):
    r"""
    Используем строго заданную маску r'\d{4}\.\d{2}\.(\d{2})\.(\d{2})\.\d{1}\.\d{2}'
    Если находим — возвращаем префикс 'GG.HH' (group1.group2).
    """
    s = normalize(s)
    m = STRICT_MASK.search(s)
    if m:
        g1, g2 = m.group(1), m.group(2)
        return f"{g1}.{g2}"
    return None


def extract_any_pair_prefix(s: str):
    """
    Фолбэк: ищем любую пару 'NN.NN' в тексте (например '05.06' внутри '1603.01.05.06...' или в лейбле).
    """
    m = re.search(r'(\d{2}\.\d{2})', s)
    return m.group(1) if m else None


def is_combikorm_token(s: str):
    # распознаём 'кк', 'кк10', 'кк №10', 'комбиком', 'кормосмесь' и пр.
    if re.search(r'\bкк\b', s) or re.search(r'\bкк[\s№]*\d+',
                                            s) or 'комбиком' in s or 'кормосмесь' in s or 'комбикорм' in s:
        return True
    return False


def categorize_feed(feed_names_dict):
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
    dict_of_names = {}
    for i in feed_types.values():
        dict_of_names[i] = ''
    feed_names = feed_names_dict.keys()
    for feed_name in feed_names:
        s = normalize(feed_name)
        found = False

        # 1) Жёсткие (длинные/точные) фразы — сначала
        exact_map = [
            ('патока свекловичная', '04'),
            ('меласса', '04'),
            ('шрот соевый', '05'),
            ('жир защищ', '07'),
            ('жом свекловичный', '15'),
            ('шрот рапсовый', '20'),
            ('жмых рапсовый', '30'),
            ('жмых льняной', '23'),
            ('премикс дойный', '31'),
            ('поташ', '43'),
            ('концентраты', '44'),
            ('кальций пропионат', '45'),
            ('соевая оболочка', '27'),
            ('дробина сухая', '28'),
            ('шрот подсолнечный', '37'),
            ('зерносмесь', '40'),
            ('фураж', '21'),
            ('рожь', '34'),
            ('тритикале', '02'),
            ('однолетние травы', '03'),
            ('лед энапкх', '35'),
            ('лед', '35'),
            ('пшеница', '25'),
            ('дрожжи', '26'),
            ('мел', '33'),  # отдельное слово "мел" — мапим в мел (но ниже есть исключение для 'мелк.')
            ('соль', '39'),
            ('мелк.', '12'),
            ('сенаж 22.02.01.01.01.1.24', '11'),
            ('сено люцерна ЛБ 2025', '14'),
            ('кукуруза_плющ_9202.01.05.06', '01'),
            ('1603.02.15.04.1.24/301024', '08'),
            ('3645.02.01.01.02.24 /11.06.25', '11'),
            ('ккд10', '17'),
            ('премикс транзит б. 07.23', '31'),
            ('Сода. ЭНАПКХ', '32'),
            ('к-ж5701.05.07.1.23 Бушовка', '19')
        ]
        for key, code in exact_map:
            key = normalize(key)
            if key in s:
                # Важное исключение: если это слово 'мел' встречается внутри 'мелк.' — мы не должны брать его как 'мел'
                if key == 'мел' and re.search(r'\bмелк.', s):
                    # пропускаем — будет обработано специальным правилом ниже
                    pass
                else:
                    dict_of_names[feed_types[code]] = feed_name
                    found = True
                    break
                    continue

        # 1.5) Комбикорм и его вариации
        if is_combikorm_token(s):
            dict_of_names[feed_types['17']] = feed_name
            found = True
            continue

        # 2) Попытка распознать по строгой маске, которую ты дал
        pref = extract_prefix_by_strict_mask(s)
        if pref and pref in reverse_prefix_map:
            dict_of_names[feed_types[reverse_prefix_map[pref]]] = feed_name
            found = True
            continue

        # 3) Фолбэк — любая пара NN.NN в тексте (например 05.06)
        pref_any = extract_any_pair_prefix(s)
        if pref_any and pref_any in reverse_prefix_map:
            dict_of_names[feed_types[reverse_prefix_map[pref_any]]] = feed_name
            found = True
            continue

        # 4) Специальные правила для "мел" и "кукуруза" (основная причина ошибок)
        # 4.1 Если 'мелк.' / 'мелкий' встречается и есть 'кукуруза' -> трактуем как мел (33)
        if re.search(r'\bмелк(?:\.|ий|\b)', s) and 'кукуруза' in s:
            dict_of_names[feed_types['12']] = feed_name
            found = True
            continue

        # 4.2 Если слово 'мел' отдельно (не 'мелк.') — уже обработано выше.
        # Но если всё же 'мел' где-то — вернуть '33'
        if re.search(r'\bмел\b', s):
            dict_of_names[feed_types['33']] = feed_name
            found = True
            continue

        # 4.3 Кукуруза — разберём по контексту (приоритеты внутри кукурузы):
        if 'кукуруза' in s:
            # плющенное (плющ, плющенное, 'плющ зерно', 'плющена')
            if 'плющ' in s or 'плющенное' in s or 'плющена' in s or 'плющ зерно' in s:
                dict_of_names[feed_types['01']] = feed_name
                found = True
                continue
            # влажная
            if 'влаж' in s or 'вл.' in s:
                dict_of_names[feed_types['22']] = feed_name
                found = True
                continue
            # корнаж / к-ж
            if 'корнаж' in s or re.search(r'\bк-?ж\b', s) or 'к-ж' in s:
                dict_of_names[feed_types['19']] = feed_name
                found = True
                continue
            # силос (включая сокращения 'с-', 'с-с')
            if 'силос' in s or re.search(r'\bс-([ )]|$)', s) or 'с-с' in s:
                dict_of_names[feed_types['06']] = feed_name
                found = True
                continue
            # сенаж (с-ж, сенаж)
            if 'сенаж' in s or 'с-ж' in s or re.search(r'\bсж\b', s):
                dict_of_names[feed_types['42']] = feed_name
                found = True
                continue
            # мелк. (обработано выше) — на всякий случай:
            if re.search(r'\bмелк', s):
                dict_of_names[feed_types['12']] = feed_name
                found = True
                continue
            # явное указание "сух" или "сухая" -> кукуруза сухая
            if 'сух' in s or 'сухая' in s:
                dict_of_names[feed_types['12']] = feed_name
                found = True
                continue
            # default для 'кукуруза' -> считаем сухой (12)
            dict_of_names[feed_types['12']] = feed_name
            found = True
            continue

        # 5) Другие общие культуры/контексты (если не кукуруза и не попало выше)
        if 'ячмень' in s:
            dict_of_names[feed_types['09']] = feed_name
            found = True
            continue
        if 'люцерна' in s:
            dict_of_names[feed_types['11']] = feed_name
            found = True
            continue
        if 'клевер' in s:
            dict_of_names[feed_types['41']] = feed_name
            found = True
            continue
        if 'суданка' in s:
            # если упомянуто 'силос' — силос версия иначе сенаж
            if 'силос' in s or re.search(r'\bс-\b', s):
                dict_of_names[feed_types['24']] = feed_name
                found = True
                continue
            dict_of_names[feed_types['13']] = feed_name
            found = True
            continue
        if 'солома' in s:
            dict_of_names[feed_types['08']] = feed_name
            found = True
            continue
        if 'сено' in s:
            dict_of_names[feed_types['14']] = feed_name
            found = True
            continue
        if 'фураж' in s:
            dict_of_names[feed_types['21']] = feed_name
            found = True
            continue
        if 'жир защищ' in s:
            dict_of_names[feed_types['07']] = feed_name
            found = True
            continue

        # 6) Если встречается 'силос' без кукурузы — отнесём к 06 (зерно силос) как общий вариант
        if 'силос' in s:
            dict_of_names[feed_types['06']] = feed_name
            found = True
            continue
        if 'сенаж' in s:
            dict_of_names[feed_types['10']] = feed_name
            found = True
            continue

        # 7) Ничего не найдено
        if found:
            continue
        else:
            dict_of_names['None'] = feed_name
            continue

    new_dict = {}
    for x in dict_of_names.keys():
        if dict_of_names[x]:
            new_dict[x] = feed_names_dict[dict_of_names[x]]
        else:
            new_dict[x] = 0

    ingredients_df = pd.DataFrame({k: [v] for k, v in new_dict.items()})
    return ingredients_df
