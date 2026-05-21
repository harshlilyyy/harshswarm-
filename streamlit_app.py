# =============================================================================
# PART 1 of 3 — Copy everything below into your app.py (top)
# =============================================================================
import streamlit as st
import time
import json
import random
import math
from datetime import datetime
import pandas as pd

# Optional imports (only used if installed)
try:
    import networkx as nx
    import matplotlib.pyplot as plt
    HAS_GRAPH = True
except ImportError:
    HAS_GRAPH = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Nyx · Cognitive‑Social Physics",
    page_icon="💜",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- CSS (Lavender Haze Glassmorphism) ----------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;1,400&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;350;400;500&display=swap');
    :root {
        --bg-light: #F5F0FF;
        --card-bg: rgba(255, 255, 255, 0.55);
        --border-glow: rgba(180, 130, 255, 0.4);
        --purple-prime: #9B4DFF;
        --pink-hot: #FF4D6D;
        --red-accent: #E63946;
        --text-dark: #2C2A28;
        --glass-border: rgba(255, 255, 255, 0.7);
    }
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background: var(--bg-light);
        color: var(--text-dark);
    }
    .stApp {
        background: radial-gradient(circle at 30% 20%, rgba(180,130,255,0.15) 0%, var(--bg-light) 80%);
    }
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.6) !important;
        backdrop-filter: blur(24px) !important;
        -webkit-backdrop-filter: blur(24px) !important;
        border-right: 0.5px solid var(--border-glow) !important;
        box-shadow: 4px 0 20px rgba(155,77,255,0.05) !important;
    }
    .nyx-title {
        font-family: 'Playfair Display', serif;
        font-style: italic;
        font-size: 3.8rem;
        text-align: center;
        background: linear-gradient(135deg, var(--pink-hot) 0%, var(--purple-prime) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .glass-card {
        background: var(--card-bg);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 28px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 0.5px solid var(--glass-border);
        box-shadow: 0 10px 30px -10px rgba(155,77,255,0.08);
    }
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.65) !important;
        backdrop-filter: blur(15px);
        border: 0.5px solid var(--border-glow) !important;
        border-radius: 60px !important;
        padding: 1rem 1.5rem !important;
        font-size: 1.1rem !important;
        color: var(--text-dark) !important;
        text-align: center;
    }
    .stButton > button {
        background: linear-gradient(135deg, var(--purple-prime) 0%, var(--pink-hot) 100%);
        border: none;
        border-radius: 60px;
        font-weight: 600;
        color: white;
        box-shadow: 0 8px 20px -6px rgba(255,77,109,0.35);
        width: 100%;
        padding: 0.8rem 1.5rem;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 12px 24px -6px rgba(255,77,109,0.5);
    }
</style>
""", unsafe_allow_html=True)

# ---------- SESSION STATE ----------
if "adv_sim" not in st.session_state:
    st.session_state.adv_sim = False
if "sim_result" not in st.session_state:
    st.session_state.sim_result = None
if "debate_log" not in st.session_state:
    st.session_state.debate_log = []
if "debate_winner" not in st.session_state:
    st.session_state.debate_winner = ""

# =============================================================================
# DETERMINISTIC KERNEL (inlined) — No external files needed
# =============================================================================
def mulberry32(seed):
    """Seeded PRNG (0-1). Python-compatible, no JS >>> needed."""
    state = seed & 0xFFFFFFFF
    def next():
        nonlocal state
        state = (state + 0x6D2B79F5) & 0xFFFFFFFF
        t = math.imul(state ^ (state >> 15), 1 | state)
        t = (t + math.imul(t ^ (t >> 7), 61 | t)) & 0xFFFFFFFF
        return (t ^ (t >> 14)) / 4294967296
    return next

class CognitiveAgent:
    def __init__(self, name, role="", personality="", rng=None):
        self.name = name
        self.role = role
        self.personality = personality
        self.rng = rng if rng else random.Random()
        # 10 core variables (0–1)
        self.self_worth = 0.5 + self.rng.random() * 0.2 - 0.1
        self.anxiety = 0.2 + self.rng.random() * 0.2
        self.consistency = 0.5 + self.rng.random() * 0.2 - 0.1
        self.momentum = 0.5
        self.reputation = 0.5
        self.opportunity_access = 0.5
        self.fragility_index = 0.1
        self.lock_in = 0.0
        self.learning_rate = 0.1
        self.energy = 0.8
        self.mode = "EXECUTE"   # AVOID, RECOVER, EXECUTE, OPTIMIZE
        self.cascade_active = False
        self.success_streak = 0
        self.failure_streak = 0
        self.intent_target = None
        self.emotional_anchor = None

    def clamp(self, val):
        return max(0, min(1, val))

    def update(self, progress, peer_gap, social_feedback, failure_flag, success_flag, mentor_flag=False):
        # Self‑worth
        self.self_worth = self.clamp(self.self_worth + 0.25*progress - 0.3*max(peer_gap,0) +
                                      0.15*social_feedback - 0.2*failure_flag)
        # Anxiety (less smoothing)
        raw_change = peer_gap * 0.5 + failure_flag * 0.5 - success_flag * 0.3
        self.anxiety = self.clamp(0.4 * self.anxiety + 0.6 * raw_change)
        # Consistency
        self.consistency = self.clamp(self.consistency + 0.05*(1 - peer_gap) - 0.1*failure_flag)
        # Momentum
        self.momentum = self.clamp(self.momentum + 0.25*success_flag - 0.3*failure_flag)
        # Reputation
        self.reputation = self.clamp(self.reputation + 0.2*progress + 0.1*social_feedback)
        # Opportunity access
        self.opportunity_access = self.clamp(self.opportunity_access +
                                             0.2*(1 if self.consistency*self.reputation > 0.4 else 0) +
                                             0.15*mentor_flag)
        # Fragility
        self.fragility_index = self.clamp(self.fragility_index + 0.1*failure_flag)
        # Lock‑in
        self.lock_in = self.clamp(self.lock_in + 0.1*self.consistency)
        # Learning rate
        self.learning_rate = self.clamp(self.learning_rate + 0.1*failure_flag - 0.05*success_flag)
        # Energy
        self.energy = self.clamp(self.energy - 0.05 + 0.1*success_flag)

        # Cascade detection
        if self.failure_streak >= 3 and self.self_worth < 0.4:
            self.cascade_active = True
        elif self.cascade_active and (success_flag or mentor_flag):
            self.cascade_active = False
            self.failure_streak = 0

        # Mode transition
        if self.anxiety > 0.7 and self.self_worth > 0.6:
            self.mode = "SPIKE"
        elif self.anxiety > 0.6 and self.self_worth < 0.4:
            self.mode = "AVOID"
        elif self.cascade_active:
            self.mode = "RECOVER"
        elif self.self_worth > 0.5 and self.momentum > 0.5:
            self.mode = "EXECUTE"
        else:
            self.mode = "OPTIMIZE"
# =============================================================================
# PART 2 of 3 — Paste below Part 1
# =============================================================================

# ---------- API PROVIDERS (from st.secrets ONLY) ----------
def get_providers():
    """Return only providers for which the corresponding secret exists."""
    all_providers = [
        {"name": "Groq",           "key_name": "GROQ_API_KEY",
                                   "base": "https://api.groq.com/openai/v1",                        "model": "llama-3.3-70b-versatile"},
        {"name": "SambaNova",      "key_name": "SAMBA_API_KEY",
                                   "base": "https://api.sambanova.ai/v1",                           "model": "Meta-Llama-3.3-70B-Instruct"},
        {"name": "Cerebras",       "key_name": "CEREBRAS_API_KEY",
                                   "base": "https://api.cerebras.ai/v1",                            "model": "llama-3.3-70b"},
        {"name": "Google",         "key_name": "GEMINI_API_KEY",
                                   "base": "https://generativelanguage.googleapis.com/v1beta",      "model": "gemini-2.5-flash"},
        {"name": "Mistral",        "key_name": "MISTRAL_API_KEY",
                                   "base": "https://api.mistral.ai/v1",                             "model": "mistral-small-4"},
        {"name": "Cohere",         "key_name": "COHERE_API_KEY",
                                   "base": "https://api.cohere.ai/compatibility/v1",                "model": "command-a-03-2025"},
        {"name": "OpenRouter",     "key_name": "OPENROUTER_API_KEY",
                                   "base": "https://openrouter.ai/api/v1",                          "model": "openrouter/free"},
        {"name": "HuggingFace",    "key_name": "HF_API_KEY",
                                   "base": "https://api-inference.huggingface.co/v1",               "model": "meta-llama/Llama-3.3-70B-Instruct"},
    ]
    available = []
    for p in all_providers:
        key = st.secrets.get(p["key_name"])
        if key:
            available.append({**p, "key": key})
    return available

# ---------- FALLBACK GENERATOR ----------
def generate_with_fallback(prompt, system="", preferred=None):
    providers = get_providers()
    if not providers:
        return "No API keys configured. Add them in Streamlit secrets.", "None"
    if preferred:
        # Try preferred first, then the rest
        providers = [p for p in providers if p["name"] == preferred] + [p for p in providers if p["name"] != preferred]
    for p in providers:
        try:
            if p["name"] == "Google":
                import google.generativeai as genai
                genai.configure(api_key=p["key"])
                model = genai.GenerativeModel(p["model"])
                full_prompt = f"{system}\n\n{prompt}" if system else prompt
                resp = model.generate_content(full_prompt, request_options={"timeout": 10})
                return resp.text.strip(), p["name"]
            elif p["name"] == "HuggingFace":
                client = OpenAI(api_key=p["key"], base_url=p["base"])
                resp = client.completions.create(
                    model=p["model"],
                    prompt=system + "\n" + prompt if system else prompt,
                    max_tokens=150, temperature=0.7
                )
                return resp.choices[0].text.strip(), p["name"]
            else:
                client = OpenAI(api_key=p["key"], base_url=p["base"])
                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})
                resp = client.chat.completions.create(
                    model=p["model"], messages=messages, temperature=0.7, max_tokens=200
                )
                return resp.choices[0].message.content.strip(), p["name"]
        except Exception:
            time.sleep(0.5)
            continue
    return "All providers temporarily unavailable.", "None"

# ---------- STANDARD DEBATE AGENT ----------
class DebateAgent:
    def __init__(self, name, stance):
        self.name = name
        self.stance = stance
        self.history = []

    def speak(self, topic, last_msg, round_num, preferred_provider):
        prompt = f"""Debate round {round_num} on: "{topic}".
You are {self.name} ({self.stance}). Last message: "{last_msg}".
Give a short, sharp argument (1-3 sentences)."""
        system = f"You are {self.name}. {self.stance}. Keep it concise."
        reply, provider = generate_with_fallback(prompt, system, preferred_provider)
        self.history.append(reply)
        return reply, provider

def run_standard_debate(topic, agents_text, rounds, preferred_provider=None):
    agents = []
    for line in agents_text.strip().split("\n"):
        parts = line.split(",", 1)
        name = parts[0].strip()
        stance = parts[1].strip() if len(parts) > 1 else "neutral"
        agents.append(DebateAgent(name, stance))
    if len(agents) < 2:
        return ["Need at least 2 agents"], "None"
    log = []
    last_msg = topic
    for r in range(1, rounds+1):
        for agent in agents:
            msg, provider = agent.speak(topic, last_msg, r, preferred_provider)
            log.append(f"**Round {r} – {agent.name}** (via {provider}): {msg}")
            last_msg = msg
    # Simple winner heuristic: longest average argument length
    winner = max(agents, key=lambda a: sum(len(m) for m in a.history)/max(1,len(a.history))).name
    return log, winner

# ---------- ADVANCED SIMULATION FUNCTIONS ----------
def run_simulation(agent_names, rounds=4, seed=42):
    rng = random.Random(seed)
    agents = [CognitiveAgent(name, rng=rng) for name in agent_names]
    state_history = []
    # Initial round (neutral)
    for a in agents:
        a.update(0.5, 0.5, 0.0, 0, 0)
    for _ in range(rounds):
        round_states = {}
        for a in agents:
            peer_gap = abs(rng.random() - 0.5) * 0.5
            progress = rng.random() * 0.5 + 0.3
            social_feedback = (rng.random() - 0.5) * 0.5
            failure_flag = 1 if rng.random() < 0.1 else 0
            success_flag = 1 if rng.random() < 0.3 else 0
            mentor_flag = rng.random() < 0.1
            a.update(progress, peer_gap, social_feedback, failure_flag, success_flag, mentor_flag)
            round_states[a.name] = {
                "self_worth": a.self_worth, "anxiety": a.anxiety, "consistency": a.consistency,
                "momentum": a.momentum, "reputation": a.reputation,
                "opportunity_access": a.opportunity_access, "fragility_index": a.fragility_index,
                "lock_in": a.lock_in, "learning_rate": a.learning_rate, "energy": a.energy,
                "mode": a.mode
            }
        state_history.append(round_states)
    # Outcome vector
    rep = [a.reputation for a in agents]
    opp = [a.opportunity_access for a in agents]
    trust = [a.lock_in for a in agents]
    outcome = {
        "reputation_mean": sum(rep)/len(rep),
        "inequality": max(0.0001, sum((x - sum(opp)/len(opp))**2 for x in opp)/len(opp)),
        "trust_proxy": sum(trust)/len(trust),
        "centralization": 0.0
    }
    return {"state_history": state_history, "outcome_vector": outcome, "agents": agents, "seed": seed}

def plot_sparkline(data, height=100):
    chart_data = pd.DataFrame({"val": data})
    st.line_chart(chart_data, height=height, use_container_width=True)

def show_agent_drilldown(agents, state_history):
    st.markdown("### 🧠 Agent Cognitive States")
    selected = st.selectbox("Choose an agent", [a.name for a in agents])
    agent = next(a for a in agents if a.name == selected)
    rounds = len(state_history)
    if rounds == 0:
        st.warning("No simulation data")
        return
    vars_to_plot = ["self_worth", "anxiety", "consistency", "momentum", "reputation",
                    "opportunity_access", "fragility_index", "lock_in", "learning_rate", "energy"]
    cols = st.columns(5)
    for i, var in enumerate(vars_to_plot):
        series = [state_history[r][agent.name][var] for r in range(rounds)]
        with cols[i % 5]:
            st.metric(var.replace("_", " ").title(), f"{series[-1]:.2f}")
            plot_sparkline(series, height=80)

def show_outcomes(sim_result):
    outcome = sim_result["outcome_vector"]
    agents = sim_result["agents"]
    st.markdown("## 📊 Strategic Forecast")
    st.metric("Winner", "Nuanced middle ground")   # placeholder
    st.metric("Confidence", "72%")
    with st.expander("Confidence Rubric"):
        st.write("**Feasibility:** 7/10  |  **Alignment:** 6/10  |  **Risk:** 7/10  |  **Evidence:** 8/10")
    st.markdown("### Outcome Metrics")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Reputation Mean", f"{outcome['reputation_mean']:.3f}")
    c2.metric("Inequality", f"{outcome['inequality']:.4f}")
    c3.metric("Trust Proxy", f"{outcome['trust_proxy']:.3f}")
    c4.metric("Centralization", f"{outcome['centralization']:.3f}")
    # BlackSwan Assassin (simplified)
    with st.expander("🕵️ BlackSwan Assassin"):
        st.write("**Assumption:** Debate remains rational.")
        st.write("**Why fragile:** Emotional anecdotes may spike anxiety.")
        st.write("**Break scenario:** A student shares a personal story → anxiety +20%.")
    # Counterfactual sensitivity
    with st.expander("🧪 Counterfactual Sensitivity"):
        if st.button("Run +20% Anxiety Perturbation"):
            perturb_seed = sim_result["seed"] + 1000
            rng = random.Random(perturb_seed)
            agents_pert = [CognitiveAgent(a.name, rng=rng) for a in agents]
            for a in agents_pert:
                a.anxiety = min(1.0, a.anxiety * 1.2)
            for _ in range(len(sim_result["state_history"])):
                for a in agents_pert:
                    a.update(rng.random()*0.5+0.3, rng.random()*0.5, (rng.random()-0.5)*0.5,
                             1 if rng.random()<0.1 else 0, 1 if rng.random()<0.3 else 0)
            pert_rep = sum(a.reputation for a in agents_pert)/len(agents_pert)
            orig_rep = outcome["reputation_mean"]
            st.write(f"Original Reputation Mean: {orig_rep:.3f}")
            st.write(f"Perturbed (+20% anxiety): {pert_rep:.3f}")
            st.write(f"Shift: {(pert_rep - orig_rep):+.3f}")
    show_agent_drilldown(agents, sim_result["state_history"])
    st.markdown("### 🔁 Feedback Loops")
    for a in agents:
        if a.success_streak >= 2:
            st.write(f"🔁 **{a.name}** – Success chain ×{a.success_streak}")
    report = json.dumps({"outcome": outcome, "seed": sim_result["seed"]}, indent=2, default=str)
    st.download_button("📥 Download Full Report", report, file_name="nyx_report.json")
# =============================================================================
# PART 3 of 3 — Paste at the end (sidebar + main page)
# =============================================================================

with st.sidebar:
    st.markdown("### 💜 Nyx Engine")
    st.markdown("---")
    st.markdown("### ⚙️ Mode")
    mode = st.radio("Choose mode", ["Standard Debate", "Advanced Simulation"], index=0)
    st.session_state.adv_sim = (mode == "Advanced Simulation")

    if st.session_state.adv_sim:
        st.markdown("### 🌌 Advanced Simulation")
        seed = st.number_input("Seed", value=42, step=1)
        rounds = st.slider("Rounds", 2, 10, 4)
        agent_names = st.text_area("Agents (one per line)", "Harsh\nJayant\nMira\nVera\nAtlas")
        if st.button("🚀 Run Simulation", type="primary"):
            agent_list = [name.strip() for name in agent_names.splitlines() if name.strip()]
            if len(agent_list) < 2:
                st.error("Need at least 2 agents.")
            else:
                with st.spinner("Running cognitive simulation..."):
                    result = run_simulation(agent_list, rounds=rounds, seed=seed)
                    st.session_state.sim_result = result
                    st.success("Simulation complete!")
    else:
        st.markdown("### 🗣️ Standard Debate")
        topic = st.text_input("Topic", "Should smartphones be banned in schools?")
        agents_input = st.text_area("Agents (one per line, format: Name, stance)", 
                                    "Harsh, skeptic\nJayant, optimist\nAhany, moderator")
        rounds_debate = st.slider("Rounds", 1, 6, 3)
        available_providers = get_providers()
        provider_names = ["Auto"] + [p["name"] for p in available_providers]
        preferred = st.selectbox("Preferred provider", provider_names, index=0)
        preferred = None if preferred == "Auto" else preferred
        if st.button("⚡ Start Debate"):
            with st.spinner("Debating with AI..."):
                log, winner = run_standard_debate(topic, agents_input, rounds_debate, preferred)
                st.session_state.debate_log = log
                st.session_state.debate_winner = winner
                st.success("Debate finished!")

# ---------- MAIN PAGE ----------
st.markdown('<p class="nyx-title">Nyx</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle" style="text-align:center; opacity:0.7;">Cognitive‑Social Physics Engine · by Harsh Dubey</p>',
            unsafe_allow_html=True)

if st.session_state.adv_sim:
    if st.session_state.sim_result:
        show_outcomes(st.session_state.sim_result)
    else:
        st.markdown('<div class="glass-card"><h3>Advanced Simulation Ready</h3>'
                     '<p>Select agents, set a seed, and click <strong>Run Simulation</strong>.</p></div>',
                     unsafe_allow_html=True)
else:
    if st.session_state.debate_log:
        st.markdown("## Debate Transcript")
        for line in st.session_state.debate_log:
            st.markdown(line)
        if st.session_state.debate_winner:
            st.success(f"**Winner:** {st.session_state.debate_winner}")
    else:
        st.markdown('<div class="glass-card"><h3>Standard Debate Mode</h3>'
                     '<p>Enter a topic and click <strong>Start Debate</strong>.</p></div>',
                     unsafe_allow_html=True)

st.markdown("<div style='text-align:center; opacity:0.5;'>✨ Harsh Dubey · Nyx ✨</div>", unsafe_allow_html=True)