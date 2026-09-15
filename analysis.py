import pandas as pd


def load_data(file_path="data/campus_energy.csv"):
    """
    Load the campus energy dataset.
    """
    df = pd.read_csv(file_path)

    # Convert timestamp into datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Add useful time features
    df["hour"] = df["timestamp"].dt.hour
    df["date"] = df["timestamp"].dt.date
    df["day"] = df["timestamp"].dt.day_name()

    return df


def get_total_energy(df):
    """
    Calculate total campus energy consumption.
    """
    return round(df["energy_kwh"].sum(), 2)


def get_average_energy(df):
    """
    Calculate average energy consumption per record.
    """
    return round(df["energy_kwh"].mean(), 2)


def get_building_consumption(df):
    """
    Calculate total energy consumption for each building.
    """
    result = (
        df.groupby("building")["energy_kwh"]
        .sum()
        .sort_values(ascending=False)
        .round(2)
    )

    return result


def get_daily_consumption(df):
    """
    Calculate daily campus energy consumption.
    """
    result = (
        df.groupby("date")["energy_kwh"]
        .sum()
        .round(2)
    )

    return result


def get_hourly_consumption(df):
    """
    Calculate average energy consumption by hour.
    """
    result = (
        df.groupby("hour")["energy_kwh"]
        .mean()
        .round(2)
    )

    return result


def get_peak_hour(df):
    """
    Find the hour with the highest average energy consumption.
    """
    hourly = get_hourly_consumption(df)

    peak_hour = hourly.idxmax()
    peak_value = hourly.max()

    return int(peak_hour), float(peak_value)


def get_highest_consuming_building(df):
    """
    Find the building with the highest total consumption.
    """
    building_data = get_building_consumption(df)

    building = building_data.idxmax()
    consumption = building_data.max()

    return building, float(consumption)


def get_efficiency_score(df):
    """
    Estimate an energy efficiency score.

    The score is based on the proportion of energy
    used during normal occupied hours.
    """

    normal_hours = df[
        (df["hour"] >= 8) &
        (df["hour"] < 18)
    ]

    normal_energy = normal_hours["energy_kwh"].sum()
    total_energy = df["energy_kwh"].sum()

    if total_energy == 0:
        return 100.0

    score = (normal_energy / total_energy) * 100

    return round(min(score, 100), 2)


def get_summary(df):
    """
    Return important campus energy statistics.
    """

    total = get_total_energy(df)
    average = get_average_energy(df)

    peak_hour, peak_value = get_peak_hour(df)

    highest_building, highest_building_energy = (
        get_highest_consuming_building(df)
    )

    efficiency = get_efficiency_score(df)

    return {
        "total_energy": total,
        "average_energy": average,
        "peak_hour": peak_hour,
        "peak_hour_energy": peak_value,
        "highest_building": highest_building,
        "highest_building_energy": highest_building_energy,
        "efficiency_score": efficiency
    }


# Test the analysis module
if __name__ == "__main__":

    df = load_data()

    summary = get_summary(df)

    print("\n===================================")
    print(" CAMPUS ENERGY ANALYSIS")
    print("===================================")

    print(f"Total Energy: {summary['total_energy']} kWh")
    print(f"Average Energy: {summary['average_energy']} kWh")

    print(
        f"Peak Hour: {summary['peak_hour']}:00 "
        f"({summary['peak_hour_energy']} kWh average)"
    )

    print(
        f"Highest Consuming Building: "
        f"{summary['highest_building']}"
    )

    print(
        f"Building Consumption: "
        f"{summary['highest_building_energy']} kWh"
    )

    print(
        f"Efficiency Score: "
        f"{summary['efficiency_score']}%"
    )

    print("\nBuilding-wise Consumption:")
    print(get_building_consumption(df))