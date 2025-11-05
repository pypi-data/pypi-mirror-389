import credentials

from sys import path
path.append('./src/bgp_data_interface')
from amr import AMR
import pandas as pd

USERNAME = "aggregator"
BGP_CERT_PATH = 'src/tests/_.bgrimmpower.crt'



def test_init_amr() -> None:
    api = AMR(USERNAME, credentials.AMR_API_KEY, BGP_CERT_PATH)

    assert api is not None
    assert isinstance(api, AMR)



def test_get_sites() -> None:
    api = AMR(USERNAME, credentials.AMR_API_KEY, BGP_CERT_PATH)
    sites = api.get_sites()

    assert sites is not None
    assert sites == []



def test_get_load_profile() -> None:
    meter_code = "AAPICO Forging PCL. (1.1)"

    api = AMR(USERNAME, credentials.AMR_API_KEY, BGP_CERT_PATH)
    df = api.get_load_profile(
        meter_code=meter_code,
        start_date="2025-10-01",
        end_date="2025-10-02"
    )

    assert df is not None
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (96, 5)
    assert list(df.columns) == [
        'meter_code',
        'date_time',
        'avg_active_power_kW',
        'avg_reactive_power_kVAR',
        'iu_code'
    ]
    assert df['meter_code'].iloc[0] == meter_code
    assert df['date_time'].iloc[0] == pd.to_datetime("2025-10-01 00:00:00")
    assert df['date_time'].iloc[-1] == pd.to_datetime("2025-10-01 23:45:00")
