import streamlit as st
import pandas as pd
import plotly.express as px

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Campus Energy Intelligence",
    page_icon="⚡",
    layout="wide"
)

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>
    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 0px;
    }

    .subtitle {
        font-size: 18px;
        color: #666;
        margin-bottom: 25px;
    }

    .alert-box {
        padding: 18px;
        border-radius: 10px;
        border-left: 6px solid #ff4b4b;
        background-color: #fff4f4;
    }

    .recommendation-box {
        padding: 18px;
        border-radius: 10px;
        background-color: #f0f7ff;
        border-left: 6px solid #2196f3;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# LOAD DATA
# ============================================================

DATA_PATH = "data/campus_energy.csv"

try:
    df = pd.read_csv(DATA_PATH)
except FileNotFoundError:
    st.error(
        "Dataset not found. Please make sure "
        "'data/campus_energy.csv' exists."
    )
    st.stop()


# ============================================================
# DATA PREPROCESSING
# ============================================================

df["timestamp"] = pd.to_datetime(df["timestamp"])

df["hour"] = df["timestamp"].dt.hour
df["date"] = df["timestamp"].dt.date

df["is_after_hours"] = (
    (df["hour"] >= 22) |
    (df["hour"] <= 6)
)

df["is_empty"] = df["occupancy"] == 0

# ============================================================
# WASTE DETECTION
# ============================================================

# Room-level typical energy consumption
room_median = (
    df.groupby(["building", "room"])["energy_kwh"]
    .transform("median")
)

df["energy_ratio"] = (
    df["energy_kwh"] / room_median.replace(0, 0.01)
)

# Potential waste conditions
df["potential_waste"] = (
    (
        df["is_empty"] &
        (df["energy_kwh"] > room_median)
    )
    |
    (
        df["is_after_hours"] &
        (df["energy_kwh"] > room_median)
    )
)

# Waste severity
def calculate_risk(row):

    score = 0

    if row["occupancy"] == 0:
        score += 2

    if row["is_after_hours"]:
        score += 2

    if row["energy_ratio"] > 1.5:
        score += 2
    elif row["energy_ratio"] > 1.2:
        score += 1

    if row["ac_status"] == "ON":
        score += 1

    if row["lights_status"] == "ON":
        score += 1

    if score >= 5:
        return "High"
    elif score >= 3:
        return "Medium"
    return "Low"


df["risk"] = df.apply(calculate_risk, axis=1)

# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.title("⚙ Filters")

buildings = ["All Buildings"] + sorted(
    df["building"].unique().tolist()
)

selected_building = st.sidebar.selectbox(
    "Select Building",
    buildings
)

min_date = df["date"].min()
max_date = df["date"].max()

selected_dates = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Apply filters
filtered_df = df.copy()

if selected_building != "All Buildings":
    filtered_df = filtered_df[
        filtered_df["building"] == selected_building
    ]

if isinstance(selected_dates, tuple) and len(selected_dates) == 2:

    start_date, end_date = selected_dates

    filtered_df = filtered_df[
        (filtered_df["date"] >= start_date) &
        (filtered_df["date"] <= end_date)
    ]


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">⚡ Campus Energy Intelligence</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Smart energy monitoring • Waste detection • Decision support'
    '</div>',
    unsafe_allow_html=True
)

st.divider()


# ============================================================
# KPI CALCULATIONS
# ============================================================

total_energy = filtered_df["energy_kwh"].sum()

average_energy = filtered_df["energy_kwh"].mean()

waste_records = filtered_df[
    filtered_df["potential_waste"]
]

waste_energy = waste_records["energy_kwh"].sum()

waste_percentage = (
    (waste_energy / total_energy) * 100
    if total_energy > 0
    else 0
)

empty_records = filtered_df[
    filtered_df["is_empty"]
]

high_risk_count = len(
    filtered_df[filtered_df["risk"] == "High"]
)


# ============================================================
# KPI CARDS
# ============================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "⚡ Total Energy",
        f"{total_energy:,.0f} kWh"
    )

with col2:
    st.metric(
        "📊 Average Usage",
        f"{average_energy:,.2f} kWh"
    )

with col3:
    st.metric(
        "⚠ Potential Waste",
        f"{waste_energy:,.0f} kWh"
    )

with col4:
    st.metric(
        "🚨 High Risk Events",
        high_risk_count
    )


# ============================================================
# ENERGY TREND
# ============================================================

st.divider()

st.subheader("📈 Energy Consumption Trend")

daily_energy = (
    filtered_df
    .groupby("date", as_index=False)["energy_kwh"]
    .sum()
)

fig_trend = px.line(
    daily_energy,
    x="date",
    y="energy_kwh",
    markers=True,
    labels={
        "date": "Date",
        "energy_kwh": "Energy Consumption (kWh)"
    }
)

fig_trend.update_layout(
    height=400,
    hovermode="x unified"
)

st.plotly_chart(
    fig_trend,
    use_container_width=True
)


# ============================================================
# BUILDING ANALYSIS
# ============================================================

col1, col2 = st.columns(2)

with col1:

    st.subheader("🏢 Building-wise Consumption")

    building_energy = (
        filtered_df
        .groupby("building", as_index=False)["energy_kwh"]
        .sum()
        .sort_values(
            "energy_kwh",
            ascending=False
        )
    )

    fig_building = px.bar(
        building_energy,
        x="building",
        y="energy_kwh",
        labels={
            "building": "Building",
            "energy_kwh": "Energy (kWh)"
        }
    )

    fig_building.update_layout(
        height=400,
        xaxis_tickangle=-30
    )

    st.plotly_chart(
        fig_building,
        use_container_width=True
    )


with col2:

    st.subheader("👥 Occupancy vs Energy")

    fig_scatter = px.scatter(
        filtered_df.sample(
            min(1000, len(filtered_df)),
            random_state=42
        ),
        x="occupancy",
        y="energy_kwh",
        size="energy_kwh",
        hover_data=[
            "building",
            "room",
            "timestamp"
        ],
        labels={
            "occupancy": "Occupancy",
            "energy_kwh": "Energy (kWh)"
        }
    )

    fig_scatter.update_layout(
        height=400
    )

    st.plotly_chart(
        fig_scatter,
        use_container_width=True
    )


# ============================================================
# WASTE DETECTION
# ============================================================

st.divider()

st.subheader("🚨 Energy Waste Detection")

st.write(
    "The system identifies potential waste by comparing "
    "energy consumption with occupancy, operating hours "
    "and equipment status."
)

if len(waste_records) > 0:

    display_waste = waste_records[
        [
            "timestamp",
            "building",
            "room",
            "energy_kwh",
            "occupancy",
            "ac_status",
            "lights_status",
            "risk"
        ]
    ].copy()

    display_waste = display_waste.sort_values(
        "energy_kwh",
        ascending=False
    )

    display_waste.columns = [
        "Time",
        "Building",
        "Room",
        "Energy (kWh)",
        "Occupancy",
        "AC",
        "Lights",
        "Risk"
    ]

    st.dataframe(
        display_waste.head(15),
        use_container_width=True,
        hide_index=True
    )

else:

    st.success(
        "No significant potential energy waste detected "
        "for the selected filters."
    )


# ============================================================
# TOP WASTE ALERT
# ============================================================

if len(waste_records) > 0:

    top_waste = (
        waste_records
        .sort_values(
            "energy_kwh",
            ascending=False
        )
        .iloc[0]
    )

    st.markdown(
        f"""
        <div class="alert-box">

        <h3>🔴 High-Priority Energy Alert</h3>

        <b>Location:</b>
        {top_waste["building"]} — {top_waste["room"]}

        <br><br>

        <b>Time:</b>
        {top_waste["timestamp"]}

        <br><br>

        <b>Energy Consumption:</b>
        {top_waste["energy_kwh"]:.2f} kWh

        <br><br>

        <b>Occupancy:</b>
        {top_waste["occupancy"]}

        <br><br>

        <b>AC:</b>
        {top_waste["ac_status"]}

        &nbsp;&nbsp;

        <b>Lights:</b>
        {top_waste["lights_status"]}

        <br><br>

        ⚠ High energy consumption detected during
        low/no occupancy or outside normal operating hours.

        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# RECOMMENDATIONS
# ============================================================

st.divider()

st.subheader("💡 Recommended Actions")

rec1, rec2, rec3 = st.columns(3)

with rec1:

    st.markdown(
        """
        <div class="recommendation-box">

        <h4>❄ HVAC Optimization</h4>

        Reduce unnecessary AC operation
        in empty rooms and during
        non-operational hours.

        </div>
        """,
        unsafe_allow_html=True
    )


with rec2:

    st.markdown(
        """
        <div class="recommendation-box">

        <h4>💡 Smart Lighting</h4>

        Switch off lights in unoccupied
        rooms and consider automated
        occupancy-based controls.

        </div>
        """,
        unsafe_allow_html=True
    )


with rec3:

    st.markdown(
        """
        <div class="recommendation-box">

        <h4>🔌 Equipment Management</h4>

        Check laboratory and computer
        equipment that remains powered
        after operating hours.

        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# INSIGHTS
# ============================================================

st.divider()

st.subheader("🧠 Key Insights")

insight1, insight2, insight3 = st.columns(3)

with insight1:

    st.info(
        f"""
        **Potential Waste Rate**

        {waste_percentage:.1f}% of analyzed
        energy records are associated
        with potential waste conditions.
        """
    )

with insight2:

    st.info(
        f"""
        **Empty Rooms**

        {len(empty_records):,} records show
        zero occupancy.

        These records are candidates
        for efficiency analysis.
        """
    )

with insight3:

    if len(building_energy) > 0:

        top_building = building_energy.iloc[0]["building"]

        st.info(
            f"""
            **Highest Consumption**

            {top_building}

            is currently the highest
            energy-consuming building
            in the selected period.
            """
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Campus Energy Intelligence | Hackathon Prototype | "
    "Data-driven energy efficiency"
)