import streamlit as st
import random
import time
import datetime
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Drone Telemetry Dashboard", layout="wide")

# Initialize session state
if "telemetry" not in st.session_state:
    st.session_state.telemetry = {
        "battery": [],
        "imu": {"roll": [], "pitch": [], "yaw": []},
        "temperature": [],
        "location": {"lat": [], "lon": []},
        "altitude": [],
        "status": [],
        "timestamps": [],
    }

# Update telemetry data
def update_data():
    new_data = {
        "battery": round(random.uniform(9.5, 12.5), 2),
        "imu": (
            round(random.uniform(-180, 180), 2),  # roll
            round(random.uniform(-90, 90), 2),    # pitch
            round(random.uniform(0, 360), 2),     # yaw
        ),
        "temperature": round(random.uniform(22.0, 40.0), 2),
        "location": (
            round(random.uniform(12.9, 13.1), 6),   # lat
            round(random.uniform(80.2, 80.4), 6),   # lon
        ),
        "altitude": round(random.uniform(50, 500), 2),
        "status": random.choice(["Excellent", "Good", "Poor", "No Signal"]),
        "timestamp": datetime.datetime.now().strftime('%H:%M:%S')
    }

    # Append to session state
    for key in st.session_state.telemetry:
        if key == "imu":
            for i, axis in enumerate(["roll", "pitch", "yaw"]):
                st.session_state.telemetry["imu"][axis].append(new_data["imu"][i])
        elif key == "location":
            st.session_state.telemetry["location"]["lat"].append(new_data["location"][0])
            st.session_state.telemetry["location"]["lon"].append(new_data["location"][1])
        elif key == "timestamps":
            st.session_state.telemetry["timestamps"].append(new_data["timestamp"])
        elif key == "status":
            st.session_state.telemetry["status"].append(new_data["status"])
        else:
            st.session_state.telemetry[key].append(new_data[key])

    # Keep only last 20
    for key in st.session_state.telemetry:
        if isinstance(st.session_state.telemetry[key], dict):
            for subkey in st.session_state.telemetry[key]:
                st.session_state.telemetry[key][subkey] = st.session_state.telemetry[key][subkey][-20:]
        else:
            st.session_state.telemetry[key] = st.session_state.telemetry[key][-20:]

    return new_data

# Main dashboard UI
st.title("🛰️ Drone Status Monitoring Dashboard")
data = update_data()

col1, col2, col3, col4 = st.columns(4)

# Extract roll, pitch, yaw
roll, pitch, yaw = data["imu"]

col1.metric("🔋 Battery (V)", f"{data['battery']} V")
col2.metric("🎯 Roll / Pitch / Yaw", f"{roll}° / {pitch}° / {yaw}°")
col3.metric("🌡️ Temp (°C)", f"{data['temperature']} °C")
col4.metric("⛰️ Altitude", f"{data['altitude']} m")

# Map location
st.subheader("📍 Drone GPS Location")
st.map(pd.DataFrame({
    'lat': [data['location'][0]],
    'lon': [data['location'][1]]
}))

# Connection status alert
st.subheader("📶 Connection Status")
connection = data['status']
if connection == "No Signal":
    st.error("🚨 Connection lost with drone!")
elif connection == "Poor":
    st.warning("⚠️ Poor signal detected.")
else:
    st.success(f"✅ Connection: {connection}")

# Telemetry charts
st.subheader("📊 Telemetry Charts (Last 20 Seconds)")
if len(st.session_state.telemetry["timestamps"]) > 1:
    df = pd.DataFrame({
        "Time": st.session_state.telemetry["timestamps"],
        "Battery Voltage": st.session_state.telemetry["battery"],
        "Temperature": st.session_state.telemetry["temperature"],
        "Altitude": st.session_state.telemetry["altitude"]
    })

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Time"], y=df["Battery Voltage"],
                             mode='lines+markers', name="Battery (V)", line=dict(color="orange")))
    fig.add_trace(go.Scatter(x=df["Time"], y=df["Temperature"],
                             mode='lines+markers', name="Temp (°C)", line=dict(color="red")))
    fig.add_trace(go.Scatter(x=df["Time"], y=df["Altitude"],
                             mode='lines+markers', name="Altitude (m)", line=dict(color="green")))
    fig.update_layout(xaxis_title="Time", yaxis_title="Value", height=400, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

# --- Enhancements Start Here ---

# 1. IMU Orientation Chart
with st.expander("📐 IMU Orientation Over Time"):
    imu_df = pd.DataFrame({
        "Time": st.session_state.telemetry["timestamps"],
        "Roll": st.session_state.telemetry["imu"]["roll"],
        "Pitch": st.session_state.telemetry["imu"]["pitch"],
        "Yaw": st.session_state.telemetry["imu"]["yaw"],
    })

    fig_imu = go.Figure()
    fig_imu.add_trace(go.Scatter(x=imu_df["Time"], y=imu_df["Roll"], mode='lines+markers', name="Roll", line=dict(color="cyan")))
    fig_imu.add_trace(go.Scatter(x=imu_df["Time"], y=imu_df["Pitch"], mode='lines+markers', name="Pitch", line=dict(color="magenta")))
    fig_imu.add_trace(go.Scatter(x=imu_df["Time"], y=imu_df["Yaw"], mode='lines+markers', name="Yaw", line=dict(color="yellow")))
    fig_imu.update_layout(xaxis_title="Time", yaxis_title="Degrees", template="plotly_dark", height=400)
    st.plotly_chart(fig_imu, use_container_width=True)

# 2. Connection Status Timeline
with st.expander("📶 Signal Strength Timeline"):
    signal_df = pd.DataFrame({
        "Time": st.session_state.telemetry["timestamps"],
        "Status": st.session_state.telemetry["status"]
    })

    status_color_map = {
        "Excellent": "green",
        "Good": "blue",
        "Poor": "orange",
        "No Signal": "red"
    }

    fig_status = go.Figure()
    fig_status.add_trace(go.Scatter(
        x=signal_df["Time"],
        y=[1]*len(signal_df),
        mode="markers",
        marker=dict(
            size=12,
            color=[status_color_map[s] for s in signal_df["Status"]]
        ),
        text=signal_df["Status"],
        hoverinfo="text"
    ))

    fig_status.update_layout(
        height=150,
        yaxis=dict(showticklabels=False),
        xaxis_title="Time",
        title="Connection Status Over Time",
        template="plotly_dark"
    )
    st.plotly_chart(fig_status, use_container_width=True)

# 3. Flight Duration Timer
if st.session_state.telemetry["timestamps"]:
    start_time = datetime.datetime.strptime(
        st.session_state.telemetry["timestamps"][0], '%H:%M:%S'
    ).time()
    now = datetime.datetime.now().time()
    elapsed = datetime.datetime.combine(datetime.date.today(), now) - datetime.datetime.combine(datetime.date.today(), start_time)
    st.info(f"🕒 **Flight Duration:** {str(elapsed).split('.')[0]}")

# --- Enhancements End ---

# Footer
st.markdown(
    "<center><sub>Made with ❤️ by Adarsh S R for Vayuputra Hackathon</sub></center>",
    unsafe_allow_html=True
)

# Auto-refresh every second
st_autorefresh(interval=1000, limit=None, key="dashboardrefresh")
