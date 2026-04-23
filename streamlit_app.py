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
    page_title="Nyx Protocol · by Harsh Dubey",
    page_icon="💗",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 💖 Pink Love Theme with Glassmorphism & Hearts Background 💖 ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&display=swap');

    :root {
        --blush: #ffe4e6;
        --soft-pink: #fbc4d5;
        --rose: #f8a5c2;
        --deep-rose: #e87b9e;
        --cream: #fff9f9;
        --charcoal: #4a3b3c;
        --glass-white: rgba(255, 255, 255, 0.75);
        --glass-pink: rgba(255, 228, 230, 0.7);
        --glass-border: rgba(232, 123, 158, 0.3);
    }

    html, body, [class*="css"] {
        font-family: 'Quicksand', sans-serif;
        background: var(--cream);
        color: var(--charcoal);
    }

    .stApp {
        background: linear-gradient(145deg, #fff0f3 0%, #ffe4e9 100%);
        background-image: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M30 15 C25 5 15 5 10 15 C5 25 15 35 30 45 C45 35 55 25 50 15 C45 5 35 5 30 15z' fill='%23fbc4d5' opacity='0.2'/%3E%3C/svg%3E");
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }

    .main .block-container {
        padding: 2rem 1rem;
        max-width: 700px;
        margin: 0 auto;
    }

    h1 {
        font-family: 'Dancing Script', cursive;
        font-size: 4rem !important;
        font-weight: 700 !important;
        background: linear-gradient(135deg, var(--deep-rose) 0%, #f7c873 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.25rem !important;
    }

    h1::before, h1::after {
        content: "💗";
        font-size: 2.5rem;
        margin: 0 15px;
        opacity: 0.8;
    }

    .subtitle {
        text-align: center;
        font-size: 1rem;
        color: var(--charcoal);
        margin-bottom: 2.5rem;
        opacity: 0.8;
    }

    /* Perplexity-style input row */
    .input-row {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        background: var(--glass-white);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 60px;
        padding: 0.5rem 0.5rem 0.5rem 1.5rem;
        border: 2px solid var(--glass-border);
        box-shadow: 0 10px 30px rgba(232, 123, 158, 0.1);
        margin-bottom: 1rem;
    }

    .input-row .stSelectbox {
        flex: 0 0 120px;
    }

    .input-row .stTextInput {
        flex: 1;
    }

    .input-row .stButton {
        flex: 0 0 auto;
    }

    /* Hide default Streamlit elements we don't need */
    div[data-testid="stToolbar"] { display: none; }
    footer { display: none; }
    [data-testid="stSidebar"] { display: none; }

    /* Inputs and selects */
    .stTextInput > div > div > input {
        background: transparent !important;
        border: none !important;
        font-size: 1.1rem !important;
        padding: 0.75rem 0.5rem !important;
        color: var(--charcoal) !important;
        font-family: 'Quicksand', sans-serif !important;
    }
    .stTextInput > div > div > input:focus {
        box-shadow: none !important;
        outline: none !important;
    }
    .stTextInput > div > div > input::placeholder {
        color: #9e7a8a !important;
        font-style: italic;
    }

    .stSelectbox > div > div {
        background: transparent !important;
        border: none !important;
        font-weight: 600;
        color: var(--deep-rose) !important;
    }

    /* Launch button */
    .stButton > button {
        background: linear-gradient(135deg, var(--rose) 0%, var(--deep-rose) 100%);
        color: white;
        font-weight: 600;
        border-radius: 60px;
        border: none;
        padding: 0.75rem 2rem;
        font-size: 1rem;
        box-shadow: 0 4px 15px rgba(232, 123, 158, 0.3);
        transition: all 0.2s;
        white-space: nowrap;
    }

    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(232, 123, 158, 0.5);
    }

    /* Chat messages */
    [data-testid="stChatMessage"] {
        background: var(--glass-white);
        backdrop-filter: blur(12px);
        border-radius: 24px 24px 24px 8px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid var(--glass-border);
        box-shadow: 0 8px 16px rgba(232, 123, 158, 0.08);
    }

    /* Verdict box */
    .verdict-box {
        background: var(--glass-white);
        backdrop-filter: blur(12px);
        border-radius: 24px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border: 1px solid var(--glass-border);
    }

    /* Scoreboard */
    [data-testid="stDataFrame"] {
        background: var(--glass-white);
        border-radius: 16px;
        padding: 0.5rem;
        border: 1px solid var(--glass-border);
    }

    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, var(--soft-pink), var(--deep-rose));
    }

    /* Signature */
    .signature {
        text-align: center;
        margin-top: 2rem;
        color: var(--deep-rose);
        font-family: 'Dancing Script', cursive;
        font-size: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)
# --- Session State ---
if "agent_stats" not in st.session_state:
    st.session_state.agent_stats = {
        "Harsh": {"wins": 0, "losses": 0}, "Jayant": {"wins": 0, "losses": 0},
        "Ritik": {"wins": 0, "losses": 0}, "Kavya": {"wins": 0, "losses": 0},
        "Nish": {"wins": 0, "losses": 0}, "Teju": {"wins": 0, "losses": 0},
        "Shivam": {"wins": 0, "losses": 0}, "Philosopher": {"wins": 0, "losses": 0},
        "Futurist": {"wins": 0, "losses": 0}, "DataScientist": {"wins": 0, "losses": 0},
        "Ethicist": {"wins": 0, "losses": 0},
    }
if "global_arguments" not in st.session_state:
    st.session_state.global_arguments = []
if "quantum_topic" not in st.session_state:
    st.session_state.quantum_topic = ""

# --- Models ---
AVAILABLE_MODELS = {
    "💗 Groq": {"provider": "groq", "model": "llama-3.3-70b-versatile", "type": "openai", "base_url": "https://api.groq.com/openai/v1"},
    "🌸 DeepSeek": {"provider": "deepseek", "model": "deepseek-chat", "type": "openai", "base_url": "https://api.deepseek.com"},
    "💕 Mistral": {"provider": "mistral", "model": "mistral-small-4", "type": "openai", "base_url": "https://api.mistral.ai/v1"},
    "💓 Cerebras": {"provider": "cerebras", "model": "llama-3.3-70b", "type": "openai", "base_url": "https://api.cerebras.ai/v1"},
    "💞 OpenRouter": {"provider": "openrouter", "model": "openrouter/auto", "type": "openai", "base_url": "https://openrouter.ai/api/v1"},
    "💖 Google": {"provider": "google", "model": "gemma-4-26b-it", "type": "google", "base_url": None},
}

PROVIDER_API_KEYS = {
    "groq": st.secrets.get("GROQ_API_KEY", ""),
    "deepseek": st.secrets.get("DEEPSEEK_API_KEY", ""),
    "mistral": st.secrets.get("MISTRAL_API_KEY", ""),
    "cerebras": st.secrets.get("CEREBRAS_API_KEY", ""),
    "openrouter": st.secrets.get("OPENROUTER_API_KEY", ""),
    "google": st.secrets.get("GEMINI_API_KEY", ""),
}

def get_model_config(selected_model_name):
    config = AVAILABLE_MODELS[selected_model_name].copy()
    config["api_key"] = PROVIDER_API_KEYS.get(config["provider"], "")
    if not config["api_key"]:
        st.error(f"Missing API key for {config['provider']}")
        st.stop()
    return config

def initialize_model(selected_model_name):
    config = get_model_config(selected_model_name)
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
        resp = openai_client.chat.completions.create(model=model_name, messages=messages, temperature=0.7, max_tokens=600)
        return resp.choices[0].message.content

def is_repetition(text, threshold=0.6):
    words = set(text.lower().split())
    for past in st.session_state.global_arguments[-10:]:
        if len(words & set(past.lower().split())) / max(len(words), 1) > threshold:
            return True
    return False

def add_global_memory(agent, text):
    st.session_state.global_arguments.append(f"{agent}: {text[:200]}")

class AI_Agent:
    def __init__(self, name, role, personality, avatar):
        self.name = name; self.role = role; self.personality = personality; self.avatar = avatar
        self.history = []; self.scores = {"logic": 0, "creativity": 0, "persuasiveness": 0}
    def speak(self, topic, last_msg, round_num, model_type, google_model, openai_client, model_name):
        history = "\n".join(self.history[-3:]) or "No previous chat."
        system_prompt = f"You are {self.name} ({self.role}). {self.personality}"
        prompt = f"""Debate round {round_num} on: "{topic}"
**Claim:** [point] **Evidence:** [fact] **Reasoning:** [why]
History: {history}
Last: "{last_msg}" """
        for _ in range(2):
            resp = generate_response(prompt, system_prompt, model_type, google_model, openai_client, model_name).strip()
            if not is_repetition(resp): break
            prompt += "\nWARNING: Repeated. New angle required."
        else: resp = "**Claim:** Point made. **Evidence:** Already presented. **Reasoning:** Moving on."
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
        prompt = f"Summarize, note contradictions, ask a sharp question. Topic: {topic} | Round: {round_num}\nHistory: {history}\nLast: {last_msg}"
        return generate_response(prompt, system_prompt, model_type, google_model, openai_client, model_name).strip()

def judge_debate(topic, messages, model_type, google_model, openai_client, model_name):
    debate_text = "\n".join(messages[-30:])
    system_prompt = "You are the JUDGE. Deliver a fair, detailed verdict."
    prompt = f"Debate on: {topic}\nTranscript: {debate_text}\nProvide: 🏆 Winner, 📝 Reasoning, Strengths/Weaknesses, 📊 Scores (1-10), ⚖️ Takeaway."
    return generate_response(prompt, system_prompt, model_type, google_model, openai_client, model_name)

def create_agents(num_extra=6):
    agents = [AI_Agent("Harsh", "Skeptic", "Finds flaws and risks.", "🔴"), AI_Agent("Jayant", "Optimist", "Sees opportunity.", "🟢"), Moderator("Ahany", "Moderator", "Sharp journalist.", "🔵")]
    extras = [("Ritik", "Policy Advisor", "Gov view.", "🟡"), ("Kavya", "Retail Investor", "Everyday person.", "🟣"), ("Nish", "Scientist", "Demands evidence.", "🟠"), ("Teju", "Tech Journalist", "Identifies trends.", "🔷"), ("Shivam", "Conspiracy Theorist", "Hidden agendas.", "⚫"), ("Philosopher", "Philosopher", "Ethical context.", "🟤"), ("Futurist", "Futurist", "Long-term view.", "🔮"), ("DataScientist", "Data Scientist", "Statistics only.", "📊"), ("Ethicist", "Ethicist", "Moral implications.", "⚖️")]
    for i in range(min(num_extra, len(extras))):
        name, role, pers, av = extras[i]
        agents.insert(-1, AI_Agent(name, role, pers, av))
    return agents

def generate_pdf(topic, log, verdict, winner):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Nyx Protocol Transcript", ln=1)
    pdf.cell(200, 10, txt=f"Topic: {topic}", ln=1)
    pdf.ln(5)
    for msg in log: pdf.multi_cell(0, 8, txt=msg.encode('latin-1','replace').decode('latin-1')); pdf.ln(2)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt=f"Winner: {winner}", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 8, txt=verdict.encode('latin-1','replace').decode('latin-1'))
    return pdf.output(dest='S').encode('latin-1')

# --- UI: Perplexity Style ---
st.title("💗 Nyx Protocol 💗")
st.markdown('<div class="subtitle">Multi‑Agent AI Debate · Judge · Live Scoring</div>', unsafe_allow_html=True)

with st.container():
    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        with st.container():
            st.markdown('<div class="input-row">', unsafe_allow_html=True)
            i1, i2, i3 = st.columns([2, 5, 2])
            with i1:
                selected_model = st.selectbox("Model", list(AVAILABLE_MODELS.keys()), label_visibility="collapsed")
            with i2:
                topic = st.text_input("Topic", value=st.session_state.quantum_topic, placeholder="Ask anything...", label_visibility="collapsed")
            with i3:
                start_btn = st.button("🚀 Launch", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Advanced options expander
        with st.expander("⚙️ Advanced Settings", expanded=False):
            rounds = st.select_slider("Rounds", [3,5,8], 3)
            extra_agents = st.slider("Extra Agents", 0, 9, 6)
            st.markdown("---")
            if st.button("🎲 Quantum Roll", use_container_width=True):
                topics = ["AI will replace all human jobs by 2040", "Space colonization should be top priority", "Social media does more harm than good", "Crypto is the future", "Schools should teach AI", "Robots deserve rights", "Tech can solve climate change", "Remote work > office"]
                st.session_state.quantum_topic = secrets.choice(topics)
                st.rerun()

# --- Debate Execution ---
if start_btn and topic:
    st.session_state.global_arguments = []
    model_type, google_model, openai_client = initialize_model(selected_model)
    model_name = AVAILABLE_MODELS[selected_model]["model"]
    agents = create_agents(extra_agents)
    log, last_msg, winner, verdict = [], "Let's begin.", None, ""

    prog = st.progress(0)
    status = st.empty()
    chat = st.empty()

    for r in range(1, rounds+1):
        prog.progress(r/rounds, f"Round {r}/{rounds}")
        round_msgs = []
        order = [a for a in agents if a.name != "Ahany"]
        for agent in order:
            with st.spinner(f"{agent.name} thinking..."):
                reply = agent.speak(topic, last_msg, r, model_type, google_model, openai_client, model_name)
            with chat.container():
                st.chat_message(agent.name, avatar=agent.avatar).markdown(reply)
            round_msgs.append(f"{agent.avatar} **{agent.name}**: {reply}")
            last_msg = reply; time.sleep(1)
        mod = next(a for a in agents if a.name == "Ahany")
        with st.spinner("Moderator summarizing..."):
            mod_reply = mod.speak(topic, last_msg, r, model_type, google_model, openai_client, model_name)
        with chat.container():
            st.chat_message(mod.name, avatar=mod.avatar).markdown(mod_reply)
        round_msgs.append(f"{mod.avatar} **{mod.name}**: {mod_reply}")
        last_msg = mod_reply
        log.append(f"### Round {r}\n\n" + "\n\n".join(round_msgs))

    prog.empty(); status.empty()
    with st.spinner("Judge deliberating..."):
        verdict = judge_debate(topic, log, model_type, google_model, openai_client, model_name)
    match = re.search(r"Winner:\s*(\w+)", verdict)
    winner = match.group(1) if match else "Unknown"
    for a in st.session_state.agent_stats:
        st.session_state.agent_stats[a]["wins" if a==winner else "losses"] += 1

    st.markdown(f'<div class="verdict-box"><h3>🏆 {winner}</h3>{verdict}</div>', unsafe_allow_html=True)
    st.balloons()

    # Stats in sidebar-like drawer
    with st.expander("📊 Agent Win Rates", expanded=False):
        for agent, s in st.session_state.agent_stats.items():
            total = s['wins']+s['losses']
            rate = f"{s['wins']/total*100:.0f}%" if total else "0%"
            st.text(f"{agent}: {s['wins']}W/{s['losses']}L ({rate})")

    # Share & PDF
    share = f"Nyx Protocol: {winner} wins on '{topic}'"
    c1, c2 = st.columns(2)
    with c1: st.markdown(f'<a href="https://twitter.com/intent/tweet?text={urllib.parse.quote(share)}" target="_blank"><button style="width:100%;">🐦 Tweet</button></a>', unsafe_allow_html=True)
    with c2: st.download_button("📄 PDF", generate_pdf(topic, log, verdict, winner), f"debate_{datetime.now():%Y%m%d_%H%M%S}.pdf")

st.markdown('<div class="signature">✨ by Harsh Dubey ✨</div>', unsafe_allow_html=True)