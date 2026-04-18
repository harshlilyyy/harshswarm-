import streamlit as st
import google.generativeai as genai
import time
import random
import json
import os
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="HarshSwarm Pro • AI Debate",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Premium Custom CSS (same as before) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    :root {
        --bg-primary: #f8fafc;
        --bg-secondary: #ffffff;
        --text-primary: #0f172a;
        --text-secondary: #475569;
        --card-bg: rgba(255, 255, 255, 0.85);
        --card-border: rgba(148, 163, 184, 0.18);
        --sidebar-bg: rgba(255, 255, 255, 0.7);
        --gradient-start: #0ea5e9;
        --gradient-mid: #8b5cf6;
        --gradient-end: #ec4899;
        --shadow-sm: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
        --shadow-lg: 0 20px 35px -8px rgba(0, 0, 0, 0.1);
    }
    [data-theme="dark"] {
        --bg-primary: #0b1120;
        --bg-secondary: #1e293b;
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --card-bg: rgba(30, 41, 59, 0.85);
        --card-border: rgba(71, 85, 105, 0.3);
        --sidebar-bg: rgba(15, 23, 42, 0.7);
        --gradient-start: #38bdf8;
        --gradient-mid: #a78bfa;
        --gradient-end: #f472b6;
        --shadow-sm: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        --shadow-lg: 0 20px 35px -8px rgba(0, 0, 0, 0.4);
    }
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background: var(--bg-primary);
        color: var(--text-primary);
        transition: background 0.3s ease, color 0.3s ease;
    }
    .main .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1400px; }
    h1 {
        background: linear-gradient(135deg, var(--gradient-start) 0%, var(--gradient-mid) 50%, var(--gradient-end) 100%);
        background-size: 200% 200%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
        font-size: 3.2rem !important;
        letter-spacing: -0.02em;
        margin-bottom: 0.25rem !important;
        animation: gradientShift 8s ease infinite;
    }
    @keyframes gradientShift { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
    [data-testid="stSidebar"] { background: var(--sidebar-bg); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border-right: 1px solid var(--card-border); }
    [data-testid="stChatMessage"] {
        background: var(--card-bg); backdrop-filter: blur(12px); border-radius: 24px; padding: 1.25rem 1.75rem;
        box-shadow: var(--shadow-sm); margin-bottom: 1.25rem; border-left: 6px solid; border: 1px solid var(--card-border);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    [data-testid="stChatMessage"]:hover { transform: translateY(-6px) scale(1.01); box-shadow: var(--shadow-lg); }
    .stButton > button {
        background: linear-gradient(135deg, var(--gradient-start) 0%, var(--gradient-mid) 100%);
        color: white; font-weight: 700; font-size: 1.1rem; padding: 0.9rem 2rem; border-radius: 60px; border: none;
        box-shadow: 0 8px 20px rgba(14, 165, 233, 0.25); transition: all 0.3s ease; letter-spacing: 0.3px;
        border: 1px solid rgba(255, 255, 255, 0.1); animation: pulseGlow 2s infinite;
    }
    @keyframes pulseGlow { 0% { box-shadow: 0 8px 20px rgba(14, 165, 233, 0.25); } 50% { box-shadow: 0 12px 28px rgba(139, 92, 246, 0.4); } 100% { box-shadow: 0 8px 20px rgba(14, 165, 233, 0.25); } }
    .stButton > button:hover { transform: translateY(-4px) scale(1.02); box-shadow: 0 18px 35px rgba(139, 92, 246, 0.5); background: linear-gradient(135deg, #0284c7 0%, #7c3aed 100%); animation: none; }
    .verdict-box { background: var(--card-bg); backdrop-filter: blur(12px); border-radius: 28px; padding: 2rem 2.5rem; margin: 2rem 0; border: 1px solid rgba(14, 165, 233, 0.2); box-shadow: var(--shadow-sm); }
    .evolution-box { background: linear-gradient(135deg, rgba(34, 197, 94, 0.05) 0%, rgba(34, 197, 94, 0.02) 100%); border-radius: 20px; padding: 1.5rem 2rem; margin: 1.5rem 0; border: 1px solid rgba(34, 197, 94, 0.3); }
    hr { margin: 2rem 0; border: 0; height: 1px; background: linear-gradient(90deg, transparent, var(--card-border), transparent); }
</style>
""", unsafe_allow_html=True)

# --- Dark Mode Toggle ---
if "theme" not in st.session_state:
    st.session_state.theme = "light"
def toggle_theme():
    st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
st.markdown(f"""<script>document.documentElement.setAttribute('data-theme', '{st.session_state.theme}');</script>""", unsafe_allow_html=True)

st.title("⚡ HarshSwarm Pro")
st.markdown("##### *Multi‑Agent Intelligence • Personalized Debate Panel • Evolving Memory*")
st.caption("Where diverse AI perspectives collide to uncover truth.")

with st.sidebar:
    col1, col2 = st.columns([3, 1])
    with col1: st.markdown("### 🎛️ Control Panel")
    with col2:
        theme_icon = "🌙" if st.session_state.theme == "light" else "☀️"
        if st.button(theme_icon, help="Toggle dark/light mode"): toggle_theme(); st.rerun()

# --- API Key Handling ---
api_key = None
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    with st.sidebar: st.success("🔐 API key loaded")
except (KeyError, FileNotFoundError):
    with st.sidebar:
        st.warning("⚠️ No secret found. Enter key below.")
        api_key = st.text_input("🔑 Gemini API Key", type="password")
        if not api_key: st.stop()

genai.configure(api_key=api_key)
MODEL_NAME = 'gemma-3-27b-it'

# --- Evolution Memory (Robust) ---
EVO_FILE = "evolution_memory.json"

def load_evolution_memory():
    # Try file first
    if os.path.exists(EVO_FILE):
        try:
            with open(EVO_FILE, "r") as f:
                data = json.load(f)
                st.session_state.evo_memory = data
                return data
        except: pass
    # Fallback to session state
    if "evo_memory" not in st.session_state:
        st.session_state.evo_memory = []
    return st.session_state.evo_memory

def save_evolution_memory(memory):
    st.session_state.evo_memory = memory
    try:
        with open(EVO_FILE, "w") as f:
            json.dump(memory, f, indent=2)
    except: pass  # Silently fail if no write permissions

def add_winning_strategy(topic, verdict, winning_side, key_arguments):
    memory = load_evolution_memory()
    entry = {
        "timestamp": datetime.now().isoformat(),
        "topic": topic,
        "verdict_summary": verdict,
        "winning_side": winning_side,
        "key_arguments": key_arguments
    }
    memory.append(entry)
    if len(memory) > 30: memory = memory[-30:]
    save_evolution_memory(memory)
    return entry

def get_relevant_strategies(topic, max_entries=3):
    memory = load_evolution_memory()
    if not memory: return []
    topic_lower = topic.lower()
    scored = []
    for entry in memory:
        entry_topic = entry["topic"].lower()
        # Simple overlap scoring
        topic_words = set(topic_lower.split())
        entry_words = set(entry_topic.split())
        overlap = len(topic_words & entry_words)
        # Bonus for longer phrase matches
        if topic_lower in entry_topic or entry_topic in topic_lower: overlap += 5
        scored.append((overlap, entry))
    scored.sort(key=lambda x: x[0], reverse=True)
    # Return top entries with score > 0
    return [entry for score, entry in scored[:max_entries] if score > 0]

# --- Sidebar ---
with st.sidebar:
    st.markdown("### 📰 Debate Topic")
    topic = st.text_area("Paste a headline or article snippet", value="Apple announces new AI chip that uses 50% less power and is carbon neutral.", height=150)
    st.markdown("---")
    st.markdown("### ⚙️ Core Settings")
    rounds = st.slider("Debate Rounds", 2, 6, 3)
    use_tones = st.checkbox("🎭 Randomize agent tones", True)
    st.markdown("---")
    st.markdown("### 🧑‍🤝‍🧑 Panel Members")
    extra_agents = st.multiselect(
        "Invite more voices",
        ["👔 Ritik (Policy Advisor)", "💰 Kavya (Retail Investor)", "🔬 Nish (Scientist)", 
         "📱 Teju (Tech Journalist)", "🕵️ Shivam (Conspiracy Theorist)"],
        default=["💰 Kavya (Retail Investor)", "📱 Teju (Tech Journalist)"]
    )
    st.markdown("---")
    with st.expander("🧬 Evolution Memory", expanded=True):
        memory = load_evolution_memory()
        if memory:
            st.metric("Stored Strategies", len(memory))
            for entry in memory[-3:]:
                st.markdown(f"- *{entry['topic'][:35]}...* ({entry['winning_side']})")
        else:
            st.caption("No strategies yet. Save one after a debate!")
    # Debug toggle (optional)
    debug_mode = st.checkbox("🐞 Debug mode", value=False)

# --- Agent Classes ---
class AI_Agent:
    def __init__(self, name, personality, avatar):
        self.name = name
        self.personality = personality
        self.avatar = avatar
        self.history = []

    def speak(self, topic, last_msg, model, round_num, tone=None, evolution_context=""):
        history_text = "\n".join(self.history[-3:]) if self.history else "No previous chat."
        tone_str = f"Tone: {tone}." if tone else ""
        # Stronger prompt injection for evolution
        evo_instruction = ""
        if evolution_context:
            evo_instruction = f"""
IMPORTANT - EVOLUTION MEMORY:
The swarm has learned from past winning strategies on similar topics:
{evolution_context}
You MUST incorporate this wisdom into your argument. Reference a past winning insight if appropriate.
"""
        prompt = f"""
You are {self.name}. {self.personality} {tone_str}
Debate round {round_num} about: "{topic}"
Recent memory:
{history_text}
{evo_instruction}
Last said: "{last_msg}"
Respond in 2-4 sentences. Be persuasive and stay in character.
"""
        response = model.generate_content(prompt)
        reply = response.text
        self.history.append(f"{self.name}: {reply}")
        return reply

class Moderator(AI_Agent):
    def speak(self, topic, last_msg, model, round_num, tone=None, evolution_context=""):
        history_text = "\n".join(self.history[-5:]) if self.history else "No debate yet."
        evo_instruction = ""
        if evolution_context:
            evo_instruction = f"""
EVOLUTION MEMORY (past winning strategies on similar topics):
{evolution_context}
Use this to challenge panelists or highlight patterns.
"""
        prompt = f"""
You are {self.name}, a sharp journalist and moderator.
Topic: "{topic}" | Round: {round_num}
History:
{history_text}
{evo_instruction}
Last exchange: "{last_msg}"
Summarize key points, identify contradictions, and ask a provocative question.
Keep it to 3-4 sentences.
"""
        response = model.generate_content(prompt)
        reply = response.text
        self.history.append(f"{self.name}: {reply}")
        return reply

def get_verdict(topic, messages, model):
    debate_text = "\n".join(messages[-20:])
    prompt = f"""
Expert analysis of debate on: "{topic}"
Transcript excerpt:
{debate_text}
Provide:
1. 🏆 Strongest arguments (which panelist made the most compelling case)
2. ⚠️ Key risks identified
3. 🚀 Key opportunities identified
4. ⚖️ Balanced conclusion (2-3 sentences)
"""
    return model.generate_content(prompt).text

def random_tone():
    return random.choice(["calm", "aggressive", "sarcastic", "curious", "dismissive", "passionate"])

# --- Agent Factory (same as before) ---
def create_agents(extra_agent_keys):
    agents = {
        "harsh": AI_Agent("Harsh", "Skeptical analyst. You find flaws, risks, and unintended consequences in every optimistic claim. You question assumptions and demand evidence.", "🔴"),
        "jayant": AI_Agent("Jayant", "Optimistic visionary. You see opportunity and growth in disruption. You believe technology and innovation solve problems and create a better future.", "🟢"),
        "ahany": Moderator("Ahany", "Lead moderator and sharp journalist. You challenge all sides, identify weak logic, and keep the debate focused and productive.", "🔵")
    }
    extra_map = {
        "👔 Ritik (Policy Advisor)": ("Ritik", "Policy advisor. Government/regulatory perspective. Focus on public good and political feasibility.", "🟡"),
        "💰 Kavya (Retail Investor)": ("Kavya", "Retail investor. Everyday person perspective. Practical impact on savings and lifestyle.", "🟣"),
        "🔬 Nish (Scientist)": ("Nish", "Scientific skeptic. Demands empirical evidence and peer review.", "🟠"),
        "📱 Teju (Tech Journalist)": ("Teju", "Tech journalist. Identifies trends and market narratives.", "🔷"),
        "🕵️ Shivam (Conspiracy Theorist)": ("Shivam", "Conspiracy theorist. Sees hidden agendas and questions official narratives.", "⚫")
    }
    for key in extra_agent_keys:
        if key in extra_map:
            name, persona, avatar = extra_map[key]
            agents[name.lower()] = AI_Agent(name, persona, avatar)
    return agents

# --- Main Debate Function ---
def run_debate(topic, rounds, use_tones, extra_agent_keys):
    model = genai.GenerativeModel(MODEL_NAME)
    
    strategies = get_relevant_strategies(topic)
    evolution_context = ""
    if strategies:
        evolution_context = "PAST WINNING STRATEGIES:\n"
        for s in strategies:
            evolution_context += f"- Topic: {s['topic']}\n  Winner: {s['winning_side']}\n  Key Argument: {s['key_arguments'][:300]}\n\n"
    
    agents = create_agents(extra_agent_keys)
    
    st.divider()
    st.subheader(f"📰 Topic: {topic}")
    st.caption(f"Rounds: {rounds} | Model: {MODEL_NAME} | Panelists: {len(agents)}")
    if debug_mode:
        st.write("🐞 Evolution context being used:", evolution_context if evolution_context else "None")
    if strategies:
        st.info(f"🧬 Evolution active: {len(strategies)} relevant past strategies loaded.")
    else:
        st.info("ℹ️ No relevant past strategies found for this topic. Starting fresh.")

    log = []
    last_msg = "Let's begin the debate."
    
    speaking_order = ["harsh", "jayant"]
    for key in agents:
        if key not in ["harsh", "jayant", "ahany"]:
            speaking_order.append(key)
    
    for r in range(1, rounds + 1):
        st.markdown(f"### 🔄 Round {r}")
        
        for agent_key in speaking_order:
            if agent_key not in agents: continue
            agent = agents[agent_key]
            tone = random_tone() if use_tones else None
            with st.spinner(f"{agent.name} is thinking..."):
                msg = agent.speak(topic, last_msg, model, r, tone, evolution_context)
            with st.chat_message(agent.name, avatar=agent.avatar):
                st.write(msg)
            log.append(f"{agent.avatar} {agent.name}: {msg}")
            last_msg = msg
            time.sleep(1.2)
        
        moderator = agents["ahany"]
        tone_m = random_tone() if use_tones else None
        with st.spinner(f"{moderator.name} is analyzing..."):
            msg_m = moderator.speak(topic, last_msg, model, r, tone_m, evolution_context)
        with st.chat_message(moderator.name, avatar=moderator.avatar):
            st.write(msg_m)
        log.append(f"{moderator.avatar} {moderator.name}: {msg_m}")
        last_msg = msg_m
        time.sleep(1.2)
        
        st.divider()
    
    # Verdict
    st.markdown("---")
    st.subheader("🧠 Expert Verdict")
    with st.spinner("Expert panel is deliberating..."):
        verdict = get_verdict(topic, log, model)
        st.markdown('<div class="verdict-box">' + verdict + '</div>', unsafe_allow_html=True)
    st.success("✅ Debate concluded")
    st.balloons()
    
    # Evolution save
    st.markdown("---")
    st.subheader("🧬 Evolve the Swarm")
    
    winner = "Unknown"
    verdict_lower = verdict.lower()
    if "jayant" in verdict_lower: winner = "Jayant"
    elif "harsh" in verdict_lower: winner = "Harsh"
    elif "ritik" in verdict_lower: winner = "Ritik"
    elif "kavya" in verdict_lower: winner = "Kavya"
    elif "nish" in verdict_lower: winner = "Nish"
    elif "teju" in verdict_lower: winner = "Teju"
    elif "shivam" in verdict_lower: winner = "Shivam"
    elif "balanced" in verdict_lower or "tie" in verdict_lower: winner = "Tie"
    
    with st.expander("💾 Save this winning strategy to evolution memory", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            panel_names = ["Harsh", "Jayant"] + [k.split(" ")[1] for k in extra_agent_keys]
            winning_side = st.selectbox("Which panelist had the strongest arguments?", panel_names,
                                        index=panel_names.index(winner) if winner in panel_names else 0)
        with col2:
            key_arg = st.text_input("Key winning argument (brief)", value=verdict[:120] + "...")
        
        if st.button("🧬 Save to Evolution Memory", use_container_width=True):
            entry = add_winning_strategy(topic, verdict, winning_side, key_arg)
            st.success(f"✅ Strategy saved! The swarm now has {len(load_evolution_memory())} learned strategies.")
            st.balloons()
    
    return verdict

# --- Main Execution ---
col1, col2, col3 = st.columns([1, 2.5, 1])
with col2:
    if st.button("🚀 Launch Multi-Agent Debate", use_container_width=True):
        if not topic:
            st.error("Please enter a topic in the sidebar.")
        else:
            try:
                run_debate(topic, rounds, use_tones, extra_agents)
            except Exception as e:
                st.error(f"❌ Error: {e}")
                st.info("💡 If quota exceeded, wait a minute and try again.")
