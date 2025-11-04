import pandas as pd


def get_data_from_excel(is_bissextile: bool = False) -> pd.DataFrame:
    """

    :param is_bissextile:
    :return:
    """
    excel_path = r"\\WinFS\SIG\CL-6370\01 Gestion CT\Gestion CT\Feuille Prev\Outil_Optim_Hydro\rootfolder\data\limites_cote_leman - for SQL.xlsx"
    sheet_name = "Année bissextile" if is_bissextile else "Année normale"
    df = pd.read_excel(excel_path, sheet_name=sheet_name)
    return df


if __name__ == "__main__":
    get_data_from_excel()