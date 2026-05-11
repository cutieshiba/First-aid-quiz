import streamlit as st
import pandas as pd
import re
import io
import urllib.request
import random

# ==================== CONFIGURATION ====================
st.set_page_config(page_title="First Aid Quiz", page_icon="🚑")

YOUR_SHEET_URL = "https://docs.google.com/spreadsheets/d/1V9Xz1p4XDr4F21QubQ2aKJ0iY9I-ue7GEpDFviVye3k/edit?gid=285802447#gid=285802447"

# ==================== FUNCTIONS ====================

def get_csv_export_url(sheet_url):
    """Convert Google Sheets URL to CSV export URL"""
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', sheet_url)
    if not match: return None
    sheet_id = match.group(1)
    gid_match = re.search(r'gid=(\d+)', sheet_url)
    gid = gid_match.group(1) if gid_match else '0'
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

@st.cache_data # This prevents re-downloading the sheet every time you click a button
def load_data(url):
    csv_url = get_csv_export_url(url)
    with urllib.request.urlopen(csv_url) as response:
        csv_data = response.read().decode('utf-8')
    return pd.read_csv(io.StringIO(csv_data))

# ==================== SESSION STATE (The Brain) ====================
if 'quiz_started' not in st.session_state:
    st.session_state.quiz_started = False
    st.session_state.current_index = 0
    st.session_state.score = 0
    st.session_state.questions = []
    st.session_state.answered = False
    st.session_state.feedback = None

# ==================== UI: MAIN MENU ====================
if not st.session_state.quiz_started:
    st.markdown("""
        <div style="background: linear-gradient(135deg, #1e3c72 0%, #2b4c7c 100%); color: white; padding: 25px; border-radius: 15px; text-align: center;">
            <h1>🚑 FIRST AID QUIZ</h1>
            <p>Instant Feedback - Learn as you go!</p>
        </div>
        """, unsafe_allow_html=True)

    try:
        df = load_data(YOUR_SHEET_URL)
        st.success(f"📚 {len(df)} Questions available!")
        
        mode = st.selectbox("Select Mode:", ["Random Quiz (10 questions)", "Full Exam", "Custom Number"])
        
        num_q = 10
        if mode == "Custom Number":
            num_q = st.number_input("How many questions?", min_value=1, max_value=len(df), value=10)
        elif mode == "Full Exam":
            num_q = len(df)

        if st.button("▶ START QUIZ", use_container_width=True):
            # Prep questions
            questions_pool = df.to_dict('records')
            if "Random" in mode or mode == "Custom Number":
                st.session_state.questions = random.sample(questions_pool, min(num_q, len(questions_pool)))
            else:
                st.session_state.questions = questions_pool
            
            st.session_state.quiz_started = True
            st.rerun()

    except Exception as e:
        st.error(f"Error loading sheet: {e}")
        st.info("Make sure your Google Sheet is set to 'Anyone with the link can view'")

# ==================== UI: QUIZ MODE ====================
else:
    q_list = st.session_state.questions
    idx = st.session_state.current_index

    if idx < len(q_list):
        q = q_list[idx]
        
        # Progress bar
        st.progress((idx) / len(q_list))
        st.write(f"**Question {idx + 1} of {len(q_list)}**")

        # Display Question
        st.markdown(f"""
            <div style="background: #f0f8ff; padding: 20px; border-radius: 12px; border-left: 5px solid #2196F3; margin-bottom: 20px;">
                <div style="font-size: 18px; color: #1e3c72;"><b>{q['Question Text']}</b></div>
            </div>
            """, unsafe_allow_html=True)

        # Options
        opts = {
            f"A. {q['Option A']}": "A",
            f"B. {q['Option B']}": "B",
            f"C. {q['Option C']}": "C",
            f"D. {q['Option D']}": "D"
        }
        
        # Use a radio button for selection
        user_choice = st.radio("Select your answer:", list(opts.keys()), index=None)

        col1, col2 = st.columns(2)

        # CHECK ANSWER BUTTON
        if col1.button("✓ CHECK ANSWER", disabled=st.session_state.answered, use_container_width=True):
            if user_choice:
                st.session_state.answered = True
                selected_letter = opts[user_choice]
                correct_letter = str(q['Correct Answer']).strip()
                
                if selected_letter == correct_letter:
                    st.session_state.score += 1
                    st.session_state.feedback = ("success", "✅ CORRECT! Great job!")
                else:
                    correct_text = q[f'Option {correct_letter}']
                    st.session_state.feedback = ("error", f"❌ INCORRECT. The correct answer was **{correct_letter}: {correct_text}**")
            else:
                st.warning("Please select an answer first!")

        # Show Feedback
        if st.session_state.feedback:
            type, msg = st.session_state.feedback
            if type == "success": st.success(msg)
            else: st.error(msg)

        # NEXT BUTTON
        if col2.button("➡ NEXT QUESTION", disabled=not st.session_state.answered, use_container_width=True):
            st.session_state.current_index += 1
            st.session_state.answered = False
            st.session_state.feedback = None
            st.rerun()

    # ==================== UI: RESULTS ====================
    else:
        score = st.session_state.score
        total = len(q_list)
        percent = (score / total) * 100
        
        st.balloons()
        st.markdown(f"""
            <div style="background: #764ba2; padding: 30px; border-radius: 15px; color: white; text-align: center;">
                <h2>Quiz Complete!</h2>
                <h1 style="font-size: 60px;">{score} / {total}</h1>
                <h3>{percent:.1f}%</h3>
            </div>
            """, unsafe_allow_html=True)
        
        if st.button("🔄 Restart Quiz"):
            st.session_state.quiz_started = False
            st.session_state.current_index = 0
            st.session_state.score = 0
            st.rerun()