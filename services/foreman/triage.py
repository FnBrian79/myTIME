from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# The Blacklist/Learning Repo connection
DATABASE_URL = os.environ.get("LEARNING_REPO_URL", "http://learning-repo:5000/check-number")

@app.route('/health')
def health():
    """Health check endpoint for service monitoring."""
    return jsonify({
        "status": "active",
        "service": "foreman",
        "mode": "Sovereign",
        "integrity": "verified"
    })

@app.route('/triage', methods=['POST'])
def triage_call():
    incoming_number = request.json.get('number')
    if not incoming_number:
        return jsonify({"error": "No number provided"}), 400
    
    # Check if number is in the Learning Repo or known blacklist
    try:
        response = requests.post(DATABASE_URL, json={"number": incoming_number}, timeout=2)
        status = response.json()
    except Exception as e:
        print(f"Fallback: Database offline ({e})")
        status = {'is_scam': False}
    
    if status.get('is_scam'):
        # Returns a 'Combat' flag to your phone (via Tasker/Termux)
        return jsonify({
            "action": "COMBAT_RING", 
            "multiplier": "5x",
            "persona_suggestion": "Hazel"
        })
    
    return jsonify({"action": "DEFAULT_RING", "multiplier": "1x"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
