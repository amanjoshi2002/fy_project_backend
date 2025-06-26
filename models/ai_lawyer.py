import json
from typing import List, Dict
import google.generativeai as genai
from utils.web_search import perform_web_search

class AILawyer:
    def __init__(self, name: str, model: genai.GenerativeModel, role_description: str):
        self.name = name
        self.model = model
        self.role_description = role_description
        self.stance = role_description  # Add this line to fix the error
        self.evidence = []  # Initialize evidence list
        
    def make_argument(self, message: str, opposing_argument: str = None) -> str:
        """Generate an argument about the message"""
        if opposing_argument:
            prompt = f"""
            You are {self.name}, {self.role_description}.
            
            Analyze this message objectively:
            "{message}"
            
            The opposing analyst has argued:
            "{opposing_argument}"
            
            Provide your professional analysis considering:
            - Factual evidence and patterns
            - Industry standards and practices
            - Common fraud indicators vs legitimate practices
            - Objective assessment criteria
            
            Focus on evidence-based reasoning, not assumptions.
            Be thorough but concise (200-300 words).
            """
        else:
            prompt = f"""
            You are {self.name}, {self.role_description}.
            
            Analyze this message objectively:
            "{message}"
            
            Provide your professional analysis considering:
            - Factual evidence and patterns
            - Industry standards and practices
            - Common fraud indicators vs legitimate practices
            - Objective assessment criteria
            
            Focus on evidence-based reasoning, not assumptions.
            Be thorough but concise (200-300 words).
            """
            
        response = self.model.generate_content(prompt)
        return response.text

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