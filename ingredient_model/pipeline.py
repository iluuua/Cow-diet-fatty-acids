from xgboost import XGBRegressor
import numpy as np

from preprocessing import prepare_ingredients


def _load_ingredient_model():
    models = []
    for i in range(16):
        model = XGBRegressor()
        model.load_model(f"parameters/xgb_output_{i}.json")
        models.append(model)
    return models


INGR_MODEL = _load_ingredient_model()


def predict_from_ingredients(ingredients_by_name):
    """Предсказывает кислоты из состава ингредиентов."""
    X_df = prepare_ingredients(ingredients_by_name)
    preds = []
    for model in INGR_MODEL:
        y_pred = model.predict(X_df.to_numpy())
        preds.append(y_pred)
    Y_pred = np.column_stack(preds)  # [n_samples, n_targets]
    return Y_pred
