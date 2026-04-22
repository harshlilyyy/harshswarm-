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

# --- Premium Custom CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    :root {
        --bg-primary: #0b0c10;
        --bg-secondary: #14151a;
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --card-bg: rgba(20, 21, 26, 0.9);
        --card-border: rgba(168, 85, 247, 0.2);
        --gradient-start: #a855f7;
        --gradient-mid: #8b5cf6;
        --gradient-end: #06b6d4;
    }
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background: var(--bg-primary);
        color: var(--text-primary);
    }
    .main .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1400px; }
    h1 {
        background: linear-gradient(135deg, var(--gradient-start) 0%, var(--gradient-mid) 50%, var(--gradient-end) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
        font-size: 3.5rem !important;
        text-align: center;
        margin-bottom: 0.25rem !important;
    }
    @keyframes pulse {
        0% { opacity: 0.7; text-shadow: 0 0 5px #a855f7; }
        50% { opacity: 1; text-shadow: 0 0 20px #a855f7, 0 0 30px #06b6d4; }
        100% { opacity: 0.7; text-shadow: 0 0 5px #a855f7; }
    }
    .hero-subtitle { text-align: center; font-size: 1.2rem; color: var(--text-secondary); margin-bottom: 2rem; }
    [data-testid="stSidebar"] { background: var(--bg-secondary); border-right: 1px solid var(--card-border); }
    [data-testid="stChatMessage"] {
        background: var(--card-bg); border-radius: 24px; padding: 1.25rem 1.75rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2); margin-bottom: 1.25rem; border-left: 6px solid;
        border: 1px solid var(--card-border);
    }
    .stButton > button {
        background: linear-gradient(135deg, var(--gradient-start) 0%, var(--gradient-mid) 100%);
        color: white; font-weight: 700; border-radius: 60px; border: none;
        box-shadow: 0 4px 15px rgba(168, 85, 247, 0.3); transition: all 0.2s;
    }
    .stButton > button:hover { transform: scale(1.02); box-shadow: 0 6px 20px rgba(6, 182, 212, 0.4); }
    .verdict-box {
        background: var(--card-bg); border-radius: 28px; padding: 2rem;
        margin: 2rem 0; border: 1px solid var(--card-border);
    }
</style>
""", unsafe_allow_html=True)

# --- Multi-Model Router ---
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
    """Test each model in the chain and return the first working configuration."""
    for config in MODEL_CHAIN:
        if not config["api_key"]:
            st.sidebar.warning(f"⚠️ {config['provider']} API key missing")
            continue
        try:
            if config["type"] == "google":
                import google.generativeai as genai
                genai.configure(api_key=config["api_key"])
                # Quick test
                model = genai.GenerativeModel(config["model"])
                model.generate_content("test", request_options={"timeout": 5})
            else:
                # For OpenAI-compatible, just verify key format (we'll test on first real call)
                pass
            st.sidebar.success(f"✅ Active: {config['provider']} ({config['model']})")
            return config
        except Exception as e:
            st.sidebar.warning(f"⚠️ {config['provider']} failed: {str(e)[:40]}")
            continue
    st.error("🚨 No working models available. Check your API keys in Secrets.")
    st.stop()

# Get active model configuration
ACTIVE_MODEL = get_working_model()

# Initialize the appropriate client
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
    """Unified generation function that uses the active model."""
    if ACTIVE_MODEL["type"] == "google":
        # Google doesn't use system prompt separately; we prepend it
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

# --- Session State Initialization ---
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

# --- Quantum Topics ---
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

# --- Helper Functions ---
def is_repetition(text, threshold=0.6):
    words = set(text.lower().split())
    for past in st.session_state.global_arguments[-10:]:
        past_words = set(past.lower().split())
        if len(words & past_words) / max(len(words), 1) > threshold:
            return True
    return False

def add_global_memory(agent, text):
    st.session_state.global_arguments.append(f"{agent}: {text[:200]}")

# --- Agent Classes ---
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
    extra = st.selectbox("Extra Agents", [0, 1, 2, 3, 4, 5], index=4)
    st.markdown("---")
    st.markdown("### 📊 Agent Win Rates")
    for agent, stats in st.session_state.agent_stats.items():
        total = stats["wins"] + stats["losses"]
        rate = f"{(stats['wins']/total*100):.0f}%" if total > 0 else "0%"
        st.text(f"{agent}: {stats['wins']}W / {stats['losses']}L ({rate})")

# --- Main UI ---
st.title("🌑 Nyx Protocol")
st.markdown('<div class="hero-subtitle">Multi‑Agent AI Debate · Judge · Live Scoring · Quantum Randomness</div>', unsafe_allow_html=True)

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
        st.markdown(f"<h2 style='text-align: center; animation: pulse 1.5s infinite;'>⚔️ ROUND {r} — ENGAGE ⚔️</h2>", unsafe_allow_html=True)
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
    
    share_text = f"Nyx Protocol verdict on '{topic}':\n\nWinner: {winner}\n\n{verdict[:200]}...\n\nTry it: https://y4ekqcz3uzgejwapp3.streamlit.app"
    tweet = urllib.parse.quote(share_text)
    twitter_url = f"https://twitter.com/intent/tweet?text={tweet}"
    linkedin_url = f"https://www.linkedin.com/sharing/share-offsite/?url={urllib.parse.quote('https://y4ekqcz3uzgejwapp3.streamlit.app')}"
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<a href="{twitter_url}" target="_blank"><button style="background:#1DA1F2; color:white; border:none; padding:10px 20px; border-radius:30px; font-weight:bold; width:100%;">🐦 Share on X</button></a>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<a href="{linkedin_url}" target="_blank"><button style="background:#0077B5; color:white; border:none; padding:10px 20px; border-radius:30px; font-weight:bold; width:100%;">💼 Share on LinkedIn</button></a>', unsafe_allow_html=True)
    
    pdf_data = generate_pdf(topic, log, verdict, winner)
    st.download_button(
        label="📄 Download Full Debate (PDF)",
        data=pdf_data,
        file_name=f"nyx_debate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        mime="application/pdf"
    )