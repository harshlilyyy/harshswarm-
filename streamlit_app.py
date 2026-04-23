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

# --- Page Configuration ---
st.set_page_config(
    page_title="Nyx Protocol · The Arena",
    page_icon="🌑",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Cyber-Noir CSS: Midnight Protocol Theme (INCLUDES AGENT BORDERS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

    :root {
        --bg-deep: #05070A;
        --surface-dark: #10141A;
        --glass-bg: rgba(16, 20, 26, 0.6);
        --neon-pink: #FF007F;
        --electric-cyan: #00F3FF;
        --text-primary: #E0E6ED;
        --text-muted: #6F7D8C;
        --border-glow: rgba(255, 0, 127, 0.3);
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background: var(--bg-deep);
        color: var(--text-primary);
    }

    .stApp {
        background: radial-gradient(circle at 30% 10%, #1a0a1a, #05070A 80%);
    }

    [data-testid="stSidebar"] { display: none; }
    .main .block-container {
        padding: 0.5rem 1rem 1rem 1rem;
        max-width: 100%;
    }

    /* ----- GLOBAL HEADER ----- */
    .global-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.5rem 1.5rem;
        background: var(--glass-bg);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-bottom: 1px solid var(--border-glow);
        position: sticky;
        top: 0;
        z-index: 100;
        margin-bottom: 1rem;
        border-radius: 0 0 16px 16px;
    }

    .logo {
        font-family: 'Syne', sans-serif;
        font-weight: 800;
        font-size: 1.8rem;
        letter-spacing: 2px;
        background: linear-gradient(135deg, var(--neon-pink), var(--electric-cyan));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        transition: all 0.15s ease;
    }
    .logo:hover {
        text-shadow: 0 0 8px var(--neon-pink), 0 0 15px var(--electric-cyan);
        letter-spacing: 3px;
    }

    .active-topic {
        font-family: 'JetBrains Mono', monospace;
        color: var(--text-primary);
        background: rgba(0, 243, 255, 0.05);
        padding: 0.4rem 1.5rem;
        border-radius: 40px;
        border: 1px solid var(--border-glow);
        font-size: 0.95rem;
        max-width: 400px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .quantum-roll-btn {
        background: transparent;
        border: 1px solid var(--neon-pink);
        color: var(--neon-pink);
        font-family: 'Syne', sans-serif;
        font-weight: 600;
        padding: 0.4rem 1rem;
        border-radius: 40px;
        cursor: pointer;
        transition: all 0.1s;
    }
    .quantum-roll-btn:hover {
        background: var(--neon-pink);
        color: #05070A;
        box-shadow: 0 0 15px var(--neon-pink);
    }

    .header-right {
        display: flex;
        align-items: center;
        gap: 1.5rem;
    }
    .api-pulse {
        display: flex;
        align-items: center;
        gap: 6px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        color: var(--electric-cyan);
    }
    .pulse-dot {
        width: 8px;
        height: 8px;
        background: var(--electric-cyan);
        border-radius: 50%;
        box-shadow: 0 0 10px var(--electric-cyan);
        animation: pulse-anim 1.5s infinite;
    }
    @keyframes pulse-anim {
        0% { opacity: 1; }
        50% { opacity: 0.4; }
        100% { opacity: 1; }
    }

    /* ----- 3-COLUMN LAYOUT ----- */
    .arena-container {
        display: flex;
        gap: 1rem;
        height: calc(100vh - 100px);
    }
    .col-left {
        flex: 1.8;
        background: var(--glass-bg);
        backdrop-filter: blur(8px);
        border-radius: 20px;
        border: 1px solid var(--border-glow);
        padding: 1rem;
        overflow-y: auto;
    }
    .col-center {
        flex: 4;
        background: var(--glass-bg);
        backdrop-filter: blur(8px);
        border-radius: 20px;
        border: 1px solid var(--border-glow);
        padding: 1rem;
        overflow-y: auto;
    }
    .col-right {
        flex: 2;
        background: var(--glass-bg);
        backdrop-filter: blur(8px);
        border-radius: 20px;
        border: 1px solid var(--border-glow);
        padding: 1rem;
        overflow-y: auto;
    }

    /* ----- AGENT MESSAGE BORDERS (ALL VARIANTS) ----- */
    .agent-message {
        background: var(--glass-bg);
        backdrop-filter: blur(8px);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        border-left: 4px solid;
    }
    .border-neon-pink { border-left-color: #FF007F; }
    .border-electric-cyan { border-left-color: #00F3FF; }
    .border-moderator { border-left-color: #FFB800; }
    .border-philosopher { border-left-color: #9D4EDD; }
    .border-futurist { border-left-color: #00F5D4; }
    .border-data { border-left-color: #00BBF9; }
    .border-ethicist { border-left-color: #F15BB5; }
    .border-policy { border-left-color: #EAB308; }
    .border-investor { border-left-color: #8B5CF6; }
    .border-scientist { border-left-color: #F97316; }
    .border-journalist { border-left-color: #06B6D4; }
    .border-conspiracy { border-left-color: #64748B; }

    /* ----- VERDICT BOX ----- */
    .verdict-box {
        background: var(--glass-bg);
        border: 1px solid var(--neon-pink);
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 1rem;
    }

    /* ----- BUTTONS & INPUTS ----- */
    .stButton > button {
        background: transparent;
        border: 1px solid var(--electric-cyan);
        color: var(--electric-cyan);
        font-family: 'Syne', sans-serif;
        font-weight: 600;
        border-radius: 4px;
        transition: 0.15s;
    }
    .stButton > button:hover {
        background: var(--electric-cyan);
        color: #05070A;
        box-shadow: 0 0 12px var(--electric-cyan);
    }

    .stTextInput > div > div > input, .stTextArea textarea {
        background: rgba(16, 20, 26, 0.8);
        border: 1px solid var(--border-glow);
        border-radius: 4px;
        color: var(--text-primary);
        font-family: 'JetBrains Mono', monospace;
    }

    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--neon-pink); border-radius: 6px; }
</style>
""", unsafe_allow_html=True)
# --- Session State Initialization (if not already present) ---
if "agent_stats" not in st.session_state:
    st.session_state.agent_stats = {
        "Harsh": {"wins": 0, "losses": 0},
        "Jayant": {"wins": 0, "losses": 0},
        "Ritik": {"wins": 0, "losses": 0},
        "Kavya": {"wins": 0, "losses": 0},
        "Nish": {"wins": 0, "losses": 0},
        "Teju": {"wins": 0, "losses": 0},
        "Shivam": {"wins": 0, "losses": 0},
        "Philosopher": {"wins": 0, "losses": 0},
        "Futurist": {"wins": 0, "losses": 0},
        "DataScientist": {"wins": 0, "losses": 0},
        "Ethicist": {"wins": 0, "losses": 0},
    }
if "global_arguments" not in st.session_state:
    st.session_state.global_arguments = []
if "quantum_topic" not in st.session_state:
    st.session_state.quantum_topic = ""
if "current_topic" not in st.session_state:
    st.session_state.current_topic = "Select a topic via Quantum Roll"

QUANTUM_TOPICS = [
    "AI will replace all human jobs by 2040",
    "Space colonization should be humanity's top priority",
    "Social media does more harm than good",
    "Cryptocurrency is the future of finance",
    "Schools should teach AI prompting as a core subject",
    "Robots should have legal rights",
    "Climate change can only be solved by technology",
    "Remote work is better than office work",
]

# --- Global Header (Sticky) ---
st.markdown('<div class="global-header">', unsafe_allow_html=True)
col_logo, col_topic, col_quantum, col_right = st.columns([1, 3, 1, 2])

with col_logo:
    st.markdown('<div class="logo">NYX//PROTOCOL</div>', unsafe_allow_html=True)

with col_topic:
    st.markdown(f'<div class="active-topic">⚡ {st.session_state.current_topic}</div>', unsafe_allow_html=True)

with col_quantum:
    if st.button("🎲 QUANTUM ROLL", key="quantum_roll_header", help="Glitch the topic"):
        # Glitch effect will be added in Phase 4; for now just randomize
        new_topic = secrets.choice(QUANTUM_TOPICS)
        st.session_state.current_topic = new_topic
        st.session_state.quantum_topic = new_topic
        st.rerun()

with col_right:
    st.markdown(f'''
        <div class="header-right">
            <span class="api-pulse"><span class="pulse-dot"></span> API: ACTIVE</span>
            <span style="font-family: 'JetBrains Mono', monospace;">{datetime.now().strftime("%H:%M:%S")}</span>
        </div>
    ''', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- 3-Column Arena Layout ---
st.markdown('<div class="arena-container">', unsafe_allow_html=True)

# Left Column: Configuration & Model Selection
st.markdown('<div class="col-left">', unsafe_allow_html=True)
st.markdown("### 🧬 KERNEL VAULT")
st.markdown("*Model selection & debate settings*")

# Placeholder for model cards (Phase 2)
selected_model = st.selectbox("Active Model", ["Groq (Llama 3.3)", "DeepSeek", "Mistral", "Cerebras", "OpenRouter", "Google Gemma"], index=0)
st.markdown("---")
st.markdown("### ⚙️ DEBATE PARAMETERS")
rounds = st.select_slider("Rounds", options=[3, 5, 8], value=3)
extra_agents = st.slider("Extra Agents", 0, 9, 6)
manual_override = st.toggle("DIRECT KERNEL ACCESS", value=True, help="Lock to selected model; disable for auto-fallback")

st.markdown("---")
st.markdown("### 📊 AGENT STATS")
for agent, stats in list(st.session_state.agent_stats.items())[:8]:  # Show first 8 for space
    total = stats["wins"] + stats["losses"]
    rate = f"{(stats['wins']/total*100):.0f}%" if total > 0 else "0%"
    st.text(f"{agent}: {stats['wins']}W / {stats['losses']}L ({rate})")
st.markdown('</div>', unsafe_allow_html=True)

# Center Column: The Debate Arena
st.markdown('<div class="col-center">', unsafe_allow_html=True)
st.markdown("### ⚔️ THE ARENA")
st.markdown("*Live debate transcript*")

# Topic input (compact, inline with arena)
topic = st.text_input("Debate Topic", value=st.session_state.current_topic, placeholder="Enter topic...", label_visibility="collapsed")
if topic != st.session_state.current_topic:
    st.session_state.current_topic = topic
    st.session_state.quantum_topic = topic

# Launch button
start_debate = st.button("▶ INITIATE PROTOCOL", use_container_width=True)

# Placeholder for debate messages (will be populated in Phase 3)
debate_placeholder = st.empty()
st.markdown('</div>', unsafe_allow_html=True)

# Right Column: Live Scoreboard & Verdict
st.markdown('<div class="col-right">', unsafe_allow_html=True)
st.markdown("### 📈 LIVE TELEMETRY")
scoreboard_placeholder = st.empty()
st.markdown("---")
st.markdown("### 🧠 VERDICT")
verdict_placeholder = st.empty()
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)  # Close arena-container
# ==================== CHUNK 3 + 4 COMBINED ====================
# Session state, model router, agent classes, and debate execution

# --- Session State ---
if "agent_stats" not in st.session_state:
    st.session_state.agent_stats = {
        "Harsh": {"wins": 0, "losses": 0},
        "Jayant": {"wins": 0, "losses": 0},
        "Ritik": {"wins": 0, "losses": 0},
        "Kavya": {"wins": 0, "losses": 0},
        "Nish": {"wins": 0, "losses": 0},
        "Teju": {"wins": 0, "losses": 0},
        "Shivam": {"wins": 0, "losses": 0},
        "Philosopher": {"wins": 0, "losses": 0},
        "Futurist": {"wins": 0, "losses": 0},
        "DataScientist": {"wins": 0, "losses": 0},
        "Ethicist": {"wins": 0, "losses": 0},
    }
if "global_arguments" not in st.session_state:
    st.session_state.global_arguments = []
if "quantum_topic" not in st.session_state:
    st.session_state.quantum_topic = ""
if "current_topic" not in st.session_state:
    st.session_state.current_topic = "Select a topic via Quantum Roll"

QUANTUM_TOPICS = [
    "AI will replace all human jobs by 2040",
    "Space colonization should be humanity's top priority",
    "Social media does more harm than good",
    "Cryptocurrency is the future of finance",
    "Schools should teach AI prompting as a core subject",
    "Robots should have legal rights",
    "Climate change can only be solved by technology",
    "Remote work is better than office work",
]

# --- Available Models ---
AVAILABLE_MODELS = {
    "Groq (Llama 3.3 70B)": {"provider": "groq", "model": "llama-3.3-70b-versatile", "type": "openai", "base_url": "https://api.groq.com/openai/v1"},
    "DeepSeek (DeepSeek-Chat)": {"provider": "deepseek", "model": "deepseek-chat", "type": "openai", "base_url": "https://api.deepseek.com"},
    "Mistral (Mistral Small 4)": {"provider": "mistral", "model": "mistral-small-4", "type": "openai", "base_url": "https://api.mistral.ai/v1"},
    "Cerebras (Llama 3.3 70B)": {"provider": "cerebras", "model": "llama-3.3-70b", "type": "openai", "base_url": "https://api.cerebras.ai/v1"},
    "OpenRouter (Auto)": {"provider": "openrouter", "model": "openrouter/auto", "type": "openai", "base_url": "https://openrouter.ai/api/v1"},
    "Google (Gemma 4 26B)": {"provider": "google", "model": "gemma-4-26b-it", "type": "google", "base_url": None},
}

PROVIDER_API_KEYS = {
    "groq": st.secrets.get("GROQ_API_KEY", ""),
    "deepseek": st.secrets.get("DEEPSEEK_API_KEY", ""),
    "mistral": st.secrets.get("MISTRAL_API_KEY", ""),
    "cerebras": st.secrets.get("CEREBRAS_API_KEY", ""),
    "openrouter": st.secrets.get("OPENROUTER_API_KEY", ""),
    "google": st.secrets.get("GEMINI_API_KEY", ""),
}

def get_model_config(manual_override, selected_model_name):
    if manual_override:
        for display, config in AVAILABLE_MODELS.items():
            if selected_model_name == display:
                config = config.copy()
                config["api_key"] = PROVIDER_API_KEYS.get(config["provider"], "")
                if not config["api_key"]:
                    st.error(f"Missing API key for {config['provider']}")
                    st.stop()
                return config
    else:
        for provider, model in [("groq", "llama-3.3-70b-versatile"), ("deepseek", "deepseek-chat"),
                                ("mistral", "mistral-small-4"), ("cerebras", "llama-3.3-70b"),
                                ("openrouter", "openrouter/auto"), ("google", "gemma-4-26b-it")]:
            key = PROVIDER_API_KEYS.get(provider, "")
            if key:
                try:
                    if provider == "google":
                        import google.generativeai as genai
                        genai.configure(api_key=key)
                        genai.GenerativeModel(model).generate_content("test", request_options={"timeout": 5})
                    return {"provider": provider, "model": model, "api_key": key,
                            "type": "google" if provider=="google" else "openai",
                            "base_url": AVAILABLE_MODELS.get(provider, {}).get("base_url")}
                except: continue
    st.error("No working models available.")
    st.stop()

def initialize_model(selected_model_display, manual_override):
    config = get_model_config(manual_override, selected_model_display)
    if config["type"] == "google":
        import google.generativeai as genai
        genai.configure(api_key=config["api_key"])
        google_model = genai.GenerativeModel(config["model"])
        return ("google", google_model, None)
    else:
        from openai import OpenAI
        client = OpenAI(api_key=config["api_key"], base_url=config["base_url"])
        return ("openai", None, client)

def generate_response(prompt, system_prompt, model_type, google_model, openai_client, model_name):
    if model_type == "google":
        full = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        return google_model.generate_content(full).text
    else:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        resp = openai_client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.7,
            max_tokens=600
        )
        return resp.choices[0].message.content

def is_repetition(text, threshold=0.6):
    words = set(text.lower().split())
    for past in st.session_state.global_arguments[-10:]:
        past_words = set(past.lower().split())
        if len(words & past_words) / max(len(words), 1) > threshold:
            return True
    return False

def add_global_memory(agent, text):
    st.session_state.global_arguments.append(f"{agent}: {text[:200]}")

class AI_Agent:
    def __init__(self, name, role, personality, avatar, border_style):
        self.name = name
        self.role = role
        self.personality = personality
        self.avatar = avatar
        self.border_style = border_style
        self.history = []
        self.scores = {"logic": 0, "creativity": 0, "persuasiveness": 0}

    def speak(self, topic, last_msg, round_num, model_type, google_model, openai_client, model_name):
        history = "\n".join(self.history[-3:]) or "No previous chat."
        system_prompt = f"You are {self.name} ({self.role}). {self.personality}"
        prompt = f"""
Debate round {round_num} on: "{topic}"

FORMAT (must follow):
**Claim:** [your main point]
**Evidence:** [supporting fact]
**Reasoning:** [why it matters]

Avoid repeating previous arguments. History:
{history}

Last said: "{last_msg}"
"""
        for _ in range(2):
            resp = generate_response(prompt, system_prompt, model_type, google_model, openai_client, model_name).strip()
            if not is_repetition(resp):
                break
            prompt += "\nWARNING: Argument repeated. Provide a NEW angle."
        else:
            resp = "**Claim:** I've made my point. **Evidence:** Already presented. **Reasoning:** Let's move on."
        self.history.append(f"{self.name}: {resp}")
        add_global_memory(self.name, resp)
        if "claim:" in resp.lower(): self.scores["logic"] += 2
        if "evidence:" in resp.lower(): self.scores["creativity"] += 2
        if "reasoning:" in resp.lower(): self.scores["persuasiveness"] += 2
        return resp

class Moderator(AI_Agent):
    def speak(self, topic, last_msg, round_num, model_type, google_model, openai_client, model_name):
        history = "\n".join(self.history[-5:]) or "No debate yet."
        system_prompt = f"You are {self.name}, the moderator. Be sharp and impartial."
        prompt = f"""
Summarize key points, note contradictions, and ask a sharp question.
Topic: "{topic}" | Round: {round_num}
History: {history}
Last exchange: "{last_msg}"
Keep it 3-4 sentences.
"""
        return generate_response(prompt, system_prompt, model_type, google_model, openai_client, model_name).strip()

def judge_debate(topic, messages, model_type, google_model, openai_client, model_name):
    debate_text = "\n".join(messages[-30:])
    system_prompt = "You are the JUDGE. Deliver a fair, detailed verdict."
    prompt = f"""
Debate on: "{topic}"
Transcript: {debate_text}

Provide:
🏆 Winner: [Name]
📝 Reasoning: [2-3 sentences]
Strengths & Weaknesses for each panelist.
📊 Scores (1-10) for Logic, Creativity, Persuasiveness in a table.
⚖️ Final Takeaway: [1-2 sentences]
"""
    return generate_response(prompt, system_prompt, model_type, google_model, openai_client, model_name)

def create_agents(num_extra=6):
    agents = [
        AI_Agent("Harsh", "Skeptic", "Pessimistic economist.", "🔴", "border-neon-pink"),
        AI_Agent("Jayant", "Optimist", "Cheerful tech investor.", "🟢", "border-electric-cyan"),
        Moderator("Ahany", "Moderator", "Sharp journalist.", "🔵", "border-moderator"),
    ]
    extras = [
        ("Ritik", "Policy Advisor", "Gov/regulation view.", "🟡", "border-policy"),
        ("Kavya", "Retail Investor", "Everyday person.", "🟣", "border-investor"),
        ("Nish", "Scientist", "Demands evidence.", "🟠", "border-scientist"),
        ("Teju", "Tech Journalist", "Identifies trends.", "🔷", "border-journalist"),
        ("Shivam", "Conspiracy Theorist", "Hidden agendas.", "⚫", "border-conspiracy"),
        ("Philosopher", "Philosopher", "Ethical context.", "🟤", "border-philosopher"),
        ("Futurist", "Futurist", "Long-term view.", "🔮", "border-futurist"),
        ("DataScientist", "Data Scientist", "Statistics only.", "📊", "border-data"),
        ("Ethicist", "Ethicist", "Moral implications.", "⚖️", "border-ethicist"),
    ]
    for i in range(min(num_extra, len(extras))):
        name, role, pers, av, border = extras[i]
        agents.insert(-1, AI_Agent(name, role, pers, av, border))
    return agents

def generate_pdf(topic, log, verdict, winner):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Nyx Protocol Debate Transcript", ln=1, align='C')
    pdf.cell(200, 10, txt=f"Topic: {topic}", ln=1)
    pdf.ln(10)
    for msg in log:
        clean = msg.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 10, txt=clean)
        pdf.ln(2)
    pdf.ln(10)
    pdf.set_font("Arial", style='B', size=14)
    pdf.cell(200, 10, txt=f"Winner: {winner}", ln=1)
    pdf.set_font("Arial", size=12)
    verdict_clean = verdict.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, txt=verdict_clean)
    return pdf.output(dest='S').encode('latin-1')

# --- LAYOUT RENDERING (Header + 3 Columns) ---
st.markdown('<div class="global-header">', unsafe_allow_html=True)
col_logo, col_topic, col_quantum, col_right = st.columns([1, 3, 1, 2])
with col_logo:
    st.markdown('<div class="logo">NYX//PROTOCOL</div>', unsafe_allow_html=True)
with col_topic:
    st.markdown(f'<div class="active-topic">⚡ {st.session_state.current_topic}</div>', unsafe_allow_html=True)
with col_quantum:
    if st.button("🎲 QUANTUM ROLL", key="quantum_roll_header"):
        new_topic = secrets.choice(QUANTUM_TOPICS)
        st.session_state.current_topic = new_topic
        st.session_state.quantum_topic = new_topic
        st.rerun()
with col_right:
    st.markdown(f'''
        <div class="header-right">
            <span class="api-pulse"><span class="pulse-dot"></span> API: ACTIVE</span>
            <span style="font-family: 'JetBrains Mono', monospace;">{datetime.now().strftime("%H:%M:%S")}</span>
        </div>
    ''', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="arena-container">', unsafe_allow_html=True)

# LEFT COLUMN
st.markdown('<div class="col-left">', unsafe_allow_html=True)
st.markdown("### 🧬 KERNEL VAULT")
selected_model = st.selectbox("Active Model", list(AVAILABLE_MODELS.keys()), index=0)
st.markdown("---")
st.markdown("### ⚙️ DEBATE PARAMETERS")
rounds = st.select_slider("Rounds", options=[3, 5, 8], value=3)
extra_agents = st.slider("Extra Agents", 0, 9, 6)
manual_override = st.toggle("DIRECT KERNEL ACCESS", value=True)
st.markdown("---")
st.markdown("### 📊 AGENT STATS")
for agent, stats in list(st.session_state.agent_stats.items())[:8]:
    total = stats["wins"] + stats["losses"]
    rate = f"{(stats['wins']/total*100):.0f}%" if total > 0 else "0%"
    st.text(f"{agent}: {stats['wins']}W / {stats['losses']}L ({rate})")
st.markdown('</div>', unsafe_allow_html=True)

# CENTER COLUMN
st.markdown('<div class="col-center">', unsafe_allow_html=True)
st.markdown("### ⚔️ THE ARENA")
topic = st.text_input("Debate Topic", value=st.session_state.current_topic, label_visibility="collapsed")
if topic != st.session_state.current_topic:
    st.session_state.current_topic = topic
    st.session_state.quantum_topic = topic
start_debate = st.button("▶ INITIATE PROTOCOL", use_container_width=True)
debate_placeholder = st.empty()
st.markdown('</div>', unsafe_allow_html=True)

# RIGHT COLUMN
st.markdown('<div class="col-right">', unsafe_allow_html=True)
st.markdown("### 📈 LIVE TELEMETRY")
scoreboard_placeholder = st.empty()
st.markdown("---")
st.markdown("### 🧠 VERDICT")
verdict_placeholder = st.empty()
st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- DEBATE EXECUTION ---
if start_debate and topic:
    st.session_state.global_arguments = []
    model_type, google_model, openai_client = initialize_model(selected_model, manual_override)
    model_name = AVAILABLE_MODELS[selected_model]["model"]
    agents = create_agents(extra_agents)
    log = []
    last_msg = "Let's begin."
    winner = None
    verdict = ""

    with debate_placeholder.container():
        for r in range(1, rounds + 1):
            st.markdown(f"<h3 style='text-align: center; font-family: Syne; color: var(--neon-pink);'>⚔️ ROUND {r} — ENGAGE ⚔️</h3>", unsafe_allow_html=True)
            round_msgs = []
            order = [a for a in agents if a.name != "Ahany"]
            for agent in order:
                with st.spinner(f"{agent.name} generating..."):
                    reply = agent.speak(topic, last_msg, r, model_type, google_model, openai_client, model_name)
                st.markdown(f"""
                <div class="agent-message {agent.border_style}">
                    <span class="agent-avatar">{agent.avatar}</span>
                    <strong>{agent.name} ({agent.role})</strong><br>
                    <span style="font-family: 'JetBrains Mono', monospace;">{reply}</span>
                </div>
                """, unsafe_allow_html=True)
                round_msgs.append(f"{agent.avatar} **{agent.name}**: {reply}")
                last_msg = reply
                time.sleep(1.2)
            mod = next(a for a in agents if a.name == "Ahany")
            with st.spinner("Moderator analyzing..."):
                mod_reply = mod.speak(topic, last_msg, r, model_type, google_model, openai_client, model_name)
            st.markdown(f"""
            <div class="agent-message border-moderator">
                <span class="agent-avatar">{mod.avatar}</span>
                <strong>{mod.name}</strong><br>
                <span style="font-family: 'JetBrains Mono', monospace;">{mod_reply}</span>
            </div>
            """, unsafe_allow_html=True)
            round_msgs.append(f"{mod.avatar} **{mod.name}**: {mod_reply}")
            last_msg = mod_reply
            log.append(f"### 🔄 Round {r}\n\n" + "\n\n".join(round_msgs))
            score_data = [{"Agent": f"{a.avatar} {a.name}", "Logic": a.scores["logic"], "Creativity": a.scores["creativity"], "Persuasiveness": a.scores["persuasiveness"]} for a in agents]
            scoreboard_placeholder.dataframe(score_data, use_container_width=True, hide_index=True)
            time.sleep(0.5)

    with st.spinner("JUDGE DELIBERATING..."):
        verdict = judge_debate(topic, log, model_type, google_model, openai_client, model_name)
    match = re.search(r"Winner:\s*(\w+)", verdict)
    winner = match.group(1) if match else "Unknown"
    for agent in st.session_state.agent_stats:
        if agent == winner:
            st.session_state.agent_stats[agent]["wins"] += 1
        else:
            st.session_state.agent_stats[agent]["losses"] += 1

    verdict_placeholder.markdown(f"""
    <div class="verdict-box">
        <h2 style="color: var(--neon-pink);">PROTOCOL COMPLETE</h2>
        <h3>🏆 VICTORY: {winner}</h3>
        <p>{verdict}</p>
    </div>
    """, unsafe_allow_html=True)

    share_text = f"Nyx Protocol verdict on '{topic}': Winner {winner}. {verdict[:150]}..."
    tweet = urllib.parse.quote(share_text)
    twitter_url = f"https://twitter.com/intent/tweet?text={tweet}"
    linkedin_url = f"https://www.linkedin.com/sharing/share-offsite/?url={urllib.parse.quote('https://harshswarmdev.streamlit.app')}"
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<a href="{twitter_url}" target="_blank"><button>🐦 Share</button></a>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<a href="{linkedin_url}" target="_blank"><button>💼 Post</button></a>', unsafe_allow_html=True)

    pdf_data = generate_pdf(topic, log, verdict, winner)
    st.download_button("📄 Download Transcript", pdf_data, file_name=f"nyx_debate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")