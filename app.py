import streamlit as st
import time
import requests

def get_mock_search_results():
    return [
        {"ts": "0:03", "type": "Attack", "player": "Player 2"},
        {"ts": "0:11", "type": "Set",    "player": "Player 5"},
        {"ts": "0:18", "type": "Dig",    "player": "Player 3"},
        {"ts": "0:27", "type": "Attack", "player": "Player 1"},
        {"ts": "0:34", "type": "Serve",  "player": "Player 6"},
        {"ts": "0:41", "type": "Block",  "player": "Player 4"},
    ]

# ─────────────────────────────────────────────
# PAGE CONFIG  (must be first st call)
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Haikyu Vision",
    page_icon="🏐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# BACKEND CONFIG
# ─────────────────────────────────────────────
try:
    TUNNEL_URL = st.secrets["TUNNEL_URL"]
    SECRET_TOKEN = st.secrets["SECRET_TOKEN"]
except Exception:
    TUNNEL_URL = ""
    SECRET_TOKEN = ""

def send_to_backend(video_bytes):
    # Fallback simulation if secrets not populated
    if not TUNNEL_URL:
        time.sleep(2)
        return {"status": "success"}

    headers = {"X-Secret-Token": SECRET_TOKEN}
    try:
        response = requests.post(
            f"{TUNNEL_URL}/process",
            headers=headers,
            files={"video": video_bytes}
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print("Backend request failed:", e)
    return None

# ─────────────────────────────────────────────
# SESSION STATE DEFAULTS
# ─────────────────────────────────────────────
defaults = {
    "upload_status": None,      # None | "analyzing" | "confirmed" | "rejected"
    "show_overlay": False,
    "search_results": [],
    "selected_timestamp": None,
    "play_type": "All",
    "player_id": "",
    "video_bytes": None,
    "searching": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">

<style>
/* ── Reset & root vars ── */
:root {
    --bg:        #0F1923;
    --panel:     #111D2B;
    --navy:      #1A3C5E;
    --accent:    #2E6DA4;
    --accent-hi: #4A90D9;
    --green:     #1DB86A;
    --red:       #E53E3E;
    --amber:     #F6AD55;
    --text:      #E8EDF2;
    --muted:     #6B84A0;
    --border:    rgba(46,109,164,0.25);
    --glow:      rgba(46,109,164,0.18);
}

/* ── App shell ── */
.stApp {
    background: var(--bg);
    font-family: 'DM Sans', sans-serif;
    color: var(--text);
}

/* hide default Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding: 1.5rem 2rem 3rem 2rem !important;
    max-width: 1400px;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--panel) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.5rem;
}

/* ── Headings via markdown ── */
h1, h2, h3 {
    font-family: 'Barlow Condensed', sans-serif !important;
    letter-spacing: 0.04em;
}

/* ── Buttons ── */
.stButton > button {
    background: var(--accent) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 6px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    font-size: 0.78rem !important;
    padding: 0.55rem 1.4rem !important;
    transition: background 0.2s, box-shadow 0.2s !important;
    cursor: pointer !important;
}
.stButton > button:hover {
    background: var(--accent-hi) !important;
    box-shadow: 0 0 18px var(--glow) !important;
}
.stButton > button:active {
    transform: scale(0.98) !important;
}

/* ── Selectbox & text input ── */
.stSelectbox > div > div,
.stTextInput > div > div > input {
    background: #0D1820 !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 6px !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stSelectbox > div > div:hover,
.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px var(--glow) !important;
}
label {
    color: var(--muted) !important;
    font-size: 0.75rem !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: #0D1820 !important;
    border: 2px dashed var(--border) !important;
    border-radius: 12px !important;
    padding: 1rem !important;
    transition: border-color 0.2s !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--accent) !important;
}
[data-testid="stFileUploader"] label {
    color: var(--muted) !important;
}

/* ── Video player ── */
video {
    border-radius: 10px !important;
    width: 100% !important;
    background: #000 !important;
}
[data-testid="stVideo"] {
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 8px 40px rgba(0,0,0,0.5);
}

/* ── Divider ── */
hr {
    border-color: var(--border) !important;
    margin: 1.2rem 0 !important;
}

/* ── Spinner ── */
.stSpinner > div {
    border-top-color: var(--accent) !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div style="
    display:flex;
    align-items:center;
    gap:1.1rem;
    padding: 1.1rem 1.6rem 1.1rem 1.6rem;
    background: linear-gradient(135deg, #111D2B 0%, #0F1923 60%);
    border: 1px solid rgba(46,109,164,0.22);
    border-radius: 14px;
    margin-bottom: 1.6rem;
    box-shadow: 0 4px 32px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.04);
    position: relative;
    overflow: hidden;
">
    <!-- background accent line -->
    <div style="
        position:absolute; top:0; left:0; right:0; height:3px;
        background: linear-gradient(90deg, #2E6DA4, #4A90D9, #2E6DA4);
    "></div>

    <!-- icon -->
    <div style="
        font-size:2.6rem;
        line-height:1;
        filter: drop-shadow(0 0 14px rgba(74,144,217,0.55));
    ">🏐</div>

    <!-- text block -->
    <div>
        <div style="
            font-family: 'Barlow Condensed', sans-serif;
            font-size: 2.15rem;
            font-weight: 800;
            letter-spacing: 0.06em;
            color: #E8EDF2;
            line-height: 1.1;
            text-transform: uppercase;
        ">Haikyu Vision</div>
        <div style="
            font-family: 'DM Sans', sans-serif;
            font-size: 0.74rem;
            font-weight: 500;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: #4A90D9;
            margin-top: 1px;
        ">Pepperdine × StatsPerform &nbsp;·&nbsp; AI Practice Analysis</div>
    </div>

    <!-- right badge -->
    <div style="margin-left:auto; display:flex; gap:0.5rem; align-items:center;">
        <div style="
            background: rgba(46,109,164,0.15);
            border: 1px solid rgba(46,109,164,0.3);
            border-radius: 6px;
            padding: 0.3rem 0.8rem;
            font-family: 'DM Sans', sans-serif;
            font-size: 0.68rem;
            font-weight: 600;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: #4A90D9;
        ">⚡ AI-Powered</div>
        <div style="
            background: rgba(29,184,106,0.12);
            border: 1px solid rgba(29,184,106,0.3);
            border-radius: 6px;
            padding: 0.3rem 0.8rem;
            font-family: 'DM Sans', sans-serif;
            font-size: 0.68rem;
            font-weight: 600;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: #1DB86A;
        ">● Live</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR — SEARCH PANEL
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="
        font-family:'Barlow Condensed',sans-serif;
        font-size:1.25rem;
        font-weight:700;
        letter-spacing:0.1em;
        text-transform:uppercase;
        color:#E8EDF2;
        border-bottom: 2px solid rgba(46,109,164,0.35);
        padding-bottom: 0.6rem;
        margin-bottom: 1rem;
    ">🔍 &nbsp;Play Search</div>
    """, unsafe_allow_html=True)

    play_type = st.selectbox(
        "Play Type",
        ["All", "Attack", "Set", "Dig", "Serve", "Block"],
        index=["All", "Attack", "Set", "Dig", "Serve", "Block"].index(
            st.session_state.play_type
        ),
    )
    st.session_state.play_type = play_type

    player_id = st.text_input(
        "Player ID (optional)",
        value=st.session_state.player_id,
        placeholder="e.g. P2",
    )
    st.session_state.player_id = player_id

    st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)
    search_clicked = st.button("⚡  Search Plays", use_container_width=True)

    # ── SEARCH LOGIC ──
   if search_clicked:
    st.session_state.searching = True
    with st.spinner("Scanning footage..."):
        time.sleep(1.2)

        mock_results = get_search_results()

        filtered = [
            r for r in mock_results
            if (play_type == "All" or r["type"] == play_type) and
               (not player_id or player_id.lower() in r["player"].lower())
        ]

        st.session_state.search_results = filtered

    st.session_state.searching = False

    # ── SEARCH RESULTS ──
    if st.session_state.search_results:
        count = len(st.session_state.search_results)
        st.markdown(f"""
        <div style="
            margin-top:1rem;
            font-family:'DM Sans',sans-serif;
            font-size:0.7rem;
            font-weight:600;
            letter-spacing:0.1em;
            text-transform:uppercase;
            color:#6B84A0;
            margin-bottom:0.5rem;
        ">{count} result{'s' if count != 1 else ''} found</div>
        """, unsafe_allow_html=True)

        type_colors = {
            "Attack": "#E53E3E",
            "Set":    "#4A90D9",
            "Dig":    "#1DB86A",
            "Serve":  "#F6AD55",
            "Block":  "#9B59B6",
        }

        for i, r in enumerate(st.session_state.search_results):
            color = type_colors.get(r["type"], "#6B84A0")
            is_selected = st.session_state.selected_timestamp == r["ts"]
            bg = "rgba(46,109,164,0.18)" if is_selected else "rgba(255,255,255,0.03)"
            border = "#2E6DA4" if is_selected else "rgba(46,109,164,0.18)"

            # render result card
            st.markdown(f"""
            <div style="
                background:{bg};
                border:1px solid {border};
                border-radius:8px;
                padding:0.55rem 0.75rem;
                margin-bottom:0.4rem;
                cursor:pointer;
                transition: all 0.15s;
            ">
                <div style="display:flex;align-items:center;gap:0.5rem;">
                    <span style="
                        font-family:'Barlow Condensed',sans-serif;
                        font-size:1rem;
                        font-weight:700;
                        color:#E8EDF2;
                        min-width:2.5rem;
                    ">{r['ts']}</span>
                    <span style="
                        background:{color}22;
                        border:1px solid {color}66;
                        color:{color};
                        border-radius:4px;
                        padding:0.15rem 0.45rem;
                        font-size:0.65rem;
                        font-weight:700;
                        letter-spacing:0.08em;
                        text-transform:uppercase;
                        font-family:'DM Sans',sans-serif;
                    ">{r['type']}</span>
                </div>
                <div style="
                    font-family:'DM Sans',sans-serif;
                    font-size:0.72rem;
                    color:#6B84A0;
                    margin-top:0.2rem;
                ">{r['player']}</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"▶  Jump to {r['ts']}", key=f"ts_{i}", use_container_width=True):
                st.session_state.selected_timestamp = r["ts"]
                st.rerun()

    elif search_clicked:
        st.markdown("""
        <div style="
            margin-top:1rem;
            background:rgba(229,62,62,0.08);
            border:1px solid rgba(229,62,62,0.25);
            border-radius:8px;
            padding:0.8rem 1rem;
            font-family:'DM Sans',sans-serif;
            font-size:0.82rem;
            color:#E88080;
        ">No plays matched your filter.</div>
        """, unsafe_allow_html=True)

    # ── Sidebar footer ──
    st.markdown("""
    <div style="
        position:absolute;
        bottom:1.5rem;
        left:1rem;
        right:1rem;
        font-family:'DM Sans',sans-serif;
        font-size:0.65rem;
        color:#364D63;
        text-align:center;
        letter-spacing:0.06em;
    ">Haikyu Vision · StatsPerform API</div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# MAIN LAYOUT  — two columns
# ─────────────────────────────────────────────
left_col, right_col = st.columns([3, 2], gap="large")

# ══════════════════════════════════════════════
# LEFT — Upload + Video Player
# ══════════════════════════════════════════════
with left_col:

    # ── Section label ──
    st.markdown("""
    <div style="
        font-family:'Barlow Condensed',sans-serif;
        font-size:1.05rem;
        font-weight:700;
        letter-spacing:0.12em;
        text-transform:uppercase;
        color:#6B84A0;
        margin-bottom:0.6rem;
    ">📹 &nbsp;Footage Input</div>
    """, unsafe_allow_html=True)

    # ── Upload zone ──
    uploaded = st.file_uploader(
        "Drag & drop your practice recording here, or click to browse",
        type=["mp4"],
        label_visibility="visible",
    )

    # ── Status indicator ──
    if uploaded and st.session_state.upload_status is None:
        st.session_state.upload_status = "analyzing"
        st.session_state.video_bytes = uploaded

    if uploaded:
        status = st.session_state.upload_status

        if status == "analyzing":
            with st.spinner(""):
                st.markdown("""
                <div style="
                    display:flex; align-items:center; gap:0.75rem;
                    background: rgba(246,173,85,0.08);
                    border: 1px solid rgba(246,173,85,0.3);
                    border-radius:10px;
                    padding: 0.8rem 1.1rem;
                    font-family:'DM Sans',sans-serif;
                    font-size:0.88rem;
                    color:#F6AD55;
                    margin: 0.8rem 0;
                ">
                    <span style="font-size:1.1rem">🔄</span>
                    <div>
                        <div style="font-weight:600">Analyzing footage...</div>
                        <div style="font-size:0.72rem;color:#A07030;margin-top:2px">
                            Sending pipeline request to processing backend ...
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # ACTUAL BACKEND CONNECTION
                res = send_to_backend(uploaded.getvalue())
                
                if res is not None:
                    st.session_state.upload_status = "confirmed"
                else:
                    st.session_state.upload_status = "rejected"
                    
                st.rerun()

        elif status == "confirmed":
            st.markdown("""
            <div style="
                display:flex; align-items:center; gap:0.75rem;
                background: rgba(29,184,106,0.08);
                border: 1px solid rgba(29,184,106,0.3);
                border-radius:10px;
                padding: 0.8rem 1.1rem;
                font-family:'DM Sans',sans-serif;
                font-size:0.88rem;
                color:#1DB86A;
                margin: 0.8rem 0;
            ">
                <span style="font-size:1.2rem">✅</span>
                <div>
                    <div style="font-weight:600">6v6 session confirmed</div>
                    <div style="font-size:0.72rem;color:#0F8044;margin-top:2px">
                        Formation detected · Ready to search plays
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        elif status == "rejected":
            st.markdown("""
            <div style="
                display:flex; align-items:center; gap:0.75rem;
                background: rgba(229,62,62,0.08);
                border: 1px solid rgba(229,62,62,0.3);
                border-radius:10px;
                padding: 0.8rem 1.1rem;
                font-family:'DM Sans',sans-serif;
                font-size:0.88rem;
                color:#E53E3E;
                margin: 0.8rem 0;
            ">
                <span style="font-size:1.2rem">❌</span>
                <div>
                    <div style="font-weight:600">Analysis Failed</div>
                    <div style="font-size:0.72rem;color:#A02020;margin-top:2px">
                        The backend API encountered an error.
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Video Player ──
    if uploaded:
        st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="
            font-family:'Barlow Condensed',sans-serif;
            font-size:1.05rem;
            font-weight:700;
            letter-spacing:0.12em;
            text-transform:uppercase;
            color:#6B84A0;
            margin-bottom:0.5rem;
        ">▶ &nbsp;Video Playback</div>
        """, unsafe_allow_html=True)

        # timestamp jump info
        if st.session_state.selected_timestamp:
            st.markdown(f"""
            <div style="
                display:inline-flex; align-items:center; gap:0.5rem;
                background:rgba(46,109,164,0.15);
                border:1px solid rgba(46,109,164,0.35);
                border-radius:6px;
                padding:0.3rem 0.8rem;
                font-family:'DM Sans',sans-serif;
                font-size:0.76rem;
                color:#4A90D9;
                margin-bottom:0.5rem;
            ">
                📍 Jumped to {st.session_state.selected_timestamp}
            </div>
            """, unsafe_allow_html=True)

        # video display
        if st.session_state.show_overlay:
            # overlay_video would come from backend — show placeholder for now
            st.video(uploaded)
            st.markdown("""
            <div style="
                background:rgba(74,144,217,0.1);
                border:1px solid rgba(74,144,217,0.3);
                border-radius:6px;
                padding:0.35rem 0.8rem;
                font-family:'DM Sans',sans-serif;
                font-size:0.73rem;
                color:#4A90D9;
                margin-top:0.4rem;
                display:inline-block;
            ">🎯 Ball trajectory overlay active (overlay video will load from backend)</div>
            """, unsafe_allow_html=True)
        else:
            st.video(uploaded)

        # ── Trajectory Toggle ──
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        toggle_label = "Hide Ball Trajectory" if st.session_state.show_overlay else "Show Ball Trajectory"
        toggle_icon  = "🔵" if st.session_state.show_overlay else "⚪"
        active_style = (
            "background:rgba(74,144,217,0.2); border:1.5px solid #4A90D9; color:#4A90D9;"
            if st.session_state.show_overlay
            else "background:rgba(255,255,255,0.04); border:1.5px solid rgba(46,109,164,0.3); color:#6B84A0;"
        )

        st.markdown(f"""
        <style>
        div[data-testid="stHorizontalBlock"] .stButton:first-child > button {{
            {active_style}
            font-size:0.8rem !important;
            padding: 0.5rem 1.2rem !important;
        }}
        </style>
        """, unsafe_allow_html=True)

        tog_col, _ = st.columns([1, 2])
        with tog_col:
            if st.button(f"{toggle_icon} {toggle_label}", key="trajectory_toggle"):
                with st.spinner("Switching view..."):
                    time.sleep(0.6)
                st.session_state.show_overlay = not st.session_state.show_overlay
                st.rerun()

    elif not uploaded:
        # empty state
        st.markdown("""
        <div style="
            display:flex;
            flex-direction:column;
            align-items:center;
            justify-content:center;
            min-height:200px;
            background:rgba(255,255,255,0.02);
            border:1px dashed rgba(46,109,164,0.2);
            border-radius:12px;
            margin-top:1rem;
            padding:2rem;
            text-align:center;
        ">
            <div style="font-size:2.8rem;margin-bottom:0.75rem;opacity:0.4">🏐</div>
            <div style="
                font-family:'Barlow Condensed',sans-serif;
                font-size:1.1rem;
                font-weight:600;
                color:#3A5570;
                letter-spacing:0.08em;
                text-transform:uppercase;
            ">No footage loaded</div>
            <div style="
                font-family:'DM Sans',sans-serif;
                font-size:0.78rem;
                color:#2E4458;
                margin-top:0.4rem;
            ">Upload an .mp4 file above to begin analysis</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Reset button (utility) ──
    if uploaded:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        if st.button("↺  Reset Session", key="reset"):
            for k, v in defaults.items():
                st.session_state[k] = v
            st.rerun()


# ══════════════════════════════════════════════
# RIGHT — Stats & Results Panel
# ══════════════════════════════════════════════
with right_col:

    st.markdown("""
    <div style="
        font-family:'Barlow Condensed',sans-serif;
        font-size:1.05rem;
        font-weight:700;
        letter-spacing:0.12em;
        text-transform:uppercase;
        color:#6B84A0;
        margin-bottom:0.6rem;
    ">📊 &nbsp;Session Overview</div>
    """, unsafe_allow_html=True)

    # ── Stats cards ──
    stat_data = [
        ("Total Plays",  "—" if not st.session_state.search_results else str(len(st.session_state.search_results)), "#4A90D9"),
        ("Play Type",    st.session_state.play_type, "#1DB86A"),
        ("Players Tagged", "—" if not st.session_state.player_id else st.session_state.player_id, "#F6AD55"),
    ]

    cols = st.columns(3)
    for col, (label, value, color) in zip(cols, stat_data):
        with col:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, rgba(26,60,94,0.3), rgba(15,25,35,0.6));
                border: 1px solid rgba(46,109,164,0.22);
                border-top: 3px solid {color};
                border-radius:10px;
                padding:0.9rem 0.8rem;
                text-align:center;
            ">
                <div style="
                    font-family:'Barlow Condensed',sans-serif;
                    font-size:1.75rem;
                    font-weight:800;
                    color:{color};
                    line-height:1;
                ">{value}</div>
                <div style="
                    font-family:'DM Sans',sans-serif;
                    font-size:0.65rem;
                    font-weight:600;
                    color:#6B84A0;
                    letter-spacing:0.1em;
                    text-transform:uppercase;
                    margin-top:0.35rem;
                ">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)

    # ── Results card list ──
    st.markdown("""
    <div style="
        font-family:'Barlow Condensed',sans-serif;
        font-size:1.05rem;
        font-weight:700;
        letter-spacing:0.12em;
        text-transform:uppercase;
        color:#6B84A0;
        margin-bottom:0.6rem;
        border-top:1px solid rgba(46,109,164,0.2);
        padding-top:1rem;
    ">🗂 &nbsp;Play Results</div>
    """, unsafe_allow_html=True)

    type_colors = {
        "Attack": "#E53E3E",
        "Set":    "#4A90D9",
        "Dig":    "#1DB86A",
        "Serve":  "#F6AD55",
        "Block":  "#9B59B6",
    }
    type_icons = {
        "Attack": "⚡",
        "Set":    "🔷",
        "Dig":    "🛡",
        "Serve":  "🏐",
        "Block":  "🧱",
    }

    if st.session_state.search_results:
        for i, r in enumerate(st.session_state.search_results):
            color = type_colors.get(r["type"], "#6B84A0")
            icon  = type_icons.get(r["type"], "●")
            is_sel = st.session_state.selected_timestamp == r["ts"]
            sel_glow = f"box-shadow: 0 0 0 2px {color}44;" if is_sel else ""
            sel_bg   = f"rgba(46,109,164,0.15)" if is_sel else "rgba(255,255,255,0.025)"

            st.markdown(f"""
            <div style="
                background:{sel_bg};
                border:1px solid {'rgba(46,109,164,0.45)' if is_sel else 'rgba(46,109,164,0.15)'};
                border-left: 4px solid {color};
                border-radius:8px;
                padding: 0.75rem 1rem;
                margin-bottom:0.5rem;
                {sel_glow}
            ">
                <div style="display:flex; align-items:flex-start; justify-content:space-between;">
                    <div>
                        <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.2rem;">
                            <span style="font-size:0.95rem">{icon}</span>
                            <span style="
                                font-family:'Barlow Condensed',sans-serif;
                                font-size:1.05rem;
                                font-weight:700;
                                color:#E8EDF2;
                            ">{r['type']}</span>
                            {'<span style="font-size:0.65rem;background:#2E6DA4;color:#fff;border-radius:4px;padding:1px 6px;margin-left:4px;font-family:DM Sans;font-weight:600;">SELECTED</span>' if is_sel else ''}
                        </div>
                        <div style="
                            font-family:'DM Sans',sans-serif;
                            font-size:0.75rem;
                            color:#6B84A0;
                        ">{r['player']}</div>
                    </div>
                    <div style="
                        font-family:'Barlow Condensed',sans-serif;
                        font-size:1.4rem;
                        font-weight:800;
                        color:{color};
                        line-height:1;
                        margin-top:0.1rem;
                    ">{r['ts']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    elif not st.session_state.search_results and not search_clicked:
        st.markdown("""
        <div style="
            display:flex;
            flex-direction:column;
            align-items:center;
            text-align:center;
            padding:2.5rem 1.5rem;
            background:rgba(255,255,255,0.015);
            border:1px dashed rgba(46,109,164,0.15);
            border-radius:12px;
        ">
            <div style="font-size:2rem;margin-bottom:0.6rem;opacity:0.35">🔍</div>
            <div style="
                font-family:'Barlow Condensed',sans-serif;
                font-size:1rem;
                font-weight:700;
                letter-spacing:0.08em;
                text-transform:uppercase;
                color:#2E4458;
            ">Awaiting Search</div>
            <div style="
                font-family:'DM Sans',sans-serif;
                font-size:0.75rem;
                color:#1E3348;
                margin-top:0.4rem;
                max-width:200px;
            ">Use the sidebar to filter plays and jump to key moments</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Play breakdown chart (static visual) ──
    if st.session_state.search_results:
        st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="
            font-family:'Barlow Condensed',sans-serif;
            font-size:1.05rem;
            font-weight:700;
            letter-spacing:0.12em;
            text-transform:uppercase;
            color:#6B84A0;
            margin-bottom:0.6rem;
            border-top:1px solid rgba(46,109,164,0.2);
            padding-top:1rem;
        ">📈 &nbsp;Play Breakdown</div>
        """, unsafe_allow_html=True)

        # count by type
        from collections import Counter
        counts = Counter(r["type"] for r in st.session_state.search_results)
        total = len(st.session_state.search_results)

        for ptype, cnt in sorted(counts.items(), key=lambda x: -x[1]):
            pct = int((cnt / total) * 100)
            color = type_colors.get(ptype, "#6B84A0")
            icon  = type_icons.get(ptype, "●")
            st.markdown(f"""
            <div style="margin-bottom:0.55rem;">
                <div style="
                    display:flex;
                    justify-content:space-between;
                    font-family:'DM Sans',sans-serif;
                    font-size:0.75rem;
                    color:#9AAABB;
                    margin-bottom:0.25rem;
                ">
                    <span>{icon} {ptype}</span>
                    <span style="color:{color};font-weight:600">{cnt} play{'s' if cnt!=1 else ''}</span>
                </div>
                <div style="
                    background:rgba(255,255,255,0.06);
                    border-radius:4px;
                    height:6px;
                    overflow:hidden;
                ">
                    <div style="
                        width:{pct}%;
                        height:100%;
                        background: linear-gradient(90deg, {color}99, {color});
                        border-radius:4px;
                        transition:width 0.4s ease;
                    "></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
