# ai/methodology_engine.py
# Author         : Member 2
# Responsibility : Generates methodology using Ollama.
# ------------------------------------------------------------

import requests
import json
import yaml
import os
from loguru import logger

class MethodologyEngine:
    def __init__(self, ollama_host: str = "http://localhost:11434", model: str = "llama3"):
        self.ollama_host = ollama_host
        self.model = model

    def generate(self, prompt: str) -> dict:
        """
        Calls Ollama to generate a HuntForge methodology YAML and parses it.
        Falls back to default_methodology.yaml on failure.
        """
        logger.info(f"Asking Ollama ({self.model}) to generate methodology for: {prompt}")
        
        system_prompt = """
You are HuntForge AI, an expert bug bounty methodology generator.
Generate a valid YAML methodology based on the user's prompt.
Your output MUST be ONLY valid YAML. No markdown formatting, no explanations.
"""
        
        try:
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.model,
                    "system": system_prompt,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            response.raise_for_status()
            
            output_text = response.json().get('response', '')
            
            # Clean up markdown around YAML if the LLM leaked it
            if "```yaml" in output_text:
                output_text = output_text.split("```yaml")[1].split("```")[0]
            elif "```" in output_text:
                output_text = output_text.split("```")[1].split("```")[0]
                
            methodology = yaml.safe_load(output_text)
            
            # Basic validation
            if not isinstance(methodology, dict) or 'phases' not in methodology:
                raise ValueError("Generated YAML missing 'phases' root key")
                
            return methodology
            
        except Exception as e:
            logger.error(f"Failed to generate methodology via Ollama: {e}")
            logger.warning("Falling back to default methodology.")
            return self._load_default()

    def _load_default(self) -> dict:
        with open(os.path.join('config', 'default_methodology.yaml'), 'r') as f:
            return yaml.safe_load(f)

# Wrapper function for the CLI
def generate_methodology(prompt: str) -> dict:
    engine = MethodologyEngine()
    return engine.generate(prompt)
