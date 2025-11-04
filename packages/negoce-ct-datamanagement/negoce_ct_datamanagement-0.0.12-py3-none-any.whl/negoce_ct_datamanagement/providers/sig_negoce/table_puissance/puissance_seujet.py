import pandas as pd
from pathlib import Path

EXCEL_PATH_SEUJET = Path(r"\\WinFS\SIG\CL-6370\01 Gestion CT\Gestion CT\Feuille Prev\Feuille gestion Salva\Annexe\table cote débit.xls")


def _melt_group_columns(df: pd.DataFrame, groupe: int) -> pd.DataFrame:
    """
    Transforms the DataFrame from wide to long format for a given group.

    - Renames columns: first column to 'debit', others to their float values.
    - Melts the DataFrame so each row represents a (debit, cote_leman, power) tuple.
    - Adds a 'groupe' column to indicate the group number.
    - Rounds 'power' and 'cote_leman' values to 3 decimal places.

    :param df: DataFrame with columns to be melted.
    :param groupe: Group number to annotate in the result.
    :return: Long-format DataFrame with columns ['Debit', 'Groupe', 'Cote_leman', 'Power']
    """
    # Rename columns: first is 'debit', others are floats
    columns = ['Debit'] + [float(col) for col in df.columns[1:]]
    df.columns = columns

    # Melt the DataFrame to long format
    df_long = df.melt(
        id_vars=['Debit'],
        var_name='Cote_leman',
        value_name='Power'
    )
    # Annotate group number
    df_long['Groupe'] = groupe

    # Round 'Power' and 'Cote_leman' to 3 decimal places
    df_long['Power'] = df_long['Power'].round(3)
    df_long['Cote_leman'] = pd.to_numeric(df_long['Cote_leman'], errors='coerce').round(3)

    # Reorder columns so groupe comes second
    df_long = df_long[['Debit', 'Groupe', 'Power', 'Cote_leman']]

    return df_long

def get_data_from_excel() -> pd.DataFrame:
    """
    Reads the Seujet data from an Excel file and returns it as a DataFrame.
    :return: DataFrame with Seujet Power data.
    """
    dfs = []
    for g in range(1, 4):
        sheet_name = f'table cote débits {g} gr'
        try:
            df = pd.read_excel(EXCEL_PATH_SEUJET, sheet_name, skiprows=range(0, 11), usecols=list(range(1, 57)), engine="xlrd")
            df = df.drop(df.index[0])
        except ValueError:
            continue

        df_long = _melt_group_columns(df, g)

        dfs.append(df_long)
    
    df_longs = pd.concat(dfs, ignore_index=True)

    return df_longs

        


if __name__ == "__main__":
    get_data_from_excel()
    