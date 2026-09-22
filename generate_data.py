"""
generate_data.py
-----------------
Creates fake but realistic entrepreneur signup data across South African
cities, simulating the FNB e-Identity Services funnel:

  Digital ID created -> CIPC registered -> Funding requested -> Funded

Run this once to produce fake_signups.csv, which dashboard.py then reads.
"""

import pandas as pd
import numpy as np
import random
from datetime import date, timedelta

random.seed(42)
np.random.seed(42)

# Major South African cities with approximate coordinates (for map plotting)
# and a "strength" weight -- bigger cities get proportionally more signups,
# mimicking real population/economic activity differences.
CITIES = {
    "Johannesburg": {"lat": -26.2041, "lon": 28.0473, "province": "Gauteng", "weight": 30},
    "Pretoria":     {"lat": -25.7479, "lon": 28.2293, "province": "Gauteng", "weight": 18},
    "Cape Town":    {"lat": -33.9249, "lon": 18.4241, "province": "Western Cape", "weight": 25},
    "Durban":       {"lat": -29.8587, "lon": 31.0218, "province": "KwaZulu-Natal", "weight": 20},
    "Gqeberha":     {"lat": -33.9608, "lon": 25.6022, "province": "Eastern Cape", "weight": 10},
    "Bloemfontein": {"lat": -29.0852, "lon": 26.1596, "province": "Free State", "weight": 8},
    "East London":  {"lat": -33.0153, "lon": 27.9116, "province": "Eastern Cape", "weight": 7},
    "Polokwane":    {"lat": -23.9045, "lon": 29.4689, "province": "Limpopo", "weight": 9},
    "Mbombela":     {"lat": -25.4753, "lon": 30.9694, "province": "Mpumalanga", "weight": 8},
    "Kimberley":    {"lat": -28.7282, "lon": 24.7499, "province": "Northern Cape", "weight": 5},
}

BUSINESS_TYPES = ["Spaza Shop", "Hair Salon", "Catering", "Construction",
                   "Retail", "Transport", "Tech Services", "Food Stall"]

START_DATE = date(2026, 1, 1)
END_DATE = date(2026, 9, 21)
DAYS = (END_DATE - START_DATE).days

rows = []
signup_id = 1

total_weight = sum(c["weight"] for c in CITIES.values())

for day_offset in range(DAYS):
    current_date = START_DATE + timedelta(days=day_offset)

    # Vary daily volume a bit, with slow overall growth over the year
    growth_factor = 1 + (day_offset / DAYS) * 0.8
    daily_signups = int(np.random.poisson(15) * growth_factor)

    for _ in range(daily_signups):
        city = random.choices(
            list(CITIES.keys()),
            weights=[c["weight"] for c in CITIES.values()],
        )[0]
        city_info = CITIES[city]

        # Funnel: each stage has a chance to drop off, and some cities
        # convert better than others (simulating real regional gaps)
        city_conversion_bonus = {
            "Johannesburg": 0.05, "Cape Town": 0.08, "Pretoria": 0.03,
            "Durban": 0.0, "Kimberley": -0.10, "East London": -0.08,
            "Polokwane": -0.05, "Mbombela": -0.03, "Bloemfontein": -0.02,
            "Gqeberha": -0.04,
        }.get(city, 0)

        digital_id_created = True  # everyone in this dataset starts here
        cipc_registered = random.random() < (0.65 + city_conversion_bonus)
        funding_requested = cipc_registered and random.random() < (0.45 + city_conversion_bonus)
        funded = funding_requested and random.random() < (0.35 + city_conversion_bonus)

        rows.append({
            "SignupID": signup_id,
            "Date": current_date.isoformat(),
            "City": city,
            "Province": city_info["province"],
            "Lat": city_info["lat"],
            "Lon": city_info["lon"],
            "BusinessType": random.choice(BUSINESS_TYPES),
            "DigitalIDCreated": digital_id_created,
            "CIPCRegistered": cipc_registered,
            "FundingRequested": funding_requested,
            "Funded": funded,
        })
        signup_id += 1

df = pd.DataFrame(rows)
df.to_csv("fake_signups.csv", index=False)
print(f"Generated {len(df)} fake signups across {df['City'].nunique()} cities")
print(df.groupby("City").size().sort_values(ascending=False))
