import streamlit as st
import requests

TUNNEL_URL = st.secrets["TUNNEL_URL"]
SECRET_TOKEN = st.secrets["SECRET_TOKEN"]

def send_to_backend(video_bytes):
    headers = {"X-Secret-Token": SECRET_TOKEN}
    response = requests.post(
        f"{TUNNEL_URL}/process",
        headers=headers,
        files={"video": video_bytes}
    )
    return response.json()

st.set_page_config(page_title="Haikyu Vision", layout="wide")
st.title("🏐 Haikyu Vision")
st.caption("Pepperdine × StatsPerform AI Hackathon")

uploaded = st.file_uploader("Upload practice video (.mp4)", type=["mp4"])

if uploaded:
    st.video(uploaded)
    with st.spinner("Sending to processing pipeline..."):
        response = requests.post(
            f"{TUNNEL_URL}/process",
            headers={"X-Secret-Token": SECRET_TOKEN},
            files={"video": uploaded.getvalue()}
        )
        if response.status_code == 200:
            st.success("Pipeline triggered!")
        else:
            st.error("Backend unreachable.")

st.sidebar.header("Search Plays")
play_type = st.sidebar.selectbox("Play Type", ["All", "Attack", "Set", "Dig", "Serve", "Block"])
player_id = st.sidebar.text_input("Player ID (optional)")
search = st.sidebar.button("Search")

if search:
    st.sidebar.info("Search results will appear here.")