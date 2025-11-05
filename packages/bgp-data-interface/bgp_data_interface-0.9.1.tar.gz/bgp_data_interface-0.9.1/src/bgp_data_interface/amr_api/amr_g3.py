import pandas as pd
import requests
from requests.exceptions import HTTPError
from typing import Any

AMR_URL = "https://apig3-test.bgrimmpower.com"

TOKEN_PARAMS = {
    "grant_type": "password",
    "client_id": "amr_data",
}



class AMR_G3:

    access_token: str



    def __init__(self, username: str, api_key: str, cert_path: str):
        self.cert_path = cert_path
        self.__get_access_token(username, api_key)



    def __get_access_token(self, username: str, api_key: str) -> None:

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        params = TOKEN_PARAMS | {
            "username": username,
            "password": api_key
        }

        try:
            response = requests.post(
                f"{AMR_URL}/api/token",
                headers=headers,
                data=params,
                verify=self.cert_path
            )
            response.raise_for_status()
            self.access_token = response.json().get("access_token")

        except HTTPError as e:
            print(f"Error obtaining access token: {e}")



    def get_sites(self) -> dict[str, Any]:
        site_headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(
                f"{AMR_URL}/api/Site", 
                headers=site_headers, 
                verify=self.cert_path
            )
            response.raise_for_status()

            return response.json()

        except HTTPError as e:
            print(f"Error obtaining site data: {e}")

        return {}



    def get_load_profile(self, 
            meter_code: str,
            start_date: str,
            end_date: str) -> pd.DataFrame:

        url = f"{AMR_URL}/api/Elec/LoadProfile"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        params = {
            "start_date": start_date,
            "end_date": end_date,
            "meter_code": meter_code,
            "site_id": "",
            "output": "JSON"
        }

        try:
            response = requests.get(url, 
                    headers=headers,
                    params=params,
                    verify=self.cert_path
            )
            response.raise_for_status()

            load_profile = response.json()
            df = self.__transform_load_profile(load_profile)
            return df

        except HTTPError as e:
            print(f"Error obtaining load profile data: {e}")
            return pd.DataFrame()



    def __transform_load_profile(self,
            load_profile: dict[str, Any]) -> pd.DataFrame:

        selected_columns = [
            'meter_code',
            'data_time',
            'avg_ademand_im',
            'avg_rdemand_im',
            'ora_customer_code'
        ]

        df = pd.DataFrame(load_profile)
        df = df[selected_columns]
        df = df.rename(columns={
            'data_time': 'date_time',
            'avg_ademand_im': 'avg_active_demand_kW',
            'avg_rdemand_im': 'avg_reactive_demand_kVAR',
            'ora_customer_code': 'iu_code'
        })
        df = df[:-1]

        return df
