import google.generativeai as genai
import requests
from typing import List, Dict
import json
import time
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify

# Load environment variables
load_dotenv()

# Configure the two different Gemini instances
GEMINI_KEY_1 = os.getenv('GEMINI_KEY_1')
GEMINI_KEY_2 = os.getenv('GEMINI_KEY_2')

# Configure Google Custom Search API (for web search)
GOOGLE_SEARCH_API = "https://www.googleapis.com/customsearch/v1"
SEARCH_ENGINE_ID = os.getenv('SEARCH_ENGINE_ID')

def setup_gemini(api_key: str) -> genai.GenerativeModel:
    """Initialize a Gemini model instance"""
    genai.configure(api_key=api_key)
    
    # Configure the model with generation config
    generation_config = {
        "temperature": 0.7,
        "top_p": 1,
        "top_k": 1,
        "max_output_tokens": 2048,
    }
    
    # Create the model with specific configuration
    model = genai.GenerativeModel(
        model_name='gemini-2.0-flash',  # Using the stable release version
        generation_config=generation_config
    )
    
    return model

def perform_web_search(query: str, num_results: int = 3) -> List[Dict]:
    """Perform a web search and return relevant results"""
    try:
        params = {
            'q': query,
            'key': os.getenv('GOOGLE_SEARCH_API_KEY'),  # Need a proper Google Search API key, not Gemini key
            'cx': SEARCH_ENGINE_ID,
            'num': num_results
        }
        response = requests.get(GOOGLE_SEARCH_API, params=params)
        results = response.json().get('items', [])
        return [{'title': r['title'], 'snippet': r['snippet'], 'link': r['link']} for r in results]
    except Exception as e:
        print(f"Search error: {e}")
        return []

class AILawyer:
    def __init__(self, name: str, model: genai.GenerativeModel, stance: str):
        self.name = name
        self.model = model
        self.stance = stance
        self.evidence = []

    def gather_evidence(self, topic: str) -> List[Dict]:
        """Gather evidence through web search"""
        search_query = f"{topic} {self.stance} evidence cases reports"
        results = perform_web_search(search_query)
        self.evidence.extend(results)
        return results

    def make_argument(self, topic: str, opponent_argument: str = None) -> str:
        """Generate an argument using Gemini and gathered evidence"""
        # Gather new evidence
        new_evidence = self.gather_evidence(topic)
        
        # Construct the prompt
        prompt = f"""
        You are {self.name}, a lawyer {self.stance}.
        Topic: {topic}
        
        Your collected evidence:
        {json.dumps(new_evidence, indent=2)}
        
        Previous argument:
        {opponent_argument if opponent_argument else 'Opening statement'}
        
        Please provide a concise argument in the following format:
        1. Key Point 1
        - Supporting Evidence: (cite specific source)
        - Counter to Opponent: (address opponent's evidence with contradicting data)
        
        2. Key Point 2
        - Supporting Evidence: (cite specific source)
        - Counter to Opponent: (address opponent's evidence with contradicting data)
        
        3. Key Point 3
        - Supporting Evidence: (cite specific source)
        - Counter to Opponent: (address opponent's evidence with contradicting data)
        
        Requirements:
        - Make exactly 3 clear, distinct points
        - Each point must have both supporting evidence AND counter-evidence
        - Directly address and refute opponent's claims with specific data
        - Keep responses brief and focused
        - Cite sources with URLs when referencing evidence
        - Use real statistics and data to counter opponent's claims
        """
    
        # Generate response using Gemini
        response = self.model.generate_content(prompt)
        return response.text

class Judge:
    def __init__(self, model: genai.GenerativeModel):
        self.model = model
        self.debate_history = []
        
    def record_argument(self, speaker: str, argument: str):
        """Record each argument for final analysis"""
        self.debate_history.append({
            "speaker": speaker,
            "argument": argument
        })
    
    def analyze_debate(self, topic: str) -> str:
        """Analyze the entire debate and provide a verdict"""
        debate_text = json.dumps(self.debate_history, indent=2)
        
        prompt = f"""
        As an impartial judge, analyze this debate about "{topic}" and provide:

        1. VERDICT: Whether the discussed scenario is likely a scam or legitimate
        2. KEY EVIDENCE: List the most compelling evidence from both sides
        3. REASONING: Explain your verdict based on:
           - Strength of evidence presented
           - Credibility of sources
           - Pattern recognition with known scam characteristics
        4. RECOMMENDATIONS: Provide practical advice for similar situations
        
        Format your response in clear sections with bullet points.
        Base your verdict solely on the evidence and arguments presented.
        """
        
        response = self.model.generate_content(prompt)
        return response.text

def start_debate(topic: str):
    """Initialize and run a debate on the given topic"""
    # Setup the participants
    prosecutor = AILawyer(
        "Prosecutor Thompson",
        setup_gemini(GEMINI_KEY_1),
        f"arguing that {topic} is a serious threat to public safety"
    )
    
    defender = AILawyer(
        "Defender Rodriguez",
        setup_gemini(GEMINI_KEY_2),
        f"arguing for a balanced perspective on {topic}"
    )
    
    judge = Judge(setup_gemini(GEMINI_KEY_1))

    # Number of debate rounds
    rounds = 3

    print("\n=== AI Legal Debate ===")
    print(f"Topic: {topic}")
    print("=" * 50)

    last_argument = None
    for round_num in range(rounds):
        print(f"\nRound {round_num + 1}")
        print("-" * 20)

        # Prosecutor's turn
        print(f"\n{prosecutor.name}:")
        prosecutor_argument = prosecutor.make_argument(topic, last_argument)
        print(prosecutor_argument)
        judge.record_argument(prosecutor.name, prosecutor_argument)
        last_argument = prosecutor_argument
        
        time.sleep(2)

        # Defender's turn
        print(f"\n{defender.name}:")
        defender_argument = defender.make_argument(topic, last_argument)
        print(defender_argument)
        judge.record_argument(defender.name, defender_argument)
        last_argument = defender_argument
        
        time.sleep(2)
    
    # Judge's final verdict
    print("\n=== Judge's Verdict ===")
    print("=" * 50)
    verdict = judge.analyze_debate(topic)
    print(verdict)

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
    # Prosecutor's analysis
    prosecutor_argument = prosecutor.make_argument(message)
    judge.record_argument(prosecutor.name, prosecutor_argument)
    
    # Defender's analysis
    defender_argument = defender.make_argument(message, prosecutor_argument)
    judge.record_argument(defender.name, defender_argument)
    
    # Get judge's verdict
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
    # Example topics - can be changed to any online scam topic
    scam_topics = [
        "Romance scams on dating websites",
        "Job offer email scams",
        "Fake online shopping websites",
        "Tech support scam calls",
        "Investment fraud schemes",
        "Phishing emails impersonating banks"
    ]
    
    # Let user choose a topic
    print("Available scam topics for debate:")
    for i, topic in enumerate(scam_topics, 1):
        print(f"{i}. {topic}")
    
    try:
        choice = int(input("\nChoose a topic number (or 0 to enter your own): "))
        if choice == 0:
            custom_topic = input("Enter your own scam topic: ")
            start_debate(custom_topic)
        else:
            start_debate(scam_topics[choice - 1])
    except (ValueError, IndexError):
        print("Invalid choice. Starting debate with default topic.")
        start_debate(scam_topics[0])