# ai/report_generator.py
# Author         : HuntForge Agent
# Responsibility : Generates the final bug bounty report using Google Gemini.
# ------------------------------------------------------------

import os
import json
from loguru import logger
import google.generativeai as genai

class ReportGenerator:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")

        if self.api_key:
            genai.configure(api_key=self.api_key)

    def generate(self, domain: str, tag_manager, output_dir: str):
        if not self.api_key:
            logger.error("Gemini API key not found. Set GEMINI_API_KEY environment variable. Skipping AI Report.")
            return

        logger.info(f"Generating final AI report for {domain} via Gemini API...")
        
        # Read the tags from the tag manager to provide context
        tags = tag_manager.get_all()
        
        # Build context from processed output files if they exist
        context = f"Domain: {domain}\n\nDiscovered Tags (Intelligence):\n"
        for t, data in tags.items():
            context += f"- {t} (Confidence: {data.get('confidence')})\n"
            
        system_prompt = "You are HuntForge AI, a senior offensive security analyst. Write a professional, concise executive summary and vulnerability report based on the provided reconnaissance tags and intelligence. Highlight critical risks."
        
        # Combine system prompt and context for Gemini
        final_prompt = f"{system_prompt}\n\n[USER Context]\n{context}"
        
        try:
            # Using Gemini 1.5 Flash for fast textual generation
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(final_prompt)
            
            report_text = response.text
            
            # Ensure the logs directory exists
            os.makedirs(os.path.join(output_dir, 'logs'), exist_ok=True)
            report_path = os.path.join(output_dir, 'logs', 'ai_report.md')
            
            with open(report_path, 'w') as f:
                f.write(report_text)
                
            logger.success(f"AI Report written to {report_path}")
            
        except Exception as e:
            logger.error(f"Failed to generate report via Gemini API: {e}")

# CLI wrapper
def generate_report(domain, tag_manager, output_dir):
    bot = ReportGenerator()
    bot.generate(domain, tag_manager, output_dir)
