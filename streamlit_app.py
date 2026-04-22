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
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 💖 Pink Love Theme · Pinterest Aesthetic 💖 ---
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
        --mauve: #d9b8c4;
        --gold: #f7c873;
    }

    html, body, [class*="css"] {
        font-family: 'Quicksand', sans-serif;
        background: var(--cream);
        color: var(--charcoal);
    }

    .stApp {
        background: linear-gradient(145deg, #fff0f3 0%, #ffe4e9 100%);
        background-image: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M30 15 C25 5 15 5 10 15 C5 25 15 35 30 45 C45 35 55 25 50 15 C45 5 35 5 30 15z' fill='%23fbc4d5' opacity='0.15'/%3E%3C/svg%3E");
    }

    .main .block-container {
        padding: 2rem 2rem 2rem 2rem;
        max-width: 1440px;
    }

    h1 {
        font-family: 'Dancing Script', cursive;
        font-size: 4.2rem !important;
        font-weight: 700 !important;
        background: linear-gradient(135deg, #e87b9e 0%, #f7c873 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.25rem !important;
        filter: drop-shadow(0 4px 6px rgba(232, 123, 158, 0.2));
        position: relative;
    }

    h1::before, h1::after {
        content: "💗";
        font-size: 2.5rem;
        margin: 0 20px;
        opacity: 0.7;
        display: inline-block;
    }

    .hero-subtitle {
        text-align: center;
        font-size: 1.2rem;
        color: var(--charcoal);
        margin-bottom: 0.5rem;
        font-weight: 500;
        letter-spacing: 1px;
    }

    .signature {
        text-align: center;
        font-family: 'Dancing Script', cursive;
        font-size: 1.8rem;
        color: #e87b9e;
        margin-top: -0.5rem;
        margin-bottom: 2rem;
    }

    [data-testid="stSidebar"] {
        background: rgba(255, 240, 245, 0.85);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-right: 1px solid var(--soft-pink);
        box-shadow: 5px 0 20px rgba(232, 123, 158, 0.1);
    }

    [data-testid="stSidebar"] .block-container {
        padding: 2rem 1.5rem;
    }

    [data-testid="stChatMessage"] {
        background: white;
        border-radius: 32px 32px 32px 8px;
        padding: 1.5rem 1.8rem;
        margin-bottom: 1.5rem;
        border: 1px solid var(--soft-pink);
        box-shadow: 0 10px 20px -8px rgba(232, 123, 158, 0.15);
        transition: all 0.3s ease;
        position: relative;
    }

    [data-testid="stChatMessage"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 30px -8px rgba(232, 123, 158, 0.25);
        border-color: var(--deep-rose);
    }

    [data-testid="stChatMessage"]::before {
        content: "📌";
        position: absolute;
        top: -10px;
        left: 20px;
        font-size: 1.5rem;
        filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
    }

    [data-testid="stChatMessage"]:has(span:contains("🔴")) { border-left: 6px solid #e87b9e; }
    [data-testid="stChatMessage"]:has(span:contains("🟢")) { border-left: 6px solid #a7d0b0; }
    [data-testid="stChatMessage"]:has(span:contains("🔵")) { border-left: 6px solid #a3c4d6; }
    [data-testid="stChatMessage"]:has(span:contains("🟡")) { border-left: 6px solid #f7d794; }
    [data-testid="stChatMessage"]:has(span:contains("🟣")) { border-left: 6px solid #c9b2d9; }
    [data-testid="stChatMessage"]:has(span:contains("🟠")) { border-left: 6px solid #f5b895; }
    [data-testid="stChatMessage"]:has(span:contains("🔷")) { border-left: 6px solid #a0d6db; }
    [data-testid="stChatMessage"]:has(span:contains("⚫")) { border-left: 6px solid #b8a9a9; }

    .stButton > button {
        background: linear-gradient(135deg, #f8a5c2 0%, #e87b9e 100%);
        color: white;
        font-weight: 600;
        border-radius: 60px;
        border: none;
        padding: 0.75rem 2rem;
        font-size: 1.1rem;
        box-shadow: 0 8px 18px -6px rgba(232, 123, 158, 0.4);
        transition: all 0.3s ease;
        letter-spacing: 0.5px;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }

    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 14px 24px -8px rgba(232, 123, 158, 0.6);
        background: linear-gradient(135deg, #e87b9e 0%, #d45d82 100%);
    }

    .verdict-box {
        background: white;
        border-radius: 40px 40px 40px 12px;
        padding: 2rem 2.5rem;
        margin: 2rem 0;
        border: 1px solid var(--rose);
        box-shadow: 0 20px 30px -10px rgba(232, 123, 158, 0.15);
        position: relative;
    }

    .verdict-box::after {
        content: "💌";
        position: absolute;
        bottom: -15px;
        right: 30px;
        font-size: 2rem;
        opacity: 0.7;
    }

    [data-testid="stDataFrame"] {
        background: white;
        border-radius: 24px;
        padding: 0.5rem;
        box-shadow: 0 8px 16px -8px rgba(232, 123, 158, 0.1);
        border: 1px solid var(--soft-pink);
    }

    .stTextArea textarea {
        background: white;
        border: 2px solid var(--soft-pink);
        border-radius: 30px;
        padding: 1rem 1.5rem;
        font-size: 1rem;
        color: var(--charcoal);
        box-shadow: inset 0 2px 6px rgba(0,0,0,0.02);
    }

    .stTextArea textarea:focus {
        border-color: var(--deep-rose);
        box-shadow: 0 0 0 4px rgba(232, 123, 158, 0.1);
    }

    h2 {
        font-family: 'Dancing Script', cursive;
        color: var(--deep-rose);
        font-size: 2.5rem !important;
        text-align: center;
    }

    @keyframes pulse {
        0% { opacity: 0.8; text-shadow: 0 0 5px #fbc4d5; }
        50% { opacity: 1; text-shadow: 0 0 20px #f8a5c2, 0 0 30px #f7c873; }
        100% { opacity: 0.8; text-shadow: 0 0 5px #fbc4d5; }
    }

    .stProgress > div > div {
        background: linear-gradient(90deg, #fbc4d5, #e87b9e);
        border-radius: 20px;
    }

    .streamlit-expanderHeader {
        background: rgba(255, 240, 245, 0.5);
        border-radius: 30px;
        border: 1px solid var(--soft-pink);
    }

    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #ffe4e6; border-radius: 10px; }
    ::-webkit-scrollbar-thumb { background: #f8a5c2; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #e87b9e; }
</style>
""", unsafe_allow_html=True)

# --- Multi-Model Router (Secure) ---
MODEL_CHAIN = [
    {
        "provider": "groq",
        "model": "llama-3.3-70b-versatile",
        "api_key": st.secrets.get("GROQ_API_KEY", ""),
        "base_url": "https://api.groq.com/openai/v1",
        "type": "openai"
    },
    {
        "provider": "deepseek",
        "model": "deepseek-chat",
        "api_key": st.secrets.get("DEEPSEEK_API_KEY", ""),
        "base_url": "https://api.deepseek.com",
        "type": "openai"
    },
    {
        "provider": "google",
        "model": "gemma-4-26b-it",
        "api_key": st.secrets.get("GEMINI_API_KEY", ""),
        "base_url": None,
        "type": "google"
    },
]

def get_working_model():
    for config in MODEL_CHAIN:
        if not config["api_key"]:
            st.sidebar.warning(f"⚠️ {config['provider']} API key missing")
            continue
        try:
            if config["type"] == "google":
                import google.generativeai as genai
                genai.configure(api_key=config["api_key"])
                model = genai.GenerativeModel(config["model"])
                model.generate_content("test", request_options={"timeout": 5})
            st.sidebar.success(f"✅ Active: {config['provider']} ({config['model']})")
            return config
        except Exception as e:
            st.sidebar.warning(f"⚠️ {config['provider']} failed: {str(e)[:40]}")
            continue
    st.error("🚨 No working models available. Check your API keys in Secrets.")
    st.stop()

ACTIVE_MODEL = get_working_model()

if ACTIVE_MODEL["type"] == "google":
    import google.generativeai as genai
    genai.configure(api_key=ACTIVE_MODEL["api_key"])
    google_model = genai.GenerativeModel(ACTIVE_MODEL["model"])
else:
    from openai import OpenAI
    client = OpenAI(
        api_key=ACTIVE_MODEL["api_key"],
        base_url=ACTIVE_MODEL["base_url"]
    )

def generate_response(prompt, system_prompt=None):
    if ACTIVE_MODEL["type"] == "google":
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        response = google_model.generate_content(full_prompt)
        return response.text
    else:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        response = client.chat.completions.create(
            model=ACTIVE_MODEL["model"],
            messages=messages,
            temperature=0.7,
            max_tokens=600
        )
        return response.choices[0].message.content

# --- Session State ---
if "agent_stats" not in st.session_state:
    st.session_state.agent_stats = {
        "Harsh": {"wins": 0, "losses": 0},
        "Jayant": {"wins": 0, "losses": 0},
        "Ritik": {"wins": 0, "losses": 0},
        "Kavya": {"wins": 0, "losses": 0},
        "Nish": {"wins": 0, "losses": 0},
        "Teju": {"wins": 0, "losses": 0},
        "Shivam": {"wins": 0, "losses": 0},
    }
if "global_arguments" not in st.session_state:
    st.session_state.global_arguments = []
if "quantum_topic" not in st.session_state:
    st.session_state.quantum_topic = "Apple announces new AI chip that uses 50% less power and is carbon neutral."

QUANTUM_TOPICS = [
    "AI will replace all human jobs by 2040",
    "Space colonization should be humanity's top priority",
    "Social media does more harm than good",
    "Cryptocurrency is the future of finance",
    "Schools should teach AI prompting as a core subject",
    "Robots should have legal rights",
    "Climate change can only be solved by technology",
    "Remote work is better than office work",
]

def is_repetition(text, threshold=0.6):
    words = set(text.lower().split())
    for past in st.session_state.global_arguments[-10:]:
        past_words = set(past.lower().split())
        if len(words & past_words) / max(len(words), 1) > threshold:
            return True
    return False

def add_global_memory(agent, text):
    st.session_state.global_arguments.append(f"{agent}: {text[:200]}")

class AI_Agent:
    def __init__(self, name, role, personality, avatar, color):
        self.name = name
        self.role = role
        self.personality = personality
        self.avatar = avatar
        self.color = color
        self.history = []
        self.scores = {"logic": 0, "creativity": 0, "persuasiveness": 0}

    def speak(self, topic, last_msg, round_num):
        history = "\n".join(self.history[-3:]) or "No previous chat."
        system_prompt = f"You are {self.name} ({self.role}). {self.personality}"
        prompt = f"""
Debate round {round_num} on: "{topic}"

FORMAT (must follow):
**Claim:** [your main point]
**Evidence:** [supporting fact]
**Reasoning:** [why it matters]

Avoid repeating previous arguments. History:
{history}

Last said: "{last_msg}"
"""
        for _ in range(2):
            resp = generate_response(prompt, system_prompt).strip()
            if not is_repetition(resp):
                break
            prompt += "\nWARNING: Argument repeated. Provide a NEW angle."
        else:
            resp = "**Claim:** I've made my point. **Evidence:** Already presented. **Reasoning:** Let's move on."
        self.history.append(f"{self.name}: {resp}")
        add_global_memory(self.name, resp)
        if "claim:" in resp.lower(): self.scores["logic"] += 2
        if "evidence:" in resp.lower(): self.scores["creativity"] += 2
        if "reasoning:" in resp.lower(): self.scores["persuasiveness"] += 2
        return resp

class Moderator(AI_Agent):
    def speak(self, topic, last_msg, round_num):
        history = "\n".join(self.history[-5:]) or "No debate yet."
        system_prompt = f"You are {self.name}, the moderator. Be sharp and impartial."
        prompt = f"""
Summarize key points, note contradictions, and ask a sharp question.
Topic: "{topic}" | Round: {round_num}
History: {history}
Last exchange: "{last_msg}"
Keep it 3-4 sentences.
"""
        return generate_response(prompt, system_prompt).strip()

def judge_debate(topic, messages):
    debate_text = "\n".join(messages[-30:])
    system_prompt = "You are the JUDGE. Deliver a fair, detailed verdict."
    prompt = f"""
Debate on: "{topic}"
Transcript: {debate_text}

Provide:
🏆 Winner: [Name]
📝 Reasoning: [2-3 sentences]

Strengths & Weaknesses for each panelist.
📊 Scores (1-10) for Logic, Creativity, Persuasiveness in a table.
⚖️ Final Takeaway: [1-2 sentences]
"""
    return generate_response(prompt, system_prompt)

def create_agents(num_extra=4):
    agents = [
        AI_Agent("Harsh", "Skeptic", "Pessimistic economist. Finds flaws and risks.", "🔴", "#ef4444"),
        AI_Agent("Jayant", "Optimist", "Cheerful tech investor. Sees opportunity.", "🟢", "#10b981"),
        Moderator("Ahany", "Moderator", "Sharp journalist.", "🔵", "#3b82f6"),
    ]
    extras = [
        ("Ritik", "Policy Advisor", "Government/regulation view.", "🟡", "#eab308"),
        ("Kavya", "Retail Investor", "Everyday person perspective.", "🟣", "#8b5cf6"),
        ("Nish", "Scientist", "Demands empirical evidence.", "🟠", "#f97316"),
        ("Teju", "Tech Journalist", "Identifies trends.", "🔷", "#06b6d4"),
        ("Shivam", "Conspiracy Theorist", "Sees hidden agendas.", "⚫", "#334155"),
    ]
    for i in range(min(num_extra, len(extras))):
        name, role, pers, av, col = extras[i]
        agents.insert(-1, AI_Agent(name, role, pers, av, col))
    return agents

def generate_pdf(topic, log, verdict, winner):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Nyx Protocol Debate Transcript", ln=1, align='C')
    pdf.cell(200, 10, txt=f"Topic: {topic}", ln=1)
    pdf.ln(10)
    for msg in log:
        clean = msg.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 10, txt=clean)
        pdf.ln(2)
    pdf.ln(10)
    pdf.set_font("Arial", style='B', size=14)
    pdf.cell(200, 10, txt=f"Winner: {winner}", ln=1)
    pdf.set_font("Arial", size=12)
    verdict_clean = verdict.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, txt=verdict_clean)
    return pdf.output(dest='S').encode('latin-1')

# --- Sidebar ---
with st.sidebar:
    st.markdown("### 💗 Nyx Protocol")
    st.markdown("---")
    st.markdown("### 🎲 Quantum Roll")
    if st.button("🌀 Generate Random Topic"):
        topic = secrets.choice(QUANTUM_TOPICS)
        first = secrets.choice(["Harsh", "Jayant"])
        st.session_state.quantum_topic = topic
        st.session_state.first_speaker = first
        st.sidebar.success(f"Topic: {topic}")
        st.sidebar.info(f"First speaker: {first}")
    st.markdown("---")
    st.markdown("### ⚙️ Debate Settings")
    mode = st.selectbox("Mode", ["Quick (3 rounds)", "Standard (5 rounds)", "Deep (8 rounds)"])
    rounds = 3 if "Quick" in mode else 5 if "Standard" in mode else 8
    extra = st.selectbox("Extra Agents", [0, 1, 2, 3, 4, 5], index=4)
    st.markdown("---")
    st.markdown("### 📊 Agent Win Rates")
    for agent, stats in st.session_state.agent_stats.items():
        total = stats["wins"] + stats["losses"]
        rate = f"{(stats['wins']/total*100):.0f}%" if total > 0 else "0%"
        st.text(f"{agent}: {stats['wins']}W / {stats['losses']}L ({rate})")
    st.markdown("---")
    st.markdown(
        "<p style='font-family: \"Dancing Script\", cursive; font-size: 1.5rem; color: #e87b9e; text-align: center;'>"
        "by Harsh Dubey"
        "</p>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align: center; font-size: 0.8rem; color: #d9b8c4;'>"
        "💕 AI Debate • Pink Love Edition 💕"
        "</p>",
        unsafe_allow_html=True
    )

# --- Main UI ---
st.title("💗 Nyx Protocol 💗")
st.markdown('<div class="hero-subtitle">Multi‑Agent AI Debate · Judge · Live Scoring · Quantum Randomness</div>', unsafe_allow_html=True)
st.markdown('<div class="signature">✨ crafted with love by Harsh Dubey ✨</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    topic = st.text_area(
        "📰 **What should the panel debate?**",
        value=st.session_state.quantum_topic,
        height=120,
        placeholder="Enter any topic..."
    )
    start_btn = st.button("🚀 Launch Debate", use_container_width=True)

# --- Debate Execution ---
if start_btn and topic:
    st.session_state.global_arguments = []
    agents = create_agents(extra)

    log = []
    last_msg = "Let's begin."
    winner = None
    verdict = ""

    left, right = st.columns([2.2, 1])
    with right:
        score_place = st.empty()
        prog_place = st.empty()
    with left:
        chat_place = st.empty()

    for r in range(1, rounds + 1):
        prog_place.progress(r / rounds, f"Round {r} of {rounds}")
        st.markdown("---")
        st.markdown(f"<h2 style='text-align: center; animation: pulse 2s infinite;'>🌸 Round {r} — Let Love Decide 🌸</h2>", unsafe_allow_html=True)
        st.markdown("---")

        round_msgs = []
        order = [a for a in agents if a.name != "Ahany"]
        for agent in order:
            with st.spinner(f"{agent.name} thinking..."):
                reply = agent.speak(topic, last_msg, r)
            round_msgs.append(f"{agent.avatar} **{agent.name} ({agent.role})**: {reply}")
            last_msg = reply
            time.sleep(1.2)

        mod = next(a for a in agents if a.name == "Ahany")
        with st.spinner("Moderator summarizing..."):
            mod_reply = mod.speak(topic, last_msg, r)
        round_msgs.append(f"{mod.avatar} **{mod.name}**: {mod_reply}")
        last_msg = mod_reply

        log.append(f"### 🔄 Round {r}\n\n" + "\n\n".join(round_msgs))
        chat_place.markdown("\n\n".join(log))

        score_data = [{"Agent": f"{a.avatar} {a.name}", "Logic": a.scores["logic"], "Creativity": a.scores["creativity"], "Persuasiveness": a.scores["persuasiveness"]} for a in agents]
        score_place.dataframe(score_data, use_container_width=True, hide_index=True)
        time.sleep(0.5)

    # Verdict
    with st.spinner("🧑‍⚖️ Judge deliberating..."):
        verdict = judge_debate(topic, log)

    match = re.search(r"Winner:\s*(\w+)", verdict)
    winner = match.group(1) if match else "Unknown"

    for agent in st.session_state.agent_stats:
        if agent == winner:
            st.session_state.agent_stats[agent]["wins"] += 1
        else:
            st.session_state.agent_stats[agent]["losses"] += 1

    st.markdown("---")
    st.subheader("🧑‍⚖️ Judge's Verdict")
    st.markdown(f'<div class="verdict-box">{verdict}</div>', unsafe_allow_html=True)
    st.success(f"💖 Cupid's Choice: {winner} 💖")
    st.balloons()

    # Social Share
    share_text = f"Nyx Protocol verdict on '{topic}':\n\nWinner: {winner}\n\n{verdict[:200]}...\n\nTry it: https://harshswarmdev.streamlit.app"
    tweet = 