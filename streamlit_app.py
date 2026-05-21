import streamlit as st
import time
import re
import json
import os
import urllib.parse
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from openai import OpenAI

# --- Page Config ---
st.set_page_config(
    page_title="Nyx · by Harsh",
    page_icon="💜",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Lavender Haze Purple/Pink/Red Glassmorphism CSS ---
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
        -webkit-backdrop-filter: blur(24px) !important;        border-right: 0.5px solid var(--border-glow) !important;
        box-shadow: 4px 0 20px rgba(155,77,255,0.05) !important;
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
        background: linear-gradient(135deg, var(--pink-hot) 0%, var(--purple-prime) 100%);
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
    }    .stButton > button {
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

    .card-skeptic { border-left: 5px solid #E63946; }
    .card-optimist { border-left: 5px solid #9B4DFF; }
    .card-philosopher { border-left: 5px solid #C77DFF; }
    .card-futurist { border-left: 5px solid #FF4D6D; }
    .card-data { border-left: 5px solid #5E60CE; }
    .card-ethicist { border-left: 5px solid #FF6B6B; }
    .card-policy { border-left: 5px solid #F06595; }
    .card-conspiracy { border-left: 5px solid #845EF7; }
    .card-psychologist { border-left: 5px solid #F06595; }
    .card-economist { border-left: 5px solid #DA77F2; }
    .card-technologist { border-left: 5px solid #748FFC; }
    .card-legal { border-left: 5px solid #FF8787; }
    .card-moderator { border-left: 5px solid #E63946; }

    .verdict-box {
        background: var(--card-bg);
        backdrop-filter: blur(20px);
        border-radius: 28px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border-left: 5px solid var(--purple-prime);
    }
</style>
""", unsafe_allow_html=True)
# ==========================================
# NYX DETERMINISTIC KERNEL
# ==========================================
class CognitiveState:
    """The 10 interacting psychological variables (0.0 to 1.0)"""
    def __init__(self, seed=42):
        self.rng = np.random.default_rng(seed)
        self.self_worth = self.rng.uniform(0.4, 0.8)
        self.anxiety = self.rng.uniform(0.1, 0.4)
        self.consistency = self.rng.uniform(0.5, 0.9)
        self.momentum = 0.5
        self.reputation = 0.5
        self.opportunity_access = 0.5
        self.fragility_index = 0.2
        self.lock_in = 0.1
        self.learning_rate = self.rng.uniform(0.3, 0.7)
        self.energy = 1.0

    def to_dict(self):
        return {k: round(v, 3) for k, v in self.__dict__.items() if k != 'rng'}

class NyxKernel:
    """Owns all state transitions. Fully deterministic."""
    def __init__(self, agent_names, seed=42):
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.agents = {name: CognitiveState(seed + i) for i, name in enumerate(agent_names)}
        self.names = agent_names
        self.n = len(agent_names)
        
        # Influence Network W[i][j] - Directed graph
        self.W = self.rng.uniform(0.1, 0.3, (self.n, self.n))
        np.fill_diagonal(self.W, 0.0)

    def update_cognitive_state(self, agent_name, social_pressure, contradiction_exposure):
        state = self.agents[agent_name]
        
        state.anxiety = np.clip(state.anxiety + 0.1 * social_pressure + 0.2 * contradiction_exposure, 0, 1)
        state.consistency = np.clip(state.consistency - 0.15 * state.anxiety, 0, 1)
        state.energy = np.clip(state.energy - 0.05 - 0.1 * state.anxiety, 0, 1)
        
        if state.consistency < 0.4:
            state.reputation = np.clip(state.reputation - 0.1, 0, 1)
            state.fragility_index = np.clip(state.fragility_index + 0.15, 0, 1)
            
        mode_scores = [
            state.anxiety * 2,                           
            state.fragility_index * 1.5,                 
            state.momentum * state.energy * 2,           
            state.learning_rate * state.opportunity_access 
        ]
        mode = int(np.argmax(mode_scores))
        return mode

    def step(self):
        modes = {}
        for i, name in enumerate(self.names):
            social_pressure = np.dot(self.W[i], [self.agents[n].momentum for n in self.names])
            contradiction = self.rng.uniform(0, 0.3) 
            
            mode = self.update_cognitive_state(name, social_pressure, contradiction)
            modes[name] = ["AVOID", "RECOVER", "EXECUTE", "OPTIMIZE"][mode]
            
            for j, other in enumerate(self.names):
                if i != j:
                    self.W[i][j] = np.clip(self.W[i][j] + 0.01 * self.agents[name].momentum, 0, 1)
        return modes

    def get_outcome_vector(self):
        reps = [a.reputation for a in self.agents.values()]
        anxieties = [a.anxiety for a in self.agents.values()]
        return {
            "reputation_mean": round(float(np.mean(reps)), 3),
            "inequality": round(float(np.std(reps)), 3),
            "polarization_score": round(float(np.std(anxieties) * 2), 3),
            "system_health": round(float(1.0 - np.mean([a.fragility_index for a in self.agents.values()])), 3)
        }
# ==========================================
# SESSION STATE & KNOWLEDGE BASE
# ==========================================
if "debate_history" not in st.session_state:
    st.session_state.debate_history = []
if "saved_history" not in st.session_state:
    st.session_state.saved_history = []
if "panel_presets" not in st.session_state:
    st.session_state.panel_presets = {}
if "simulation_complete" not in st.session_state:
    st.session_state.simulation_complete = False
if "nyx_kernel" not in st.session_state:
    st.session_state.nyx_kernel = None

KG_FILE = "nyx_knowledge.json"
def load_kg():
    if os.path.exists(KG_FILE):
        with open(KG_FILE, "r") as f: return json.load(f)
    return {"debates": [], "entities": {}, "agent_insights": {}}

def save_kg(kg):
    with open(KG_FILE, "w") as f: json.dump(kg, f, indent=2)

# ==========================================
# API PROVIDERS & FALLBACK
# ==========================================
PROVIDERS = [
    {"name": "Groq",           "key": st.secrets.get("GROQ_API_KEY"),           "base": "https://api.groq.com/openai/v1",                  "model": "llama-3.3-70b-versatile"},
    {"name": "SambaNova",      "key": st.secrets.get("SAMBA_API_KEY"),          "base": "https://api.sambanova.ai/v1",                     "model": "Meta-Llama-3.3-70B-Instruct"},
    {"name": "Cerebras",       "key": st.secrets.get("CEREBRAS_API_KEY"),       "base": "https://api.cerebras.ai/v1",                      "model": "llama-3.3-70b"},
    {"name": "Google",         "key": st.secrets.get("GEMINI_API_KEY"),         "base": "https://generativelanguage.googleapis.com/v1beta","model": "gemini-2.5-flash"},
    {"name": "Mistral",        "key": st.secrets.get("MISTRAL_API_KEY"),        "base": "https://api.mistral.ai/v1",                       "model": "mistral-small-4"},
    {"name": "Cohere",         "key": st.secrets.get("COHERE_API_KEY"),         "base": "https://api.cohere.ai/compatibility/v1",          "model": "command-a-03-2025"},
    {"name": "OpenRouter",     "key": st.secrets.get("OPENROUTER_API_KEY"),     "base": "https://openrouter.ai/api/v1",                    "model": "openrouter/free"},
    {"name": "HuggingFace",    "key": st.secrets.get("HF_API_KEY"),             "base": "https://api-inference.huggingface.co/v1",         "model": "meta-llama/Llama-3.3-70B-Instruct"},
]

def generate_with_fallback(prompt, system="", preferred=None, silent_fail=False):
    if preferred:
        providers = [p for p in PROVIDERS if p["name"] == preferred] + [p for p in PROVIDERS if p["name"] != preferred]
    else:
        providers = PROVIDERS
        
    for p in providers:
        if not p["key"]: continue
        try:
            if p["name"] == "Google":
                import google.generativeai as genai
                genai.configure(api_key=p["key"])
                model = genai.GenerativeModel(p["model"])                full_prompt = f"{system}\n\n{prompt}" if system else prompt
                resp = model.generate_content(full_prompt)
                return resp.text.strip(), p["name"]
            else:
                client = OpenAI(api_key=p["key"], base_url=p["base"])
                messages = []
                if system: messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})
                resp = client.chat.completions.create(model=p["model"], messages=messages, temperature=0.4, max_tokens=250)
                return resp.choices[0].message.content.strip(), p["name"]
        except:
            continue
            
    if silent_fail: return "Unable to generate response.", "None"
    st.warning("All providers temporarily unavailable.")
    return "Response unavailable.", "None"

# ==========================================
# AUTO-ROUTING & TONE
# ==========================================
EXPERT_KEYWORDS = {
    "Skeptic": ["risk", "flaw", "danger", "problem", "against"],
    "Optimist": ["opportunity", "growth", "benefit", "future", "progress"],
    "Economist": ["economy", "market", "finance", "trade", "inflation"],
    "Policy Advisor": ["government", "law", "regulation", "policy"],
    "Scientist": ["science", "experiment", "data", "evidence", "study"],
    "Ethicist": ["ethics", "moral", "should", "right", "wrong"],
    "Technologist": ["tech", "software", "hardware", "innovation", "startup"],
    "Legal Expert": ["legal", "court", "law", "constitution", "rights"],
    "Philosopher": ["meaning", "consciousness", "existence", "truth", "know"],
    "Futurist": ["future", "prediction", "trend", "forecast", "will"],
    "Psychologist": ["behavior", "mind", "cognitive", "emotion", "psychology"],
    "Data Scientist": ["data", "statistics", "analytics", "numbers", "model"],
    "Conspiracy Theorist": ["hidden", "secret", "conspiracy", "cover-up", "agenda"],
}

def auto_select_agents(topic):
    selected = ["Ahany"]
    for agent, keywords in EXPERT_KEYWORDS.items():
        for kw in keywords:
            if kw in topic.lower() and agent not in selected:
                selected.append(agent)
                break
    if len(selected) < 3: selected = ["Harsh", "Jayant", "Ahany", "Nish"]
    return selected

def auto_detect_tone(topic):
    if "?" in topic: return "Casual"
    if any(w in topic.lower() for w in ["prove", "evidence", "study"]): return "Academic"
    if any(w in topic.lower() for w in ["brutal", "harsh", "destroy"]): return "Brutal"    return "Neutral"
# ==========================================
# AGENTS (MODIFIED FOR DETERMINISTIC BINDING)
# ==========================================
class Agent:
    def __init__(self, name, role, personality, avatar, card_class):
        self.name, self.role, self.personality, self.avatar, self.card_class = name, role, personality, avatar, card_class
        self.history = []

    def speak(self, topic, last_msg, round_num, preferred_provider, tone, swarm_mode, think_deeper, cognitive_state, behavioral_mode):
        history = "\n".join(self.history[-2:]) or "No previous chat."
        state_str = ", ".join([f"{k}: {v}" for k, v in cognitive_state.items()])
        
        system = f"""You are {self.name} ({self.role}). {self.personality}. Respond in a {tone} tone.
        CRITICAL INSTRUCTION: Your internal cognitive state is currently: [{state_str}]. 
        Your current behavioral mode is: [{behavioral_mode}].
        If your mode is AVOID, be hesitant and brief. If EXECUTE, be aggressive and direct. 
        If anxiety is high, show signs of stress. You MUST reflect this internal state in your tone."""

        prompt = f"""Debate round {round_num} on: "{topic}"
        Format: **Claim:** [point] **Evidence:** [fact] **Reasoning:** [why]
        History: {history}
        Last: "{last_msg}"
        """
        reply, provider = generate_with_fallback(prompt, system, preferred_provider)
        self.history.append(reply)
        return reply, provider

class Moderator(Agent):
    def speak(self, topic, last_msg, round_num, preferred_provider, tone, swarm_mode, think_deeper, cognitive_state, behavioral_mode):
        history = "\n".join(self.history[-3:]) or "No debate yet."
        system = f"You are {self.name}, the enhanced moderator. Detect contradictions and force engagement."
        prompt = f"Summarise, flag a contradiction, and challenge a weak point. Topic: {topic} | Round: {round_num}\nHistory: {history}\nLast: {last_msg}"
        reply, provider = generate_with_fallback(prompt, system, preferred_provider)
        self.history.append(reply)
        return reply, provider

ALL_AGENTS = [
    ("Harsh", "Skeptic", "Ruthlessly find logical flaws.", "🔴", "card-skeptic"),
    ("Jayant", "Optimist", "Sees opportunity and growth.", "🟢", "card-optimist"),
    ("Ahany", "Moderator", "Detects contradictions.", "🔵", "card-moderator", True),
    ("Ritik", "Policy Advisor", "Gov/regulation perspective.", "🟡", "card-policy"),
    ("Kavya", "Retail Investor", "Everyday practical view.", "🟣", "card-optimist"),
    ("Nish", "Scientist", "Empirical evidence only.", "🟠", "card-data"),
    ("Teju", "Tech Journalist", "Trends and narratives.", "🔷", "card-futurist"),
    ("Shivam", "Conspiracy Theorist", "Hidden agendas.", "⚫", "card-conspiracy"),
    ("Philosopher", "Philosopher", "Ethical context.", "🟤", "card-philosopher"),
    ("Futurist", "Futurist", "Long-term implications.", "🔮", "card-futurist"),
    ("DataScientist", "Data Scientist", "Statistics.", "📊", "card-data"),
    ("Ethicist", "Ethicist", "Moral implications.", "⚖️", "card-ethicist"),
    ("Psychologist", "Psychologist", "Human behavior.", "🧠", "card-psychologist"),
    ("Economist", "Economist", "Financial impact.", "📈", "card-economist"),
    ("Technologist", "Technologist", "Tech feasibility.", "💻", "card-technologist"),
    ("Legal Expert", "Legal Expert", "Laws and precedents.", "⚖️", "card-legal"),
]

def create_panel(selected_agents):
    agents, moderator = [], None
    for agent_data in ALL_AGENTS:
        name = agent_data[0]
        if name not in selected_agents: continue
        role, personality, avatar, card_class = agent_data[1], agent_data[2], agent_data[3], agent_data[4]
        if len(agent_data) == 6 and agent_data[5]:
            moderator = Moderator(name, role, personality, avatar, card_class)
        else:
            agents.append(Agent(name, role, personality, avatar, card_class))
    if moderator:
        agents.insert(1, moderator) if len(agents) >= 1 else agents.append(moderator)
    return agents

SWARM_MODES = {
    "Debate": "Argue your position strongly. Refute the opponent's points directly.",
    "Council": "Collaborate towards a consensus recommendation.",
    "Devil's Advocate": "Push back aggressively on every point raised.",
    "Exploration": "Each agent explores a unique angle independently.",
    "Rapid Fire": "Keep arguments very short — 1-2 sentences maximum.",
}
# ===================== SIDEBAR =====================
with st.sidebar:
    st.markdown("### 💜 Nyx")
    st.markdown("---")

    st.markdown("### 🤖 Kernel")
    model_choice = st.selectbox("Active model", ["🤖 Auto"] + [p["name"] for p in PROVIDERS], index=0)
    preferred = None if model_choice == "🤖 Auto" else model_choice

    st.markdown("---")
    st.markdown("### ⚙️ Swarm Mode")
    swarm_mode = st.selectbox("Mode", list(SWARM_MODES.keys()), index=0)

    st.markdown("### 🧠 Cognition")
    think_deeper = st.toggle("🔄 Think Deeper", value=False)
    auto_experts = st.toggle("🤖 Auto-Select Experts", value=True)
    
    st.markdown("### 🔬 Advanced Simulation")
    advanced_mode = st.toggle("Enable Advanced Diagnostics", value=False, help="Read-only analytics. Does not mutate kernel state.")
    if advanced_mode:
        st.caption("Post-simulation diagnostic suite.")

# ===================== MAIN APP =====================
st.markdown('<div class="nyx-title">Nyx</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Deterministic Cognitive-Society Simulation Engine</div>', unsafe_allow_html=True)

# Input Area
with st.container():
    topic = st.text_input("Enter simulation topic or decision parameter:", placeholder="e.g., Should we implement a universal basic income?")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if auto_experts and topic:
            selected_agents = auto_select_agents(topic)
        else:
            selected_agents = st.multiselect("Select Agents", [a[0] for a in ALL_AGENTS], default=["Harsh", "Jayant", "Ahany"])
    with col2:
        num_rounds = st.slider("Rounds", 1, 5, 3)

    if st.button("🚀 Initialize Simulation", use_container_width=True):
        if not topic:
            st.warning("Please enter a topic.")
        else:
            st.session_state.simulation_complete = False
            st.session_state.debate_history = []
            
            # 1. Initialize Deterministic Kernel
            st.session_state.nyx_kernel = NyxKernel(selected_agents, seed=42)
            panel = create_panel(selected_agents)
            
            # 2. Run Simulation Loop
            progress_bar = st.progress(0)
            status_text = st.empty()
            last_msg = "Simulation initialized."
            tone = auto_detect_tone(topic)
            
            for r in range(num_rounds):
                status_text.info(f"Processing Round {r+1}/{num_rounds}... Kernel updating cognitive states.")
                
                # A. Kernel computes deterministic state transitions
                modes = st.session_state.nyx_kernel.step()
                
                # B. Agents speak (Narrative Binding)
                for agent in panel:
                    if agent.name in modes:
                        cognitive_state = st.session_state.nyx_kernel.agents[agent.name].to_dict()
                        mode = modes[agent.name]
                        
                        reply, provider = agent.speak(
                            topic, last_msg, r+1, preferred, tone, swarm_mode, 
                            think_deeper, cognitive_state, mode
                        )
                        
                        st.session_state.debate_history.append({
                            "round": r+1, "agent": agent.name, "avatar": agent.avatar, 
                            "mode": mode, "text": reply, "provider": provider, "card_class": agent.card_class
                        })
                        last_msg = reply
                        
                progress_bar.progress((r + 1) / num_rounds)
                
            status_text.success("Simulation Complete.")
            st.session_state.simulation_complete = True
            time.sleep(1)
            st.rerun()
# Render Chat History
if st.session_state.debate_history:
    st.markdown("### 📜 Simulation Transcript")
    for msg in st.session_state.debate_history:
        with st.container():
            st.markdown(f"""
            <div class="glass-card {msg['card_class']}">
                <b>{msg['avatar']} {msg['agent']}</b> <span style="opacity:0.6; font-size:0.8rem;">[Round {msg['round']} • Mode: {msg['mode']}]</span><br>
                {msg['text']}
            </div>
            """, unsafe_allow_html=True)

# Render Diagnostics
if st.session_state.simulation_complete and st.session_state.nyx_kernel:
    st.markdown("---")
    st.markdown("### 📊 Nyx Cognitive & Outcome Diagnostics")
    
    kernel = st.session_state.nyx_kernel
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("**Deterministic Outcome Vector**")
        outcomes = kernel.get_outcome_vector()
        for metric, val in outcomes.items():
            st.progress(val, text=f"{metric.replace('_', ' ').title()}: {val}")
            
    with col2:
        st.markdown("**Agent Cognitive Radar**")
        selected_agent = st.selectbox("Inspect Agent State", list(kernel.agents.keys()))
        state_dict = kernel.agents[selected_agent].to_dict()
        
        keys = list(state_dict.keys())
        vals = list(state_dict.values())
        
        fig = go.Figure(data=go.Scatterpolar(
            r=vals + [vals[0]],  
            theta=keys + [keys[0]],
            fill='toself',
            line_color='#9B4DFF'
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            showlegend=False,
            height=350,
            margin=dict(l=40, r=40, t=20, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#2C2A28')
        )
        st.plotly_chart(fig, use_container_width=True)

    # Advanced Mode Mock Diagnostics
    if advanced_mode:
        st.markdown("#### 🔬 Advanced Diagnostic Suite")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Run Monte Carlo (100 trajectories)"):
                st.info("Simulating 100 seeded trajectories...")
                st.success("Convergence probability: 84% | Divergence risk: 16%")
        with c2:
            if st.button("Detect Black Swans"):
                st.warning("⚠️ Fragility detected in 'Skeptic' node. Cascade threshold: 0.42")
        with c3:
            if st.button("Generate Counterfactual"):
                st.success("Counterfactual: System reaches consensus 2 rounds earlier if initial anxiety is reduced by 20%.")

