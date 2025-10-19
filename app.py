import streamlit as st
import requests
import json
from google.oauth2 import service_account
from google.auth.transport.requests import Request

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(page_title="Customer Support Chatbot", page_icon="💬", layout="centered")
st.markdown("<h2 style='text-align:center;'>💬 Customer Support Chatbot</h2>", unsafe_allow_html=True)

# ---------------------- DIALOGFLOW SETUP ----------------------
@st.cache_resource
def get_access_token():
    try:
        credentials_info = dict(st.secrets["gcp_service_account"])
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        credentials.refresh(Request())
        return credentials.token
    except Exception as e:
        st.error(f"Error getting access token: {str(e)}")
        return None

PROJECT_ID = st.secrets["gcp_service_account"]["project_id"]
SESSION_ID = "user123"
LANGUAGE_CODE = "en"

def get_response(text):
    """Send user input to Dialogflow using REST API"""
    try:
        access_token = get_access_token()
        if not access_token:
            return "Sorry, authentication failed."
        
        url = f"https://dialogflow.googleapis.com/v2/projects/{PROJECT_ID}/agent/sessions/{SESSION_ID}:detectIntent"
        
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
        
    except Exception as e:
        st.error(f"Error getting response: {str(e)}")
        return "Sorry, I encountered an error. Please try again."

# Rest of your CSS and Streamlit code remains the same...
# [Include all the CSS and Streamlit UI code from above]
