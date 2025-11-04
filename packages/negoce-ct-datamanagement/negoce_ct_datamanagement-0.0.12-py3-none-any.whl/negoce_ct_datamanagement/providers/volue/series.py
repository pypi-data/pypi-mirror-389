from typing import List
from datetime import datetime
import json
import os
from pathlib import Path

from negoce_ct_datamanagement.providers.volue._config import VolueApi


def get_series(curves_id: List[int], date_from: datetime, date_to: datetime) -> list:
    """
        Get list of series data for a time range
    :param curves_id: (List[int]) list of curves id to get series from
    :param date_from: (datetime)
    :param date_to: (datetime)
    :return: list of requested series objects
    """
    # build request
    date_from = date_from.strftime("%Y-%m-%d")
    date_to = date_to.strftime("%Y-%m-%d")
    date_now = datetime.now().strftime("%H-%M-%S")

    # # Create the directory structure
    # output_dir = os.path.join("data_quantitative", "volue_response")
    # os.makedirs(output_dir, exist_ok=True)

    data = []
    for curve_id in curves_id:
        url = f'series/{curve_id}/?from={date_from}&to={date_to}'
        # query and get results
        vapi = VolueApi()
        response = vapi.send_request(url)
        
        # # Create filename and full path
        # filename = f"curve_{curve_id}_{date_from}_{date_to}_{date_now}.json"
        # full_path = os.path.join(output_dir, filename)
        
        # # Save to file
        # with open(full_path, 'w') as f:
        #     json.dump(response, f, indent=2)
        
        # print(f"Saved series data to {full_path}")
        data.append(response)  # Use the same response, don't call API again
    
    return data


if __name__ == "__main__":
    # load env variables
    from pathlib import Path
    from dotenv import load_dotenv
    env_file = f'.env.development'
    env_path = Path(__file__).parents[3]
    load_dotenv(env_path / env_file)
    # test request
    data = get_series(
            curves_id=[20744],  # spot_ch
            date_from=datetime(2025, 4, 1),
            date_to=datetime(2025, 4, 2)
    )
    a = 1