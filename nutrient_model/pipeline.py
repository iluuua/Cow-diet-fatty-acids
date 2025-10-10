import pandas as pd
import joblib


def load_model(path="parameters/nutrients-_acids_01617_140.pkl"):
    return joblib.load(path)


def run_predictions(data, model):
    X_pred = ['Value_3', 'Value_5', 'Value_7', 'Value_12', 'Value_14', 'Value_17',
          'Value_18', 'Value_22', 'Value_24', 'Value_29', 'Value_33', 'Value_37',
          'Value_39', 'Value_40', 'Value_43', 'Value_45', 'Value_50', 'Value_57']
    df = data.copy()
    df = df.applymap(lambda x: str(x).replace(',', '.') if pd.notnull(x) else x)
    df = df.apply(pd.to_numeric, errors='coerce')
    df = df.fillna(0)
    df = df.drop([col for col in df.columns if col not in X_pred], axis=1)
    print("___" * 30)
    print(df, len(df))
    print("___" * 30)
    y_pred = model.predict(df)
    return y_pred
