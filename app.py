import streamlit as st
import joblib
import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model

st.set_page_config(
    page_title="Network Intrusion Detection System",
    page_icon="🛡️",
    layout="centered"
)

# Custom styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0;
    }
    .subtitle {
        color: #888;
        font-size: 1rem;
        margin-top: 0;
        margin-bottom: 1.5rem;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_all_models():
    autoencoder = load_model('autoencoder_model.keras')
    xgb_model = joblib.load('xgb_model.pkl')
    scaler = joblib.load('scaler.pkl')
    le = joblib.load('label_encoder.pkl')
    threshold = joblib.load('threshold.pkl')
    feature_columns = joblib.load('feature_columns.pkl')
    default_values = joblib.load('default_values.pkl')
    return autoencoder, xgb_model, scaler, le, threshold, feature_columns, default_values

autoencoder, xgb_model, scaler, le, threshold, feature_columns, default_values = load_all_models()

st.markdown('<p class="main-title">🛡️ Network Intrusion Detection System</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">A two-stage ML pipeline: Autoencoder anomaly detection + XGBoost attack classification</p>', unsafe_allow_html=True)

st.sidebar.header("Connection Parameters")

duration = st.sidebar.number_input("Duration (seconds)", min_value=0, value=0)
src_bytes = st.sidebar.number_input("Source Bytes", min_value=0, value=0)
dst_bytes = st.sidebar.number_input("Destination Bytes", min_value=0, value=0)
count = st.sidebar.number_input("Connection Count (last 2s)", min_value=0, value=0)

protocol_choice = st.sidebar.selectbox("Protocol Type", ["tcp", "udp", "icmp"])
flag_choice = st.sidebar.selectbox("Connection Flag", ["SF", "S0", "REJ", "RSTR", "RSTO"])

st.sidebar.markdown("---")
analyze_button = st.sidebar.button("🔍 Analyze Connection", use_container_width=True)

if analyze_button:
    input_row = default_values.copy()
    input_row['duration'] = duration
    input_row['src_bytes'] = src_bytes
    input_row['dst_bytes'] = dst_bytes
    input_row['count'] = count

    for col in feature_columns:
        if col.startswith('protocol_type_'):
            input_row[col] = 0
    input_row[f'protocol_type_{protocol_choice}'] = 1

    for col in feature_columns:
        if col.startswith('flag_'):
            input_row[col] = 0
    input_row[f'flag_{flag_choice}'] = 1

    input_df = pd.DataFrame([input_row])[feature_columns]
    input_scaled = scaler.transform(input_df)

    reconstructed = autoencoder.predict(input_scaled, verbose=0)
    error = np.mean(np.square(input_scaled - reconstructed))

    col1, col2 = st.columns(2)
    col1.metric("Reconstruction Error", f"{error:.4f}")
    col2.metric("Decision Threshold", f"{threshold:.4f}")

    st.markdown("---")

    if error <= threshold:
        st.success("✅ **Normal Connection** — No suspicious behavior detected.")
    else:
        st.error("⚠️ **Suspicious Connection Detected**")
        attack_pred_encoded = xgb_model.predict(input_scaled)
        attack_pred_label = le.inverse_transform(attack_pred_encoded)[0]
        st.warning(f"**Predicted Attack Type:** {attack_pred_label}")
else:
    st.info("👈 Enter connection parameters in the sidebar and click **Analyze Connection**.")