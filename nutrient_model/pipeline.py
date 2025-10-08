import pandas
import torch


def load_model(path="../parameters/nutrients-_acids_03941_400_MLP.pkl"):
    return joblib.load(path)


def run_predictions(data: pandas.DataFrame, model, scaler_X, scaler_y) -> torch.Tensor:
    params_removed_possible_multicollin_columns = ['Value_0', 'Value_2', 'Value_3', 'Value_4',
                                                   'Value_5', 'Value_6', 'Value_8', 'Value_9', 'Value_10',
                                                   'Value_11', 'Value_13', 'Value_15', 'Value_16',
                                                   'Value_17']
    X = data[params_removed_possible_multicollin_columns]
    X = scaler_X.transform(X)
    X_tensor = torch.tensor(X, dtype=torch.float32).to(device)
    model.eval()
    with torch.no_grad():
        y_pred_scaled = model(X_tensor).cpu().numpy()
    y_pred = scaler_y.inverse_transform(y_pred_scaled)
    return torch.tensor(y_pred, dtype=torch.float32)