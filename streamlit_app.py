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

# --- 💖 Pink Love Theme with Glassmorphism & Hearts Background 💖 ---
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
        --glass-white: rgba(255, 255, 255, 0.75);
        --glass-pink: rgba(255, 228, 230, 0.7);
        --glass-border: rgba(232, 123, 158, 0.3);
    }

    html, body, [class*="css"] {
        font-family: 'Quicksand', sans-serif;
        background: var(--cream);
        color: var(--charcoal);
    }

    .stApp {
        background: linear-gradient(145deg, #fff0f3 0%, #ffe4e9 100%);
        background-image: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M30 15 C25 5 15 5 10 15 C5 25 15 35 30 45 C45 35 55 25 50 15 C45 5 35 5 30 15z' fill='%23fbc4d5' opacity='0.2'/%3E%3C/svg%3E");
    }

    .main .block-container {
        padding: 2rem 2rem 2rem 2rem;
        max-width: 1440px;
    }

    h1 {
        font-family: 'Dancing Script', cursive;
        font-size: 4.2rem !important;
        font-weight: 700 !important;
        background: linear-gradient(135deg, var(--deep-rose) 0%, #f7c873 100%);
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
        opacity: 0.8;
        display: inline-block;
    }

    .hero-subtitle {
        text-align: center;
        font-size: 1.2rem;
        color: var(--charcoal);
        margin-bottom: 2rem;
        font-weight: 500;
    }

    /* Sidebar - Frosted Pink Glass */
    [data-testid="stSidebar"] {
        background: var(--glass-pink);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-right: 1px solid var(--glass-border);
        box-shadow: 5px 0 20px rgba(232, 123, 158, 0.1);
    }

    [data-testid="stSidebar"] .block-container {
        padding: 2rem 1.5rem;
    }

    /* Chat Messages - White Glass with Pink Border */
    [data-testid="stChatMessage"] {
        background: var(--glass-white);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 32px 32px 32px 8px;
        padding: 1.5rem 1.8rem;
        margin-bottom: 1.5rem;
        border: 1px solid var(--glass-border);
        box-shadow: 0 10px 20px -8px rgba(232, 123, 158, 0.15);
        color: var(--charcoal);
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

    /* Input Fields - Glass with Pink Border */
    .stTextArea textarea, .stSelectbox > div > div, .stTextInput > div > div > input {
        background: var(--glass-white) !important;
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border: 2px solid var(--glass-border) !important;
        border-radius: 30px !important;
        color: var(--charcoal) !important;
        padding: 1rem 1.5rem !important;
        font-size: 1rem !important;
    }

    .stTextArea textarea:focus, .stSelectbox > div > div:focus {
        border-color: var(--deep-rose) !important;
        box-shadow: 0 0 0 4px rgba(232, 123, 158, 0.15) !important;
    }

    /* Buttons - Pink Gradient */
    .stButton > button {
        background: linear-gradient(135deg, var(--rose) 0%, var(--deep-rose) 100%);
        color: white;
        font-weight: 600;
        border-radius: 60px;
        border: none;
        padding: 0.75rem 2rem;
        font-size: 1.1rem;
        box-shadow: 0 8px 18px -6px rgba(232, 123, 158, 0.4);
        transition: all 0.3s ease;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }

    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 14px 24px -8px rgba(232, 123, 158, 0.6);
        background: linear-gradient(135deg, var(--deep-rose) 0%, #d45d82 100%);
    }

    /* Verdict Box - Glass */
    .verdict-box {
        background: var(--glass-white);
        backdrop-filter: blur(12px);
        border-radius: 40px 40px 40px 12px;
        padding: 2rem 2.5rem;
        margin: 2rem 0;
        border: 1px solid var(--glass-border);
        box-shadow: 0 20px 30px -10px rgba(232, 123, 158, 0.15);
        color: var(--charcoal);
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

    /* Dataframe / Scoreboard - Glass */
    [data-testid="stDataFrame"] {
        background: var(--glass-white);
        backdrop-filter: blur(8px);
        border-radius: 24px;
        padding: 0.5rem;
        border: 1px solid var(--glass-border);
        box-shadow: 0 8px 16px -8px rgba(232, 123, 158, 0.1);
    }

    /* Progress Bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, var(--soft-pink), var(--deep-rose));
        border-radius: 20px;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: var(--blush); border-radius: 10px; }
    ::-webkit-scrollbar-thumb { background: var(--rose); border-radius: 10px; }
</style>
""", unsafe_allow_html=True)
# --- Available Models for Selector ---
AVAILABLE_MODELS = {
    "💗 Groq (Llama 3.3 70B)": {"provider": "groq", "model": "llama-3.3-70b-versatile", "type": "openai", "base_url": "https://api.groq.com/openai/v1"},
    "🌸 DeepSeek (DeepSeek-Chat)": {"provider": "deepseek", "model": "deepseek-chat", "type": "openai", "base_url": "https://api.deepseek.com"},
    "💕 Mistral (Mistral Small 4)": {"provider": "mistral", "model": "mistral-small-4", "type": "openai", "base_url": "https://api.mistral.ai/v1"},
    "💓 Cerebras (Llama 3.3 70B)": {"provider": "cerebras", "model": "llama-3.3-70b", "type": "openai", "base_url": "https://api.cerebras.ai/v1"},
    "💞 OpenRouter (Auto)": {"provider": "openrouter", "model": "openrouter/auto", "type": "openai", "base_url": "https://openrouter.ai/api/v1"},
    "💖 Google (Gemma 4 26B)": {"provider": "google", "model": "gemma-4-26b-it", "type": "google", "base_url": None},
}

PROVIDER_API_KEYS = {
    "groq": st.secrets.get("GROQ_API_KEY", ""),
    "deepseek": st.secrets.get("DEEPSEEK_API_KEY", ""),
    "mistral": st.secrets.get("MISTRAL_API_KEY", ""),
    "cerebras": st.secrets.get("CEREBRAS_API_KEY", ""),
    "openrouter": st.secrets.get("OPENROUTER_API_KEY", ""),
    "google": st.secrets.get("GEMINI_API_KEY", ""),
}

def get_model_config(manual_override, selected_model_name):
    if manual_override:
        config = AVAILABLE_MODELS[selected_model_name].copy()
        config["api_key"] = PROVIDER_API_KEYS.get(config["provider"], "")
        if not config["api_key"]:
            st.error(f"❌ Missing API key for {config['provider']}")
            st.stop()
        return config
    else:
        # Auto‑fallback chain
        for provider, model in [("groq", "llama-3.3-70b-versatile"), ("deepseek", "deepseek-chat"),
                                ("mistral", "mistral-small-4"), ("cerebras", "llama-3.3-70b"),
                                ("openrouter", "openrouter/auto"), ("google", "gemma-4-26b-it")]:
            key = PROVIDER_API_KEYS.get(provider, "")
            if key:
                try:
                    if provider == "google":
                        import google.generativeai as genai
                        genai.configure(api_key=key)
                        genai.GenerativeModel(model).generate_content("test", request_options={"timeout": 5})
                    return {"provider": provider, "model": model, "api_key": key,
                            "type": "google" if provider=="google" else "openai",
                            "base_url": AVAILABLE_MODELS.get(provider, {}).get("base_url")}
                except: continue
        st.error("No working models available.")
        st.stop()

# This will be initialized after we get manual_override and selected_model_name from UI
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

def create_agents(num_extra=6):
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
# --- Sidebar (Settings, Quantum Roll, Win Rates) ---
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
    extra = st.selectbox("Extra Agents", list(range(10)), index=6)
    manual_override = st.checkbox("Use selected model (override auto‑fallback)", value=True)
    st.markdown("---")
    st.markdown("### 📊 Agent Win Rates")
    for agent, stats in st.session_state.agent_stats.items():
        total = stats["wins"] + stats["losses"]
        rate = f"{(stats['wins']/total*100):.0f}%" if total > 0 else "0%"
        st.text(f"{agent}: {stats['wins']}W / {stats['losses']}L ({rate})")
    st.markdown("---")
    st.markdown("<p style='text-align: center; color: #e87b9e;'>by Harsh Dubey</p>", unsafe_allow_html=True)

# --- Main UI: Perplexity-Style Centered Input ---
st.title("💗 Nyx Protocol 💗")
st.markdown('<div class="hero-subtitle">Multi‑Agent AI Debate · Judge · Live Scoring · Quantum Randomness</div>', unsafe_allow_html=True)

st.markdown("""
<div style="max-width: 700px; margin: 0 auto;">
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 4])
with col1:
    selected_model_name = st.selectbox(
        "🤖 Model",
        list(AVAILABLE_MODELS.keys()),
        index=0,
        label_visibility="collapsed"
    )
with col2:
    topic = st.text_input(
        "Ask anything...",
        value=st.session_state.get("quantum_topic", ""),
        placeholder="Ask anything...",
        label_visibility="collapsed"
    )

col3, col4, col5 = st.columns([1, 2, 1])
with col4:
    start_btn = st.button("🚀 Launch Debate", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# --- Initialize Model (after we have manual_override and selected_model_name) ---
MODEL_CONFIG = get_model_config(manual_override, selected_model_name)
if MODEL_CONFIG["type"] == "google":
    import google.generativeai as genai
    genai.configure(api_key=MODEL_CONFIG["api_key"])
    google_model = genai.GenerativeModel(MODEL_CONFIG["model"])
else:
    from openai import OpenAI
    client = OpenAI(api_key=MODEL_CONFIG["api_key"], base_url=MODEL_CONFIG["base_url"])

def generate_response(prompt, system_prompt=None):
    if MODEL_CONFIG["type"] == "google":
        full = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        return google_model.generate_content(full).text
    else:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        resp = client.chat.completions.create(
            model=MODEL_CONFIG["model"],
            messages=messages,
            temperature=0.7,
            max_tokens=600
        )
        return resp.choices[0].message.content

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
    st.markdown("<p style='text-align: center; color: #e87b9e;'>💗 Nyx Protocol · by Harsh Dubey 💗</p>", unsafe_allow_html=True)
