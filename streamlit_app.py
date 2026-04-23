import streamlit as st
import time
import random
import json
import os
import urllib.parse
import secrets
import re
from datetime import datetime
from fpdf import FPDF

# --- Page Configuration (Mobile-First) ---
st.set_page_config(
    page_title="Nyx",
    page_icon="🤍",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items=None
)

# --- Cosmic Pearl Theme: iOS 18 Glass, Light, Spatial Layers ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital@0;1&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Courier+Prime&display=swap');

    :root {
        --pearl: #F9F6F0;
        --champagne: #E8D5B5;
        --rose-gold: #D4A5A5;
        --warm-charcoal: #2C2A28;
        --taupe: #7A7672;
        --glass-border: rgba(255,255,255,0.6);
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background: var(--pearl);
        color: var(--warm-charcoal);
    }

    .stApp {
        background: radial-gradient(circle at 50% 30%, rgba(232,213,181,0.2) 0%, var(--pearl) 80%);
        background-image: url('data:image/svg+xml;utf8,<svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><rect width="100" height="100" fill="none" stroke="%23E8E0D5" stroke-width="0.3" opacity="0.15"/></svg>');
    }

    [data-testid="stSidebar"] { display: none; }
    footer { display: none; }
    .main .block-container {
        padding: 0 !important;
        max-width: 100% !important;
        margin: 0 !important;
    }

    /* ----- LAYER 1: Persistent Left Rail (Frosted Glass) ----- */
    .left-rail {
        position: fixed;
        left: 0;
        top: 0;
        bottom: 0;
        width: 64px;
        background: rgba(255, 255, 255, 0.55);
        backdrop-filter: blur(25px);
        -webkit-backdrop-filter: blur(25px);
        border-right: 0.5px solid var(--glass-border);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: space-between;
        padding: 24px 0 16px 0;
        z-index: 100;
        box-shadow: 8px 0 30px rgba(0,0,0,0.02);
    }

    .rail-logo {
        writing-mode: vertical-rl;
        text-orientation: mixed;
        font-family: 'Playfair Display', serif;
        font-style: italic;
        font-size: 22px;
        font-weight: 500;
        background: linear-gradient(145deg, var(--rose-gold), var(--champagne));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: 6px;
        transform: rotate(180deg);
    }

    .agent-orbs {
        display: flex;
        flex-direction: column;
        gap: 14px;
        align-items: center;
    }

    .orb {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: rgba(255,255,255,0.7);
        backdrop-filter: blur(8px);
        border: 0.5px solid var(--glass-border);
        box-shadow: 0 4px 10px rgba(0,0,0,0.02);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        animation: breathe 3s infinite ease-in-out;
        transition: transform 0.15s;
    }
    .orb:active { transform: scale(0.92); }

    @keyframes breathe {
        0%, 100% { opacity: 0.8; box-shadow: 0 0 5px var(--rose-gold); }
        50% { opacity: 1; box-shadow: 0 0 12px var(--champagne); }
    }

    .live-badge {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        font-family: 'Inter', sans-serif;
        font-weight: 300;
        font-size: 11px;
        letter-spacing: 2px;
        color: var(--taupe);
    }
    .live-dot {
        width: 8px;
        height: 8px;
        background: #8EC0B5;
        border-radius: 50%;
        box-shadow: 0 0 12px #A8D8CC;
    }

    /* ----- LAYER 2: Main Stage (Floating Cards) ----- */
    .main-stage {
        margin-left: 64px;
        padding: 20px 16px 90px 16px;
        display: flex;
        flex-direction: column;
        gap: 24px;
    }

    .topic-card {
        background: rgba(255, 255, 255, 0.55);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 36px;
        padding: 28px 24px;
        border: 0.5px solid var(--glass-border);
        box-shadow: 0 15px 35px -10px rgba(0,0,0,0.04);
        text-align: center;
    }

    .topic-text {
        font-family: 'Playfair Display', serif;
        font-style: italic;
        font-size: 26px;
        line-height: 1.3;
        background: linear-gradient(145deg, var(--rose-gold), #B58D8D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }

    .debate-card {
        background: rgba(255, 255, 255, 0.5);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 28px;
        padding: 20px 22px;
        margin-bottom: 14px;
        border-left: 5px solid;
        border-image: none;
        box-shadow: 0 10px 25px -8px rgba(0,0,0,0.03);
        transition: transform 0.2s;
    }

    .card-skeptic { border-left-color: #D4A5A5; }
    .card-optimist { border-left-color: #B5C9B5; }
    .card-moderator { border-left-color: #C5B5D4; }
    .card-philosopher { border-left-color: #D4B5A5; }
    .card-futurist { border-left-color: #A5C9D4; }
    .card-data { border-left-color: #A5D4C0; }
    .card-ethicist { border-left-color: #D4A5C0; }

    .agent-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 10px;
        font-weight: 500;
        color: var(--warm-charcoal);
    }

    .agent-message {
        font-family: 'Inter', sans-serif;
        font-weight: 350;
        font-size: 15px;
        line-height: 1.5;
        color: var(--warm-charcoal);
        padding-left: 6px;
    }

    .round-separator {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 16px;
        margin: 8px 0 16px;
    }
    .separator-line {
        flex: 1;
        height: 0.5px;
        background: linear-gradient(90deg, transparent, var(--taupe), transparent);
    }
    .dot-sequence {
        font-size: 10px;
        letter-spacing: 4px;
        color: var(--rose-gold);
    }

    /* ----- LAYER 3: Floating Action Dock ----- */
    .action-dock {
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        margin-left: 32px;
        width: calc(100% - 96px);
        max-width: 380px;
        height: 60px;
        background: rgba(255, 255, 255, 0.65);
        backdrop-filter: blur(30px);
        -webkit-backdrop-filter: blur(30px);
        border-radius: 60px;
        border: 0.5px solid var(--glass-border);
        box-shadow: 0 20px 40px -10px rgba(0,0,0,0.05), 0 0 0 1px rgba(255,255,255,0.5) inset;
        display: flex;
        align-items: center;
        justify-content: space-evenly;
        padding: 0 8px;
        z-index: 200;
    }

    .dock-icon {
        width: 48px;
        height: 48px;
        border-radius: 48px;
        background: transparent;
        border: none;
        font-size: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.15s;
        color: var(--warm-charcoal);
    }
    .dock-icon:active {
        background: rgba(255,255,255,0.5);
        transform: scale(0.9);
    }

    /* ----- Popover / Modal (Stats hidden behind (i)) ----- */
    .stats-popover {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(40px);
        border-radius: 36px;
        padding: 20px;
        border: 0.5px solid var(--glass-border);
    }

    /* ----- Streamlit Overrides ----- */
    .stButton > button {
        background: transparent;
        border: none;
        font-size: 24px;
        padding: 12px;
    }
    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.5);
        border: 0.5px solid var(--glass-border);
        border-radius: 40px;
        padding: 16px 20px;
        font-family: 'Inter', sans-serif;
        backdrop-filter: blur(10px);
    }
    .stSelectbox > div > div {
        background: transparent !important;
        border: none !important;
    }
    [data-testid="stExpander"] details {
        background: transparent;
        border: none;
    }
</style>
""", unsafe_allow_html=True)
# --- Session State & Constants ---
if "agent_stats" not in st.session_state:
    st.session_state.agent_stats = {
        "Harsh": {"wins": 0, "losses": 0}, "Jayant": {"wins": 0, "losses": 0},
        "Philosopher": {"wins": 0, "losses": 0}, "Futurist": {"wins": 0, "losses": 0},
        "DataScientist": {"wins": 0, "losses": 0}, "Ethicist": {"wins": 0, "losses": 0},
    }
if "current_topic" not in st.session_state:
    st.session_state.current_topic = "Should AI have a conscience?"
if "global_arguments" not in st.session_state:
    st.session_state.global_arguments = []

# Models
AVAILABLE_MODELS = {
    "🤍 Groq": {"provider": "groq", "model": "llama-3.3-70b-versatile", "type": "openai", "base_url": "https://api.groq.com/openai/v1"},
    "🤍 DeepSeek": {"provider": "deepseek", "model": "deepseek-chat", "type": "openai", "base_url": "https://api.deepseek.com"},
}
PROVIDER_API_KEYS = {
    "groq": st.secrets.get("GROQ_API_KEY", ""),
    "deepseek": st.secrets.get("DEEPSEEK_API_KEY", ""),
}

def get_client(selected_model):
    config = AVAILABLE_MODELS[selected_model]
    key = PROVIDER_API_KEYS[config["provider"]]
    from openai import OpenAI
    return OpenAI(api_key=key, base_url=config["base_url"]), config["model"]

# --- Agents ---
class Agent:
    def __init__(self, name, role, personality, avatar, card_class):
        self.name, self.role, self.personality, self.avatar, self.card_class = name, role, personality, avatar, card_class
        self.history = []
    def speak(self, topic, last_msg, round_num, client, model):
        history = "\n".join(self.history[-2:])
        prompt = f"You are {self.name} ({self.role}). {self.personality}\nDebate round {round_num} on '{topic}'.\nHistory: {history}\nLast: '{last_msg}'\nRespond in 2-4 sentences with Claim/Reasoning."
        resp = client.chat.completions.create(model=model, messages=[{"role":"user","content":prompt}], temperature=0.7, max_tokens=200)
        reply = resp.choices[0].message.content
        self.history.append(reply)
        return reply

def create_panel():
    return [
        Agent("Harsh", "Skeptic", "Finds flaws.", "🔴", "card-skeptic"),
        Agent("Jayant", "Optimist", "Sees opportunity.", "🟢", "card-optimist"),
        Agent("Philosopher", "Philosopher", "Ethical lens.", "🟤", "card-philosopher"),
        Agent("Futurist", "Futurist", "Long-term view.", "🔮", "card-futurist"),
        Agent("DataScientist", "Data Sci", "Evidence only.", "📊", "card-data"),
        Agent("Ethicist", "Ethicist", "Moral compass.", "⚖️", "card-ethicist"),
    ]

# --- Render Left Rail (Persistent) ---
st.markdown("""
<div class="left-rail">
    <div class="rail-logo">NYX</div>
    <div class="agent-orbs">
        <div class="orb">🔴</div><div class="orb">🟢</div><div class="orb">🟤</div>
        <div class="orb">🔮</div><div class="orb">📊</div><div class="orb">⚖️</div>
    </div>
    <div class="live-badge">
        <span class="live-dot"></span>
        <span>LIVE</span>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Main Stage Layout ---
st.markdown('<div class="main-stage">', unsafe_allow_html=True)

# Topic Card
st.markdown(f'<div class="topic-card"><div class="topic-text">{st.session_state.current_topic}</div></div>', unsafe_allow_html=True)

# Model & Settings (Hidden in Expander)
with st.expander("⚙️", expanded=False):
    selected_model = st.selectbox("Model", list(AVAILABLE_MODELS.keys()))
    rounds = st.select_slider("Rounds", [2,3,4], 3)
    if st.button("🎲 New Topic"):
        topics = ["Is AI art real art?", "Should robots have rights?", "Will AI cure loneliness?", "Is crypto the future?"]
        st.session_state.current_topic = secrets.choice(topics)
        st.rerun()

# Debate trigger (we use the dock button instead)
debate_placeholder = st.empty()

st.markdown('</div>', unsafe_allow_html=True)

# --- Floating Action Dock (Footer) ---
st.markdown("""
<div class="action-dock">
    <div class="dock-icon" id="shuffle-topic">↻</div>
    <div class="dock-icon" id="launch-debate">▶</div>
    <div class="dock-icon" id="share-sheet">⎘</div>
</div>
""", unsafe_allow_html=True)

# Dock interactions via Streamlit buttons (hidden but triggered by custom JS not possible, so we use columns in dock style)
# We'll use a horizontal layout that mimics the dock
dock_cols = st.columns([1,1,1])
with dock_cols[0]:
    if st.button("↻", key="shuffle", help="New topic", use_container_width=True):
        topics = ["Is AI art real art?", "Should robots have rights?", "Will AI cure loneliness?"]
        st.session_state.current_topic = secrets.choice(topics)
        st.rerun()
with dock_cols[1]:
    launch_btn = st.button("▶", key="launch", help="Start debate", use_container_width=True)
with dock_cols[2]:
    if st.button("⎘", key="share", help="Share", use_container_width=True):
        st.info("📋 Verdict copied! (Share sheet simulation)")

# --- Debate Execution (when launch is clicked) ---
if launch_btn:
    client, model = get_client(selected_model)
    agents = create_panel()
    log = []
    last_msg = "Let's begin."
    
    with debate_placeholder.container():
        for r in range(1, rounds+1):
            st.markdown(f'<div class="round-separator"><span class="separator-line"></span><span class="dot-sequence">{"●"*r}{"○"*(rounds-r)}</span><span class="separator-line"></span></div>', unsafe_allow_html=True)
            for agent in agents[:4]:  # Show first 4 agents per round to keep it compact
                with st.spinner(f"{agent.name}"):
                    reply = agent.speak(st.session_state.current_topic, last_msg, r, client, model)
                st.markdown(f"""
                <div class="debate-card {agent.card_class}">
                    <div class="agent-header"><span>{agent.avatar}</span> {agent.name} · {agent.role}</div>
                    <div class="agent-message">{reply}</div>
                </div>
                """, unsafe_allow_html=True)
                last_msg = reply
                time.sleep(0.8)
        
        # Verdict
        judge_prompt = f"Debate on '{st.session_state.current_topic}'. Transcript: {log[-200:]}. Give winner and 2-sentence reasoning."
        verdict_resp = client.chat.completions.create(model=model, messages=[{"role":"user","content":judge_prompt}], temperature=0.5)
        verdict = verdict_resp.choices[0].message.content
        st.markdown(f"""
        <div class="debate-card" style="border-left-color: #D4A5A5;">
            <div class="agent-header">⚖️ JUDGMENT</div>
            <div class="agent-message" style="font-family: 'Courier Prime', monospace;">{verdict}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Stats hidden in popover (simulated)
        with st.expander("📊 Agent Insights", expanded=False):
            for agent in agents:
                st.text(f"{agent.name}: {random.randint(1,5)} wins")

# Remove Streamlit default padding
st.markdown('<style>div.block-container{padding:0;}</style>', unsafe_allow_html=True)