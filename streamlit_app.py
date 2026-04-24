import streamlit as st
import time
import re
import urllib.parse
from datetime import datetime
from fpdf import FPDF
from openai import OpenAI

# --- Page Config ---
st.set_page_config(
    page_title="Nyx · by Harsh",
    page_icon="🤍",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- Cosmic Pearl Glassmorphism CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;1,400&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;350;400;500&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Courier+Prime&display=swap');

    :root {
        --pearl: #F9F6F0;
        --rose-gold: #D4A5A5;
        --champagne: #E8D5B5;
        --warm-charcoal: #2C2A28;
        --glass-border: rgba(255,255,255,0.6);
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background: var(--pearl);
        color: var(--warm-charcoal);
    }

    .stApp {
        background: radial-gradient(circle at 50% 20%, rgba(232,213,181,0.25) 0%, var(--pearl) 80%);
    }

    .main .block-container {
        padding: 2rem 1.25rem !important;
        max-width: 640px !important;
        margin: 0 auto !important;
    }

    [data-testid="stToolbar"], footer, [data-testid="stSidebar"] {
        display: none !important;
    }

    .nyx-title {
        font-family: 'Playfair Display', serif;
        font-style: italic;
        font-size: 3.8rem;
        text-align: center;
        background: linear-gradient(145deg, var(--rose-gold), #B58D8D);
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
        background: rgba(255, 255, 255, 0.5);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 28px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 0.5px solid var(--glass-border);
        box-shadow: 0 10px 30px -10px rgba(0,0,0,0.05);
    }

    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.6) !important;
        backdrop-filter: blur(15px);
        border: 0.5px solid var(--glass-border) !important;
        border-radius: 60px !important;
        padding: 1rem 1.5rem !important;
        font-size: 1.1rem !important;
        color: var(--warm-charcoal) !important;
        text-align: center;
    }

    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.6) !important;
        backdrop-filter: blur(15px lifetime);
        border: 0.5px solid var(--glass-border) !important;
        border-radius: 60px !important;
    }

    .stButton > button {
        background: linear-gradient(145deg, var(--rose-gold), var(--champagne));
        border: none;
        border-radius: 60px;
        font-weight: 500;
        color: white;
        box-shadow: 0 8px 20px -8px rgba(212,165,165,0.4);
        width: 100%;
        padding: 0.8rem 1.5rem;
    }

    .debate-card {
        background: rgba(255, 255, 255, 0.45);
        backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 0.8rem;
        border-left: 5px solid;
    }

    .card-skeptic { border-left-color: #D4A5A5; }
    .card-optimist { border-left-color: #B5C9B5; }
    .card-philosopher { border-left-color: #C5B5D4; }
    .card-futurist { border-left-color: #A5C9D4; }
    .card-data { border-left-color: #A5D4C0; }
    .card-ethicist { border-left-color: #D4A5C0; }
    .card-policy { border-left-color: #E8D5B5; }
    .card-conspiracy { border-left-color: #B5A5C0; }

    .verdict-box {
        background: rgba(255, 255, 255, 0.5);
        backdrop-filter: blur(20px);
        border-radius: 28px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border-left: 5px solid var(--rose-gold);
        font-family: 'Courier Prime', monospace;
    }

    .round-tracker {
        text-align: center;
        margin: 0.5rem 0 0.8rem;
        font-weight: 600;
        font-size: 1.1rem;
        opacity: 0.8;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State ---
if "agent_stats" not in st.session_state:
    st.session_state.agent_stats = {
        "Harsh": {"wins": 0, "losses": 0}, "Jayant": {"wins": 0, "losses": 0},
        "Ritik": {"wins": 0, "losses": 0}, "Kavya": {"wins": 0, "losses": 0},
        "Nish": {"wins": 0, "losses": 0}, "Teju": {"wins": 0, "losses": 0},
        "Shivam": {"wins": 0, "losses": 0}, "Philosopher": {"wins": 0, "losses": 0},
        "Futurist": {"wins": 0, "losses": 0}, "DataScientist": {"wins": 0, "losses": 0},
        "Ethicist": {"wins": 0, "losses": 0}, "Ahany": {"wins": 0, "losses": 0},
    }
if "debate_history" not in st.session_state:
    st.session_state.debate_history = []

# --- API Providers (6 providers, Groq reserved for Judge) ---
PROVIDERS = [
    {"name": "Groq", "key": st.secrets.get("GROQ_API_KEY"), "base": "https://api.groq.com/openai/v1", "model": "llama-3.3-70b-versatile"},
    {"name": "DeepSeek", "key": st.secrets.get("DEEPSEEK_API_KEY"), "base": "https://api.deepseek.com", "model": "deepseek-chat"},
    {"name": "Cerebras", "key": st.secrets.get("CEREBRAS_API_KEY"), "base": "https://api.cerebras.ai/v1", "model": "llama3.3-70b"},
    {"name": "OpenRouter", "key": st.secrets.get("OPENROUTER_API_KEY"), "base": "https://openrouter.ai/api/v1", "model": "openrouter/auto"},
    {"name": "Mistral", "key": st.secrets.get("MISTRAL_API_KEY"), "base": "https://api.mistral.ai/v1", "model": "mistral-small-2409"},
    {"name": "Google", "key": st.secrets.get("GEMINI_API_KEY"), "base": "https://generativelanguage.googleapis.com/v1beta", "model": "gemini-2.0-flash"},
{"name": "NVIDIA", "key": st.secrets.get("NVIDIA_API_KEY"), "base": "https://integrate.api.nvidia.com/v1", "model": "meta/llama-3.3-70b-instruct"},
]

def get_client(provider):
    return OpenAI(api_key=provider["key"], base_url=provider["base"])

def generate_with_fallback(prompt, system="", preferred=None, silent_fail=False):
    if preferred:
        providers = [p for p in PROVIDERS if p["name"] == preferred] + [p for p in PROVIDERS if p["name"] != preferred]
    else:
        providers = PROVIDERS

    last_error = None
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
        except Exception as e:
            last_error = str(e)[:80]
            continue

    if silent_fail:
        return "Unable to generate response due to API limits.", "None"
    else:
        st.warning(f"⚠️ All providers temporarily unavailable. Last error: {last_error}")
        return "Response unavailable.", "None"

# --- Agents ---
class Agent:
    def __init__(self, name, role, personality, avatar, card_class):
        self.name, self.role, self.personality, self.avatar, self.card_class = name, role, personality, avatar, card_class
        self.history = []
    def speak(self, topic, last_msg, round_num, preferred_provider):
        history = "\n".join(self.history[-3:]) or "No previous chat."
        system = f"You are {self.name} ({self.role}). {self.personality}"
        prompt = f"""Debate round {round_num} on: "{topic}"
**Claim:** [point] **Evidence:** [fact] **Reasoning:** [why]
History: {history}
Last: "{last_msg}"
"""
        reply, _ = generate_with_fallback(prompt, system, preferred_provider)
        self.history.append(reply)
        return reply

class Moderator(Agent):
    def speak(self, topic, last_msg, round_num, preferred_provider):
        history = "\n".join(self.history[-5:]) or "No debate yet."
        system = f"You are {self.name}, the moderator. Be sharp and impartial."
        prompt = f"Summarize, note contradictions, ask a provocative question. Topic: {topic} | Round: {round_num}\nHistory: {history}\nLast: {last_msg}"
        reply, _ = generate_with_fallback(prompt, system, preferred_provider)
        self.history.append(reply)
        return reply

ALL_AGENTS = [
    ("Harsh", "Skeptic", "Finds flaws and risks.", "🔴", "card-skeptic"),
    ("Jayant", "Optimist", "Sees opportunity.", "🟢", "card-optimist"),
    ("Ahany", "Moderator", "Sharp journalist.", "🔵", "card-skeptic", True),
    ("Ritik", "Policy Advisor", "Gov/regulation lens.", "🟡", "card-policy"),
    ("Kavya", "Retail Investor", "Everyday person.", "🟣", "card-optimist"),
    ("Nish", "Scientist", "Empirical evidence.", "🟠", "card-data"),
    ("Teju", "Tech Journalist", "Trends and narratives.", "🔷", "card-futurist"),
    ("Shivam", "Conspiracy Theorist", "Hidden agendas.", "⚫", "card-conspiracy"),
    ("Philosopher", "Philosopher", "Ethical/historical context.", "🟤", "card-philosopher"),
    ("Futurist", "Futurist", "50-year perspective.", "🔮", "card-futurist"),
    ("DataScientist", "Data Scientist", "Statistics only.", "📊", "card-data"),
    ("Ethicist", "Ethicist", "Moral implications.", "⚖️", "card-ethicist"),
]

def create_panel(count=6):
    if count < 3:
        count = 3
    agents = []
    moderator = None
    for i, agent_data in enumerate(ALL_AGENTS):
        if i >= count:
            break
        if len(agent_data) == 6 and agent_data[5]:
            moderator = Moderator(agent_data[0], agent_data[1], agent_data[2], agent_data[3], agent_data[4])
        else:
            agents.append(Agent(agent_data[0], agent_data[1], agent_data[2], agent_data[3], agent_data[4]))
    if moderator and len(agents) >= 2:
        agents.insert(2, moderator)
    return agents

def judge(topic, messages):
    text = "\n".join(messages[-20:])
    prompt = f"""You are the JUDGE of a debate. Analyze the transcript below.
**Debate Topic:** "{topic}"
**Transcript:** {text}

Return your verdict in exactly this format:
Winner: [Name]
Reasoning: [2-3 sentences on why they won]
Logic: [score 1-10]
Evidence: [score 1-10]
Rebuttal: [score 1-10]
Persuasiveness: [score 1-10]
Takeaway: [1 sentence final insight]
"""
    # Reserve Groq exclusively for the judge
    reply, _ = generate_with_fallback(prompt, "You are an impartial expert judge.", preferred="Groq", silent_fail=True)
    return reply

def make_pdf(topic, log, verdict, winner):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Nyx Debate Transcript", ln=1)
    pdf.cell(200, 10, txt=f"Topic: {topic}", ln=1)
    pdf.ln(5)
    for msg in log:
        clean = msg.encode('latin-1','replace').decode('latin-1')
        pdf.multi_cell(0, 8, txt=clean)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt=f"Winner: {winner}", ln=1)
    pdf.multi_cell(0, 8, txt=verdict.encode('latin-1','replace').decode('latin-1'))
    return pdf.output(dest='S').encode('latin-1')
# --- UI: Header with Subtitle ---
st.markdown('<div class="nyx-title">Nyx</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">An AI debate arena. Ask anything.</div>', unsafe_allow_html=True)

# --- Compact Input Card ---
with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    topic = st.text_input("Ask anything...", value="Should AI have a conscience?", placeholder="Ask anything...", label_visibility="collapsed")
    
    # Advanced settings (hidden by default)
    with st.expander("⚙️ Customize debate", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.caption("Depth")
            rounds = st.select_slider("Rounds", options=[2, 3, 4], value=2, label_visibility="collapsed")
        with col2:
            st.caption("Debaters")
            agent_count = st.select_slider("Agents", options=list(range(3, 13)), value=6, label_visibility="collapsed")
        with col3:
            st.caption("Speed vs. quality")
            mode = st.radio("Provider", ["⚡ Fast", "🧠 Smart", "🤖 Auto"], horizontal=True, index=2, label_visibility="collapsed")
        show_args = st.checkbox("Show arguments", value=True)
    
    launch = st.button("Start Debate", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- Debate Execution ---
if launch and topic:
    # Map mode to preferred provider (but Groq is reserved for judge, so we never use it for agents)
    if mode == "⚡ Fast":
        preferred = "Cerebras"
    elif mode == "🧠 Smart":
        preferred = "DeepSeek"
    else:
        preferred = None  # Auto will try all except Groq (since it's reserved)
    
    agents = create_panel(agent_count)
    log = []
    last_msg = "Let's begin."
    winner = None
    verdict = ""
    used_provider = None
    fallback_warning = False
    
    if show_args:
        st.markdown("### ⚔️ THE ARENA")
    
    for r in range(1, rounds+1):
        st.markdown(f'<div class="round-tracker">Round {r} of {rounds}</div>', unsafe_allow_html=True)
        round_msgs = []
        order = [a for a in agents if a.name != "Ahany"]
        
        # Persona chips
        persona_html = " · ".join([f"{a.avatar} {a.name}" for a in order])
        st.markdown(f'<div style="text-align:center;opacity:0.6;margin-bottom:0.8rem;">{persona_html}</div>', unsafe_allow_html=True)
        
        for agent in order:
            reply, provider = generate_with_fallback(
                f"Round {r} on '{topic}'. History: {last_msg}",
                f"You are {agent.name} ({agent.role}). {agent.personality}",
                preferred
            )
            if used_provider and provider != used_provider:
                fallback_warning = True
            used_provider = provider
            
            if show_args:
                with st.expander(f"{agent.avatar} {agent.name} · {agent.role}", expanded=True):
                    st.markdown(f'<div class="debate-card {agent.card_class}">{reply}</div>', unsafe_allow_html=True)
            round_msgs.append(f"{agent.avatar} {agent.name}: {reply}")
            last_msg = reply
            time.sleep(0.8)  # Throttle to avoid rate limits
        
        mod = next((a for a in agents if a.name == "Ahany"), None)
        if mod:
            mod_reply, provider = generate_with_fallback(
                f"Moderate round {r} on '{topic}'. Last: {last_msg}",
                f"You are {mod.name}, the moderator.",
                preferred
            )
            if show_args:
                with st.expander(f"{mod.avatar} {mod.name} · Moderator", expanded=True):
                    st.markdown(f'<div class="debate-card" style="border-left-color:#D4A5A5;">{mod_reply}</div>', unsafe_allow_html=True)
            round_msgs.append(f"{mod.avatar} {mod.name}: {mod_reply}")
            last_msg = mod_reply
        log.append("\n".join(round_msgs))
    
    st.session_state.debate_history = log
    
    if used_provider:
        st.caption(f"⚙️ Powered by {used_provider}")
    if fallback_warning:
        st.warning("⚠️ The primary provider was unavailable; the debate automatically switched to a backup model.")
    
    with st.spinner("Judgment..."):
        verdict = judge(topic, log)
    
    # Parse verdict into structured display
    winner_match = re.search(r"Winner:\s*(.+)", verdict)
    reasoning_match = re.search(r"Reasoning:\s*(.+)", verdict)
    logic_match = re.search(r"Logic:\s*(\d+)", verdict)
    evidence_match = re.search(r"Evidence:\s*(\d+)", verdict)
    rebuttal_match = re.search(r"Rebuttal:\s*(\d+)", verdict)
    persuasiveness_match = re.search(r"Persuasiveness:\s*(\d+)", verdict)
    
    winner = winner_match.group(1).strip() if winner_match else "Unknown"
    reasoning = reasoning_match.group(1).strip() if reasoning_match else "No detailed reasoning provided."
    
    # Update stats
    for agent in st.session_state.agent_stats:
        if agent == winner:
            st.session_state.agent_stats[agent]["wins"] += 1
        else:
            st.session_state.agent_stats[agent]["losses"] += 1
    
    # Verdict display with scorecard
    st.markdown(f"""
    <div class="verdict-box">
        <h3>🏆 {winner}</h3>
        <p><strong>Reasoning:</strong> {reasoning}</p>
        <hr style="margin:1rem 0;border:0.5px solid rgba(0,0,0,0.1);"/>
        <div style="display:flex;flex-wrap:wrap;gap:1rem;font-size:0.9rem;">
            <div><strong>Logic:</strong> {logic_match.group(1) if logic_match else '?'}/10</div>
            <div><strong>Evidence:</strong> {evidence_match.group(1) if evidence_match else '?'}/10</div>
            <div><strong>Rebuttal:</strong> {rebuttal_match.group(1) if rebuttal_match else '?'}/10</div>
            <div><strong>Persuasiveness:</strong> {persuasiveness_match.group(1) if persuasiveness_match else '?'}/10</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Follow‑up
    with st.container():
        st.markdown('<div class="glass-card" style="margin-top:0.5rem;">', unsafe_allow_html=True)
        st.markdown("**💬 Follow‑up**")
        follow_up = st.text_input("Ask about the debate...", placeholder="e.g., 'Why that winner?'", key="follow_up", label_visibility="collapsed")
        if st.button("Ask", key="ask_follow") and follow_up:
            context = "\n".join(st.session_state.debate_history[-5:])
            reply, _ = generate_with_fallback(f"Previous debate on '{topic}':\n{context}\n\nUser asks: {follow_up}\n\nRespond helpfully in 2-3 sentences.", "", "DeepSeek", silent_fail=True)
            st.markdown(f"""
            <div class="debate-card" style="border-left-color:#D4A5A5;">
                <div class="agent-name">💬 Nyx</div>
                <div class="agent-message">{reply}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Stats & Sharing
    with st.expander("📊 Agent Leaderboard"):
        for agent, s in st.session_state.agent_stats.items():
            total = s['wins']+s['losses']
            rate = f"{s['wins']/total*100:.0f}%" if total else "0%"
            st.text(f"{agent}: {s['wins']}W / {s['losses']}L ({rate})")
    
    share = f"Nyx verdict: {winner} wins on '{topic}'"
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f'<a href="https://twitter.com/intent/tweet?text={urllib.parse.quote(share)}" target="_blank"><button style="width:100%;background:#1DA1F2;color:white;border:none;border-radius:60px;padding:0.5rem;">🐦 Tweet</button></a>', unsafe_allow_html=True)
    with col_b:
        pdf = make_pdf(topic, log, verdict, winner)
        st.download_button("📄 PDF", pdf, f"nyx_{datetime.now():%Y%m%d_%H%M}.pdf")

# --- Footer ---
st.markdown('<div style="text-align:center; margin-top:2rem; opacity:0.6; font-family:\'Playfair Display\',serif; font-style:italic;">✨ Harsh Dubey · Nyx ✨</div>', unsafe_allow_html=True)
