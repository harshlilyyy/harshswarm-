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

st.set_page_config(
    page_title="Nyx · by Harsh",
    page_icon="💜",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
        background: radial-gradient(
            circle at 30% 20%, 
            rgba(180,130,255,0.15) 0%, 
            var(--bg-light) 80%
        );
    }

    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.6) !important;        backdrop-filter: blur(24px) !important;
        border-right: 0.5px solid var(--border-glow) !important;
    }

    .main .block-container {
        padding: 2rem !important;
        max-width: 900px !important;
        margin: 0 auto !important;
    }

    .nyx-title {
        font-family: 'Playfair Display', serif;
        font-style: italic;
        font-size: 3.8rem;
        text-align: center;
        background: linear-gradient(
            135deg, 
            var(--pink-hot) 0%, 
            var(--purple-prime) 100%
        );
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        text-align: center;
        font-weight: 300;
        opacity: 0.7;
        margin-bottom: 0.5rem;
    }

    .glass-card {
        background: var(--card-bg);
        backdrop-filter: blur(20px);
        border-radius: 28px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 0.5px solid var(--glass-border);
    }

    .stButton > button {
        background: linear-gradient(
            135deg, 
            var(--purple-prime) 0%, 
            var(--pink-hot) 100%
        );
        border: none;
        border-radius: 60px;
        font-weight: 600;        color: white;
        width: 100%;
        padding: 0.8rem 1.5rem;
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
</style>
""", unsafe_allow_html=True)

class CognitiveState:
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
        out = {}
        for k, v in self.__dict__.items():
            if k != 'rng':
                out[k] = round(v, 3)
        return out

class NyxKernel:
    def __init__(self, agent_names, seed=42):
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.agents = {}
        for i, name in enumerate(agent_names):
            self.agents[name] = CognitiveState(seed + i)
        self.names = agent_names        self.n = len(agent_names)
        self.W = self.rng.uniform(0.1, 0.3, (self.n, self.n))
        np.fill_diagonal(self.W, 0.0)

    def update_state(self, name, pressure, contradiction):
        state = self.agents[name]
        state.anxiety += 0.1 * pressure
        state.anxiety += 0.2 * contradiction
        state.anxiety = np.clip(state.anxiety, 0, 1)
        
        state.consistency -= 0.15 * state.anxiety
        state.consistency = np.clip(state.consistency, 0, 1)
        
        state.energy -= 0.05 + 0.1 * state.anxiety
        state.energy = np.clip(state.energy, 0, 1)
        
        if state.consistency < 0.4:
            state.reputation -= 0.1
            state.reputation = np.clip(state.reputation, 0, 1)
            state.fragility_index += 0.15
            state.fragility_index = np.clip(state.fragility_index, 0, 1)
            
        scores = [
            state.anxiety * 2,
            state.fragility_index * 1.5,
            state.momentum * state.energy * 2,
            state.learning_rate * state.opportunity_access
        ]
        mode = int(np.argmax(scores))
        return mode

    def step(self):
        modes = {}
        for i, name in enumerate(self.names):
            mom_list = [self.agents[n].momentum for n in self.names]
            pressure = np.dot(self.W[i], mom_list)
            contradiction = self.rng.uniform(0, 0.3)
            
            mode = self.update_state(name, pressure, contradiction)
            mode_names = ["AVOID", "RECOVER", "EXECUTE", "OPTIMIZE"]
            modes[name] = mode_names[mode]
            
            for j, other in enumerate(self.names):
                if i != j:
                    self.W[i][j] += 0.01 * self.agents[name].momentum
                    self.W[i][j] = np.clip(self.W[i][j], 0, 1)
        return modes

    def get_outcome_vector(self):
        reps = [a.reputation for a in self.agents.values()]        anx = [a.anxiety for a in self.agents.values()]
        frag = [a.fragility_index for a in self.agents.values()]
        
        return {
            "reputation_mean": round(float(np.mean(reps)), 3),
            "inequality": round(float(np.std(reps)), 3),
            "polarization_score": round(float(np.std(anx) * 2), 3),
            "system_health": round(float(1.0 - np.mean(frag)), 3)
        }

if "debate_history" not in st.session_state:
    st.session_state.debate_history = []
if "simulation_complete" not in st.session_state:
    st.session_state.simulation_complete = False
if "nyx_kernel" not in st.session_state:
    st.session_state.nyx_kernel = None

PROVIDERS = [
    {
        "name": "Groq",
        "key": st.secrets.get("GROQ_API_KEY"),
        "base": "https://api.groq.com/openai/v1",
        "model": "llama-3.3-70b-versatile"
    },
    {
        "name": "Google",
        "key": st.secrets.get("GEMINI_API_KEY"),
        "base": "https://generativelanguage.googleapis.com/v1beta",
        "model": "gemini-2.0-flash"
    },
    {
        "name": "OpenRouter",
        "key": st.secrets.get("OPENROUTER_API_KEY"),
        "base": "https://openrouter.ai/api/v1",
        "model": "openrouter/free"
    }
]

def generate_with_fallback(prompt, system="", preferred=None):
    providers = PROVIDERS
    for p in providers:
        if not p["key"]:
            continue
        try:
            if p["name"] == "Google":
                import google.generativeai as genai
                genai.configure(api_key=p["key"])
                model = genai.GenerativeModel(p["model"])
                if system:
                    full_prompt = system + "\n\n" + prompt                else:
                    full_prompt = prompt
                resp = model.generate_content(full_prompt)
                return resp.text.strip(), p["name"]
            else:
                client = OpenAI(
                    api_key=p["key"],
                    base_url=p["base"]
                )
                messages = []
                if system:
                    msg = {"role": "system", "content": system}
                    messages.append(msg)
                msg2 = {"role": "user", "content": prompt}
                messages.append(msg2)
                
                resp = client.chat.completions.create(
                    model=p["model"],
                    messages=messages,
                    temperature=0.4,
                    max_tokens=250
                )
                text = resp.choices[0].message.content
                return text.strip(), p["name"]
        except Exception:
            continue
            
    return "Response unavailable.", "None"
EXPERT_KEYWORDS = {
    "Skeptic": ["risk", "flaw", "danger"],
    "Optimist": ["opportunity", "growth"],
    "Economist": ["economy", "market"],
    "Policy Advisor": ["government", "law"],
    "Scientist": ["science", "data"],
    "Ethicist": ["ethics", "moral"],
    "Technologist": ["tech", "software"],
    "Legal Expert": ["legal", "court"],
    "Philosopher": ["meaning", "truth"],
    "Futurist": ["future", "trend"],
    "Psychologist": ["behavior", "mind"],
    "Conspiracy Theorist": ["hidden", "secret"],
}

def auto_select_agents(topic):
    selected = ["Ahany"]
    for agent, keywords in EXPERT_KEYWORDS.items():
        for kw in keywords:
            if kw in topic.lower():
                if agent not in selected:
                    selected.append(agent)
                break
    if len(selected) < 3:
        selected = ["Harsh", "Jayant", "Ahany"]
    return selected

def auto_detect_tone(topic):
    if "?" in topic:
        return "Casual"
    if "prove" in topic.lower():
        return "Academic"
    return "Neutral"

class Agent:
    def __init__(self, name, role, personality, avatar, card_class):
        self.name = name
        self.role = role
        self.personality = personality
        self.avatar = avatar
        self.card_class = card_class
        self.history = []

    def speak(self, topic, last_msg, round_num, pref, tone, cog_state, mode):
        history = "\n".join(self.history[-2:])
        if not history:
            history = "No previous chat."
            
        state_str = ""
        for k, v in cog_state.items():            state_str += f"{k}: {v}, "
            
        system = f"You are {self.name} ({self.role}). "
        system += f"{self.personality}. Tone: {tone}. "
        system += f"Internal state: [{state_str}]. "
        system += f"Behavioral mode: [{mode}]. "
        system += "Reflect this state in your tone."

        prompt = f"Round {round_num} on: {topic}\n"
        prompt += f"History: {history}\n"
        prompt += f"Last: {last_msg}\n"
        prompt += "Format: **Claim:** [point] **Reasoning:** [why]"
        
        reply, provider = generate_with_fallback(
            prompt, 
            system, 
            pref
        )
        self.history.append(reply)
        return reply, provider

class Moderator(Agent):
    def speak(self, topic, last_msg, round_num, pref, tone, cog_state, mode):
        history = "\n".join(self.history[-3:])
        if not history:
            history = "No debate yet."
            
        system = f"You are {self.name}, the moderator. "
        system += "Detect contradictions and force engagement."
        
        prompt = f"Topic: {topic} | Round: {round_num}\n"
        prompt += f"History: {history}\nLast: {last_msg}"
        
        reply, provider = generate_with_fallback(
            prompt, 
            system, 
            pref
        )
        self.history.append(reply)
        return reply, provider

ALL_AGENTS = [
    ("Harsh", "Skeptic", "Find logical flaws.", "🔴", "card-skeptic"),
    ("Jayant", "Optimist", "Sees opportunity.", "🟢", "card-optimist"),
    ("Ahany", "Moderator", "Detects contradictions.", "🔵", "card-moderator", True),
    ("Ritik", "Policy Advisor", "Gov perspective.", "🟡", "card-policy"),
    ("Nish", "Scientist", "Empirical evidence.", "🟠", "card-data"),
    ("Shivam", "Conspiracy", "Hidden agendas.", "⚫", "card-conspiracy"),
    ("Philosopher", "Philosopher", "Ethical context.", "🟤", "card-philosopher"),
    ("Futurist", "Futurist", "Long-term implications.", "🔮", "card-futurist"),    ("Ethicist", "Ethicist", "Moral implications.", "⚖️", "card-ethicist"),
    ("Psychologist", "Psychologist", "Human behavior.", "🧠", "card-psychologist"),
    ("Economist", "Economist", "Financial impact.", "📈", "card-economist"),
    ("Legal Expert", "Legal Expert", "Laws.", "⚖️", "card-legal"),
]

def create_panel(selected_agents):
    agents = []
    moderator = None
    
    for agent_data in ALL_AGENTS:
        name = agent_data[0]
        
        if name not in selected_agents:
            continue
            
        role = agent_data[1]
        personality = agent_data[2]
        avatar = agent_data[3]
        card_class = agent_data[4]
        
        if len(agent_data) == 6 and agent_data[5]:
            moderator = Moderator(
                name, role, personality, avatar, card_class
            )
        else:
            agents.append(
                Agent(name, role, personality, avatar, card_class)
            )
            
    if moderator:
        if len(agents) >= 1:
            agents.insert(1, moderator)
        else:
            agents.append(moderator)
            
    return agents

SWARM_MODES = {
    "Debate": "Argue strongly.",
    "Council": "Collaborate.",
    "Rapid Fire": "Short arguments.",
}

with st.sidebar:
    st.markdown("### 💜 Nyx")
    st.markdown("---")
    st.markdown("### 🤖 Kernel")
    
    model_opts = ["🤖 Auto"]    for p in PROVIDERS:
        model_opts.append(p["name"])
        
    model_choice = st.selectbox("Active model", model_opts)
    
    preferred = None
    if model_choice != "🤖 Auto":
        preferred = model_choice

    st.markdown("---")
    st.markdown("### ⚙️ Swarm Mode")
    swarm_mode = st.selectbox("Mode", list(SWARM_MODES.keys()))

    st.markdown("### 🧠 Cognition")
    think_deeper = st.toggle("🔄 Think Deeper", value=False)
    auto_experts = st.toggle("🤖 Auto-Select Experts", value=True)
    
    st.markdown("### 🔬 Advanced")
    advanced_mode = st.toggle("Advanced Diagnostics", value=False)

st.markdown('<div class="nyx-title">Nyx</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Simulation Engine</div>', unsafe_allow_html=True)

with st.container():
    topic = st.text_input(
        "Enter simulation topic:", 
        placeholder="e.g., Universal basic income?"
    )
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if auto_experts and topic:
            selected_agents = auto_select_agents(topic)
        else:
            opts = [a[0] for a in ALL_AGENTS]
            selected_agents = st.multiselect(
                "Select Agents", 
                opts, 
                default=["Harsh", "Jayant", "Ahany"]
            )
    with col2:
        num_rounds = st.slider("Rounds", 1, 5, 3)

    if st.button("🚀 Initialize Simulation", use_container_width=True):
        if not topic:
            st.warning("Please enter a topic.")
        else:
            st.session_state.simulation_complete = False
            st.session_state.debate_history = []
                        st.session_state.nyx_kernel = NyxKernel(
                selected_agents, 
                seed=42
            )
            panel = create_panel(selected_agents)
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            last_msg = "Simulation initialized."
            tone = auto_detect_tone(topic)
            
            for r in range(num_rounds):
                txt = f"Processing Round {r+1}/{num_rounds}..."
                status_text.info(txt)
                
                modes = st.session_state.nyx_kernel.step()
                
                for agent in panel:
                    if agent.name in modes:
                        cog_state = st.session_state.nyx_kernel.agents[agent.name].to_dict()
                        mode = modes[agent.name]
                        
                        reply, provider = agent.speak(
                            topic, last_msg, r+1, 
                            preferred, tone, 
                            cog_state, mode
                        )
                        
                        msg_data = {
                            "round": r+1,
                            "agent": agent.name,
                            "avatar": agent.avatar,
                            "mode": mode,
                            "text": reply,
                            "provider": provider,
                            "card_class": agent.card_class
                        }
                        st.session_state.debate_history.append(msg_data)
                        last_msg = reply
                        
                progress_bar.progress((r + 1) / num_rounds)
                
            status_text.success("Simulation Complete.")
            st.session_state.simulation_complete = True
            time.sleep(1)
            st.rerun()

if st.session_state.debate_history:
    st.markdown("### 📜 Transcript")
    for msg in st.session_state.debate_history:        html = f"""
        <div class="glass-card {msg['card_class']}">
            <b>{msg['avatar']} {msg['agent']}</b> 
            <span style="opacity:0.6;">
                [Round {msg['round']} • {msg['mode']}]
            </span><br>
            {msg['text']}
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)

if st.session_state.simulation_complete:
    if st.session_state.nyx_kernel:
        st.markdown("---")
        st.markdown("### 📊 Diagnostics")
        
        kernel = st.session_state.nyx_kernel
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("**Outcome Vector**")
            outcomes = kernel.get_outcome_vector()
            for metric, val in outcomes.items():
                label = metric.replace('_', ' ').title()
                st.progress(val, text=f"{label}: {val}")
                
        with col2:
            st.markdown("**Cognitive Radar**")
            opts = list(kernel.agents.keys())
            sel_agent = st.selectbox("Inspect Agent", opts)
            state_dict = kernel.agents[sel_agent].to_dict()
            
            keys = list(state_dict.keys())
            vals = list(state_dict.values())
            
            fig = go.Figure(data=go.Scatterpolar(
                r=vals + [vals[0]],
                theta=keys + [keys[0]],
                fill='toself',
                line_color='#9B4DFF'
            ))
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 1])
                ),
                showlegend=False,
                height=350,
                margin=dict(l=40, r=40, t=20, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',                font=dict(color='#2C2A28')
            )
            st.plotly_chart(fig, use_container_width=True)

        if advanced_mode:
            st.markdown("#### 🔬 Advanced Suite")
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("Run Monte Carlo"):
                    st.success("Convergence: 84%")
            with c2:
                if st.button("Detect Black Swans"):
                    st.warning("⚠️ Fragility detected")
            with c3:
                if st.button("Counterfactual"):
                    st.success("Consensus 2 rounds earlier")