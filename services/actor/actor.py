import yaml
import requests
import json
import os
from flask import Flask, jsonify, request
from hallucination_engine import HallucinationEngine

app = Flask(__name__)

class Actor:
    def __init__(self, ollama_url="http://ollama:11434", model="llama3"):
        self.ollama_url = ollama_url
        self.model = model
        self.he = HallucinationEngine()
        self.personas = self._load_personas()
        self.current_persona = "hazel" # Default

    def _load_personas(self):
        with open("personas.yaml", "r") as f:
            return yaml.safe_load(f)["personas"]

    def set_persona(self, persona_name):
        if persona_name in self.personas:
            self.current_persona = persona_name
            print(f"Actor Mask Swapped: {self.personas[persona_name]['name']}")

    def generate_response(self, transcript_history):
        # Scan for AI
        last_exchange = transcript_history[-1] if transcript_history else ""
        is_ai = self.he.detect_ai_artifacts(last_exchange)
        
        system_prompt = self.personas[self.current_persona]["system_prompt"]
        
        if is_ai:
            system_prompt += "\nNote: Active AI Scammer detected. Use confusing logic and contradictions from your Hallucination Engine."
            trick = self.he.generate_contradiction()
            transcript_history.append(f"Instruction: Inject contradiction -> {trick}")

        payload = {
            "model": self.model,
            "system": system_prompt,
            "prompt": "\n".join(transcript_history),
            "stream": False
        }

        try:
            response = requests.post(f"{self.ollama_url}/api/generate", json=payload)
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            return f"Error connecting to Actor Model: {str(e)}"

actor = Actor()

@app.route('/health')
def health():
    """Health check endpoint for service monitoring."""
    return jsonify({
        "status": "active",
        "service": "actor",
        "mode": "Sovereign",
        "integrity": "verified",
        "current_persona": actor.current_persona
    })

@app.route('/set_persona', methods=['POST'])
def set_persona_route():
    """Endpoint to change the current persona."""
    data = request.json
    persona_name = data.get('persona_name')
    if persona_name:
        actor.set_persona(persona_name)
        return jsonify({"success": True, "persona": actor.current_persona})
    return jsonify({"success": False, "error": "No persona_name provided"}), 400

@app.route('/generate', methods=['POST'])
def generate_response_route():
    """Endpoint to generate a response from the actor."""
    data = request.json
    transcript_history = data.get('transcript_history', [])
    response = actor.generate_response(transcript_history)
    return jsonify({"response": response})

if __name__ == "__main__":
    print(f"Actor Service Started. Using Persona: {actor.current_persona}")
    
    # Start Flask server
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)
