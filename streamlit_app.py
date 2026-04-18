import streamlit as st
import google.generativeai as genai
import time
import random
import json
import os
import re
from datetime import datetime

# --- Page Config ---
st.set_page_config(page_title="HarshSwarm Pro", page_icon="⚡", layout="wide")

# --- Premium CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    :root {
        --bg: #f8fafc;
        --card: #ffffff;
        --text: #0f172a;
        --muted: #475569;
        --border: #e2e8f0;
    }
    .stApp { background: var(--bg); font-family: 'Inter', sans-serif; }
    h1 { font-weight: 800; font-size: 2.8rem; background: linear-gradient(135deg, #0ea5e9, #8b5cf6, #ec4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0; }
    .subtitle { color: var(--muted); font-size: 1.1rem; }
    .control-bar { background: var(--card); border-radius: 24px; padding: 1.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.04); margin-bottom: 1.5rem; border: 1px solid var(--border); }
    .debate-card { background: var(--card); border-radius: 20px; padding: 1.5rem; margin-bottom: 1rem; border-left: 6px solid; box-shadow: 0 2px 8px rgba(0,0,0,0.02); }
    .scoreboard { background: var(--card); border-radius: 20px; padding: 1.5rem; border: 1px solid var(--border); margin-bottom: 1.5rem; }
    .verdict-box { background: linear-gradient(145deg, #f1f5f9, #ffffff); border-radius: 28px; padding: 2rem; margin-top: 2rem; border: 1px solid #cbd5e1; }
    .highlight { background: #fef9c3; padding: 0.1rem 0.3rem; border-radius: 6px; font-weight: 500; }
    .marker { background: #fee2e2; color: #b91c1c; padding: 0.1rem 0.4rem; border-radius: 12px; font-size: 0.8rem; font-weight: 600; margin-right: 6px; }
    .stButton>button { background: linear-gradient(135deg, #0ea5e9, #8b5cf6); color: white; border: none; border-radius: 60px; padding: 0.6rem 2rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# --- API Key Handling ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    st.error("API key not found in secrets.")
    st.stop()
genai.configure(api_key=api_key)
MODEL_NAME = 'gemma-3-27b-it'

# --- Global Anti-Repetition Memory (per debate) ---
if "global_arguments" not in st.session_state:
    st.session_state.global_arguments = []

def add_global_memory(agent, text):
    st.session_state.global_arguments.append(f"{agent}: {text[:200]}")

def is_repetition(text, threshold=0.6):
    words = set(text.lower().split())
    for past in st.session_state.global_arguments[-10:]:
        past_words = set(past.lower().split())
        if len(words & past_words) / max(len(words),1) > threshold:
            return True
    return False

# --- Agent Class ---
class AI_Agent:
    def __init__(self, name, role, personality, avatar, color):
        self.name = name
        self.role = role
        self.personality = personality
        self.avatar = avatar
        self.color = color
        self.history = []
        self.scores = {"logic": 0, "creativity": 0, "persuasiveness": 0}

    def speak(self, topic, last_msg, model, round_num, tone=None):
        history_text = "\n".join(self.history[-3:]) if self.history else "No previous chat."
        prompt = f"""
You are {self.name} ({self.role}). {self.personality}
Debate round {round_num} about: "{topic}"

STRICT FORMAT:
**Claim:** [Your main point]
**Evidence:** [Supporting fact/example]
**Reasoning:** [Why it matters]

DO NOT repeat previous arguments. Check history:
{history_text}

Last said: "{last_msg}"

Your response:
"""
        for attempt in range(2):
            response = model.generate_content(prompt)
            reply = response.text.strip()
            if not is_repetition(reply):
                break
            prompt += "\nWARNING: Argument repeated. Provide a NEW angle."
        else:
            reply = "**Claim:** I stand by my position. **Evidence:** Already presented. **Reasoning:** Further discussion is needed."
        self.history.append(f"{self.name}: {reply}")
        add_global_memory(self.name, reply)
        return reply

# --- Moderator ---
class Moderator(AI_Agent):
    def speak(self, topic, last_msg, model, round_num, tone=None):
        history = "\n".join(self.history[-5:]) if self.history else "No debate yet."
        prompt = f"""
You are {self.name}, the moderator. Summarize key points, highlight contradictions, and ask a sharp question.
Topic: "{topic}" | Round: {round_num}
History: {history}
Last exchange: "{last_msg}"
Keep it to 3-4 sentences.
"""
        response = model.generate_content(prompt)
        reply = response.text.strip()
        self.history.append(f"{self.name}: {reply}")
        return reply

# --- Judge ---
def judge_debate(topic, messages, model):
    debate_text = "\n".join(messages[-30:])
    prompt = f"""
You are the JUDGE. Debate on: "{topic}"
Transcript: {debate_text}

Provide:
🏆 Winner: [Name]
📝 Reasoning: [2-3 sentences]

Strengths & Weaknesses for each:
- Harsh (Skeptic): ...
- Jayant (Optimist): ...
(others as applicable)

📊 Scores (1-10) for Logic, Creativity, Persuasiveness in a table.

⚖️ Final Takeaway: [1-2 sentences]
"""
    resp = model.generate_content(prompt)
    return resp.text

# --- Score Calculator (simple heuristic based on structured arguments) ---
def update_scores(agent, response):
    text = response.lower()
    if "claim:" in text: agent.scores["logic"] += 2
    if "evidence:" in text: agent.scores["creativity"] += 2
    if "reasoning:" in text: agent.scores["persuasiveness"] += 2
    # Cap at 10 per round? We'll just accumulate and normalize later

# --- Create Agents ---
def create_agents(num_extra=2):
    agents = [
        AI_Agent("Harsh", "Skeptic", "Pessimistic economist. Finds flaws and risks.", "🔴", "#ef4444"),
        AI_Agent("Jayant", "Optimist", "Cheerful tech investor. Sees opportunity.", "🟢", "#10b981"),
        Moderator("Ahany", "Moderator", "Sharp journalist.", "🔵", "#3b82f6")
    ]
    extra_pool = [
        ("Ritik", "Policy Advisor", "Government/regulation view.", "🟡", "#eab308"),
        ("Kavya", "Retail Investor", "Everyday person perspective.", "🟣", "#8b5cf6"),
        ("Nish", "Scientist", "Demands empirical evidence.", "🟠", "#f97316"),
        ("Teju", "Tech Journalist", "Identifies trends.", "🔷", "#06b6d4"),
        ("Shivam", "Conspiracy Theorist", "Sees hidden agendas.", "⚫", "#334155")
    ]
    for i in range(min(num_extra, len(extra_pool))):
        name, role, pers, av, col = extra_pool[i]
        agents.insert(-1, AI_Agent(name, role, pers, av, col))
    return agents

# --- Main App ---
st.title("⚡ HarshSwarm Pro")
st.markdown('<div class="subtitle">Multi‑Agent AI Debate Engine • Judge • Live Scoring</div>', unsafe_allow_html=True)
st.caption("Structured debates with anti‑repetition and expert judging.")

# --- Control Bar ---
with st.container():
    st.markdown('<div class="control-bar">', unsafe_allow_html=True)
    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
    with col1:
        topic = st.text_input("📰 Debate Topic", value="Apple announces new AI chip that uses 50% less power and is carbon neutral.")
    with col2:
        mode = st.selectbox("⚡ Mode", ["Quick (3 rounds)", "Standard (5 rounds)", "Deep (8 rounds)"])
        rounds = 3 if "Quick" in mode else 5 if "Standard" in mode else 8
    with col3:
        num_extra = st.selectbox("👥 Extra Agents", [0,1,2,3,4,5], index=2)
    with col4:
        start_btn = st.button("🚀 Start Debate", use_container_width=True)
    with col5:
        reset_btn = st.button("🔄 Reset", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

if reset_btn:
    for key in ["debate_log", "scores", "summary", "verdict", "progress", "debate_active"]:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.global_arguments = []
    st.rerun()

# --- Initialize Debate State ---
if "debate_active" not in st.session_state:
    st.session_state.debate_active = False
if "debate_log" not in st.session_state:
    st.session_state.debate_log = []
if "scores" not in st.session_state:
    st.session_state.scores = {}
if "summary" not in st.session_state:
    st.session_state.summary = ""
if "verdict" not in st.session_state:
    st.session_state.verdict = ""
if "progress" not in st.session_state:
    st.session_state.progress = 0

# --- Layout Columns ---
left_col, right_col = st.columns([2.2, 1])

# --- Right Sidebar Panel ---
with right_col:
    st.markdown("### 📊 Live Scoreboard")
    score_placeholder = st.empty()
    
    st.markdown("### 📈 Debate Progress")
    progress_placeholder = st.empty()
    
    st.markdown("### 📝 Running Summary")
    summary_placeholder = st.empty()

# --- Left Debate Area ---
with left_col:
    chat_placeholder = st.empty()

# --- Bottom Verdict Area ---
verdict_placeholder = st.empty()

# --- Run Debate if Start clicked ---
if start_btn and not st.session_state.debate_active:
    st.session_state.debate_active = True
    st.session_state.debate_log = []
    st.session_state.global_arguments = []
    st.session_state.scores = {}
    st.session_state.summary = ""
    st.session_state.verdict = ""
    st.session_state.progress = 0
    
    model = genai.GenerativeModel(MODEL_NAME)
    agents = create_agents(num_extra)
    for a in agents:
        st.session_state.scores[a.name] = {"logic": 0, "creativity": 0, "persuasiveness": 0}
    
    log = []
    last_msg = "Let's begin the debate."
    
    # --- Debate Loop ---
    for r in range(1, rounds+1):
        st.session_state.progress = r / rounds
        progress_placeholder.progress(st.session_state.progress, f"Round {r} of {rounds}")
        
        round_msgs = []
        # Speaking order: Harsh, Jayant, extras, Moderator
        order = [a for a in agents if a.name != "Ahany"]
        for agent in order:
            with st.spinner(f"{agent.name} is thinking..."):
                reply = agent.speak(topic, last_msg, model, r)
            round_msgs.append(f"{agent.avatar} **{agent.name} ({agent.role})**: {reply}")
            update_scores(agent, reply)
            last_msg = reply
            time.sleep(1)
        # Moderator
        mod = next(a for a in agents if a.name == "Ahany")
        with st.spinner("Moderator summarizing..."):
            mod_reply = mod.speak(topic, last_msg, model, r)
        round_msgs.append(f"{mod.avatar} **{mod.name} ({mod.role})**: {mod_reply}")
        last_msg = mod_reply
        
        log.append(f"### 🔄 Round {r}\n\n" + "\n\n".join(round_msgs))
        st.session_state.debate_log = log.copy()
        
        # Update scoreboard display
        score_df = []
        for a in agents:
            score_df.append({
                "Agent": f"{a.avatar} {a.name}",
                "Logic": a.scores["logic"],
                "Creativity": a.scores["creativity"],
                "Persuasiveness": a.scores["persuasiveness"]
            })
        score_placeholder.dataframe(score_df, use_container_width=True, hide_index=True)
        
        # Generate running summary (every 2 rounds)
        if r % 2 == 0 or r == rounds:
            summary_prompt = f"Summarize key insights so far from debate on '{topic}'. 2-3 bullet points."
            summ = model.generate_content(summary_prompt).text
            st.session_state.summary = summ
            summary_placeholder.markdown(f"**Key Insights:**\n\n{summ}")
        
        # Update chat display
        full_chat = "\n\n".join(log)
        chat_placeholder.markdown(full_chat)
        time.sleep(0.5)
    
    # --- Judge Verdict ---
    with st.spinner("🧑‍⚖️ Judge is deliberating..."):
        verdict = judge_debate(topic, log, model)
        st.session_state.verdict = verdict
    verdict_placeholder.markdown(f'<div class="verdict-box">{verdict}</div>', unsafe_allow_html=True)
    
    st.session_state.debate_active = False
    st.balloons()

# --- Display existing state if debate already finished ---
elif not st.session_state.debate_active and st.session_state.debate_log:
    chat_placeholder.markdown("\n\n".join(st.session_state.debate_log))
    if st.session_state.verdict:
        verdict_placeholder.markdown(f'<div class="verdict-box">{st.session_state.verdict}</div>', unsafe_allow_html=True)
    # Rebuild scoreboard from stored scores
    score_data = []
    for name, s in st.session_state.scores.items():
        score_data.append({"Agent": name, "Logic": s["logic"], "Creativity": s["creativity"], "Persuasiveness": s["persuasiveness"]})
    if score_data:
        score_placeholder.dataframe(score_data, use_container_width=True, hide_index=True)
    progress_placeholder.progress(1.0, "Completed")
    if st.session_state.summary:
        summary_placeholder.markdown(f"**Key Insights:**\n\n{st.session_state.summary}")
