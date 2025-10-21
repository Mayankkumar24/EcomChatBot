import os
import json
from flask import Flask, request, render_template, jsonify
from google.oauth2 import service_account
from google.cloud import dialogflow_v2 as dialogflow

app = Flask(__name__, static_folder="static", template_folder="templates")

# ------------------ Dialogflow client init ------------------
def init_dialogflow_client():
    """Initialize Dialogflow client using JSON from env var GCP_SERVICE_ACCOUNT_JSON."""
    gcp_json = os.environ.get("GCP_SERVICE_ACCOUNT_JSON")
    if not gcp_json:
        raise RuntimeError("GCP_SERVICE_ACCOUNT_JSON env var missing. Add service account JSON in Render environment variables.")
    try:
        creds_info = json.loads(gcp_json)
    except Exception as e:
        raise RuntimeError("Failed to parse GCP_SERVICE_ACCOUNT_JSON: " + str(e))

    credentials = service_account.Credentials.from_service_account_info(creds_info)
    client = dialogflow.SessionsClient(credentials=credentials)
    project_id = creds_info.get("project_id")
    if not project_id:
        raise RuntimeError("project_id not found in service account JSON.")
    return client, project_id

# Initialize once at startup
try:
    session_client, PROJECT_ID = init_dialogflow_client()
except Exception as e:
    # Keep app up but flag error on endpoints
    session_client = None
    PROJECT_ID = None
    init_error = str(e)
else:
    init_error = None

@app.route("/")
def index():
    if init_error:
        # show warning in UI if init failed
        return render_template("index.html", init_error=init_error)
    return render_template("index.html", init_error=None)

@app.route("/api/chat", methods=["POST"])
def chat():
    """POST JSON: { "text": "user message", "session_id": "optional" }"""
    if session_client is None:
        return jsonify({"error": "Dialogflow client not initialized", "detail": init_error}), 500

    data = request.get_json(force=True)
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400
    session_id = data.get("session_id", "web-session-1")

    # Build session path and request
    session = session_client.session_path(PROJECT_ID, session_id)
    text_input = dialogflow.TextInput(text=text, language_code="en")
    query_input = dialogflow.QueryInput(text=text_input)

    try:
        response = session_client.detect_intent(request={"session": session, "query_input": query_input})
        reply = response.query_result.fulfillment_text
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": "Dialogflow detect_intent failed", "detail": str(e)}), 500

# Health check
@app.route("/health")
def health():
    if session_client is None:
        return ("Dialogflow not initialized: " + (init_error or "unknown"), 500)
    return ("ok", 200)

if __name__ == "__main__":
    # Local dev: ensure env var exists or read local file
    if os.environ.get("FLASK_ENV") == "development" and not os.environ.get("GCP_SERVICE_ACCOUNT_JSON"):
        # optional: try to load local file named gcp_key.json if present (dev convenience only)
        if os.path.exists("gcp_key.json"):
            with open("gcp_key.json", "r") as f:
                os.environ["GCP_SERVICE_ACCOUNT_JSON"] = f.read()
            # reinitialize
            session_client, PROJECT_ID = init_dialogflow_client()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
