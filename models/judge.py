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
    
    def check_similar_case(self, topic: str) -> Tuple[bool, str]:
        """Check if there's a similar case and return verdict if found"""
        if not isinstance(topic, str):
            logger.info(f"Invalid topic type provided: {type(topic)}")
            return False, ""
            
        if not topic.strip():
            logger.info("Empty topic provided")
            return False, ""
            
        logger.info(f"Checking for similar cases for topic: {topic[:100]}...")
        similar_cases = self.rag_store.find_similar_cases(topic)
        
        if similar_cases:
            best_match = similar_cases[0]
            similarity = best_match['similarity']
            logger.info(f"Best match similarity score: {similarity:.2f}")
            
            # If similarity is above threshold, return cached response
            if similarity > 0.65:  # Threshold is 0.65 (65%)
                logger.info(f"Found highly similar case with similarity: {similarity:.2f}")
                cached_response = self._format_cached_response(best_match)
                return True, cached_response
                
        logger.info("No highly similar cases found")
        return False, ""
    
    def direct_verdict(self, topic: str) -> str:
        """Provide verdict directly based on topic without debate"""
        logger.info(f"Providing direct verdict for topic: {topic[:100]}...")
        
        prompt = f"""
        As an impartial judge, analyze this scenario about "{topic}" and provide:

        1. VERDICT: Whether the discussed scenario is likely a scam or legitimate
        2. REASONING: Based on:
           - Pattern recognition with known scam characteristics
           - Similar historical cases
           - Common red flags
        3. RECOMMENDATIONS: Provide practical advice for this situation
        
        Format your response in clear sections with bullet points.
        """
        
        response = self.model.generate_content(prompt)
        verdict = response.text
        
        # Store the case
        case = {
            'topic': topic,
            'verdict': verdict,
            'key_evidence': 'Direct verdict without debate',
            'timestamp': time.time()
        }
        self.rag_store.add_case(case)
        logger.info("Direct verdict generated and stored")
        
        return verdict
    
    def analyze_debate(self, topic: str) -> str:
        """Analyze the entire debate and provide a verdict"""
        logger.info(f"Analyzing debate for topic: {topic[:100]}...")
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
        verdict = response.text
        
        # Store the new case
        self._store_case(topic, verdict)
        logger.info("Debate analysis completed and verdict stored")
        
        return verdict
    
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