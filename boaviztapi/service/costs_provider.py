import os
from datetime import datetime, timezone

import pandas as pd
import requests
import xmltodict

from boaviztapi import data_dir

df = pd.read_csv(os.path.join(data_dir, 'electricity/eic_codes.csv'))


def get_eic_countries() -> list[dict]:
    """
    Get the list of EIC codes and their countries and return it as a dict
    """
    return df.to_dict(orient='records')


def get_EIC_for_country(iso3_country: str) -> str:
    return df.query(f"`ISO3 Code` == '{iso3_country}' ")["EIC_code"].iloc[0]


def get_price_for_country(iso3_country: str) -> dict:
    security_token = "f36a22c1-8b9b-48f0-b575-e8e8cd6f79df"
    eic_code = get_EIC_for_country(iso3_country)

    periodStart = datetime.now(timezone.utc).replace(hour=0, minute=0)
    day = periodStart.day
    periodEnd = datetime.now(timezone.utc).replace(day=day + 1, hour=0, minute=0)

    periodStart = periodStart.strftime("%Y%m%d%H%M")  # YYYYMMDDHHMM e.g. 202509061200
    periodEnd = periodEnd.strftime("%Y%m%d%H%M")

    url = f"https://web-api.tp.entsoe.eu/api?documentType=A44&periodStart={periodStart}&periodEnd={periodEnd}&out_Domain={eic_code}&in_Domain={eic_code}&securityToken={security_token}"
    r = requests.get(url)
    return xmltodict.parse(r.content)
