import time
import requests
import json

class GhostBuffer:
    def __init__(self, ollama_url="http://ollama:11434"):
        self.ollama_url = ollama_url
        self.buffer = []
        self.is_active = False

    def capture_transcript(self, text, speaker="Scammer"):
        """Adds a line of transcript to the buffer."""
        timestamp = time.strftime("%H:%M:%S")
        entry = f"[{timestamp}] {speaker}: {text}"
        self.buffer.append(entry)
        print(f"Captured: {entry}")

    def get_context(self):
        """Returns the full context for the LLM."""
        return "\n".join(self.buffer)

    def trigger_handover(self, persona_prompt):
        """Prepares the AI with the current context."""
        context = self.get_context()
        print("\n--- TRIGGERING HANDOVER ---")
        
        full_prompt = f"""
        System: {persona_prompt}
        
        Recent Conversation History:
        {context}
        
        Human just handed over the call to you. 
        Continue the conversation seamlessly in character.
        """
        
        # This would call Ollama to pre-generate or start the session
        # requests.post(f"{self.ollama_url}/api/generate", json={"model": "llama3", "prompt": full_prompt})
        
        return full_prompt

if __name__ == "__main__":
    gb = GhostBuffer()
    
    # Simulate a call
    print("Call started. Ghost Buffer active (Silent Listen).")
    gb.capture_transcript("Hello, this is Steve from Microsoft Windows calling about your computer virus.")
    time.sleep(1)
    gb.capture_transcript("Yes, I'm looking at my screen now. It's very slow!", speaker="User")
    time.sleep(1)
    gb.capture_transcript("Okay, I need you to go to www.scam-website.com and download the support tool.")
    
    # Handover trigger
    hazel_persona = "You are Hazel, a 75-year-old grandmother who is very friendly but can't hear well and is terrible with technology."
    prompt = gb.trigger_handover(hazel_persona)
    print("\nPROMPT SENT TO ACTOR:")
    print(prompt)
