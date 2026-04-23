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
    page_title="Nyx Protocol · AI Debate",
    page_icon="🌑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Professional Dark Theme with Subtle Accents ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --bg-deep: #0a0a0f;
        --bg-card: rgba(18, 20, 28, 0.9);
        --border-glow: rgba(168, 85, 247, 0.3);
        --accent-purple: #a855f7;
        --accent-cyan: #06b6d4;
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background: var(--bg-deep);
        color: var(--text-primary);
    }

    .stApp {
        background: radial-gradient(circle at 20% 30%, #1a1025, #0a0a0f 80%);
    }

    .main .block-container {
        padding: 2rem 2rem 2rem 2rem;
        max-width: 1440px;
    }

    h1 {
        background: linear-gradient(135deg, #a855f7 0%, #06b6d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700 !important;
        font-size: 3.2rem !important;
        text-align: center;
        margin-bottom: 0.5rem !important;
        letter-spacing: -0.02em;
    }

    .hero-subtitle {
        text-align: center;
        font-size: 1.2rem;
        color: var(--text-secondary);
        margin-bottom: 2rem;
    }

    [data-testid="stSidebar"] {
        background: rgba(15, 17, 22, 0.8);
        backdrop-filter: blur(12px);
        border-right: 1px solid var(--border-glow);
    }

    [data-testid="stChatMessage"] {
        background: var(--bg-card);
        border-radius: 20px;
        padding: 1.5rem 1.8rem;
        margin-bottom: 1.25rem;
        border-left: 6px solid;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
    }

    [data-testid="stChatMessage"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 28px rgba(0, 0, 0, 0.5);
    }

    .stButton > button {
        background: linear-gradient(135deg, #a855f7 0%, #06b6d4 100%);
        color: white;
        font-weight: 600;
        border-radius: 60px;
        border: none;
        padding: 0.75rem 2rem;
        font-size: 1.1rem;
        box-shadow: 0 4px 15px rgba(168, 85, 247, 0.3);
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(6, 182, 212, 0.4);
    }

    .verdict-box {
        background: var(--bg-card);
        border-radius: 24px;
        padding: 2rem;
        margin: 2rem 0;
        border: 1px solid var(--border-glow);
    }

    .stTextArea textarea {
        background: var(--bg-card);
        border: 1px solid var(--border-glow);
        border-radius: 16px;
        color: var(--text-primary);
        padding: 1rem;
    }

    .stTextArea textarea:focus {
        border-color: var(--accent-purple);
        box-shadow: 0 0 0 3px rgba(168, 85, 247, 0.2);
    }

    .stProgress > div > div {
        background: linear-gradient(90deg, #a855f7, #06b6d4);
    }

    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #1a1a2e; }
    ::-webkit-scrollbar-thumb { background: #a855f7; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)
# --- Expanded Multi-Model Router ---
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
        "provider": "mistral",
        "model": "mistral-small-4",
        "api_key": st.secrets.get("MISTRAL_API_KEY", ""),
        "base_url": "https://api.mistral.ai/v1",
        "type": "openai"
    },
    {
        "provider": "cerebras",
        "model": "llama-3.3-70b",
        "api_key": st.secrets.get("CEREBRAS_API_KEY", ""),
        "base_url": "https://api.cerebras.ai/v1",
        "type": "openai"
    },
    {
        "provider": "openrouter",
        "model": "openrouter/auto",
        "api_key": st.secrets.get("OPENROUTER_API_KEY", ""),
        "base_url": "https://openrouter.ai/api/v1",
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
        "Philosopher": {"wins": 0, "losses": 0},
        "Futurist": {"wins": 0, "losses": 0},
        "DataScientist": {"wins": 0, "losses": 0},
        "Ethicist": {"wins": 0, "losses": 0},
    }
if "global_arguments" not in st.session_state:
    st.session_state.global_arguments = []
if "quantum_topic" not in st.session_state:
    st.session_state.quantum_topic = ""

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
    def __init__(self, name, role, personality, avatar):
        self.name = name
        self.role = role
        self.personality = personality
        self.avatar = avatar
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
        AI_Agent("Harsh", "Skeptic", "Pessimistic economist. Finds flaws and risks in every claim.", "🔴"),
        AI_Agent("Jayant", "Optimist", "Cheerful tech investor. Sees opportunity everywhere.", "🟢"),
        Moderator("Ahany", "Moderator", "Sharp journalist who challenges all sides.", "🔵"),
    ]
    extras = [
        ("Ritik", "Policy Advisor", "Government/regulation perspective. Focuses on public good and political feasibility.", "🟡"),
        ("Kavya", "Retail Investor", "Everyday person perspective. Cares about practical impact on daily life.", "🟣"),
        ("Nish", "Scientist", "Demands empirical evidence and peer review. Skeptical of unproven claims.", "🟠"),
        ("Teju", "Tech Journalist", "Identifies trends and market narratives. Looks for the story behind the tech.", "🔷"),
        ("Shivam", "Conspiracy Theorist", "Sees hidden agendas and questions official narratives.", "⚫"),
        ("Philosopher", "Philosopher", "Brings historical and ethical context. Questions underlying assumptions.", "🟤"),
        ("Futurist", "Futurist", "Argues from a 50-year perspective. Sees long-term implications and radical possibilities.", "🔮"),
        ("DataScientist", "Data Scientist", "Only argues with statistics and evidence. Rejects emotional appeals.", "📊"),
        ("Ethicist", "Ethicist", "Evaluates moral implications. Asks 'Should we?' not just 'Can we?'", "⚖️"),
    ]
    for i in range(min(num_extra, len(extras))):
        name, role, pers, av = extras[i]
        agents.insert(-1, AI_Agent(name, role, pers, av))
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
    st.markdown("### 🌑 Nyx Protocol")
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
    extra = st.selectbox("Extra Agents", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], index=6)
    st.markdown("---")
    st.markdown("### 📊 Agent Win Rates")
    for agent, stats in st.session_state.agent_stats.items():
        total = stats["wins"] + stats["losses"]
        rate = f"{(stats['wins']/total*100):.0f}%" if total > 0 else "0%"
        st.text(f"{agent}: {stats['wins']}W / {stats['losses']}L ({rate})")
    st.markdown("---")
    st.markdown("<p style='text-align: center; color: #a855f7;'>by Harsh Dubey</p>", unsafe_allow_html=True)

# --- Main UI ---
st.title("🌑 Nyx Protocol")
st.markdown('<div class="hero-subtitle">Multi‑Agent AI Debate · Judge · Live Scoring · Quantum Randomness</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    topic = st.text_area(
        "📰 **What should the panel debate?**",
        value=st.session_state.quantum_topic,
        height=120,
        placeholder="Enter a debate topic..."
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
        st.markdown(f"<h3 style='text-align: center;'>⚔️ ROUND {r} — ENGAGE ⚔️</h3>", unsafe_allow_html=True)
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
    st.success(f"🏆 Winner: {winner}")
    st.balloons()

    # Social Share
    share_text = f"Nyx Protocol verdict on '{topic}':\n\nWinner: {winner}\n\n{verdict[:200]}...\n\nTry it: https://harshswarmdev.streamlit.app"
    tweet = urllib.parse.quote(share_text)
    twitter_url = f"https://twitter.com/intent/tweet?text={tweet}"
    linkedin_url = f"https://www.linkedin.com/sharing/share-offsite/?url={urllib.parse.quote('https://harshswarmdev.streamlit.app')}"

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<a href="{twitter_url}" target="_blank"><button style="background:#1DA1F2; color:white; border:none; padding:10px 20px; border-radius:30px; font-weight:bold; width:100%;">🐦 Share on X</button></a>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<a href="{linkedin_url}" target="_blank"><button style="background:#0077B5; color:white; border:none; padding:10px 20px; border-radius:30px; font-weight:bold; width:100%;">💼 Share on LinkedIn</button></a>', unsafe_allow_html=True)

    # PDF Export
    pdf_data = generate_pdf(topic, log, verdict, winner)
    st.download_button(
        label="📄 Download Full Debate (PDF)",
        data=pdf_data,
        file_name=f"nyx_debate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        mime="application/pdf"
    )

    # Footer
    st.markdown("---")
    st.markdown("<p style='text-align: center; color: #a855f7;'>🌑 Nyx Protocol · by Harsh Dubey</p>", unsafe_allow_html=True)

