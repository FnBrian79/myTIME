from flask import Flask, jsonify, request, send_from_directory
import sqlite3
import os
import time
import threading
from steward import Steward

app = Flask(__name__)
steward = Steward()

@app.route('/api/leaderboard')
def get_leaderboard():
    results = steward.get_leaderboard()
    leaderboard = []
    for row in results:
        leaderboard.append({
            "user_id": row[0],
            "level": row[1],
            "credits": row[2],
            "total_time_wasted": row[3]
        })
    return jsonify(leaderboard)

@app.route('/api/stats/<user_id>')
def get_user_stats(user_id):
    conn = sqlite3.connect(steward.db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify({
            "user_id": row[0],
            "credits": row[1],
            "level": row[2],
            "xp": row[3],
            "total_time_wasted": row[4]
        })
    return jsonify({"error": "User not found"}), 404

@app.route('/api/log_call', methods=['POST'])
def log_call():
    """
    Called by the Dojo Bridge to score a Combat Ring session.
    Applies mode multipliers: auto=1x, handoff=2x, live=5x.

    Expected JSON:
      {
        "user_id": "Brian_Sovereign",
        "session_id": "uuid",
        "duration_seconds": 300,
        "mode": "live",
        "scam_type": "combat_ring"
      }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON payload"}), 400

    user_id = data.get("user_id", "anonymous")
    session_id = data.get("session_id", f"call_{int(time.time())}")
    duration = int(data.get("duration_seconds", 0))
    mode = data.get("mode", "auto")
    scam_type = data.get("scam_type", "unknown")

    credits_earned, new_level = steward.log_call(
        user_id=user_id,
        session_id=session_id,
        duration_seconds=duration,
        scam_type=scam_type,
        mode=mode,
    )

    return jsonify({
        "user_id": user_id,
        "credits_earned": credits_earned,
        "new_level": new_level,
        "mode": mode,
        "duration_seconds": duration,
    })

@app.route('/')
@app.route('/<path:path>')
def serve_dashboard(path='index.html'):
    return send_from_directory('dashboard', path)

if __name__ == "__main__":
    # Start the Flask API
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
