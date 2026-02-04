from flask import Flask, jsonify, send_from_directory
import sqlite3
import os
import threading
from steward import Steward

app = Flask(__name__)
steward = Steward()

@app.route('/health')
def health():
    """Health check endpoint for service monitoring."""
    return jsonify({
        "status": "active",
        "service": "steward",
        "mode": "Sovereign",
        "integrity": "verified",
        "db_path": steward.db_path
    })

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

@app.route('/')
@app.route('/<path:path>')
def serve_dashboard(path='index.html'):
    return send_from_directory('dashboard', path)

if __name__ == "__main__":
    # Start the Flask API
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
