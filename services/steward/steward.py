import os
import sqlite3
import time
from datetime import datetime

class Steward:
    def __init__(self, db_path="/data/vault/steward.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                credits INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                total_time_wasted INTEGER DEFAULT 0
            )
        ''')
        
        # Calls/Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS call_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                duration_seconds INTEGER,
                scam_type TEXT,
                is_unique BOOLEAN,
                credits_earned INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def calculate_credits(self, duration_seconds, is_unique=False, ai_on_ai=False):
        # Base: 10 credits per minute
        base_credits = (duration_seconds // 60) * 10
        
        # Multipliers
        multiplier = 1.0
        if is_unique:
            multiplier += 2.0  # 3x for new/unique scams
        if ai_on_ai:
            multiplier += 1.5  # 2.5x for AI detection/combat
            
        return int(base_credits * multiplier)

    def log_call(self, user_id, session_id, duration_seconds, scam_type="unknown", is_unique=False, ai_on_ai=False):
        credits_earned = self.calculate_credits(duration_seconds, is_unique, ai_on_ai)
        xp_earned = duration_seconds // 10 # 1 XP per 10 seconds
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update or create user
        cursor.execute('''
            INSERT INTO users (user_id, credits, xp, total_time_wasted)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                credits = credits + ?,
                xp = xp + ?,
                total_time_wasted = total_time_wasted + ?
        ''', (user_id, credits_earned, xp_earned, duration_seconds, credits_earned, xp_earned, duration_seconds))
        
        # Handle leveling up (Level = sqrt(XP/100) + 1 approx)
        cursor.execute('SELECT xp FROM users WHERE user_id = ?', (user_id,))
        xp = cursor.fetchone()[0]
        new_level = int((xp / 100) ** 0.5) + 1
        cursor.execute('UPDATE users SET level = ? WHERE user_id = ?', (new_level, user_id))
        
        # Log session
        cursor.execute('''
            INSERT INTO call_sessions (session_id, user_id, start_time, end_time, duration_seconds, scam_type, is_unique, credits_earned)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (session_id, user_id, datetime.now(), datetime.now(), duration_seconds, scam_type, is_unique, credits_earned))
        
        conn.commit()
        conn.close()
        return credits_earned, new_level

    def get_leaderboard(self, limit=10):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, level, credits, total_time_wasted FROM users ORDER BY total_time_wasted DESC LIMIT ?', (limit,))
        results = cursor.fetchall()
        conn.close()
        return results

if __name__ == "__main__":
    # Example usage / Test
    steward = Steward()
    print("Steward initialized. Game logic ready.")
    
    # Simulate a call
    uid = "Brian_Sovereign"
    sid = f"call_{int(time.time())}"
    earned, level = steward.log_call(uid, sid, 650, "PCH_Scam", is_unique=True)
    print(f"Logged call for {uid}: Earned {earned} credits, Level {level}")
    
    # Show leaderboard
    print("\n--- SOVEREIGN SENTINEL LEADERBOARD ---")
    for row in steward.get_leaderboard():
        print(f"User: {row[0]} | Level: {row[1]} | Credits: {row[2]} | Time Wasted: {row[3]//60}m")
