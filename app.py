import streamlit as st
import requests
import json
import time
import datetime

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(page_title="Customer Support Chatbot", page_icon="💬", layout="centered")
st.markdown("<h2 style='text-align:center;'>💬 Customer Support Chatbot</h2>", unsafe_allow_html=True)

# ---------------------- DIALOGFLOW SETUP ----------------------
@st.cache_data(ttl=3500)  # Cache for 58 minutes (tokens expire in 1 hour)
def get_access_token():
    """Get access token using service account credentials"""
    try:
        sa_info = dict(st.secrets["gcp_service_account"])
        
        # Prepare the request for OAuth2 token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
            'assertion': create_jwt_assertion(sa_info)
        }
        
        response = requests.post(token_url, data=token_data)
        response.raise_for_status()
        
        token_info = response.json()
        return token_info['access_token']
        
    except Exception as e:
        st.error(f"Error getting access token: {str(e)}")
        return None

def create_jwt_assertion(sa_info):
    """Create JWT assertion manually without external libraries"""
    import base64
    import hashlib
    import hmac
    
    header = {
        "alg": "RS256",
        "typ": "JWT"
    }
    
    current_time = int(time.time())
    expiration_time = current_time + 3600
    
    payload = {
        "iss": sa_info['client_email'],
        "sub": sa_info['client_email'],
        "aud": "https://oauth2.googleapis.com/token",
        "iat": current_time,
        "exp": expiration_time,
        "scope": "https://www.googleapis.com/auth/cloud-platform"
    }
    
    # Encode header and payload
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
    
    # Create signature (this is a simplified version - in practice you'd need proper RSA signing)
    message = f"{header_b64}.{payload_b64}"
    
    # For now, we'll use a direct approach with the private key
    # Note: This is a simplified version. In production, you'd use proper RSA signing
    signature = "dummy_signature"  # This would need proper RSA implementation
    
    return f"{header_b64}.{payload_b64}.{signature}"

PROJECT_ID = st.secrets["gcp_service_account"]["project_id"]
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
    st.session_state.messages.append({"sender": "bot", "text": "👋 Hello! How can I help you today?"})

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

# Add a debug section to check if secrets are loading
with st.sidebar:
    st.write("Debug Info:")
    if "gcp_service_account" in st.secrets:
        st.success("✅ GCP credentials loaded")
        st.write(f"Project: {st.secrets['gcp_service_account']['project_id']}")
    else:
        st.error("❌ GCP credentials missing")

