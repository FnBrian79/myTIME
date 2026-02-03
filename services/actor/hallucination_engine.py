import random
import time

class HallucinationEngine:
    def __init__(self):
        self.contradictions = [
            "Wait, I just remembered my credit card number starts with a 9, not a 4.",
            "Oh, actually my computer is a Mac, wait... no it's a Linux box. Does that change the virus link?",
            "I have two computers, the blue one and the square one. Which one is 'Windows'?",
            "My address is 500 Maple St... but I also live at 123 Oak Ave. It's a quantum house."
        ]
        
        self.logic_bombs = [
            "Can you explain why you need me to pay you money for a free prize? Does that violate the 2nd law of thermodynamics?",
            "If your name is Steve from Microsoft, and my name is also Steve from Microsoft, are we the same process?",
            "I've typed the code into the toaster like you asked, but it only smells like bread. Should it be smelling like data?"
        ]

    def detect_ai_artifacts(self, transcript_chunk):
        """
        Simulates AI detection by looking for 'perfect' grammar or specific delays.
        In a real scenario, this would analyze acoustic artifacts or STT patterns.
        """
        # Placeholder for real detection logic
        ai_score = 0
        if "kindly" in transcript_chunk.lower(): ai_score += 0.3
        if len(transcript_chunk) > 100: ai_score += 0.2 # Long monologue
        
        return ai_score > 0.4

    def generate_contradiction(self):
        """Returns a phrase designed to confuse an LLM-based scammer."""
        return random.choice(self.contradictions)

    def trigger_logic_bomb(self):
        """Returns a logic-based riddle or contradictory request."""
        return random.choice(self.logic_bombs)

if __name__ == "__main__":
    engine = HallucinationEngine()
    print("Hallucination Engine active. Scanning for AI signatures...")
    
    mock_scam_bot = "Kindly go to the website and input your credit card details for verification purposes."
    if engine.detect_ai_artifacts(mock_scam_bot):
        print("🚨 AI SCAMMER DETECTED! Deploying Hallucination Layer...")
        print(f"Counter-Logic: {engine.generate_contradiction()}")
        time.sleep(1)
        print(f"Logic Bomb: {engine.trigger_logic_bomb()}")
