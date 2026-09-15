import pandas as pd


def calculate_waste_risk(row):
    """
    Calculate energy waste risk for one record.

    Risk is based on:
    - Occupancy
    - Energy consumption
    - AC status
    - Lighting status
    - Operating hours
    """

    score = 0
    reasons = []

    hour = row["hour"]
    occupancy = row["occupancy"]
    energy = row["energy_kwh"]

    # After-hours usage
    after_hours = hour >= 22 or hour < 6

    # High energy threshold
    high_energy = energy >= 15

    # Empty or nearly empty room
    low_occupancy = occupancy <= 2

    # Rule 1: Empty room + high energy
    if low_occupancy and high_energy:
        score += 3
        reasons.append("High energy with low occupancy")

    # Rule 2: After-hours energy consumption
    if after_hours and energy >= 10:
        score += 3
        reasons.append("High consumption during after-hours")

    # Rule 3: AC running in empty room
    if low_occupancy and row["ac_status"] == "ON":
        score += 2
        reasons.append("AC running with low occupancy")

    # Rule 4: Lights running in empty room
    if occupancy == 0 and row["lights_status"] == "ON":
        score += 2
        reasons.append("Lights ON in empty room")

    # Determine risk
    if score >= 6:
        risk = "HIGH"
    elif score >= 3:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    return pd.Series({
        "waste_score": score,
        "risk": risk,
        "waste_reason": "; ".join(reasons)
    })


def detect_waste(df):
    """
    Detect possible energy waste across campus.
    """

    result = df.copy()

    # Make sure hour exists
    if "hour" not in result.columns:
        result["timestamp"] = pd.to_datetime(result["timestamp"])
        result["hour"] = result["timestamp"].dt.hour

    risk_data = result.apply(calculate_waste_risk, axis=1)

    result = pd.concat([result, risk_data], axis=1)

    return result


def get_waste_records(df):
    """
    Return only medium and high-risk records.
    """

    result = detect_waste(df)

    waste = result[
        result["risk"].isin(["HIGH", "MEDIUM"])
    ].copy()

    return waste.sort_values(
        by="waste_score",
        ascending=False
    )


def get_high_risk_records(df):
    """
    Return only high-risk energy waste records.
    """

    result = detect_waste(df)

    return result[
        result["risk"] == "HIGH"
    ].sort_values(
        by="waste_score",
        ascending=False
    )


def get_waste_summary(df):
    """
    Generate summary statistics for energy waste.
    """

    result = detect_waste(df)

    high = (result["risk"] == "HIGH").sum()
    medium = (result["risk"] == "MEDIUM").sum()

    total_records = len(result)

    waste_records = high + medium

    if total_records > 0:
        waste_percentage = (
            waste_records / total_records
        ) * 100
    else:
        waste_percentage = 0

    return {
        "high_risk": int(high),
        "medium_risk": int(medium),
        "total_waste_records": int(waste_records),
        "waste_percentage": round(waste_percentage, 2)
    }


# Test the waste detection module
if __name__ == "__main__":

    from analysis import load_data

    df = load_data()

    result = detect_waste(df)

    summary = get_waste_summary(df)

    print("\n===================================")
    print(" ENERGY WASTE DETECTION")
    print("===================================")

    print(f"High Risk: {summary['high_risk']}")
    print(f"Medium Risk: {summary['medium_risk']}")
    print(f"Total Waste Records: {summary['total_waste_records']}")
    print(f"Waste Percentage: {summary['waste_percentage']}%")

    print("\nTop 10 Waste Alerts:")

    alerts = get_high_risk_records(df)

    columns = [
        "timestamp",
        "building",
        "room",
        "energy_kwh",
        "occupancy",
        "ac_status",
        "lights_status",
        "waste_score",
        "risk",
        "waste_reason"
    ]

    print(
        alerts[columns].head(10).to_string(index=False)
    )
    