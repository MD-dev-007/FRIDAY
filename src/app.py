import streamlit as st
from llm_utils import stream_ollama, query_ollama
from memory import save_message, retrieve_memory, get_memory_stats, get_all_messages, summarize_and_compact, clear_all_memory, delete_message_by_id, pin_message, unpin_message, get_pinned_messages, push_working_goal, list_working_goals, forget_by_text
from persona import generate_adaptive_prompt, detect_sentiment, load_persona_config
import datetime
import json
import time
import re
from pathlib import Path

# Resolve project root (one level up from src)
ROOT_PATH = Path(__file__).resolve().parent.parent

st.set_page_config(page_title="FRIDAY Bot", page_icon="🤖", layout="wide")

# Global styles and subtle AI-themed effects (mobile-friendly)
def inject_global_styles():
    st.markdown(
        """
        <style>
        /* Layout tweaks */
        .block-container {max-width: 1200px; padding-top: 1rem; padding-bottom: 4rem;}
        @media (max-width: 640px) {
          .block-container {padding-left: 0.8rem; padding-right: 0.8rem;}
          section[data-testid="stSidebar"] {width: 80vw !important;}
        }

        /* Animated tech gradient background */
        html, body {background: radial-gradient(1200px 800px at 80% -10%, rgba(0, 255, 170, 0.08), transparent),
                                  radial-gradient(1000px 700px at -10% 110%, rgba(0, 140, 255, 0.08), transparent),
                                  linear-gradient(120deg, #0b1020, #0a0f1a 35%, #0b1020 65%, #0a0f1a);
                     background-attachment: fixed;}
        body::before {content: ""; position: fixed; inset: 0; pointer-events: none;
          background: repeating-linear-gradient(180deg, rgba(255,255,255,0.02) 0px, rgba(255,255,255,0.02) 1px, transparent 2px, transparent 6px);
          animation: scan 10s linear infinite;}
        @keyframes scan {0% {transform: translateY(-10%);} 50% {transform: translateY(10%);} 100% {transform: translateY(-10%);} }

        /* Title glow + AI pulse underline */
        h1 {letter-spacing: 0.3px;}
        h1:after {content: ""; display: block; height: 3px; margin-top: 6px; border-radius: 3px;
          background: linear-gradient(90deg, #00ffa8, #00b3ff, #6f5bff);
          box-shadow: 0 0 16px rgba(0, 255, 168, 0.35), 0 0 28px rgba(0, 179, 255, 0.25);
          animation: pulse 3s ease-in-out infinite;}
        @keyframes pulse {0%,100% {opacity: 0.55;} 50% {opacity: 1;}}

        /* Glassmorphism cards for chat messages */
        div[data-testid="stChatMessage"] {border: 1px solid rgba(255,255,255,0.08); border-radius: 14px;
          background: rgba(255,255,255,0.03); backdrop-filter: blur(8px); padding: 10px 12px;}
        /* User vs assistant accent bar */
        div[data-testid="stChatMessage"][data-testid*="user"] {box-shadow: inset 2px 0 0 0 #00b3ff66;}
        div[data-testid="stChatMessage"][data-testid*="assistant"] {box-shadow: inset 2px 0 0 0 #00ffa866;}

        /* Buttons: neon hover */
        .stButton>button {border-radius: 10px; border: 1px solid rgba(255,255,255,0.12);
          background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.03));
          transition: box-shadow .25s ease, transform .06s ease;}
        .stButton>button:hover {box-shadow: 0 0 0 2px #00ffa850, 0 0 18px #00ffa830, inset 0 0 0 1px rgba(255,255,255,0.25);} 
        .stButton>button:active {transform: translateY(1px);} 

        /* Tabs glow underline */
        button[role="tab"][aria-selected="true"] {box-shadow: inset 0 -2px 0 0 #00ffa8aa;}

        /* Chat input visibility on mobile */
        @media (max-width: 640px) {
          div[data-baseweb="input"] textarea {font-size: 0.95rem;}
        }

        /* Metrics and expanders: compact spacing */
        [data-testid="stMetric"] {background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 8px;}
        [data-testid="stExpander"] {border: 1px solid rgba(255,255,255,0.08); border-radius: 12px;}
        </style>
        """,
        unsafe_allow_html=True,
    )

def hero_banner():
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
          <div style="width:10px;height:10px;border-radius:50%;background:conic-gradient(#00ffa8, #00b3ff, #6f5bff, #00ffa8);box-shadow:0 0 12px #00ffa880, 0 0 22px #00b3ff60;"></div>
          <div style="color:#9cc;opacity:0.9;font-size:0.95rem;">On‑device AI • Private • Fast • Memory‑augmented</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

inject_global_styles()

# Title
st.title("🤖 FRIDAY - Your AI Assistant")
hero_banner()
st.write("Chat with your local LLaMA model powered by Ollama with persistent memory.")

# Load preferences from project root
def load_preferences():
    try:
        with open(ROOT_PATH / 'preferences.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "tone_weight": {"motivational": 0.9, "comedy": 0.6, "directness": 1.0},
            "ui_preferences": {"personality_toggle": 0.5, "show_memory_tags": True, "show_latency_monitor": True}
        }

preferences = load_preferences()

# Create tabs for different sections
tab1, tab2, tab3 = st.tabs(["💬 Chat", "🧠 Memory Analysis", "⚙️ Settings"])

# Chat Tab
with tab1:
    # Sidebar for chat controls
    with st.sidebar:
        st.header("💬 Chat Controls")
        memory_count = get_memory_stats()
        st.metric("📊 Total Messages", memory_count)
        
        # Memory toggle
        use_memory = st.checkbox("Use Memory Context", value=True, help="Enable/disable memory retrieval")
        
        # Personality toggle
        personality_toggle = st.slider("Personality", 0.0, 1.0, preferences["ui_preferences"]["personality_toggle"], 
                                     help="0 = Strict, 0.5 = Balanced, 1 = Playful")
        
        # Show current sentiment
        if "last_sentiment" in st.session_state:
            st.info(f"Detected mood: {st.session_state.last_sentiment}")
        
        # Memory management buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear All Memory", type="secondary"):
                st.session_state.show_clear_password = True
        
        with col2:
            if st.button("🧹 Compact Memory"):
                with st.spinner("Compacting memory..."):
                    summarize_and_compact()
                st.success("Memory compacted!")
        
        # Password verification for memory clearing
        if st.session_state.get('show_clear_password', False):
            st.warning("⚠️ Password required to clear all memory")
            password = st.text_input("Enter password:", type="password", key="clear_password")
            col_pwd1, col_pwd2 = st.columns(2)
            with col_pwd1:
                if st.button("✅ Confirm Clear", key="confirm_clear_pwd"):
                    if password == "md07":  # Set your desired password here
                        with st.spinner("Clearing all memory..."):
                            if clear_all_memory():
                                st.success("All memory cleared!")
                                st.session_state.messages = []  # Clear session too
                                st.session_state.show_clear_password = False
                                st.rerun()
                            else:
                                st.error("Failed to clear memory")
                    else:
                        st.error("❌ Incorrect password!")
            with col_pwd2:
                if st.button("❌ Cancel", key="cancel_clear"):
                    st.session_state.show_clear_password = False
                    st.rerun()
        
        # Show pinned messages count
        pinned_count = len(get_pinned_messages())
        if pinned_count > 0:
            st.info(f"📌 {pinned_count} pinned messages")
        
    # Chat interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Session state for chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat history
        for chat in st.session_state.messages:
            with st.chat_message(chat["role"]):
                st.markdown(chat["content"])

        # Helper: parse commands
        def handle_command(cmd: str) -> bool:
            lc = cmd.strip()
            if lc.lower().startswith("friday: pin "):
                note = lc[len("friday: pin "):].strip()
                # pin the last assistant message
                messages = get_all_messages(limit=50)
                candidates = [m for m in messages if m['role'] == 'assistant']
                if candidates:
                    last = candidates[-1]
                    if pin_message(last['id'], note):
                        st.success("Pinned last assistant message.")
                    else:
                        st.error("Failed to pin.")
                else:
                    st.info("No assistant messages found to pin.")
                return True
            if lc.lower().startswith("friday: forget "):
                text = lc[len("friday: forget "):].strip()
                deleted = forget_by_text(text, top_k=5)
                st.success(f"Forgot {deleted} similar memories.")
                return True
            if lc.lower().startswith("friday: goals"):
                goals = list_working_goals()
                if goals:
                    st.info("Working goals:\n- " + "\n- ".join(goals))
                else:
                    st.info("No working goals yet. State a new goal to track it.")
                return True
            return False

        # Chat input
        if prompt := st.chat_input("Type your message or commands like 'FRIDAY: pin <note>', 'FRIDAY: forget <text>', 'FRIDAY: goals' ..."):
            # Command handling
            if handle_command(prompt):
                st.session_state.messages.append({"role": "system", "content": f"[Handled command: {prompt}]"})
            else:
                # Add user message to session
                st.session_state.messages.append({"role": "user", "content": prompt})

                with st.chat_message("user"):
                    st.markdown(prompt)

                # Get response from Ollama with memory context
                with st.chat_message("assistant"):
                    start_time = time.time()
                    
                    with st.spinner("Thinking..."):
                        # Detect sentiment and store in session
                        sentiment = detect_sentiment(prompt)
                        st.session_state.last_sentiment = sentiment

                        # Heuristic: treat explicit goals and push to working memory
                        if re.search(r"\b(my goal|new goal|objective|plan to|i want to)\b", prompt, re.I):
                            push_working_goal(prompt)
                        
                        if use_memory:
                            # Retrieve relevant past context (limit to 2-3 items)
                            memories = retrieve_memory(prompt, top_k=2)
                            context_lines = [f"{m['role']}: {m['content']}" for m in memories]
                            # Include working goals in context
                            goals = list_working_goals()
                            if goals:
                                context_lines.append("Working goals: " + "; ".join(goals))
                            context_block = "\n".join(context_lines) if context_lines else "—"
                        else:
                            context_block = "—"
                        
                        # Generate adaptive prompt based on sentiment and personality
                        persona_config = load_persona_config(root_path=ROOT_PATH)
                        base_prompt = generate_adaptive_prompt(prompt, persona_config)
                        
                        # Adjust based on personality toggle
                        if personality_toggle > 0.7:
                            base_prompt += "\n- Add more humor and casual tone"
                        elif personality_toggle < 0.3:
                            base_prompt += "\n- Be more direct and professional"
                        
                        # Build final prompt
                        final_prompt = f"""{base_prompt}

Relevant memory:
{context_block}

Team (Exynos Thinkers): {prompt}
Assistant:"""
                        
                        # Stream the response for better UX
                        placeholder = st.empty()
                        buf = []
                        for tok in stream_ollama(final_prompt):
                            buf.append(tok)
                            placeholder.markdown("".join(buf))
                        response = "".join(buf)
                        
                        # Calculate and display latency
                        latency = time.time() - start_time
                        if preferences["ui_preferences"]["show_latency_monitor"]:
                            st.caption(f"Response time: {latency:.2f}s")

                # Save both messages to persistent memory (filtered)
                save_message("user", prompt)
                save_message("assistant", response)
                
                # Periodic memory compaction (every 20 messages)
                memory_count = get_memory_stats()
                if memory_count > 0 and memory_count % 20 == 0:
                    summarize_and_compact()
                
                # Save response to session
                st.session_state.messages.append({"role": "assistant", "content": response})
    
    with col2:
        st.header("📈 Quick Stats")
        st.metric("Session Messages", len(st.session_state.messages))
        if use_memory:
            st.success("✅ Memory Enabled")
        else:
            st.warning("⚠️ Memory Disabled")

# Memory Analysis Tab
with tab2:
    st.header("🧠 Memory Analysis Panel")
    
    # Memory overview
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        memory_count = get_memory_stats()
        st.metric("📊 Total Messages", memory_count)
    
    with col2:
        if memory_count > 0:
            messages = get_all_messages(limit=100)
            user_count = len([m for m in messages if m['role'] == 'user'])
            assistant_count = len([m for m in messages if m['role'] == 'assistant'])
            st.metric("👤 User Messages", user_count)
        else:
            st.metric("👤 User Messages", 0)
    
    with col3:
        if memory_count > 0:
            st.metric("🤖 Assistant Messages", assistant_count)
        else:
            st.metric("🤖 Assistant Messages", 0)
    
    with col4:
        pinned_count = len(get_pinned_messages())
        st.metric("📌 Pinned Messages", pinned_count)
    
    # Memory inspection controls
    st.subheader("🔍 Memory Inspection")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        limit = st.slider("Number of messages to show", 5, 50, 10)
        role_filter = st.selectbox("Filter by role", ["All", "user", "assistant"])
    
    with col2:
        if st.button("🔄 Refresh Memory"):
            st.rerun()
    
    # Display memory contents
    if memory_count > 0:
        messages = get_all_messages(limit=limit)
        
        # Apply role filter
        if role_filter != "All":
            messages = [m for m in messages if m['role'] == role_filter]
        
        st.subheader(f"📝 Recent Messages ({len(messages)} shown)")
        
        for i, msg in enumerate(messages, 1):
            with st.expander(f"#{i} {msg['role'].upper()}: {msg['content'][:60]}...", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write("**Content:**")
                    st.text_area("Message Content", msg['content'], height=100, key=f"content_{i}", disabled=True, label_visibility="collapsed")
                
                with col2:
                    st.write("**Metadata:")
                    timestamp = datetime.datetime.fromtimestamp(msg['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                    st.write(f"**Time:** {timestamp}")
                    st.write(f"**Role:** {msg['role']}")
                    st.write(f"**ID:** {msg['id']}")
                    
                    # Check if message is pinned
                    is_pinned = msg.get('pinned', False)
                    if is_pinned:
                        st.success("📌 PINNED")
                        if msg.get('pin_note'):
                            st.write(f"**Note:** {msg['pin_note']}")
                    
                    # Action buttons
                    col_actions1, col_actions2 = st.columns(2)
                    with col_actions1:
                        if not is_pinned:
                            if st.button(f"📌 Pin", key=f"pin_{i}"):
                                pin_note = st.text_input(f"Pin note for message {i}:", key=f"pin_note_{i}")
                                if pin_message(msg['id'], pin_note):
                                    st.success("Message pinned!")
                                    st.rerun()
                        else:
                            if st.button(f"📌 Unpin", key=f"unpin_{i}"):
                                if unpin_message(msg['id']):
                                    st.success("Message unpinned!")
                                    st.rerun()
                    
                    with col_actions2:
                        if st.button(f"🗑️ Delete", key=f"delete_{i}", type="secondary"):
                            if delete_message_by_id(msg['id']):
                                st.success("Message deleted!")
                                st.rerun()
                    
                    # Test similarity search
                    if st.button(f"🔍 Test Similarity", key=f"similar_{i}"):
                        similar = retrieve_memory(msg['content'], top_k=3)
                        st.write("**Similar messages:**")
                        for j, sim_msg in enumerate(similar, 1):
                            st.write(f"{j}. {sim_msg[:100]}...")
    else:
        st.info("No messages stored in memory yet. Start chatting to see memory in action!")
    
    # Pinned Messages Section
    st.subheader("📌 Pinned Messages")
    pinned_messages = get_pinned_messages()
    
    if pinned_messages:
        for i, msg in enumerate(pinned_messages, 1):
            with st.expander(f"📌 #{i} {msg['role'].upper()}: {msg['content'][:60]}...", expanded=True):
                st.write("**Content:**")
                st.text_area("Pinned Content", msg['content'], height=100, key=f"pinned_content_{i}", disabled=True, label_visibility="collapsed")
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    timestamp = datetime.datetime.fromtimestamp(msg['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                    st.write(f"**Time:** {timestamp}")
                    st.write(f"**Role:** {msg['role']}")
                    if msg.get('pin_note'):
                        st.write(f"**Pin Note:** {msg['pin_note']}")
                
                with col2:
                    if st.button(f"📌 Unpin", key=f"unpin_pinned_{i}"):
                        if unpin_message(msg['id']):
                            st.success("Message unpinned!")
                            st.rerun()
                    
                    if st.button(f"🗑️ Delete", key=f"delete_pinned_{i}", type="secondary"):
                        if delete_message_by_id(msg['id']):
                            st.success("Message deleted!")
                            st.rerun()
    else:
        st.info("No pinned messages yet. Pin important messages to keep them easily accessible!")

# Settings Tab
with tab3:
    st.header("⚙️ FRIDAY Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎭 Personality Preferences")
        
        # Tone weights
        st.write("**Tone Weights:**")
        motivational_weight = st.slider("Motivational", 0.0, 1.0, preferences["tone_weight"]["motivational"])
        comedy_weight = st.slider("Comedy", 0.0, 1.0, preferences["tone_weight"]["comedy"])
        directness_weight = st.slider("Directness", 0.0, 1.0, preferences["tone_weight"]["directness"])
        
        # UI preferences
        st.subheader("🖥️ UI Preferences")
        show_tags = st.checkbox("Show Memory Tags", preferences["ui_preferences"]["show_memory_tags"])
        show_latency = st.checkbox("Show Latency Monitor", preferences["ui_preferences"]["show_latency_monitor"])
    
    with col2:
        st.subheader("🧠 Memory Settings")
        
        # Memory retention settings
        short_term = st.number_input("Short-term Memory (messages)", 5, 50, preferences.get("memory_retention", {}).get("short_term", 10))
        summary_interval = st.number_input("Summary Interval", 10, 50, preferences.get("memory_retention", {}).get("long_term_summary_interval", 20))
        max_context = st.number_input("Max Context Messages", 1, 10, preferences.get("memory_retention", {}).get("max_context_messages", 3))
        
        # Save preferences button
        if st.button("💾 Save Preferences"):
            new_preferences = {
                "tone_weight": {
                    "motivational": motivational_weight,
                    "comedy": comedy_weight,
                    "directness": directness_weight
                },
                "memory_retention": {
                    "short_term": short_term,
                    "long_term_summary_interval": summary_interval,
                    "max_context_messages": max_context
                },
                "ui_preferences": {
                    "personality_toggle": personality_toggle,
                    "show_memory_tags": show_tags,
                    "show_latency_monitor": show_latency
                }
            }
            
            with open(ROOT_PATH / 'preferences.json', 'w') as f:
                json.dump(new_preferences, f, indent=2)
            
            st.success("Preferences saved!")
            st.rerun()
    
    # Show current configuration
    st.subheader("📋 Current Configuration")
    config = load_persona_config(root_path=ROOT_PATH)
    st.json(config)


