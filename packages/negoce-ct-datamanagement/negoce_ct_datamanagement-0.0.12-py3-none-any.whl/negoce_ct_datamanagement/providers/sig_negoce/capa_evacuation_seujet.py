import pandas as pd


def get_data_from_excel() -> pd.DataFrame:
    """

    :param is_bissextile:
    :return:
    """
    excel_path = r"\\WinFS\SIG\CL-6370\01 Gestion CT\Gestion CT\Feuille Prev\Feuille gestion Salva\Annexe\Triplets_émissaire_Léman.xlsx"
    raw = pd.read_excel(excel_path, sheet_name='Feuil1', header=None)
   
    # 2) Pull out the “arve” values from the first row (all columns except the very first and very last)
    arve_values = raw.iloc[0, 1:-1].astype(float)

    # 3) Take the block of numeric data under those columns…
    data_block = raw.iloc[1:, 1:-1]
    data_block.columns = arve_values  # name each column by its arve height

    # 4) Grab the Q_seujet column (the very last column) and append it as its own field
    data_block['Q_seujet'] = raw.iloc[1:, -1].astype(int).values

    # 5) Melt into long form: one row per (Q_seujet, arve, cote_lac)
    df_long = (
        data_block
        .melt(
        id_vars='Q_seujet',          # keep Q_seujet fixed
        var_name='Arve',             # turn each arve-column into a row
        value_name='Cote_leman'        # its cell becomes “Cote_leman”
        )
        .reset_index(drop=True)
    )

    # 6) Filter out zeros
    df_long = df_long[df_long['Cote_leman'] != 0.0].reset_index(drop=True)

    return df_long              




if __name__ == "__main__":
    df = get_data_from_excel()
