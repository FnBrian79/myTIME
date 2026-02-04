import torch
import torchaudio
from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2Processor
import os
import requests
from flask import Flask, jsonify

app = Flask(__name__)

class DeepfakeDetector:
    def __init__(self, model_path="anthony-v-peters/wav2vec2-base-superb-ks", processor_path="anthony-v-peters/wav2vec2-base-superb-ks"):
        # Defaulting to a small, fast model for demo - in production use a specific deepfake fine-tuned one
        print(f"📡 Loading Deepfake Detection Model: {model_path}...")
        self.processor = Wav2Vec2Processor.from_pretrained(processor_path)
        self.model = Wav2Vec2ForSequenceClassification.from_pretrained(model_path)
        self.model.eval()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        print(f"✅ Model loaded on {self.device}")

    def detect_deepfake(self, audio_data):
        """
        Processes raw audio data and returns scammer type.
        """
        # Placeholder for real-time audio chunk processing
        # In a real scenario, we'd receive a 5s segment of 16k SLIN
        try:
            # Preprocess
            input_values = self.processor(audio_data, sampling_rate=16000, return_tensors="pt").input_values
            input_values = input_values.to(self.device)

            with torch.no_grad():
                logits = self.model(input_values).logits

            predicted_class_id = logits.argmax().item()
            probabilities = torch.softmax(logits, dim=-1).cpu().numpy()[0]

            # Model dependent labels - this is a categorical example
            labels = ["human", "deepfake"] 
            scammer_type = labels[predicted_class_id] if predicted_class_id < len(labels) else "unknown"
            
            return scammer_type, float(probabilities[predicted_class_id])
        except Exception as e:
            print(f"❌ Detection Error: {e}")
            return "unknown", 0.0

detector = DeepfakeDetector()
current_status = {"scammer_type": "unknown", "confidence": 0.0}

@app.route('/status')
def get_status():
    return jsonify(current_status)

# Logic to receive audio chunks from Asterisk AudioSocket (simplified)
# This would be integrated into the bridge or a separate stream listener
def process_stream_chunk(chunk):
    global current_status
    scammer_type, confidence = detector.detect_deepfake(chunk)
    current_status = {"scammer_type": scammer_type, "confidence": confidence}
    
    # Notify Foreman if type is AI
    if scammer_type == "deepfake" and confidence > 0.8:
        requests.post("http://foreman:8080/triage/update", json={"scammer_type": "AI"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
