import requests
import pandas as pd
from pathlib import Path


# Schemes we want to fetch
schemes = {
    "HDFC_Top_100": "125497",
    "SBI_Bluechip": "119551",
    "ICICI_Bluechip": "120503",
    "Nippon_Large_Cap": "118632",
    "Axis_Bluechip": "119092",
    "Kotak_Bluechip": "120841"
}


# Folder where raw API data will be saved
output_folder = Path("data/raw")


for scheme_name, amfi_code in schemes.items():

    print("\n" + "=" * 60)
    print(f"Fetching: {scheme_name}")
    print(f"AMFI Code: {amfi_code}")

    API_URL = f"https://api.mfapi.in/mf/{amfi_code}"

    response = requests.get(API_URL)

    print("Status Code:", response.status_code)

    if response.status_code != 200:
        print("Failed to fetch data.")
        continue

    data = response.json()

    nav_data = data["data"]

    print("NAV records:", len(nav_data))

    nav_df = pd.DataFrame(nav_data)

    nav_df["amfi_code"] = int(amfi_code)

    nav_df["date"] = pd.to_datetime(
        nav_df["date"],
        format="%d-%m-%Y"
    ).dt.strftime("%Y-%m-%d")

    nav_df["nav"] = pd.to_numeric(nav_df["nav"])

    nav_df = nav_df[["amfi_code", "date", "nav"]]

    output_path = output_folder / f"{scheme_name}_live_nav.csv"

    nav_df.to_csv(output_path, index=False)

    print("Saved:", output_path)
    print("Shape:", nav_df.shape)