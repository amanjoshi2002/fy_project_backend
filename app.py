import time
from flask import Flask, request, jsonify
from config import GEMINI_KEY_1, GEMINI_KEY_2
from utils.gemini_setup import setup_gemini
from models.ai_lawyer import AILawyer
from models.judge import Judge

# Initialize Flask app
app = Flask(__name__)

def analyze_message(message: str):
    """Analyze a custom message for potential scams"""
    # Setup the participants
    prosecutor = AILawyer(
        "Prosecutor Thompson",
        setup_gemini(GEMINI_KEY_1),
        "arguing that this message shows signs of being a scam"
    )
    
    defender = AILawyer(
        "Defender Rodriguez",
        setup_gemini(GEMINI_KEY_2),
        "arguing for a balanced analysis of this message"
    )
    
    judge = Judge(setup_gemini(GEMINI_KEY_1))

    # Single round for message analysis
    prosecutor_argument = prosecutor.make_argument(message)
    judge.record_argument(prosecutor.name, prosecutor_argument)
    
    defender_argument = defender.make_argument(message, prosecutor_argument)
    judge.record_argument(defender.name, defender_argument)
    
    verdict = judge.analyze_debate(message)
    
    return {
        "message": message,
        "prosecutor_argument": prosecutor_argument,
        "defender_argument": defender_argument,
        "verdict": verdict
    }

@app.route('/analyze', methods=['POST'])
def analyze_endpoint():
    """API endpoint to analyze messages"""
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    data = request.get_json()
    if 'message' not in data:
        return jsonify({"error": "Message field is required"}), 400
    
    result = analyze_message(data['message'])
    return jsonify(result)

if __name__ == "__main__":
    # Test API connection first
    try:
        test_model = setup_gemini(GEMINI_KEY_1)
        test_response = test_model.generate_content("Test connection")
        print("API connection successful!")
    except Exception as e:
        print(f"API connection failed: {e}")
        exit(1)
        
    # Continue with normal execution
    app.run(debug=True, port=5000)