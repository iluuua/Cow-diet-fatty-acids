import os
import zipfile


def load_xgboost_models_safe(zip_filename='xgboost_models.zip'):
    """Безопасная загрузка с автоматическим именованием папки"""

    # Создаем уникальное имя папки на основе времени
    import time
    extract_to = f'loaded_models_{int(time.time())}'

    # Распаковываем
    with zipfile.ZipFile(zip_filename, 'r') as zipf:
        zipf.extractall(extract_to)

    print(f"📦 Распаковано в: {extract_to}/")

    # Ищем файлы модели
    for file in os.listdir(extract_to):
        if file.endswith('.joblib'):
            model_path = os.path.join(extract_to, file)
            model = joblib.load(model_path)
            print(f"✅ Загружена модель: {file}")

            # Ищем параметры
            param_file = file.replace('.joblib', '.json').replace('_model', '_params')
            param_path = os.path.join(extract_to, param_file)

            if os.path.exists(param_path):
                with open(param_path, 'r') as f:
                    params = json.load(f)
                print(f"✅ Загружены параметры: {param_file}")
            else:
                params = {}
                print("⚠️ Параметры не найдены")

            return model, params, extract_to

    print("❌ Модель не найдена в архиве")
    return None, None, extract_to


model, params, folder = load_xgboost_models_safe('../parameters/xgboost_models.zip')
