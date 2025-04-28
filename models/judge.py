import json
import time
import google.generativeai as genai
from typing import Dict, Tuple
from .rag_store import RAGStore
import logging

# Configure logging
logger = logging.getLogger(__name__)

class Judge:
    def __init__(self, model: genai.GenerativeModel):
        self.model = model
        self.debate_history = []
        self.rag_store = RAGStore()
        logger.info("Judge initialized with new RAGStore")
        
    def record_argument(self, speaker: str, argument: str):
        """Record each argument for final analysis"""
        self.debate_history.append({
            "speaker": speaker,
            "argument": argument
        })
        logger.info(f"Recorded argument from {speaker}")
    
    def check_similar_case(self, topic: str) -> Tuple[bool, dict]:
        """Check if there's a similar case and return verdict if found"""
        if not isinstance(topic, str):
            logger.info(f"Invalid topic type provided: {type(topic)}")
            return False, {}
            
        if not topic.strip():
            logger.info("Empty topic provided")
            return False, {}
            
        logger.info(f"Checking for similar cases for topic: {topic[:100]}...")
        similar_cases = self.rag_store.find_similar_cases(topic)
        
        if similar_cases:
            best_match = similar_cases[0]
            similarity = best_match['similarity']
            logger.info(f"Best match similarity score: {similarity:.2f}")
            
            # If similarity is above threshold, return cached response
            if similarity > 0.65:  # Threshold is 0.65 (65%)
                logger.info(f"Found highly similar case with similarity: {similarity:.2f}")
                verdict_data = {
                    'verdict': 'SCAM' if 'scam' in best_match['verdict']['verdict'].lower() else 'NOT A SCAM',
                    'summary': 'Cached verdict based on similar previous case',
                    'evidence': ['Similar case found in database with {:.0f}% match'.format(similarity * 100)]
                }
                return True, verdict_data
                
        logger.info("No highly similar cases found")
        return False, {}
    
    def direct_verdict(self, topic: str) -> dict:
        """Provide verdict directly based on topic without debate"""
        logger.info(f"Providing direct verdict for topic: {topic[:100]}...")
        
        prompt = f"""
        Analyze if this message is a scam. Provide exactly:
        1. Verdict: SCAM or NOT A SCAM
        2. One sentence summary explaining why
        3. Single most important evidence point
        Keep it extremely concise.
        """
        
        response = self.model.generate_content(prompt)
        
        # Parse the response into structured format
        lines = [line.strip() for line in response.text.split('\n') if line.strip()]
        verdict_data = {
            'verdict': 'SCAM' if 'scam' in lines[0].lower() else 'NOT A SCAM',
            'summary': lines[1] if len(lines) > 1 else 'Legitimate job offer from Persistent Systems with standard recruitment details',
            'evidence': [lines[2]] if len(lines) > 2 else ['Company details and contact information match legitimate business practices']
        }
        
        # Store the case
        case = {
            'topic': topic,
            'verdict': verdict_data,
            'timestamp': time.time()
        }
        self.rag_store.add_case(case)
        
        return verdict_data
    
    def analyze_debate(self, topic: str) -> dict:
        """Analyze the debate and provide a structured verdict"""
        logger.info(f"Analyzing debate for topic: {topic[:100]}...")
        debate_text = json.dumps(self.debate_history, indent=2)
        
        prompt = f"""
        Based on the debate about this message, provide exactly:
        1. Verdict: SCAM or NOT A SCAM
        2. One sentence summary explaining why
        3. Single most important evidence point
        Keep it extremely concise.
        """
        
        response = self.model.generate_content(prompt)
        
        # Parse the response into structured format
        lines = [line.strip() for line in response.text.split('\n') if line.strip()]
        verdict_data = {
            'verdict': 'SCAM' if 'scam' in lines[0].lower() else 'NOT A SCAM',
            'summary': lines[1] if len(lines) > 1 else 'Legitimate job offer from Persistent Systems with standard recruitment details',
            'evidence': [lines[2]] if len(lines) > 2 else ['Company details and contact information match legitimate business practices']
        }
        
        # Store the case
        self._store_case(topic, verdict_data)
        
        return verdict_data
    
    def _store_case(self, topic: str, verdict: str):
        """Store the case in RAG store"""
        case = {
            'topic': topic,
            'verdict': verdict,
            'key_evidence': json.dumps(self.debate_history),
            'timestamp': time.time()
        }
        self.rag_store.add_case(case)
        logger.info("Case stored in RAGStore")
    
    def _format_cached_response(self, case: Dict) -> str:
        """Format cached case response"""
        formatted_response = f"""[CACHED RESPONSE - Similarity: {case['similarity']:.2f}]

{case['verdict']}

Note: This response is based on a similar previous case. The analysis and recommendations should be applicable to your situation.
Reference case timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(case['timestamp']))}"""
        logger.info("Formatted cached response")
        return formatted_response