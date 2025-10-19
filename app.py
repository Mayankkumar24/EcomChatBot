import streamlit as st
import requests
import json
import time
import jwt
import datetime

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(page_title="Customer Support Chatbot", page_icon="💬", layout="centered")
st.markdown("<h2 style='text-align:center;'>💬 Customer Support Chatbot</h2>", unsafe_allow_html=True)

# ---------------------- DIALOGFLOW SETUP ----------------------
@st.cache_resource
def generate_jwt():
    try:
        # Get service account info from secrets
        sa_info = dict(st.secrets["gcp_service_account"])
        
        # Create JWT token
        current_time = datetime.datetime.utcnow()
        expiration_time = current_time + datetime.timedelta(hours=1)
        
        payload = {
            'iss': sa_info['client_email'],
            'sub': sa_info['client_email'],
            'aud': 'https://dialogflow.googleapis.com/',
            'iat': current_time,
            'exp': expiration_time,
            'scope': 'https://www.googleapis.com/auth/cloud-platform'
        }
        
        # Create JWT token
        token = jwt.encode(
            payload,
            sa_info['private_key'],
            algorithm='RS256'
        )
        
        return token
        
    except Exception as e:
        st.error(f"Error generating JWT: {str(e)}")
        return None

def get_access_token():
    """Get access token using JWT"""
    try:
        jwt_token = generate_jwt()
        if not jwt_token:
            return None
            
        # Exchange JWT for access token
        response = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
                'assertion': jwt_token
            }
        )
        response.raise_for_status()
        
        token_data = response.json()
        return token_data['access_token']
        
    except Exception as e:
        st.error(f"Error getting access token: {str(e)}")
        return None

PROJECT_ID = st.secrets["gcp_service_account"]["plucky-shore-475210-n7"]
SESSION_ID = "user123"
LANGUAGE_CODE = "en"

def get_response(text):
    """Send user input to Dialogflow using REST API"""
    try:
        access_token = get_access_token()
        if not access_token:
            return "Sorry, authentication failed. Please check your credentials."
        
        url = f"https://dialogflow.googleapis.com/v2/projects/{plucky-shore-475210-n7}/agent/sessions/{SESSION_ID}:detectIntent"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "queryInput": {
                "text": {
                    "text": text,
                    "languageCode": LANGUAGE_CODE
                }
            }
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        return result['queryResult']['fulfillmentText']
        
    except requests.exceptions.RequestException as e:
        st.error(f"Network error: {str(e)}")
        return "Sorry, I'm having trouble connecting to the service."
    except Exception as e:
        st.error(f"Error getting response: {str(e)}")
        return "Sorry, I encountered an error. Please try again."

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
    st.session_state.messages.append({"sender": "user", "text": user_input})
    bot_response = get_response(user_input)
    st.session_state.messages.append({"sender": "bot", "text": bot_response})
    st.rerun()
