import streamlit as st
import time
import re
import json
import os
from datetime import datetime
from openai import OpenAI

# --- Page Config ---
st.set_page_config(
    page_title="Nyx · by Harsh",
    page_icon="🤍",
    layout="wide",
    initial_sidebar_state="expanded"
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

    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.55) !important;
        backdrop-filter: blur(24px) !important;
        -webkit-backdrop-filter: blur(24px) !important;
        border-right: 0.5px solid var(--glass-border) !important;
        box-shadow: 4px 0 20px rgba(0,0,0,0.02) !important;
    }
    [data-testid="stSidebar"] .block-container {
        padding: 2rem 1.5rem !important;
    }

    .main .block-container {
        padding: 2rem 2rem 2rem 2rem !important;
        max-width: 900px !important;
        margin: 0 auto !important;
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
        opacity: 0.7;
        margin-bottom: 0.5rem;
        font-size: 1rem;
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
    .card-psychologist { border-left-color: #F0B5C0; }
    .card-economist { border-left-color: #C0B5D4; }
    .card-technologist { border-left-color: #A5D4D0; }
    .card-legal { border-left-color: #D4C0A5; }
    .verdict-box {
        background: rgba(255, 255, 255, 0.5);
        backdrop-filter: blur(20px);
        border-radius: 28px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border-left: 5px solid var(--rose-gold);
        font-family: 'Courier Prime', monospace;
    }
    .round-tracker {
        text-align: center;
        margin: 0.5rem 0 0.8rem;
        font-weight: 600;
        font-size: 1.1rem;
        opacity: 0.8;
    }
    .copy-btn {
        background: transparent;
        border: 1px solid var(--rose-gold);
        border-radius: 20px;
        padding: 0.3rem 1rem;
        font-size: 0.8rem;
        cursor: pointer;
        color: var(--rose-gold);
    }
</style>
""", unsafe_allow_html=True)

# --- Session State ---
if "debate_history" not in st.session_state:
    st.session_state.debate_history = []
if "saved_history" not in st.session_state:
    st.session_state.saved_history = []  # local lightweight history

# --- API Providers (7 providers) ---
PROVIDERS = [
    {"name": "Groq", "key": st.secrets.get("GROQ_API_KEY"), "base": "https://api.groq.com/openai/v1", "model": "llama-3.3-70b-versatile"},
    {"name": "DeepSeek", "key": st.secrets.get("DEEPSEEK_API_KEY"), "base": "https://api.deepseek.com", "model": "deepseek-chat"},
    {"name": "Cerebras", "key": st.secrets.get("CEREBRAS_API_KEY"), "base": "https://api.cerebras.ai/v1", "model": "llama3.3-70b"},
    {"name": "OpenRouter", "key": st.secrets.get("OPENROUTER_API_KEY"), "base": "https://openrouter.ai/api/v1", "model": "openrouter/auto"},
    {"name": "Mistral", "key": st.secrets.get("MISTRAL_API_KEY"), "base": "https://api.mistral.ai/v1", "model": "mistral-small-2409"},
    {"name": "Google", "key": st.secrets.get("GEMINI_API_KEY"), "base": "https://generativelanguage.googleapis.com/v1beta", "model": "gemini-2.0-flash"},
    {"name": "NVIDIA", "key": st.secrets.get("NVIDIA_API_KEY"), "base": "https://integrate.api.nvidia.com/v1", "model": "meta/llama-3.3-70b-instruct"},
]

def get_client(provider):
    return OpenAI(api_key=provider["key"], base_url=provider["base"])

def generate_with_fallback(prompt, system="", preferred=None, silent_fail=False):
    if preferred:
        providers = [p for p in PROVIDERS if p["name"] == preferred] + [p for p in PROVIDERS if p["name"] != preferred]
    else:
        providers = PROVIDERS
    last_error = None
    for p in providers:
        if not p["key"]:
            continue
        try:
            if p["name"] == "Google":
                import google.generativeai as genai
                genai.configure(api_key=p["key"])
                model = genai.GenerativeModel(p["model"])
                full_prompt = f"{system}\n\n{prompt}" if system else prompt
                resp = model.generate_content(full_prompt)
                return resp.text.strip(), p["name"]
            else:
                client = OpenAI(api_key=p["key"], base_url=p["base"])
                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})
                resp = client.chat.completions.create(model=p["model"], messages=messages, temperature=0.7, max_tokens=250)
                return resp.choices[0].message.content.strip(), p["name"]
        except:
            continue
    if silent_fail:
        return "Unable to generate response.", "None"
    else:
        st.warning("All providers temporarily unavailable.")
        return "Response unavailable.", "None"

# --- 16 Agents ---
class Agent:
    def __init__(self, name, role, personality, avatar, card_class):
        self.name, self.role, self.personality, self.avatar, self.card_class = name, role, personality, avatar, card_class
        self.history = []
    def speak(self, topic, last_msg, round_num, preferred_provider, tone):
        history = "\n".join(self.history[-3:]) or "No previous chat."
        tone_instr = f"Respond in a {tone} tone." if tone else ""
        system = f"You are {self.name} ({self.role}). {self.personality}. {tone_instr}"
        prompt = f"""Debate round {round_num} on: "{topic}"
**Claim:** [point] **Evidence:** [fact] **Reasoning:** [why]
History: {history}
Last: "{last_msg}"
"""
        reply, _ = generate_with_fallback(prompt, system, preferred_provider)
        self.history.append(reply)
        return reply

class Moderator(Agent):
    def speak(self, topic, last_msg, round_num, preferred_provider, tone):
        history = "\n".join(self.history[-5:]) or "No debate yet."
        system = f"You are {self.name}, the moderator. Be sharp and impartial."
        prompt = f"Summarize, note contradictions, ask a provocative question. Topic: {topic} | Round: {round_num}\nHistory: {history}\nLast: {last_msg}"
        reply, _ = generate_with_fallback(prompt, system, preferred_provider)
        self.history.append(reply)
        return reply

ALL_AGENTS = [
    ("Harsh", "Skeptic", "Finds flaws and risks.", "🔴", "card-skeptic"),
    ("Jayant", "Optimist", "Sees opportunity.", "🟢", "card-optimist"),
    ("Ahany", "Moderator", "Sharp journalist.", "🔵", "card-skeptic", True),
    ("Ritik", "Policy Advisor", "Gov/regulation lens.", "🟡", "card-policy"),
    ("Kavya", "Retail Investor", "Everyday person.", "🟣", "card-optimist"),
    ("Nish", "Scientist", "Empirical evidence.", "🟠", "card-data"),
    ("Teju", "Tech Journalist", "Trends and narratives.", "🔷", "card-futurist"),
    ("Shivam", "Conspiracy Theorist", "Hidden agendas.", "⚫", "card-conspiracy"),
    ("Philosopher", "Philosopher", "Ethical/historical context.", "🟤", "card-philosopher"),
    ("Futurist", "Futurist", "50‑year perspective.", "🔮", "card-futurist"),
    ("DataScientist", "Data Scientist", "Statistics only.", "📊", "card-data"),
    ("Ethicist", "Ethicist", "Moral implications.", "⚖️", "card-ethicist"),
    ("Psychologist", "Psychologist", "Human behavior & cognitive biases.", "🧠", "card-psychologist"),
    ("Economist", "Economist", "Financial & market impact.", "📈", "card-economist"),
    ("Technologist", "Technologist", "Cutting‑edge tech feasibility.", "💻", "card-technologist"),
    ("Legal Expert", "Legal Expert", "Laws, regulations & precedents.", "⚖️", "card-legal"),
]

def create_panel(selected_agents):
    """Create panel from selected agent names. Always includes moderator at position 2."""
    agents = []
    moderator = None
    for name, role, pers, av, card in ALL_AGENTS:
        if name not in selected_agents:
            continue
        if name == "Ahany":
            moderator = Moderator(name, role, pers, av, card)
        else:
            agents.append(Agent(name, role, pers, av, card))
    if moderator and len(agents) >= 2:
        agents.insert(2, moderator)
    return agents

# --- Swarm Mode Prompts ---
SWARM_MODES = {
    "Debate": "Argue your position strongly. Challenge the other side.",
    "Council": "Collaborate towards a consensus recommendation.",
    "Devil's Advocate": "If you are the Devil's Advocate, push back aggressively on every point.",
    "Exploration": "Explore a unique angle independently.",
    "Rapid Fire": "Keep arguments very short, 1-2 sentences.",
}
# ===================== SIDEBAR =====================
with st.sidebar:
    st.markdown("### 🌑 Nyx")
    st.markdown("---")

    # Kernel / model selection
    st.markdown("### 🤖 Kernel")
    model_choice = st.selectbox("Active model", ["Groq", "DeepSeek", "Cerebras", "OpenRouter", "Mistral", "Google", "NVIDIA", "🤖 Auto"], index=7)
    preferred = None if model_choice == "🤖 Auto" else model_choice

    st.markdown("---")
    st.markdown("### ⚙️ Swarm Mode")
    swarm_mode = st.selectbox("Mode", list(SWARM_MODES.keys()), index=0)

    st.markdown("### 🎙️ Tone")
    tone = st.selectbox("Tone", ["Neutral", "Casual", "Academic", "Brutal"], index=0)

    st.markdown("### 🧑‍🤝‍🧑 Agent Picker")
    # Preselect default 4 agents
    default_agents = ["Harsh", "Jayant", "Ahany", "Nish"]
    all_agent_names = [a[0] for a in ALL_AGENTS]
    selected_agents = st.multiselect(
        "Choose panelists",
        options=all_agent_names,
        default=default_agents,
        help="Pick at least 3 agents (including moderator)."
    )
    if len(selected_agents) < 3:
        st.warning("Select at least 3 agents.")
        st.stop()

    rounds = st.select_slider("Depth (rounds)", options=[2, 3, 4], value=3)
    show_args = st.checkbox("Show arguments", value=True)

    st.markdown("---")
    st.markdown("### ⏳ Recent Debates")
    if st.session_state.saved_history:
        for i, past in enumerate(st.session_state.saved_history[-5:]):
            if st.button(f"{past['topic'][:30]}... ({past['date']})", key=f"hist_{i}"):
                st.session_state["replay_topic"] = past['topic']
    else:
        st.caption("No debates yet.")

    st.markdown("---")
    st.markdown("<p style='text-align:center;color:var(--rose-gold);'>by Harsh Dubey</p>", unsafe_allow_html=True)

# ===================== MAIN AREA =====================
st.markdown('<div class="nyx-title">Nyx</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">AI Swarm Intelligence — Your problem, debated by experts.</div>', unsafe_allow_html=True)

# Topic suggestions
st.caption("💡 Try: Is remote work better than office? · Should I learn Python or JavaScript? · Is AI art real art?")

# Topic input
with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    topic = st.text_input("Ask anything...", value="", placeholder="Ask anything...", label_visibility="collapsed")
    launch = st.button("Start Debate", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ===================== DEBATE EXECUTION =====================
if launch and topic:
    if len(selected_agents) < 3:
        st.error("Please select at least 3 agents (including moderator).")
        st.stop()

    agents = create_panel(selected_agents)
    log = []
    last_msg = "Let's begin."
    winner = None
    verdict = ""
    used_provider = None
    fallback_warning = False

    if show_args:
        st.markdown("### ⚔️ THE ARENA")

    for r in range(1, rounds+1):
        st.markdown(f'<div class="round-tracker">Round {r} of {rounds}</div>', unsafe_allow_html=True)
        round_msgs = []
        order = [a for a in agents if a.name != "Ahany"]

        persona_html = " · ".join([f"{a.avatar} {a.name}" for a in order])
        st.markdown(f'<div style="text-align:center;opacity:0.6;margin-bottom:0.8rem;">{persona_html}</div>', unsafe_allow_html=True)

        for agent in order:
            # Thinking indicator
            with st.spinner(f"{agent.name} is thinking..."):
                reply, provider = generate_with_fallback(
                    f"Round {r} on '{topic}'. History: {last_msg}",
                    f"You are {agent.name} ({agent.role}). {agent.personality}. Mode: {swarm_mode}. Tone: {tone}.",
                    preferred
                )
            if used_provider and provider != used_provider:
                fallback_warning = True
            used_provider = provider

            if show_args:
                with st.expander(f"{agent.avatar} {agent.name} · {agent.role}", expanded=True):
                    st.markdown(f'<div class="debate-card {agent.card_class}">{reply}</div>', unsafe_allow_html=True)
            round_msgs.append(f"{agent.avatar} {agent.name}: {reply}")
            last_msg = reply
            time.sleep(0.8)

        mod = next((a for a in agents if a.name == "Ahany"), None)
        if mod:
            mod_reply, provider = generate_with_fallback(
                f"Moderate round {r} on '{topic}'. Last: {last_msg}",
                f"You are {mod.name}, the moderator.",
                preferred
            )
            if show_args:
                with st.expander(f"{mod.avatar} {mod.name} · Moderator", expanded=True):
                    st.markdown(f'<div class="debate-card" style="border-left-color:#D4A5A5;">{mod_reply}</div>', unsafe_allow_html=True)
            round_msgs.append(f"{mod.avatar} {mod.name}: {mod_reply}")
            last_msg = mod_reply
        log.append("\n".join(round_msgs))

    st.session_state.debate_history = log

    if used_provider:
        st.caption(f"⚙️ Powered by {used_provider}")
    if fallback_warning:
        st.warning("⚠️ The primary provider was unavailable; the debate automatically switched to a backup model.")

    with st.spinner("Judgment..."):
        verdict_prompt = f"""You are the JUDGE of a debate. Swarm mode: {swarm_mode}. Tone: {tone}.
Debate Topic: "{topic}"
Transcript: {' '.join(log)}

Return your verdict in exactly this format:
Winner: [Name]
Reasoning: [2-3 sentences]
Confidence: [1-10]
Recommended Action: [1 sentence]
Logic: [1-10]
Evidence: [1-10]
Rebuttal: [1-10]
Persuasiveness: [1-10]
Takeaway: [1 sentence]
"""
        verdict, _ = generate_with_fallback(verdict_prompt, "You are an impartial expert judge.", preferred="Groq", silent_fail=True)

    # Parse verdict
    def extract(pattern, text):
        m = re.search(pattern, text)
        return m.group(1).strip() if m else "?"

    winner = extract(r"Winner:\s*(.+)", verdict)
    reasoning = extract(r"Reasoning:\s*(.+)", verdict)
    confidence = extract(r"Confidence:\s*(.+)", verdict)
    action = extract(r"Recommended Action:\s*(.+)", verdict)
    logic = extract(r"Logic:\s*(.+)", verdict)
    evidence = extract(r"Evidence:\s*(.+)", verdict)
    rebuttal = extract(r"Rebuttal:\s*(.+)", verdict)
    persuasiveness = extract(r"Persuasiveness:\s*(.+)", verdict)
    takeaway = extract(r"Takeaway:\s*(.+)", verdict)

    # Actionable Verdict box
    st.markdown(f"""
    <div class="verdict-box">
        <h3>🏆 {winner}</h3>
        <p><strong>Reasoning:</strong> {reasoning}</p>
        <p><strong>Confidence:</strong> {confidence}/10</p>
        <p><strong>Recommended Action:</strong> {action}</p>
        <hr style="margin:1rem 0;border:0.5px solid rgba(0,0,0,0.1);"/>
        <div style="display:flex;flex-wrap:wrap;gap:1rem;font-size:0.9rem;">
            <div><strong>Logic:</strong> {logic}/10</div>
            <div><strong>Evidence:</strong> {evidence}/10</div>
            <div><strong>Rebuttal:</strong> {rebuttal}/10</div>
            <div><strong>Persuasiveness:</strong> {persuasiveness}/10</div>
        </div>
        <p style="margin-top:1rem;"><strong>Takeaway:</strong> {takeaway}</p>
    </div>
    """, unsafe_allow_html=True)

    # Copy verdict button
    verdict_text = f"Nyx Verdict on '{topic}'\nWinner: {winner}\nReasoning: {reasoning}\nConfidence: {confidence}/10\nAction: {action}\nLogic: {logic} | Evidence: {evidence} | Rebuttal: {rebuttal} | Persuasiveness: {persuasiveness}\nTakeaway: {takeaway}"
    st.caption("📋 Verdict copied to clipboard" if st.button("📋 Copy Verdict") and st.session_state.__setitem__("clipboard", verdict_text) else "")

    # Save to lightweight history
    st.session_state.saved_history.append({
        "topic": topic,
        "winner": winner,
        "date": datetime.now().strftime("%b %d"),
        "verdict": verdict_text
    })
    if len(st.session_state.saved_history) > 10:
        st.session_state.saved_history = st.session_state.saved_history[-10:]

# --- Footer ---
st.markdown('<div style="text-align:center; margin-top:2rem; opacity:0.6; font-family:\'Playfair Display\',serif; font-style:italic;">✨ Harsh Dubey · Nyx ✨</div>', unsafe_allow_html=True)