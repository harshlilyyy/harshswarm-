import streamlit as st
import time
import re
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
        -webkit-backdrop-filter: blur(24px) !important;
        border-right: 0.5px solid var(--border-glow) !important;
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

    .round-tracker {
        text-align: center;
        margin: 0.5rem 0 0.8rem;
        font-weight: 600;
        font-size: 1.1rem;
        opacity: 0.8;
        color: var(--pink-hot);
    }
</style>
""", unsafe_allow_html=True)

# --- Session State ---
if "debate_history" not in st.session_state:
    st.session_state.debate_history = []
if "saved_history" not in st.session_state:
    st.session_state.saved_history = []

# --- API Providers (corrected, with SambaNova, Cloudflare placeholder) ---
PROVIDERS = [
    {"name": "Groq",          "key": st.secrets.get("GROQ_API_KEY"),          "base": "https://api.groq.com/openai/v1",                "model": "llama-3.3-70b-versatile"},
    {"name": "SambaNova",     "key": st.secrets.get("SAMBA_API_KEY"),         "base": "https://api.sambanova.ai/v1",                   "model": "llama-3.3-70b"},
    {"name": "DeepSeek",      "key": st.secrets.get("DEEPSEEK_API_KEY"),      "base": "https://api.deepseek.com",                      "model": "deepseek-chat"},
    {"name": "Cerebras",      "key": st.secrets.get("CEREBRAS_API_KEY"),      "base": "https://api.cerebras.ai/v1",                    "model": "llama3.3-70b"},
    {"name": "Google",        "key": st.secrets.get("GEMINI_API_KEY"),        "base": "https://generativelanguage.googleapis.com/v1beta","model": "gemini-2.0-flash"},
    {"name": "Mistral",       "key": st.secrets.get("MISTRAL_API_KEY"),       "base": "https://api.mistral.ai/v1",                     "model": "mistral-small-2409"},
    {"name": "OpenRouter",    "key": st.secrets.get("OPENROUTER_API_KEY"),    "base": "https://openrouter.ai/api/v1",                  "model": "meta-llama/llama-3.3-70b-instruct:free"},
]

def get_client(provider):
    return OpenAI(api_key=provider["key"], base_url=provider["base"])

def generate_with_fallback(prompt, system="", preferred=None, silent_fail=False):
    if preferred:
        providers = [p for p in PROVIDERS if p["name"] == preferred] + [p for p in PROVIDERS if p["name"] != preferred]
    else:
        providers = PROVIDERS
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
                resp = client.chat.completions.create(
                    model=p["model"], messages=messages, temperature=0.7, max_tokens=250
                )
                return resp.choices[0].message.content.strip(), p["name"]
        except:
            continue
    if silent_fail:
        return "Unable to generate response.", "None"
    else:
        st.warning("All providers temporarily unavailable.")
        return "Response unavailable.", "None"

def test_provider_connection(provider):
    if not provider["key"]:
        return "No API key"
    try:
        if provider["name"] == "Google":
            import google.generativeai as genai
            genai.configure(api_key=provider["key"])
            model = genai.GenerativeModel(provider["model"])
            model.generate_content("Say 'OK'", request_options={"timeout": 8})
        else:
            client = OpenAI(api_key=provider["key"], base_url=provider["base"])
            client.chat.completions.create(
                model=provider["model"],
                messages=[{"role": "user", "content": "Say OK"}],
                max_tokens=5,
                timeout=8
            )
        return "✅ Working"
    except Exception as e:
        return f"❌ {str(e)[:60]}"

# --- 16 Agents (Harsh adversarial but filter-safe) ---
class Agent:
    def __init__(self, name, role, personality, avatar, card_class):
        self.name, self.role, self.personality, self.avatar, self.card_class = name, role, personality, avatar, card_class
        self.history = []
    def speak(self, topic, last_msg, round_num, preferred_provider, tone, swarm_mode):
        history = "\n".join(self.history[-3:]) or "No previous chat."
        tone_instr = f"Respond in a {tone} tone." if tone else ""
        mode_instr = SWARM_MODES.get(swarm_mode, "")
        system = f"You are {self.name} ({self.role}). {self.personality}. {tone_instr} This is a {swarm_mode} session. {mode_instr}"
        prompt = f"""Debate round {round_num} on: "{topic}"
**Claim:** [point] **Evidence:** [fact] **Reasoning:** [why]
History: {history}
Last: "{last_msg}"
"""
        reply, provider = generate_with_fallback(prompt, system, preferred_provider)
        self.history.append(reply)
        return reply, provider

class Moderator(Agent):
    def speak(self, topic, last_msg, round_num, preferred_provider, tone, swarm_mode):
        history = "\n".join(self.history[-5:]) or "No debate yet."
        system = f"You are {self.name}, the moderator. Be sharp and impartial."
        prompt = f"Summarize, note contradictions, ask a provocative question. Topic: {topic} | Round: {round_num}\nHistory: {history}\nLast: {last_msg}"
        reply, provider = generate_with_fallback(prompt, system, preferred_provider)
        self.history.append(reply)
        return reply, provider

ALL_AGENTS = [
    ("Harsh", "Skeptic", "Ruthlessly find logical flaws. Challenge every assumption directly. Never concede without evidence.", "🔴", "card-skeptic"),
    ("Jayant", "Optimist", "Sees opportunity and growth in every challenge.", "🟢", "card-optimist"),
    ("Ahany", "Moderator", "Sharp journalist who challenges all sides.", "🔵", "card-moderator", True),
    ("Ritik", "Policy Advisor", "Gov/regulation perspective.", "🟡", "card-policy"),
    ("Kavya", "Retail Investor", "Everyday person's practical view.", "🟣", "card-optimist"),
    ("Nish", "Scientist", "Empirical evidence only.", "🟠", "card-data"),
    ("Teju", "Tech Journalist", "Trends and narratives.", "🔷", "card-futurist"),
    ("Shivam", "Conspiracy Theorist", "Hidden agendas and unconventional views.", "⚫", "card-conspiracy"),
    ("Philosopher", "Philosopher", "Ethical and historical context.", "🟤", "card-philosopher"),
    ("Futurist", "Futurist", "Long-term implications.", "🔮", "card-futurist"),
    ("DataScientist", "Data Scientist", "Statistics and evidence.", "📊", "card-data"),
    ("Ethicist", "Ethicist", "Moral implications.", "⚖️", "card-ethicist"),
    ("Psychologist", "Psychologist", "Human behavior and cognitive biases.", "🧠", "card-psychologist"),
    ("Economist", "Economist", "Financial and market impact.", "📈", "card-economist"),
    ("Technologist", "Technologist", "Cutting-edge tech feasibility.", "💻", "card-technologist"),
    ("Legal Expert", "Legal Expert", "Laws, regulations, and precedents.", "⚖️", "card-legal"),
]

def create_panel(selected_agents):
    agents = []
    moderator = None
    for agent_data in ALL_AGENTS:
        name = agent_data[0]
        if name not in selected_agents:
            continue
        role, personality, avatar, card_class = agent_data[1], agent_data[2], agent_data[3], agent_data[4]
        if len(agent_data) == 6 and agent_data[5]:
            moderator = Moderator(name, role, personality, avatar, card_class)
        else:
            agents.append(Agent(name, role, personality, avatar, card_class))
    if moderator:
        if len(agents) >= 2:
            agents.insert(2, moderator)
        else:
            agents.append(moderator)
    return agents

# --- Swarm Mode Descriptions ---
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

    # Provider tester (collapsible)
    with st.expander("🔧 Test Providers", expanded=False):
        for p in PROVIDERS:
            if st.button(f"Test {p['name']}", key=f"test_{p['name']}"):
                with st.spinner("Testing..."):
                    result = test_provider_connection(p)
                    if "✅" in result:
                        st.success(f"{p['name']}: {result}")
                    else:
                        st.error(f"{p['name']}: {result}")

    st.markdown("### 🤖 Kernel")
    model_choice = st.selectbox("Active model", ["Groq", "SambaNova", "DeepSeek", "Cerebras", "Google", "Mistral", "OpenRouter", "🤖 Auto"], index=7)
    preferred = None if model_choice == "🤖 Auto" else model_choice

    st.markdown("---")
    st.markdown("### ⚙️ Swarm Mode")
    swarm_mode = st.selectbox("Mode", list(SWARM_MODES.keys()), index=0)
    st.caption({
        "Debate": "Agents clash, judge picks winner.",
        "Council": "Agents collaborate to reach consensus.",
        "Devil's Advocate": "One agent attacks your position aggressively.",
        "Exploration": "Each agent explores a different angle.",
        "Rapid Fire": "Short, fast arguments."
    }.get(swarm_mode, ""))

    st.markdown("### 🎙️ Tone")
    tone = st.selectbox("Tone", ["Neutral", "Casual", "Academic", "Brutal"], index=0)

    st.markdown("### 🧑‍🤝‍🧑 Agent Picker")
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

    rounds = st.select_slider("Depth", options=[1, 2, 3, 4], value=2)
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
    st.markdown("<p style='text-align:center;color:var(--purple-prime);'>by Harsh Dubey</p>", unsafe_allow_html=True)

# ===================== MAIN AREA =====================
st.markdown('<div class="nyx-title">Nyx</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">AI Swarm Intelligence — Your problem, debated by experts.</div>', unsafe_allow_html=True)
st.caption("💡 Try: Is remote work better than office? · Should I learn Python or JavaScript? · Is AI art real art?")

with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    topic = st.text_input("Ask anything...", value="", placeholder="Ask anything...", label_visibility="collapsed")
    launch = st.button("Start Swarm", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ===================== DEBATE EXECUTION =====================
if launch and topic:
    if len(selected_agents) < 3:
        st.error("Please select at least 3 agents (including moderator).")
        st.stop()

    # --- Topic Sharpening ---
    with st.spinner("🎯 Sharpening your topic..."):
        sharpener_prompt = f"""Take this vague input: "{topic}" and turn it into a clear, focused resolution for a {swarm_mode} session. Do not change the meaning, just make it precise. Output only the refined topic."""
        refined, _ = generate_with_fallback(sharpener_prompt, silent_fail=True)
        if refined and refined not in ("Unable to generate response.", "Response unavailable."):
            topic = refined.strip()
            st.info(f"🎯 **Refined:** {topic}")

    agents = create_panel(selected_agents)
    log = []
    last_msg = "Let's begin."
    winner = None
    verdict = ""
    actual_first_provider = None
    fallback_warning_shown = False

    if show_args:
        st.markdown("### ⚔️ THE ARENA")

    for r in range(1, rounds+1):
        st.markdown(f'<div class="round-tracker">Round {r} of {rounds}</div>', unsafe_allow_html=True)
        order = [a for a in agents if a.name != "Ahany"]

        persona_html = " · ".join([f"{a.avatar} {a.name}" for a in order])
        st.markdown(f'<div style="text-align:center;opacity:0.6;margin-bottom:0.8rem;">{persona_html}</div>', unsafe_allow_html=True)

        for idx, agent in enumerate(order):
            with st.spinner(f"{agent.name} is thinking..."):
                reply, provider = agent.speak(topic, last_msg, r, preferred, tone, swarm_mode)

            if actual_first_provider is None:
                actual_first_provider = provider
                if preferred and preferred != "🤖 Auto" and provider != preferred and not fallback_warning_shown:
                    st.warning(f"⚠️ Preferred model `{preferred}` is unavailable. Switched to `{provider}` to keep the debate alive.")
                    fallback_warning_shown = True

            if show_args:
                with st.expander(f"{agent.avatar} {agent.name} · {agent.role}", expanded=True):
                    st.markdown(reply)
                    st.caption(f"via {provider}")
            log.append(f"{agent.avatar} {agent.name} ({provider}): {reply}")
            last_msg = reply
            time.sleep(0.8)

        mod = next((a for a in agents if a.name == "Ahany"), None)
        if mod:
            with st.spinner(f"{mod.name} is moderating..."):
                mod_reply, provider = mod.speak(topic, last_msg, r, preferred, tone, swarm_mode)
            if show_args:
                with st.expander(f"{mod.avatar} {mod.name} · Moderator", expanded=True):
                    st.markdown(mod_reply)
                    st.caption(f"via {provider}")
            log.append(f"{mod.avatar} {mod.name} ({provider}): {mod_reply}")
            last_msg = mod_reply

    st.session_state.debate_history = log

    # --- Judge Verdict (mode-specific rubric) ---
    with st.spinner("🧑‍⚖️ Judge deliberating..."):
        verdict_prompt = f"""You are a strict, professional judge. Swarm mode: {swarm_mode}. Tone: {tone}.
Evaluate the debate on: "{topic}"
Transcript: {' '.join(log[-20:])}

For Debate mode: The winner must have successfully rebutted the opponent's strongest points. Reward logical consistency, evidence quality, and rebuttal strength. Do NOT reward mere politeness or balance.

For Council mode: Reward consensus-building and synthesis of multiple perspectives.

For Devil's Advocate mode: Reward the agent who stress-tested ideas and exposed weaknesses.

For Exploration mode: Reward unique, well-reasoned angles.

For Rapid Fire mode: Reward clarity, conciseness, and impact per word.

Return exactly:
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

    # --- Copy Verdict ---
    verdict_text = f"Nyx Verdict\nTopic: {topic}\nWinner: {winner}\nReasoning: {reasoning}\nConfidence: {confidence}/10\nAction: {action}\nLogic: {logic} | Evidence: {evidence} | Rebuttal: {rebuttal} | Persuasiveness: {persuasiveness}\nTakeaway: {takeaway}"
    if st.button("📋 Copy Verdict"):
        st.session_state["clipboard"] = verdict_text
        st.success("✅ Verdict copied!")

    # --- Save History ---
    st.session_state.saved_history.append({
        "topic": topic,
        "winner": winner,
        "date": datetime.now().strftime("%b %d"),
        "verdict": verdict_text
    })
    if len(st.session_state.saved_history) > 10:
        st.session_state.saved_history = st.session_state.saved_history[-10:]

# --- Footer ---
st.markdown('<div style="text-align:center;margin-top:2rem;opacity:0.6;font-family:\'Playfair Display\',serif;font-style:italic;">✨ Harsh Dubey · Nyx ✨</div>', unsafe_allow_html=True)