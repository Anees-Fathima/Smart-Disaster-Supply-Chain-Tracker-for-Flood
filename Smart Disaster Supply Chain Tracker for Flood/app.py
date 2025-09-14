import streamlit as st
import pandas as pd
import joblib
import folium
from streamlit_folium import st_folium
import os

# Load trained Random Forest model
rf = joblib.load("random_forest_supply_priority.pkl")

# History CSV file
history_file = "prediction_history.csv"

# Initialize session state
if 'history' not in st.session_state:
    if os.path.exists(history_file):
        st.session_state.history = pd.read_csv(history_file).to_dict(orient='records')
    else:
        st.session_state.history = []

if 'last_prediction' not in st.session_state:
    st.session_state.last_prediction = None

# Streamlit Layout
st.set_page_config(page_title="🌊 Smart Disaster Supply Chain", layout="wide")
st.title("🌊 Smart Disaster Supply Chain - Flood Risk Tracker")

# Sidebar inputs
st.sidebar.title("🌊 Flood Risk Predictor Inputs")
impact_score = st.sidebar.number_input("Impact Score", 0.0, 1.0, 0.5, step=0.1)
flood_count = st.sidebar.number_input("Flood Count", 0, 50, 5)
dfsi = st.sidebar.number_input("DFSI", 0.0, 1.0, 0.5, step=0.1)
population_density = st.sidebar.number_input("Population Density", 0, 10000, 500)
fatalities_per_1000 = st.sidebar.number_input("Fatalities per 1000", 0.0, 1.0, 0.0, step=0.01)
injured_per_1000 = st.sidebar.number_input("Injured per 1000", 0.0, 1.0, 0.0, step=0.01)
event_impact = st.sidebar.number_input("Event Impact", 0.0, 1.0, 0.5, step=0.1)
avg_flood_duration = st.sidebar.number_input("Avg Flood Duration", 0, 100, 5)
max_flood_duration = st.sidebar.number_input("Max Flood Duration", 0, 100, 10)
total_flood_duration = st.sidebar.number_input("Total Flood Duration", 0, 500, 20)

# Sidebar radio buttons
action = st.sidebar.radio("Choose Action", ["Predict Risk", "View Dashboard"])

# Location input
st.sidebar.subheader("📍 Choose Location")
tab1, tab2 = st.sidebar.tabs(["Type Coordinates", "Pick on Map"])
with tab1:
    latitude = st.number_input("Latitude", -90.0, 90.0, 13.0)
    longitude = st.number_input("Longitude", -180.0, 180.0, 80.0)
with tab2:
    st.write("Click on the map to select location")
    m = folium.Map(location=[20, 80], zoom_start=4)
    map_data = st_folium(m, height=300, width=400)
    if map_data and map_data.get("last_clicked"):
        latitude = map_data["last_clicked"]["lat"]
        longitude = map_data["last_clicked"]["lng"]
        st.sidebar.success(f"Selected: {latitude:.4f}, {longitude:.4f}")

# Predict Risk
if action == "Predict Risk":
    st.header("🔍 Predict Flood Risk")
    
    if st.button("Predict"):
        new_data = pd.DataFrame({
            'Impact_Score': [impact_score],
            'Flood_Count': [flood_count],
            'DFSI': [dfsi],
            'Population_Density': [population_density],
            'Fatalities_per_1000': [fatalities_per_1000],
            'Injured_per_1000': [injured_per_1000],
            'Event_Impact': [event_impact],
            'Avg_Flood_Duration': [avg_flood_duration],
            'Max_Flood_Duration': [max_flood_duration],
            'Total_Flood_Duration': [total_flood_duration]
        })

        # Predict
        pred = rf.predict(new_data)[0]
        probs = rf.predict_proba(new_data)[0]
        confidence = max(probs) * 100
        risk_map = {0: "Low", 1: "Moderate", 2: "High"}
        risk_label = risk_map.get(pred, pred)

        # Recommended actions
        actions_dict = {
            "Low": ["Monitor weather updates", "Prepare basic supplies"],
            "Moderate": ["Alert local authorities", "Preposition relief materials", "Mobilize volunteers"],
            "High": ["Evacuate vulnerable populations", "Deploy emergency response teams", "Distribute food & medical supplies"]
        }
        recommended_actions = actions_dict.get(risk_label, [])

        # Store in session state
        st.session_state.last_prediction = {
            "Impact_Score": impact_score,
            "Flood_Count": flood_count,
            "DFSI": dfsi,
            "Population_Density": population_density,
            "Fatalities_per_1000": fatalities_per_1000,
            "Injured_per_1000": injured_per_1000,
            "Event_Impact": event_impact,
            "Avg_Flood_Duration": avg_flood_duration,
            "Max_Flood_Duration": max_flood_duration,
            "Total_Flood_Duration": total_flood_duration,
            "Latitude": latitude,
            "Longitude": longitude,
            "Risk_Level": risk_label,
            "Confidence": confidence,
            "Recommended_Actions": recommended_actions
        }
        # Append to history
        st.session_state.history.append(st.session_state.last_prediction)
        # Save to CSV
        df_record = pd.DataFrame([st.session_state.last_prediction])
        if os.path.exists(history_file):
            df_record.to_csv(history_file, mode='a', header=False, index=False)
        else:
            df_record.to_csv(history_file, index=False)

    # Display last prediction persistently
    if st.session_state.last_prediction:
        pred = st.session_state.last_prediction
        st.subheader("📊 Prediction Result")
        st.write(f"**Risk Level:** {pred['Risk_Level']}")
        st.write(f"**Confidence:** {pred['Confidence']:.2f}%")
        st.write(f"**Location:** {pred['Latitude']:.4f}, {pred['Longitude']:.4f}")
        st.write("**Recommended Actions:**")
        for act in pred['Recommended_Actions']:
            st.write(f"- {act}")
        # Map
        m2 = folium.Map(location=[pred['Latitude'], pred['Longitude']], zoom_start=6)
        color_map = {"Low": "green", "Moderate": "orange", "High": "red"}
        folium.Marker(
            [pred['Latitude'], pred['Longitude']],
            popup=f"{pred['Risk_Level']} Risk ({pred['Confidence']:.1f}%)",
            icon=folium.Icon(color=color_map.get(pred['Risk_Level'], "blue"))
        ).add_to(m2)
        st_folium(m2, height=400, width=700)


# View Dashboard
if action == "View Dashboard":
    st.header("📊 Flood Supply Chain Dashboard")
    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)
        st.subheader("Previous Predictions (All Sessions)")
        st.dataframe(df)

        # Map
        m3 = folium.Map(location=[20, 80], zoom_start=4)
        color_map = {"Low": "green", "Moderate": "orange", "High": "red"}
        for idx, row in df.iterrows():
            folium.CircleMarker(
                location=[row["Latitude"], row["Longitude"]],
                radius=8,
                color=color_map.get(row["Risk_Level"], "blue"),
                fill=True,
                fill_color=color_map.get(row["Risk_Level"], "blue"),
                popup=(f"Risk: {row['Risk_Level']}<br>"
                       f"Confidence: {row['Confidence']:.1f}%")
            ).add_to(m3)
        st.subheader("Risk Map")
        st_folium(m3, height=500, width=700)
    else:
        st.write("No prediction history available yet.")
