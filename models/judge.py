import json
import google.generativeai as genai

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