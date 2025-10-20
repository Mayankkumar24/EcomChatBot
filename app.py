import os
import streamlit as st
import dialogflow
from google.oauth2 import service_account
from google.api_core.exceptions import InvalidArgument
import json



# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(page_title="Customer Support Chatbot", page_icon="💬", layout="centered")
st.markdown("<h2 style='text-align:center;'>💬 Customer Support Chatbot</h2>", unsafe_allow_html=True)

# Load service account from environment variable and write to file
gcp_json = os.environ.get("GCP_SERVICE_ACCOUNT_JSON")
if gcp_json:
    with open("gcp_key.json", "w") as f:
        f.write(gcp_json)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_key.json"
else:
    st.warning("GCP_SERVICE_ACCOUNT_JSON not found in environment — Dialogflow won't work.")


# ---------------------- DIALOGFLOW SETUP ----------------------
@st.cache_data(show_spinner=False)
def get_session_client():
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    return dialogflow.SessionsClient(credentials=credentials)

session_client = get_session_client()

PROJECT_ID = st.secrets["gcp_service_account"]["project_id"]
SESSION_ID = "user123"
LANGUAGE_CODE = "en"

session = session_client.session_path(PROJECT_ID, SESSION_ID)


def get_response(text):
    """Send user input to Dialogflow and return bot's response"""
    text_input = dialogflow.TextInput(text=text, language_code=LANGUAGE_CODE)
    query_input = dialogflow.QueryInput(text=text_input)
    response = session_client.detect_intent(
        request={"session": session, "query_input": query_input}
    )
    return response.query_result.fulfillment_text


# ---------------------- CUSTOM CSS ----------------------
st.markdown("""
<style>
.chat-container {
    max-height: 450px;
    overflow-y: auto;
    background-color: #f7f9fb;
    padding: 10px;
    border-radius: 15px;
    border: 1px solid #ddd;
}
.user-msg {
    background-color: #DCF8C6;
    color: #000;
    padding: 8px 12px;
    border-radius: 15px;
    margin: 8px 0;
    text-align: right;
    margin-left: 30%;
}
.bot-msg {
    background-color: #E6E6E6;
    color: #000;
    padding: 8px 12px;
    border-radius: 15px;
    margin: 8px 0;
    text-align: left;
    margin-right: 30%;
}
</style>
""", unsafe_allow_html=True)

# ---------------------- SESSION STATE ----------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Greeting message
    st.session_state.messages.append({"sender": "bot", "text": "👋 Hello Sir/Ma'am! How can I help you today?"})

# ---------------------- DISPLAY CHAT ----------------------
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
for msg in st.session_state.messages:
    if msg["sender"] == "user":
        st.markdown(f"<div class='user-msg'>{msg['text']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='bot-msg'>{msg['text']}</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ---------------------- USER INPUT ----------------------
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input("Type your message:", "")
    submit_button = st.form_submit_button("Send")

if submit_button and user_input.strip():
    # Add user message
    st.session_state.messages.append({"sender": "user", "text": user_input})

    # Get bot response from Dialogflow
    bot_response = get_response(user_input)
    st.session_state.messages.append({"sender": "bot", "text": bot_response})

    # Refresh the chat display
    st.experimental_rerun()
st.write("✅ Google Dialogflow imported successfully!")








