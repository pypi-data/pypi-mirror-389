from negoce_ct_datamanagement.providers.ofev._config import OfevApi


def get_st_prex_last_7_days():
    """
    Measure of St Prex level, last 7 days, granularity 10 minutes
    :return: list dict with serie name and values (tuple(timestamp, value))
    """
    endpoint = "/plots/p_q_7days/2027_p_q_7days_fr.json"
    ofev_api = OfevApi()
    data = ofev_api.send_request(endpoint=endpoint)
    return data


def get_st_prex_last_40_days():
    """
    Measure of St Prex level, last 40 days, granularity 10 minutes
    :return: list dict with serie name and values (tuple(timestamp, value))
    """
    endpoint = "/plots/p_q_40days/2027_p_q_40days_fr.json"
    ofev_api = OfevApi()
    data = ofev_api.send_request(endpoint=endpoint)
    return data


def get_stations_leman():
    """
    Get Porte du Scex (Rhone), St-Prex (Leman), Geneve Halle de l'île (Rhone), Genève Bout du Monde (Arve)
    and Chancy Aux Ripes (Rhone) measure, last 8 days, granularity 5 minutes except St-Prex (10 minutes)
    :return: list dict with serie name and values (tuple(timestamp, value))
    """
    endpoint = "/plots/pq_group/2027_pq_group_17_fr.json"
    ofev_api = OfevApi()
    data = ofev_api.send_request(endpoint=endpoint)
    return data


if __name__ == "__main__":
    res = get_stations_leman()
    a = 1