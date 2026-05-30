# =============================================================================
# NYX – The Decision Intelligence Simulator
# A Perplexity-inspired cognitive-social physics platform
# =============================================================================
import streamlit as st
import time
import json
import math
from datetime import datetime
import pandas as pd

# Import the deterministic kernel
from nyx_kernel import (
    run_simulation,
    detect_black_swan,
    run_counterfactual,
    run_multi_trial,
    game_theory_insights,
    CognitiveAgent
)

# Optional imports (only used if installed)
try:
    import networkx as nx
    import matplotlib.pyplot as plt
    HAS_GRAPH = True
except ImportError:
    HAS_GRAPH = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Nyx · Decision Intelligence Simulator",
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
    .subtitle {
        text-align: center;
        opacity: 0.7;
        font-size: 1.1rem;
        margin-bottom: 2rem;
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
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        background: rgba(255, 255, 255, 0.65) !important;
        backdrop-filter: blur(15px);
        border: 0.5px solid var(--border-glow) !important;
        border-radius: 60px !important;
        padding: 1rem 1.5rem !important;
        font-size: 1.1rem !important;
        color: var(--text-dark) !important;
        text-align: center;
    }
    .stTextArea > div > div > textarea {
        border-radius: 20px !important;
        text-align: left !important;
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
    .metric-card {
        background: rgba(255, 255, 255, 0.4);
        border-radius: 16px;
        padding: 1rem;
        text-align: center;
    }
    .mode-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .mode-EXECUTE { background: #d4edda; color: #155724; }
    .mode-OPTIMIZE { background: #fff3cd; color: #856404; }
    .mode-AVOID { background: #f8d7da; color: #721c24; }
    .mode-RECOVER { background: #d1ecf1; color: #0c5460; }
    .mode-SPIKE { background: #e2d5f1; color: #4a2c6e; }
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
if "multi_trial_result" not in st.session_state:
    st.session_state.multi_trial_result = None


# =============================================================================
# API PROVIDERS (from st.secrets ONLY)
# =============================================================================
def get_providers():
    """Return only providers for which the corresponding secret exists."""
    all_providers = [
        {"name": "Groq", "key_name": "GROQ_API_KEY", "base": "https://api.groq.com/openai/v1", "model": "llama-3.3-70b-versatile"},
        {"name": "SambaNova", "key_name": "SAMBA_API_KEY", "base": "https://api.sambanova.ai/v1", "model": "Meta-Llama-3.3-70B-Instruct"},
        {"name": "Cerebras", "key_name": "CEREBRAS_API_KEY", "base": "https://api.cerebras.ai/v1", "model": "llama-3.3-70b"},
        {"name": "Google", "key_name": "GEMINI_API_KEY", "base": "https://generativelanguage.googleapis.com/v1beta", "model": "gemini-2.5-flash"},
        {"name": "Mistral", "key_name": "MISTRAL_API_KEY", "base": "https://api.mistral.ai/v1", "model": "mistral-small-4"},
        {"name": "Cohere", "key_name": "COHERE_API_KEY", "base": "https://api.cohere.ai/compatibility/v1", "model": "command-a-03-2025"},
        {"name": "OpenRouter", "key_name": "OPENROUTER_API_KEY", "base": "https://openrouter.ai/api/v1", "model": "openrouter/free"},
        {"name": "HuggingFace", "key_name": "HF_API_KEY", "base": "https://api-inference.huggingface.co/v1", "model": "meta-llama/Llama-3.3-70B-Instruct"},
    ]
    available = []
    for p in all_providers:
        key = st.secrets.get(p["key_name"]) if hasattr(st, 'secrets') else None
        if key:
            available.append({**p, "key": key})
    return available


# =============================================================================
# FALLBACK GENERATOR
# =============================================================================
def generate_with_fallback(prompt, system="", preferred=None):
    providers = get_providers()
    if not providers:
        return "No API keys configured. Add them in Streamlit secrets.", "None"
    if preferred:
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
                resp = client.completions.create(model=p["model"], prompt=system + "\n" + prompt if system else prompt, max_tokens=150, temperature=0.7)
                return resp.choices[0].text.strip(), p["name"]
            else:
                client = OpenAI(api_key=p["key"], base_url=p["base"])
                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})
                resp = client.chat.completions.create(model=p["model"], messages=messages, temperature=0.7, max_tokens=200)
                return resp.choices[0].message.content.strip(), p["name"]
        except Exception:
            time.sleep(0.5)
            continue
    return "All providers temporarily unavailable.", "None"


# =============================================================================
# STANDARD DEBATE AGENT
# =============================================================================
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
    for r in range(1, rounds + 1):
        for agent in agents:
            msg, provider = agent.speak(topic, last_msg, r, preferred_provider)
            log.append(f"**Round {r} – {agent.name}** (via {provider}): {msg}")
            last_msg = msg
    winner = max(agents, key=lambda a: sum(len(m) for m in a.history) / max(1, len(a.history))).name
    return log, winner


# =============================================================================
# UI HELPER FUNCTIONS
# =============================================================================
def render_mode_badge(mode):
    """Render a styled mode badge."""
    return f'<span class="mode-badge mode-{mode}">{mode}</span>'


def plot_sparkline(data, height=80, color="#9B4DFF"):
    """Create a mini sparkline chart using Plotly."""
    if not HAS_PLOTLY:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=data, mode='lines', line=dict(color=color, width=2), fill='tozeroy'))
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=height,
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(showgrid=False, showticklabels=False),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig


def render_agent_card(agent, state_history, selected_name):
    """Render detailed agent card with sparklines."""
    if not state_history:
        return
    
    rounds = len(state_history)
    agent_data = [state_history[r].get(selected_name, {}) for r in range(rounds)]
    
    vars_to_plot = [
        ("self_worth", "#9B4DFF"),
        ("anxiety", "#FF4D6D"),
        ("consistency", "#4DA6FF"),
        ("momentum", "#FFB84D"),
        ("reputation", "#4DFF88"),
        ("opportunity_access", "#FF4DD4"),
        ("fragility_index", "#8B4DFF"),
        ("lock_in", "#4DFFF5"),
        ("learning_rate", "#FFFF4D"),
        ("energy", "#FF884D")
    ]
    
    # Current values
    current = agent.get_current_state_dict()
    
    # Display metrics in columns
    cols = st.columns(5)
    for i, (var, color) in enumerate(vars_to_plot):
        series = [agent_data[r].get(var, 0) for r in range(rounds)] if agent_data and agent_data[0] else []
        with cols[i % 5]:
            display_name = var.replace("_", " ").title()
            current_val = current.get(var, 0)
            st.metric(display_name, f"{current_val:.2f}")
            if HAS_PLOTLY and series:
                fig = plot_sparkline(series, height=60, color=color)
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key=f"{selected_name}_{var}")


# =============================================================================
# RESULTS DASHBOARD TABS
# =============================================================================
def render_overview_tab(sim_result):
    """Render the Overview tab."""
    outcome = sim_result["outcome_vector"]
    agents = sim_result["agents"]
    state_history = sim_result["state_history"]
    
    # Winner & Confidence heuristic
    reputation_mean = outcome["reputation_mean"]
    trust_proxy = outcome["trust_proxy"]
    inequality = outcome["inequality"]
    
    if reputation_mean > 0.6:
        consensus_label = "Moderate consensus emerging"
        confidence = min(0.9, 0.5 + trust_proxy * 0.3 + (1 - inequality) * 0.2)
    elif trust_proxy < 0.4:
        consensus_label = "Polarized stalemate"
        confidence = 0.3 + trust_proxy * 0.3
    else:
        consensus_label = "Fragmented alignment"
        confidence = 0.5
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"### 📊 Strategic Forecast")
        st.markdown(f"**Assessment:** {consensus_label}")
    with col2:
        st.metric("Confidence", f"{confidence * 100:.0f}%")
    
    # Confidence Rubric
    with st.expander("📋 Confidence Rubric"):
        feasibility = min(10, int(reputation_mean * 10 + 2))
        alignment = min(10, int(trust_proxy * 10 + 1))
        risk = min(10, int((1 - trust_proxy) * 10 + inequality * 5))
        evidence = min(10, int((1 - inequality) * 10))
        
        c1, c2, c3, c4 = st.columns(4)
        c1.progress(feasibility / 10)
        c1.caption(f"Feasibility: {feasibility}/10")
        c2.progress(alignment / 10)
        c2.caption(f"Alignment: {alignment}/10")
        c3.progress(risk / 10)
        c3.caption(f"Risk: {risk}/10")
        c4.progress(evidence / 10)
        c4.caption(f"Evidence: {evidence}/10")
    
    # Best/Worst Case
    st.markdown("### 🔮 Scenarios")
    bc1, bc2 = st.columns(2)
    with bc1:
        st.markdown("**✅ Best Case**")
        if trust_proxy > 0.5:
            st.success("If trust remains high, policy implementation proceeds smoothly with broad adoption.")
        else:
            st.info("If engagement increases, gradual consensus may form over extended timeline.")
    with bc2:
        st.markdown("**⚠️ Worst Case**")
        if inequality > 0.1:
            st.error("High inequality may trigger cascading failures and complete consensus collapse.")
        else:
            st.warning("If external shocks occur, fragile stability could rapidly deteriorate.")
    
    # Black Swan detection
    st.markdown("### 🕵️ Hidden Failure Points")
    black_swan = detect_black_swan(agents, state_history)
    bs_card = f"""
    **Assumption:** {black_swan['assumption']}
    
    **Why Fragile:** {black_swan['why_fragile']}
    
    **Break Scenario:** {black_swan['break_scenario']}
    
    **Impact:** {black_swan['impact']}
    """
    st.info(bs_card)
    
    # Timeline of mode shifts
    st.markdown("### 📅 Mode Timeline")
    timeline_data = []
    for r_idx, round_state in enumerate(state_history):
        for name, state in round_state.items():
            timeline_data.append({
                "Round": r_idx + 1,
                "Agent": name,
                "Mode": state["mode"]
            })
    timeline_df = pd.DataFrame(timeline_data)
    st.dataframe(timeline_df, use_container_width=True, hide_index=True)


def render_agents_tab(sim_result):
    """Render the Agents tab."""
    agents = sim_result["agents"]
    state_history = sim_result["state_history"]
    
    st.markdown("### 🧠 Agent Cognitive States")
    
    agent_names = [a.name for a in agents]
    selected = st.selectbox("Choose an agent", agent_names, key="agent_selector")
    
    agent = next(a for a in agents if a.name == selected)
    
    # Render agent card with sparklines
    render_agent_card(agent, state_history, selected)
    
    # Success chains and cascade warnings
    st.markdown("### ⚠️ Status Indicators")
    status_cols = st.columns(len(agents))
    for i, a in enumerate(agents):
        with status_cols[i]:
            current = a.get_current_state_dict()
            status_parts = []
            if a.cascade_active:
                status_parts.append("🔴 CASCADE")
            if a.success_streak >= 2:
                status_parts.append(f"🟢 Success ×{a.success_streak}")
            if a.failure_streak >= 2:
                status_parts.append(f"🔴 Failures ×{a.failure_streak}")
            if not status_parts:
                status_parts.append("🟡 Stable")
            st.markdown(f"**{a.name}**: {' | '.join(status_parts)}")


def render_network_tab(sim_result):
    """Render the Network tab."""
    influence = sim_result["influence"]
    agents = sim_result["agents"]
    
    st.markdown("### 🌐 Influence Network")
    
    if HAS_PLOTLY:
        # Create Sankey diagram
        source = []
        target = []
        value = []
        labels = list(influence.keys())
        
        for src, targets in influence.items():
            for tgt, weight in targets.items():
                if weight > 0.5:  # Only show significant edges
                    source.append(labels.index(src))
                    target.append(labels.index(tgt))
                    value.append(weight)
        
        if source:
            fig = go.Figure(data=[go.Sankey(
                node=dict(pad=15, thickness=20, line=dict(color="black", width=0.5),
                          label=labels, color="#9B4DFF"),
                link=dict(source=source, target=target, value=value, color="rgba(255,77,109,0.5)")
            )])
            fig.update_layout(title_text="Influence Flow (weights > 0.5)", font_size=12)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No strong influence connections to display.")
    
    # Influence matrix table
    st.markdown("### 📊 Influence Matrix")
    inf_df = pd.DataFrame(influence)
    st.dataframe(inf_df.style.background_gradient(cmap="PuRd"), use_container_width=True)


def render_deep_dive_tab(sim_result):
    """Render the Deep Dive tab."""
    agents = sim_result["agents"]
    state_history = sim_result["state_history"]
    seed = sim_result["seed"]
    
    st.markdown("### 📈 Sentiment Ridge")
    
    # Calculate mean self_worth per round
    if HAS_PLOTLY and state_history:
        means = []
        stds = []
        rounds = []
        for r_idx, round_state in enumerate(state_history):
            sw_values = [s["self_worth"] for s in round_state.values()]
            means.append(sum(sw_values) / len(sw_values))
            variance = sum((x - means[-1]) ** 2 for x in sw_values) / len(sw_values)
            stds.append(math.sqrt(variance))
            rounds.append(r_idx + 1)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=rounds, y=means, mode='lines+markers', name='Mean Self-Worth', line=dict(color='#9B4DFF', width=3)))
        fig.add_trace(go.Scatter(x=rounds, y=[m + s for m, s in zip(means, stds)], 
                                  mode='lines', name='+1 Std Dev', line=dict(color='#9B4DFF', width=0, dash='dash'), showlegend=False))
        fig.add_trace(go.Scatter(x=rounds, y=[m - s for m, s in zip(means, stds)], 
                                  mode='lines', name='-1 Std Dev', line=dict(color='#9B4DFF', width=0, dash='dash'), 
                                  fill='tonexty', fillcolor='rgba(155,77,255,0.2)', showlegend=False))
        fig.update_layout(title="Self-Worth Evolution (Mean ± Std Dev)", xaxis_title="Round", yaxis_title="Self-Worth")
        st.plotly_chart(fig, use_container_width=True)
    
    # Variable Importance Heatmap
    st.markdown("### 🔥 Variable Variance Heatmap")
    if HAS_PLOTLY and state_history:
        vars_list = ["self_worth", "anxiety", "consistency", "momentum", "reputation"]
        heatmap_data = []
        for var in vars_list:
            row = []
            for agent in agents:
                series = [sh[agent.name].get(var, 0) for sh in state_history]
                if series:
                    variance = sum((x - sum(series)/len(series)) ** 2 for x in series) / len(series)
                    row.append(variance)
                else:
                    row.append(0)
            heatmap_data.append(row)
        
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data,
            x=[a.name for a in agents],
            y=vars_list,
            colorscale='RdYlBu'
        ))
        fig.update_layout(title="Per-Agent Variable Variance", xaxis_title="Agent", yaxis_title="Variable")
        st.plotly_chart(fig, use_container_width=True)
    
    # Counterfactual Panel
    st.markdown("### 🧪 Counterfactual Analysis")
    cf_col1, cf_col2 = st.columns([1, 2])
    with cf_col1:
        variable = st.selectbox("Variable to perturb", ["anxiety", "self_worth", "consistency", "momentum"])
        delta = st.slider("Perturbation (%)", -50, 100, 20)
        run_cf = st.button("Run Counterfactual")
    
    with cf_col2:
        if run_cf:
            agent_names = [a.name for a in agents]
            rounds = len(state_history)
            with st.spinner("Running counterfactual..."):
                cf_result = run_counterfactual(agent_names, rounds, seed, variable, delta)
            
            orig = cf_result["original_outcome"]
            pert = cf_result["perturbed_outcome"]
            delta_out = cf_result["delta"]
            
            st.markdown(f"**Perturbation:** {variable} {'+' if delta > 0 else ''}{delta}%")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Reputation Mean", f"{pert['reputation_mean']:.3f}", f"{delta_out['reputation_mean']:+.3f}")
            c2.metric("Trust Proxy", f"{pert['trust_proxy']:.3f}", f"{delta_out['trust_proxy']:+.3f}")
            c3.metric("Inequality", f"{pert['inequality']:.4f}", f"{delta_out['inequality']:+.4f}")
    
    # Multi-Trial Analysis
    st.markdown("### 🎲 Multi-Trial Monte Carlo")
    mt_col1, mt_col2 = st.columns([1, 3])
    with mt_col1:
        num_trials = st.number_input("Number of trials", 10, 200, 50, step=10)
        run_mt = st.button("Run Monte Carlo")
    
    with mt_col2:
        if run_mt or st.session_state.multi_trial_result:
            if run_mt:
                agent_names = [a.name for a in agents]
                rounds = len(state_history)
                with st.spinner(f"Running {num_trials} trials..."):
                    result = run_multi_trial(agent_names, rounds, seed, num_trials)
                    st.session_state.multi_trial_result = result
            
            result = st.session_state.multi_trial_result
            if result:
                stats = result["stats"]
                st.markdown("**Outcome Statistics**")
                stat_df = pd.DataFrame({
                    "Metric": ["Reputation Mean", "Trust Proxy", "Inequality", "Centralization"],
                    "Mean": [stats["reputation_mean"]["mean"], stats["trust_proxy"]["mean"], 
                             stats["inequality"]["mean"], stats["centralization"]["mean"]],
                    "Std Dev": [stats["reputation_mean"]["std"], stats["trust_proxy"]["std"],
                                stats["inequality"]["std"], stats["centralization"]["std"]]
                })
                st.dataframe(stat_df, use_container_width=True, hide_index=True)
                
                clusters = result["clusters"]
                if clusters:
                    st.markdown("**Cluster Distribution**")
                    cluster_df = pd.DataFrame(clusters)
                    st.bar_chart(cluster_df.set_index("id")["size"])
    
    # Game Theory Insights
    st.markdown("### ♟️ Game Theory Analysis")
    gt = game_theory_insights(agents)
    gt_col1, gt_col2 = st.columns(2)
    with gt_col1:
        st.markdown("**Mode Distribution**")
        mode_df = pd.DataFrame(list(gt["mode_counts"].items()), columns=["Mode", "Count"])
        st.bar_chart(mode_df.set_index("Mode"))
    with gt_col2:
        st.markdown("**Strategic Assessment**")
        if gt["dominant_strategy"]:
            st.success(f"Dominant strategy: {gt['dominant_strategy']}")
        for insight in gt["nash_analysis"]:
            st.info(insight)
        st.caption(f"Summary: {gt['summary']}")
    
    # Download Report
    st.markdown("### 📥 Export")
    report = {
        "seed": seed,
        "timestamp": datetime.now().isoformat(),
        "outcome_vector": sim_result["outcome_vector"],
        "final_states": {a.name: a.get_current_state_dict() for a in agents},
        "game_theory": gt
    }
    json_report = json.dumps(report, indent=2, default=str)
    st.download_button("Download JSON Report", json_report, file_name=f"nyx_report_{seed}.json", mime="application/json")


# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.markdown('<p class="nyx-title">Nyx</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Mode switch
    st.markdown("### ⚙️ Mode")
    mode = st.radio("Choose mode", ["Standard Debate", "Advanced Simulation"], index=0)
    st.session_state.adv_sim = (mode == "Advanced Simulation")
    
    if st.session_state.adv_sim:
        st.markdown("### 🌌 Advanced Simulation")
        
        seed = st.number_input("Seed", value=42, step=1)
        rounds = st.slider("Rounds", 5, 20, 10)
        n_agents = st.slider("Number of Agents", 3, 12, 6)
        
        # Generate agent names
        default_names = "Harsh\nJayant\nMira\nVera\nAtlas\nLuna"
        agent_names_input = st.text_area("Agents (one per line)", default_names, height=150)
        
        # Verify reproducibility button
        if st.button("🔍 Verify Reproducibility"):
            test_names = [n.strip() for n in agent_names_input.strip().split("\n") if n.strip()]
            result1 = run_simulation(test_names, rounds, seed)
            result2 = run_simulation(test_names, rounds, seed)
            hash1 = json.dumps(result1["outcome_vector"], sort_keys=True)
            hash2 = json.dumps(result2["outcome_vector"], sort_keys=True)
            if hash1 == hash2:
                st.success("✅ PASS: Identical outcomes with same seed")
            else:
                st.error("❌ FAIL: Outcomes differ!")
        
        if st.button("🚀 Run Simulation", type="primary"):
            agent_list = [name.strip() for name in agent_names_input.strip().split("\n") if name.strip()]
            if len(agent_list) < 2:
                st.error("Need at least 2 agents.")
            else:
                with st.spinner("Running cognitive simulation..."):
                    progress_bar = st.progress(0)
                    for i in range(rounds):
                        time.sleep(0.05)  # Visual feedback
                        progress_bar.progress((i + 1) / rounds)
                    result = run_simulation(agent_list, rounds=rounds, seed=seed)
                    st.session_state.sim_result = result
                    st.success("Simulation complete!")
    else:
        st.markdown("### 🗣️ Standard Debate")
        topic = st.text_input("Topic", "Should smartphones be banned in schools?")
        agents_input = st.text_area("Agents (Name, stance)", "Harsh, skeptic\nJayant, optimist\nAhany, moderator")
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


# =============================================================================
# MAIN PAGE
# =============================================================================
st.markdown('<p class="nyx-title">Nyx</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Decision Intelligence Simulator · Powered by Cognitive-Social Physics</p>', unsafe_allow_html=True)

if st.session_state.adv_sim:
    if st.session_state.sim_result:
        # Create tabs with glass styling
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🧠 Agents", "🌐 Network", "🔬 Deep Dive"])
        
        with tab1:
            render_overview_tab(st.session_state.sim_result)
        
        with tab2:
            render_agents_tab(st.session_state.sim_result)
        
        with tab3:
            render_network_tab(st.session_state.sim_result)
        
        with tab4:
            render_deep_dive_tab(st.session_state.sim_result)
    else:
        st.markdown("""
        <div class="glass-card" style="text-align: center; padding: 3rem;">
            <h3>🌌 Advanced Simulation Ready</h3>
            <p style="opacity: 0.7; margin: 1rem 0;">
                Configure your agent society in the sidebar and click <strong>Run Simulation</strong> 
                to explore cognitive-social dynamics.
            </p>
            <p style="font-size: 0.9rem; opacity: 0.5;">
                Same seed → identical results. Deterministic by design.
            </p>
        </div>
        """, unsafe_allow_html=True)
else:
    if st.session_state.debate_log:
        st.markdown("## 🗣️ Debate Transcript")
        for line in st.session_state.debate_log:
            st.markdown(line)
        if st.session_state.debate_winner:
            st.success(f"**🏆 Winner:** {st.session_state.debate_winner}")
    else:
        st.markdown("""
        <div class="glass-card" style="text-align: center; padding: 3rem;">
            <h3>🗣️ Standard Debate Mode</h3>
            <p style="opacity: 0.7; margin: 1rem 0;">
                Enter a topic and agent stances in the sidebar, then click <strong>Start Debate</strong>.
            </p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='text-align: center; opacity: 0.5; margin-top: 3rem;'>✨ Nyx · Decision Intelligence Simulator ✨</div>", unsafe_allow_html=True)
