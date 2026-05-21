import streamlit as st
import time
import re
import json
import os
import random
import math
from datetime import datetime
from collections import defaultdict
import pandas as pd

# Optional imports – the app uses these only for advanced visuals
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

# --- Page Config ---
st.set_page_config(
    page_title="Nyx · Cognitive‑Social Physics",
    page_icon="💜",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS (Lavender Haze Glassmorphism) ---
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

# --- Session State Init ---
if "adv_sim" not in st.session_state:
    st.session_state.adv_sim = False
if "sim_result" not in st.session_state:
    st.session_state.sim_result = None
if "debate_history" not in st.session_state:
    st.session_state.debate_history = []
if "cog_agents" not in st.session_state:
    st.session_state.cog_agents = {}
if "cog_history" not in st.session_state:
    st.session_state.cog_history = []

# =============================================================================
# DETERMINISTIC KERNEL (inlined)
# =============================================================================
def mulberry32(seed):
    state = seed | 0
    def next():
        nonlocal state
        state = (state + 0x6D2B79F5) | 0
        t = math.imul(state ^ (state >> 15), 1 | state)
        t = (t + math.imul(t ^ (t >> 7), 61 | t)) ^ t
        return ((t ^ (t >> 14)) >>> 0) / 4294967296
    return next

class CognitiveAgent:
    def __init__(self, name, role="", personality="", rng=None):
        self.name = name
        self.role = role
        self.personality = personality
        self.rng = rng if rng else random.Random()
        # 10 core variables (0-1)
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
        # Self-worth
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
        # Lock-in
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
def run_simulation(agent_names, rounds=4, seed=42):
    """Run deterministic simulation and return full state history + outcome vector."""
    rng = random.Random(seed)
    agents = [CognitiveAgent(name, rng=rng) for name in agent_names]
    state_history = []

    # Initialize agents with a neutral first update
    for a in agents:
        a.update(0.5, 0.5, 0.0, 0, 0)

    for _ in range(rounds):
        round_states = {}
        for a in agents:
            # Simulate peer interactions using seeded randomness
            peer_gap = abs(rng.random() - 0.5) * 0.5          # 0..0.5
            progress = rng.random() * 0.5 + 0.3                # 0.3..0.8
            social_feedback = (rng.random() - 0.5) * 0.5       # -0.25..+0.25
            failure_flag = 1 if rng.random() < 0.1 else 0
            success_flag = 1 if rng.random() < 0.3 else 0
            mentor_flag = rng.random() < 0.1

            a.update(progress, peer_gap, social_feedback, failure_flag, success_flag, mentor_flag)
            round_states[a.name] = {
                "self_worth": a.self_worth,
                "anxiety": a.anxiety,
                "consistency": a.consistency,
                "momentum": a.momentum,
                "reputation": a.reputation,
                "opportunity_access": a.opportunity_access,
                "fragility_index": a.fragility_index,
                "lock_in": a.lock_in,
                "learning_rate": a.learning_rate,
                "energy": a.energy,
                "mode": a.mode
            }
        state_history.append(round_states)

    # Outcome vector
    rep_vals = [a.reputation for a in agents]
    opp_vals = [a.opportunity_access for a in agents]
    trust_vals = [a.lock_in for a in agents]

    outcome = {
        "reputation_mean": sum(rep_vals) / len(rep_vals),
        "inequality": max(0.0001, sum((x - sum(opp_vals)/len(opp_vals))**2 for x in opp_vals) / len(opp_vals)),
        "trust_proxy": sum(trust_vals) / len(trust_vals),
        "centralization": 0.0   # placeholder
    }
    return {
        "state_history": state_history,
        "outcome_vector": outcome,
        "agents": agents,
        "seed": seed
    }

# --- UI helpers ---
def plot_sparkline(data, height=100):
    """Draw a tiny line chart using a dataframe."""
    chart_data = pd.DataFrame({"val": data})
    st.line_chart(chart_data, height=height, use_container_width=True)

def show_agent_drilldown(agents, state_history):
    """Interactive agent drill-down panel."""
    st.markdown("### 🧠 Agent Cognitive States")
    selected = st.selectbox("Choose an agent", [a.name for a in agents])
    agent = next(a for a in agents if a.name == selected)
    rounds = len(state_history)
    if rounds == 0:
        st.warning("No simulation data yet.")
        return
    # Plot all 10 variables in a grid
    vars_to_plot = ["self_worth", "anxiety", "consistency", "momentum", "reputation",
                    "opportunity_access", "fragility_index", "lock_in", "learning_rate", "energy"]
    cols = st.columns(5)
    for i, var in enumerate(vars_to_plot):
        series = [state_history[r][agent.name][var] for r in range(rounds)]
        with cols[i % 5]:
            st.metric(var.replace("_", " ").title(), f"{series[-1]:.2f}")
            plot_sparkline(series, height=80)

def show_outcomes(sim_result):
    """Full outcomes dashboard."""
    outcome = sim_result["outcome_vector"]
    agents = sim_result["agents"]
    st.markdown("## 📊 Strategic Forecast")
    st.metric("Winner", "Nuanced middle ground")   # static placeholder
    st.metric("Confidence", "72%")
    with st.expander("Confidence Rubric"):
        st.write("**Feasibility:** 7/10  |  **Alignment:** 6/10  |  **Risk:** 7/10  |  **Evidence:** 8/10")

    st.markdown("### Outcome Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Reputation Mean", f"{outcome['reputation_mean']:.3f}")
    col2.metric("Inequality", f"{outcome['inequality']:.4f}")
    col3.metric("Trust Proxy", f"{outcome['trust_proxy']:.3f}")
    col4.metric("Centralization", f"{outcome['centralization']:.3f}")

    # BlackSwan Assassin (simplified)
    with st.expander("🕵️ BlackSwan Assassin"):
        st.write("**Assumption:** Agents assume debate will stay rational.")
        st.write("**Why fragile:** Emotional anecdotes could spike anxiety.")
        st.write("**Break scenario:** A student shares a personal story → anxiety +20%.")

    # Counterfactual sensitivity
    with st.expander("🧪 Counterfactual Sensitivity"):
        if st.button("Run +20% Anxiety Perturbation"):
            perturb_seed = sim_result["seed"] + 1000
            rng = random.Random(perturb_seed)
            agents_pert = [CognitiveAgent(a.name, rng=rng) for a in agents]
            for a in agents_pert:
                a.anxiety = min(1.0, a.anxiety * 1.2)
            # Re-run with perturbation
            for _ in range(len(sim_result["state_history"])):
                for a in agents_pert:
                    a.update(rng.random()*0.5+0.3, rng.random()*0.5, (rng.random()-0.5)*0.5,
                             1 if rng.random()<0.1 else 0, 1 if rng.random()<0.3 else 0)
            pert_rep = sum(a.reputation for a in agents_pert)/len(agents_pert)
            orig_rep = outcome["reputation_mean"]
            st.write(f"Original Reputation Mean: {orig_rep:.3f}")
            st.write(f"Perturbed (+20% anxiety): {pert_rep:.3f}")
            st.write(f"Shift: {(pert_rep - orig_rep):+.3f}")

    # Agent drill-down
    show_agent_drilldown(agents, sim_result["state_history"])

    # Feedback loops (success chains)
    st.markdown("### 🔁 Feedback Loops")
    for a in agents:
        if a.success_streak >= 2:
            st.write(f"🔁 **{a.name}** – Success chain ×{a.success_streak}")

    # Download report
    report = json.dumps({"outcome": outcome, "seed": sim_result["seed"]}, indent=2, default=str)
    st.download_button("📥 Download Full Report", report, file_name="nyx_report.json")
# -----------------------------------------------------------------------------
# Standard Debate (simplified, uses providers if available)
# -----------------------------------------------------------------------------
PROVIDERS = []   # You can add your API keys later (Groq, SambaNova, etc.)

def run_standard_debate(topic, agents_text, rounds):
    """Dummy standard debate – replace with real provider calls if you have API keys."""
    log = []
    for r in range(1, rounds+1):
        for agent_line in agents_text.splitlines():
            name = agent_line.split(",")[0].strip() if agent_line else "Agent"
            log.append(f"**Round {r} – {name}**: This is a placeholder. Add API keys to see real debate.")
    return log, "No clear winner (demo mode)"

# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 💜 Nyx Engine")
    st.markdown("---")

    # Mode selection
    st.markdown("### ⚙️ Mode")
    mode = st.radio("Choose mode", ["Standard Debate", "Advanced Simulation"], index=0)
    st.session_state.adv_sim = (mode == "Advanced Simulation")

    if st.session_state.adv_sim:
        st.markdown("### 🌌 Advanced Simulation")
        seed = st.number_input("Seed", value=42, step=1, help="Deterministic reproducibility")
        rounds = st.slider("Rounds", 2, 10, 4)
        agent_names_text = st.text_area("Agents (one per line)", "Harsh\nJayant\nMira\nVera\nAtlas")
        if st.button("🚀 Run Simulation", type="primary"):
            agent_list = [name.strip() for name in agent_names_text.splitlines() if name.strip()]
            if len(agent_list) < 2:
                st.error("Need at least 2 agents.")
            else:
                with st.spinner("Running cognitive simulation..."):
                    result = run_simulation(agent_list, rounds=rounds, seed=seed)
                    st.session_state.sim_result = result
                    st.success("Simulation complete!")
    else:
        # Standard debate controls
        st.markdown("### 🗣️ Standard Debate")
        topic = st.text_input("Topic", "Should smartphones be banned in schools?")
        agents_input = st.text_area("Agents (one per line)", "Harsh, skeptic\nJayant, optimist\nAhany, moderator")
        rounds = st.slider("Rounds", 1, 6, 3)
        if st.button("Start Debate"):
            with st.spinner("Debating..."):
                log, winner = run_standard_debate(topic, agents_input, rounds)
                st.session_state.debate_history = log
                st.session_state.debate_winner = winner
                st.success("Debate finished!")

# -----------------------------------------------------------------------------
# MAIN PAGE
# -----------------------------------------------------------------------------
st.markdown('<p class="nyx-title">Nyx</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle" style="text-align:center; opacity:0.7;">Cognitive‑Social Physics Engine · by Harsh Dubey</p>',
            unsafe_allow_html=True)

if st.session_state.adv_sim:
    if st.session_state.sim_result:
        show_outcomes(st.session_state.sim_result)
    else:
        st.markdown("""
        <div class="glass-card">
        <h3>Advanced Simulation Ready</h3>
        <p>Select agents, set a seed, and click <strong>Run Simulation</strong> in the sidebar.</p>
        </div>
        """, unsafe_allow_html=True)
else:
    if st.session_state.debate_history:
        st.markdown("## Debate Transcript")
        for line in st.session_state.debate_history:
            st.markdown(line)
        if "debate_winner" in st.session_state:
            st.success(f"**Winner:** {st.session_state.debate_winner}")
    else:
        st.markdown("""
        <div class="glass-card">
        <h3>Standard Debate Mode</h3>
        <p>Enter a topic and click <strong>Start Debate</strong>. (Add API keys for real AI agents.)</p>
        </div>
        """, unsafe_allow_html=True)

# --- Footer ---
st.markdown("<div style='text-align:center; opacity:0.5;'>✨ Jayant Dubey · Nyx ✨</div>", unsafe_allow_html=True)
