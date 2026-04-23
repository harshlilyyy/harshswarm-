import streamlit as st
import time
import secrets
import re
import urllib.parse
from datetime import datetime
from fpdf import FPDF

# --- Page Configuration ---
st.set_page_config(
    page_title="Nyx · by Harsh",
    page_icon="🤍",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- Cosmic Pearl Glassmorphism CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;1,400&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;350;400;500&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Courier+Prime&display=swap');

    :root {
        --pearl: #F9F6F0;
        --rose-gold: #D4A5A5;
        --champagne: #E8D5B5;
        --warm-charcoal: #2C2A28;
        --glass-border: rgba(255,255,255,0.6);
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background: var(--pearl);
        color: var(--warm-charcoal);
    }

    .stApp {
        background: radial-gradient(circle at 50% 20%, rgba(232,213,181,0.25) 0%, var(--pearl) 80%);
    }

    .main .block-container {
        padding: 2rem 1.25rem !important;
        max-width: 640px !important;
        margin: 0 auto !important;
    }

    [data-testid="stToolbar"], footer, [data-testid="stSidebar"] {
        display: none !important;
    }

    .nyx-title {
        font-family: 'Playfair Display', serif;
        font-style: italic;
        font-size: 3.8rem;
        text-align: center;
        background: linear-gradient(145deg, var(--rose-gold), #B58D8D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        text-align: center;
        font-weight: 300;
        opacity: 0.6;
        margin-bottom: 2rem;
        letter-spacing: 2px;
        font-size: 0.8rem;
    }

    .glass-card {
        background: rgba(255, 255, 255, 0.5);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 28px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 0.5px solid var(--glass-border);
        box-shadow: 0 10px 30px -10px rgba(0,0,0,0.05);
    }

    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.6) !important;
        backdrop-filter: blur(15px);
        border: 0.5px solid var(--glass-border) !important;
        border-radius: 60px !important;
        padding: 1rem 1.5rem !important;
        font-size: 1.1rem !important;
        color: var(--warm-charcoal) !important;
        text-align: center;
    }

    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.6) !important;
        backdrop-filter: blur(15px);
        border: 0.5px solid var(--glass-border) !important;
        border-radius: 60px !important;
    }

    .stButton > button {
        background: linear-gradient(145deg, var(--rose-gold), var(--champagne));
        border: none;
        border-radius: 60px;
        font-weight: 500;
        color: white;
        box-shadow: 0 8px 20px -8px rgba(212,165,165,0.4);
        width: 100%;
        padding: 0.8rem 1.5rem;
    }

    .debate-card {
        background: rgba(255, 255, 255, 0.45);
        backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 0.8rem;
        border-left: 5px solid;
    }

    .card-skeptic { border-left-color: #D4A5A5; }
    .card-optimist { border-left-color: #B5C9B5; }
    .card-philosopher { border-left-color: #C5B5D4; }
    .card-futurist { border-left-color: #A5C9D4; }
    .card-data { border-left-color: #A5D4C0; }
    .card-ethicist { border-left-color: #D4A5C0; }
    .card-policy { border-left-color: #E8D5B5; }
    .card-conspiracy { border-left-color: #B5A5C0; }

    .verdict-box {
        background: rgba(255, 255, 255, 0.5);
        backdrop-filter: blur(20px);
        border-radius: 28px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border-left: 5px solid var(--rose-gold);
        font-family: 'Courier Prime', monospace;
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
        "Ethicist": {"wins": 0, "losses": 0}, "Ahany": {"wins": 0, "losses": 0},
    }
if "global_arguments" not in st.session_state:
    st.session_state.global_arguments = []
if "debate_history" not in st.session_state:
    st.session_state.debate_history = []
# --- Providers (Fixed Mistral Model) ---
PROVIDERS = {
    "🤍 Auto": {"provider": "auto", "model": None, "type": None, "base_url": None},
    "Groq (Llama 3.3)": {"provider": "groq", "model": "llama-3.3-70b-versatile", "type": "openai", "base_url": "https://api.groq.com/openai/v1"},
    "DeepSeek": {"provider": "deepseek", "model": "deepseek-chat", "type": "openai", "base_url": "https://api.deepseek.com"},
    "Mistral (Small)": {"provider": "mistral", "model": "mistral-small-latest", "type": "openai", "base_url": "https://api.mistral.ai/v1"},
    "Cerebras (Llama)": {"provider": "cerebras", "model": "llama-3.3-70b", "type": "openai", "base_url": "https://api.cerebras.ai/v1"},
    "OpenRouter": {"provider": "openrouter", "model": "openrouter/auto", "type": "openai", "base_url": "https://openrouter.ai/api/v1"},
    "Google (Gemma)": {"provider": "google", "model": "gemma-4-26b-it", "type": "google", "base_url": None},
}

PROVIDER_API_KEYS = {
    "groq": st.secrets.get("GROQ_API_KEY", ""),
    "deepseek": st.secrets.get("DEEPSEEK_API_KEY", ""),
    "mistral": st.secrets.get("MISTRAL_API_KEY", ""),
    "cerebras": st.secrets.get("CEREBRAS_API_KEY", ""),
    "openrouter": st.secrets.get("OPENROUTER_API_KEY", ""),
    "google": st.secrets.get("GEMINI_API_KEY", ""),
}

MODEL_KEYWORDS = {
    "philosoph": ["Mistral (Small)"],
    "ethics": ["Mistral (Small)"],
    "tech": ["Groq (Llama 3.3)"],
    "future": ["Groq (Llama 3.3)"],
    "data": ["Cerebras (Llama)"],
    "science": ["Cerebras (Llama)"],
    "conspiracy": ["DeepSeek"],
    "policy": ["OpenRouter"],
    "google": ["Google (Gemma)"],
}

def resolve_auto_model(topic: str) -> str:
    topic_lower = topic.lower()
    for keyword, models in MODEL_KEYWORDS.items():
        if keyword in topic_lower:
            return models[0]
    return "Groq (Llama 3.3)"

def get_actual_model_config(selected_display: str, topic: str = ""):
    if selected_display == "🤍 Auto":
        selected_display = resolve_auto_model(topic)
        st.toast(f"🤍 Auto → {selected_display}", icon="✨")
    config = PROVIDERS[selected_display].copy()
    provider = config["provider"]
    config["api_key"] = PROVIDER_API_KEYS.get(provider, "")
    if not config["api_key"]:
        for fallback in ["groq", "deepseek", "mistral", "cerebras", "openrouter", "google"]:
            key = PROVIDER_API_KEYS.get(fallback, "")
            if key:
                fallback_display = next(k for k,v in PROVIDERS.items() if v["provider"]==fallback)
                config = PROVIDERS[fallback_display].copy()
                config["api_key"] = key
                st.toast(f"⚠️ Fallback → {fallback}", icon="⚠️")
                return config
        st.error("No API keys configured.")
        st.stop()
    return config

def get_client(config):
    if config["type"] == "google":
        import google.generativeai as genai
        genai.configure(api_key=config["api_key"])
        return ("google", genai.GenerativeModel(config["model"]), None)
    else:
        from openai import OpenAI
        client = OpenAI(api_key=config["api_key"], base_url=config["base_url"])
        return ("openai", None, client)

def generate_response(prompt, system_prompt, client_tuple, model_name):
    type_, google_model, openai_client = client_tuple
    if type_ == "google":
        full = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        return google_model.generate_content(full).text
    else:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        resp = openai_client.chat.completions.create(
            model=model_name, messages=messages, temperature=0.7, max_tokens=250
        )
        return resp.choices[0].message.content.strip()

# --- 12 Agents ---
class Agent:
    def __init__(self, name, role, personality, avatar, card_class):
        self.name, self.role, self.personality, self.avatar, self.card_class = name, role, personality, avatar, card_class
        self.history = []
    def speak(self, topic, last_msg, round_num, client_tuple, model_name):
        history = "\n".join(self.history[-3:]) or "No previous chat."
        system_prompt = f"You are {self.name} ({self.role}). {self.personality}"
        prompt = f"""Debate round {round_num} on: "{topic}"
**Claim:** [point] **Evidence:** [fact] **Reasoning:** [why]
History: {history}
Last: "{last_msg}"
"""
        reply = generate_response(prompt, system_prompt, client_tuple, model_name)
        self.history.append(reply)
        return reply

class Moderator(Agent):
    def speak(self, topic, last_msg, round_num, client_tuple, model_name):
        history = "\n".join(self.history[-5:]) or "No debate yet."
        system_prompt = f"You are {self.name}, the moderator. Be sharp and impartial."
        prompt = f"Summarize, note contradictions, ask a provocative question. Topic: {topic} | Round: {round_num}\nHistory: {history}\nLast: {last_msg}"
        reply = generate_response(prompt, system_prompt, client_tuple, model_name)
        self.history.append(reply)
        return reply

def create_full_panel():
    return [
        Agent("Harsh", "Skeptic", "Finds flaws and risks.", "🔴", "card-skeptic"),
        Agent("Jayant", "Optimist", "Sees opportunity.", "🟢", "card-optimist"),
        Moderator("Ahany", "Moderator", "Sharp journalist.", "🔵", "card-skeptic"),
        Agent("Ritik", "Policy Advisor", "Gov/regulation lens.", "🟡", "card-policy"),
        Agent("Kavya", "Retail Investor", "Everyday person.", "🟣", "card-optimist"),
        Agent("Nish", "Scientist", "Empirical evidence.", "🟠", "card-data"),
        Agent("Teju", "Tech Journalist", "Trends and narratives.", "🔷", "card-futurist"),
        Agent("Shivam", "Conspiracy Theorist", "Hidden agendas.", "⚫", "card-conspiracy"),
        Agent("Philosopher", "Philosopher", "Ethical/historical context.", "🟤", "card-philosopher"),
        Agent("Futurist", "Futurist", "50-year perspective.", "🔮", "card-futurist"),
        Agent("DataScientist", "Data Scientist", "Statistics only.", "📊", "card-data"),
        Agent("Ethicist", "Ethicist", "Moral implications.", "⚖️", "card-ethicist"),
    ]

def judge_debate(topic, messages, client_tuple, model_name):
    debate_text = "\n".join(messages[-20:])
    system_prompt = "You are the JUDGE. Deliver a fair, detailed verdict."
    prompt = f"""Debate: "{topic}"\nTranscript: {debate_text}\nProvide: Winner name, 2-sentence reasoning, and final takeaway."""
    return generate_response(prompt, system_prompt, client_tuple, model_name)

def generate_pdf(topic, log, verdict, winner):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Nyx Debate Transcript", ln=1)
    pdf.cell(200, 10, txt=f"Topic: {topic}", ln=1)
    pdf.ln(5)
    for msg in log:
        clean = msg.encode('latin-1','replace').decode('latin-1')
        pdf.multi_cell(0, 8, txt=clean)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt=f"Winner: {winner}", ln=1)
    pdf.multi_cell(0, 8, txt=verdict.encode('latin-1','replace').decode('latin-1'))
    return pdf.output(dest='S').encode('latin-1')
# --- UI Header ---
st.markdown('<div class="nyx-title">Nyx</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">— AI DEBATE ARENA —</div>', unsafe_allow_html=True)

# --- Input Card ---
with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    topic = st.text_input("Debate Topic", value="Should AI have a conscience?", placeholder="Ask anything...", label_visibility="collapsed")
    col1, col2 = st.columns([3, 2])
    with col1:
        selected_model = st.selectbox("Model", list(PROVIDERS.keys()), index=0)
    with col2:
        rounds = st.select_slider("Rounds", options=[2, 3, 4, 5], value=3)
    show_args = st.checkbox("Show full debate arguments", value=True)
    launch = st.button("▶ Initiate Debate", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- Debate Execution ---
if launch and topic:
    st.session_state.global_arguments = []
    st.session_state.debate_history = []
    
    config = get_actual_model_config(selected_model, topic)
    client_tuple = get_client(config)
    model_name = config["model"]
    
    agents = create_full_panel()
    log = []
    last_msg = "Let's begin."
    winner = None
    verdict = ""
    
    if show_args:
        st.markdown("### ⚔️ THE ARENA")
    
    for r in range(1, rounds+1):
        if show_args:
            st.markdown(f"**Round {r}**")
        round_msgs = []
        order = [a for a in agents if a.name != "Ahany"]
        for agent in order:
            reply = agent.speak(topic, last_msg, r, client_tuple, model_name)
            if show_args:
                st.markdown(f"""
                <div class="debate-card {agent.card_class}">
                    <div class="agent-name">{agent.avatar} {agent.name} · {agent.role}</div>
                    <div class="agent-message">{reply}</div>
                </div>
                """, unsafe_allow_html=True)
            round_msgs.append(f"{agent.avatar} {agent.name}: {reply}")
            last_msg = reply
            time.sleep(0.6)
        
        mod = next(a for a in agents if a.name == "Ahany")
        mod_reply = mod.speak(topic, last_msg, r, client_tuple, model_name)
        if show_args:
            st.markdown(f"""
            <div class="debate-card" style="border-left-color:#D4A5A5;">
                <div class="agent-name">{mod.avatar} {mod.name} · Moderator</div>
                <div class="agent-message">{mod_reply}</div>
            </div>
            """, unsafe_allow_html=True)
        round_msgs.append(f"{mod.avatar} {mod.name}: {mod_reply}")
        last_msg = mod_reply
        log.append("\n".join(round_msgs))
    
    st.session_state.debate_history = log
    
    with st.spinner("Judgment in progress..."):
        verdict = judge_debate(topic, log, client_tuple, model_name)
    match = re.search(r"Winner:?\s*(\w+)", verdict, re.IGNORECASE)
    winner = match.group(1) if match else "Unknown"
    
    for agent in st.session_state.agent_stats:
        if agent == winner:
            st.session_state.agent_stats[agent]["wins"] += 1
        else:
            st.session_state.agent_stats[agent]["losses"] += 1
    
    st.markdown(f"""
    <div class="verdict-box">
        <h3>🏆 {winner}</h3>
        <p>{verdict}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # --- Follow‑up Layer ---
    with st.container():
        st.markdown('<div class="glass-card" style="margin-top:0.5rem;">', unsafe_allow_html=True)
        st.markdown("**💬 Continue the discussion**")
        follow_up = st.text_input("Ask a follow‑up question...", placeholder="e.g., 'Why that winner?' or 'What was the weakest argument?'", key="follow_up", label_visibility="collapsed")
        if st.button("Ask", key="ask_follow") and follow_up:
            context = "\n".join(st.session_state.debate_history[-5:])
            prompt = f"Previous debate on '{topic}':\n{context}\n\nUser asks: {follow_up}\n\nRespond helpfully in 2-3 sentences."
            reply = generate_response(prompt, None, client_tuple, model_name)
            st.markdown(f"""
            <div class="debate-card" style="border-left-color:#D4A5A5;">
                <div class="agent-name">💬 Nyx</div>
                <div class="agent-message">{reply}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Stats expander
    with st.expander("📊 Agent Win Rates"):
        for agent, s in st.session_state.agent_stats.items():
            total = s['wins']+s['losses']
            rate = f"{s['wins']/total*100:.0f}%" if total else "0%"
            st.text(f"{agent}: {s['wins']}W / {s['losses']}L ({rate})")
    
    # Share & PDF
    share = f"Nyx verdict: {winner} wins on '{topic}'"
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f'<a href="https://twitter.com/intent/tweet?text={urllib.parse.quote(share)}" target="_blank"><button style="width:100%;background:#1DA1F2;color:white;border:none;border-radius:60px;padding:0.5rem;">🐦 Tweet</button></a>', unsafe_allow_html=True)
    with col_b:
        pdf = generate_pdf(topic, log, verdict, winner)
        st.download_button("📄 PDF", pdf, f"nyx_{datetime.now():%Y%m%d_%H%M}.pdf")

# --- Footer ---
st.markdown('<div style="text-align:center; margin-top:2rem; opacity:0.6; font-family:\'Playfair Display\',serif; font-style:italic;">✨ Harsh Dubey · Nyx ✨</div>', unsafe_allow_html=True)