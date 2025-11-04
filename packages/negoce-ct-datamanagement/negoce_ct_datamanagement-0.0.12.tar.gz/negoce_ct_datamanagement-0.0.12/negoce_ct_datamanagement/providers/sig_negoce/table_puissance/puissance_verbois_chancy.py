import pandas as pd
from pathlib import Path

EXCEL_PATH = Path(r"\\WinFS\SIG\CL-6370\01 Gestion CT\Gestion CT\Feuille Prev\Outil_Optim_Hydro\Installation serveur\negoce-ct-hydraulic-optimization - GUROBI\data\Table Débits_Puissance_test.xlsx")

def _melt_group_columns(df: pd.DataFrame) -> pd.DataFrame:
        # 2) Identify all the “group” columns (those ending in “(Ng)”)
        group_cols = [col for col in df.columns if col.endswith('g)')]

        # 3) Melt into long form
        df_long = df.melt(
            id_vars=['Debit'],   # keep this column as-is
            value_vars=group_cols,       # unpivot these columns
            var_name='temps',            # temporary holder for the header string
            value_name='Power'           # the numbers under each group
        )

        # 4) Extract the integer before “g”
        df_long['Groupe'] = (
            df_long['temps']
            .str.extract(r'\((\d+)g\)')   # pull the digits inside “(…)g”
            .astype(int)
        )

        # 5) Clean up & rename
        df_long = (
            df_long
            .drop(columns=['temps'])                # no longer needed
            [['Debit', 'Groupe', 'Power']]  # reorder
            .reset_index(drop=True)
        )
        return df_long

def select_columns_by_name(df: pd.DataFrame, col_name: str) -> pd.DataFrame:
        # Find columns starting with the given col_name
        target_cols = [col for col in df.columns if str(col).startswith(col_name)]

        # Always keep the first column 
        selected_cols = [df.columns[0]] + target_cols

        df_selected = df[selected_cols]
        
        # Rename columns for consistency
        rename_dict = {df.columns[0]: 'Debit'}
        if f'{col_name} 0' in df_selected.columns:
            rename_dict[f'{col_name} 0'] = f'{col_name} (0g)'

        df_selected = df_selected.rename(columns=rename_dict)
        # Reverse columns and reset index
        df_selected = df_selected[df_selected.columns[::-1]].reset_index(drop=True)
        return df_selected

def get_data_from_excel() -> pd.DataFrame:
    """

    :param data_info:
    :return:
    """

    df = pd.read_excel(EXCEL_PATH, skiprows=3)

    dict_df = {'Verbois': None, 'Chancy-Pougny': None}
    for dam in dict_df.keys():
        if dam == 'Chancy-Pougny':
            df_dam = select_columns_by_name(df, 'Cy-Py')
        else:
            df_dam = select_columns_by_name(df, dam)

        df_long = _melt_group_columns(df_dam)

        dict_df[dam] = df_long

    return dict_df

if __name__ == "__main__":
    print(get_data_from_excel())
