import pandas as pd
import numpy as np
import os

np.random.seed(42)

buildings = {
    "Academic Block": ["A101", "A102", "A103"],
    "Engineering Block": ["E201", "E202", "E203"],
    "Library": ["L101", "L102"],
    "Hostel Block": ["H101", "H102", "H103"],
    "Laboratory Block": ["LAB1", "LAB2", "LAB3"]
}

dates = pd.date_range(
    start="2026-09-01",
    end="2026-09-07 23:00",
    freq="h"
)

records = []

for timestamp in dates:

    hour = timestamp.hour

    for building, rooms in buildings.items():

        for room in rooms:

            # Occupancy
            if 8 <= hour < 18:
                occupancy = np.random.randint(15, 60)
            elif 18 <= hour < 22:
                occupancy = np.random.randint(5, 30)
            else:
                occupancy = np.random.randint(0, 5)

            # Base energy
            energy = np.random.uniform(5, 15)

            # Occupancy increases energy
            energy += occupancy * 0.15

            # Temperature
            temperature = np.random.uniform(25, 34)

            # AC and lights
            ac_status = "ON" if 9 <= hour < 18 else "OFF"
            lights_status = "ON" if occupancy > 0 else "OFF"

            # Laboratory uses more energy
            if "Laboratory" in building:
                energy += 5

            # Engineering uses more energy
            if "Engineering" in building:
                energy += 3

            # Intentional after-hours waste
            if np.random.random() < 0.04 and hour >= 22:
                occupancy = 0
                ac_status = "ON"
                lights_status = "ON"
                energy += np.random.uniform(15, 30)

            # Intentional high-energy/low-occupancy anomaly
            if np.random.random() < 0.03:
                occupancy = np.random.randint(0, 3)
                energy += np.random.uniform(10, 25)

            records.append([
                timestamp,
                building,
                room,
                round(energy, 2),
                occupancy,
                round(temperature, 1),
                ac_status,
                lights_status
            ])

df = pd.DataFrame(records, columns=[
    "timestamp",
    "building",
    "room",
    "energy_kwh",
    "occupancy",
    "temperature",
    "ac_status",
    "lights_status"
])

# Create data folder
os.makedirs("data", exist_ok=True)

# Save dataset
df.to_csv("data/campus_energy.csv", index=False)

print("===================================")
print(" CAMPUS ENERGY DATASET CREATED")
print("===================================")
print(f"Total records: {len(df)}")
print(f"Columns: {len(df.columns)}")

print("\nFirst 5 records:")
print(df.head())

print("\nBuilding-wise energy:")
print(df.groupby("building")["energy_kwh"].sum().round(2))