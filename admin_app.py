import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from supabase import create_client
import datetime

# --- 1. CONNECT TO SUPABASE USING CLOUD SECRETS ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 2. CONNECT TO GOOGLE SHEETS USING CLOUD SECRETS ---
@st.cache_data(ttl=10)
def load_questions():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    # This reads your Google VIP pass directly from Streamlit's secure vault!
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    gc = gspread.authorize(creds)
    
    sheet = gc.open("Symposium_Quiz_Bank").sheet1
    return sheet.get_all_records()

# --- 3. BUILD THE DASHBOARD UI ---
st.set_page_config(page_title="Quizmaster Control", page_icon="🎤")
st.title("🎤 Symposium Quizmaster Control")
st.write("Cloud Remote Control active. Select a question to broadcast to the hall.")
st.divider()

try:
    questions_data = load_questions()
except Exception as e:
    st.error(f"Could not connect to Google Sheets. Error: {e}")
    st.stop()

question_options = { 
    f"Q{row['q_id']} - {row['phase']}: {row['question_text'][:40]}...": row 
    for row in questions_data if str(row.get('q_id')).isdigit() 
}

selected_q_label = st.selectbox("Select Question to Launch:", list(question_options.keys()))
selected_q_data = question_options[selected_q_label]

st.info(f"**Preview:** {selected_q_data['question_text']}")

col1, col2 = st.columns(2)

with col1:
    if st.button("🚀 LAUNCH TO AUDIENCE", type="primary", use_container_width=True):
        current_time = datetime.datetime.utcnow().isoformat()
        
        supabase.table("quiz_state").update({
            "active_q_id": int(selected_q_data['q_id']),
            "is_live": True,
            "start_timestamp": current_time,
            "question_text": selected_q_data['question_text'],
            "opt_a": selected_q_data['opt_a'],
            "opt_b": selected_q_data['opt_b'],
            "opt_c": selected_q_data['opt_c'],
            "opt_d": selected_q_data['opt_d'],
            "correct_opt": selected_q_data['correct_opt']
        }).eq("id", 1).execute()
        
        st.success(f"Question {selected_q_data['q_id']} is LIVE! Timers have started.")

with col2:
    if st.button("🛑 END QUESTION NOW", use_container_width=True):
        supabase.table("quiz_state").update({"is_live": False}).eq("id", 1).execute()
        st.warning("Question ended manually. Audience screens are locked.")