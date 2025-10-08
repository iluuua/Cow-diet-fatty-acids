import pandas as pd


def prepare_data(ration_df: pd.DataFrame) -> pd.DataFrame:
    """Prepares the ration DataFrame for model input by aggregating and dropping columns as specified."""
    data_x = ration_df.drop('pdf', axis=1)
    new_data = data_x.copy()
    new_data.iloc[:, 1] = new_data.iloc[:, [1, 2, 9, 10, 12, 15, 17, 28, 33, 35, 37, 39, 40, 41]].sum(axis=1)
    new_data_x = new_data.drop(new_data.columns[[2, 9, 10, 12, 15, 17, 28, 33, 35, 37, 39, 40, 41]], axis=1)
    new_data = new_data_x
    new_data.iloc[:, 1] = new_data.iloc[:, [4, 17]].sum(axis=1)
    new_data_x = new_data.drop(new_data.columns[17], axis=1)
    cc = ['фураж % СВ', 'жмых льняной % СВ', 'дрожжи % СВ', 'дробина сухая % СВ',
          'концентраты % СВ', 'премикс дойный % СВ', 'мел % СВ', 'соль % СВ', 'поташ % СВ']
    new_data_x = new_data_x.drop(cc, axis=1, errors='ignore')
    return new_data_x

