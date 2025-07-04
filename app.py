from flask import Flask, request, jsonify
from flask_cors import CORS  # Add this import
from config import GEMINI_KEY_1, GEMINI_KEY_2
from utils.gemini_setup import setup_gemini
from models.ai_lawyer import AILawyer
from models.judge import Judge

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Modify the analyze_message function to force a debate for testing purposes

def analyze_message(message: str):
    """Analyze a custom message for potential scams"""
    # Ensure message is a string
    if isinstance(message, dict):
        message = message.get('text', '')  # assuming the message is in 'text' field
    
    # Setup judge
    judge = Judge(setup_gemini(GEMINI_KEY_1))
    
    # First check if we have a similar case
    has_similar, cached_verdict = judge.check_similar_case(message)
    if has_similar:
        return {
            "message": message,
            "verdict": cached_verdict['verdict'],
            "summary": cached_verdict['summary'],
            "evidence": cached_verdict['evidence'],
            "source": "cached"
        }
    
    # COMMENT OUT THIS SECTION TO FORCE DEBATE FOR TESTING
    # if isinstance(message, str) and len(message.split()) < 50:  # Simple case threshold
    #     verdict_data = judge.direct_verdict(message)
    #     return {
    #         "message": message,
    #         "verdict": verdict_data['verdict'],
    #         "summary": verdict_data['summary'],
    #         "evidence": verdict_data['evidence'],
    #         "source": "direct"
    #     }
    
    # For complex cases, proceed with full debate
    prosecutor = AILawyer(
        "Scam Analyst",
        setup_gemini(GEMINI_KEY_1),
        "analyzing potential scam indicators in this message using established fraud detection criteria"
    )
    
    defender = AILawyer(
        "Legitimacy Analyst",
        setup_gemini(GEMINI_KEY_2),
        "analyzing indicators that suggest this message is legitimate using authentic communication patterns"
    )
    
    # Single round for message analysis
    prosecutor_argument = prosecutor.make_argument(message)
    judge.record_argument(prosecutor.name, prosecutor_argument)
    
    defender_argument = defender.make_argument(message, prosecutor_argument)
    judge.record_argument(defender.name, defender_argument)
    
    verdict_data = judge.analyze_debate(message)
    
    return {
        "message": message,
        "verdict": verdict_data['verdict'],
        "summary": verdict_data['summary'],
        "evidence": verdict_data['evidence'],
        "source": "debate"
    }

@app.route('/analyze', methods=['POST'])
def analyze_endpoint():
    """API endpoint to analyze messages"""
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    data = request.get_json()
    if 'message' not in data:
        return jsonify({"error": "Message field is required"}), 400
    
    # Extract the actual message text from the request
    message = data['message']
    if isinstance(message, dict):
        if 'text' not in message:
            return jsonify({"error": "Message must contain 'text' field"}), 400
        message = message['text']
    
    result = analyze_message(message)
    return jsonify(result)

# Modify the main block to work with both direct Python and Gunicorn
if __name__ == "__main__":
    # Test API connection first
    try:
        test_model = setup_gemini(GEMINI_KEY_1)
        test_response = test_model.generate_content("Test connection")
        print("API connection successful!")
    except Exception as e:
        print(f"API connection failed: {e}")
        exit(1)
        
    # Run the app (will only run when directly executed, not with Gunicorn)
    app.run(host='0.0.0.0', debug=True, port=5000)