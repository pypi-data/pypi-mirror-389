import pandas as pd
from pathlib import Path

EXCEL_PATH = Path(r"\\WinFS\SIG\CL-6370\01 Gestion CT\Gestion CT\Feuille Prev\Outil_Optim_Hydro\Installation serveur\negoce-ct-hydraulic-optimization - GUROBI\data\Table Débits_Puissance_test.xlsx")

def get_expected_debit(df: pd.DataFrame) -> pd.DataFrame:
        df_select = df[[col for col in df.columns if str(col).startswith('Unnamed')]].copy()
        if len(df_select.columns) >= 3:
            df_select.rename(columns={df_select.columns[0]: 'Debit', df_select.columns[1]: 'Débits attendus Verbois', df_select.columns[2]: 'Débits attendus Chancy-Pougny'}, inplace=True)
        
        print(df_select.columns)
        return df_select


def get_data_from_excel() -> pd.DataFrame:
    """

    :param is_bissextile:
    :return:
    """

    df = pd.read_excel(EXCEL_PATH, skiprows=3)

    df = get_expected_debit(df)


    return df

if __name__ == "__main__":
    df = get_data_from_excel()
    print(df.head())