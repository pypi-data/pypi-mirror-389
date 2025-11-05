import sys

if "pytest" in sys.modules:
    from amr_api.amr_g3 import AMR_G3
else:
    from bgp_data_interface.amr_api.amr_g3 import AMR_G3

import pandas as pd
from typing import Any

class AMR:

    _amr_g3: AMR_G3

    def __init__(self, username: str, api_key: str, cert_path: str) -> None:
        self._amr_g3 = AMR_G3(username, api_key, cert_path)

    def get_sites(self) -> dict[str, Any]:
        return self._amr_g3.get_sites()
    
    def get_load_profile(self, 
            meter_code: str,
            start_date: str,
            end_date: str) -> pd.DataFrame:
        return self._amr_g3.get_load_profile(meter_code, start_date, end_date)
