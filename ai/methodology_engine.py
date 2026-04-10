# ai/methodology_engine.py
# Author         : HuntForge Agent
# Responsibility : Generates methodology using OpenRouter API.
# ------------------------------------------------------------

import os
import yaml
from loguru import logger

from ai.openrouter_helper import OpenRouterHelper


SYSTEM_PROMPT = """\
You are HuntForge AI, an expert bug bounty methodology generator.

RULES:
1. Your output MUST be ONLY valid YAML. No markdown fences.
2. You MUST use exactly this structure (preserve the numerical phase ordering in keys so it executes in order):

phases:
  phase_1_passive:
    label: "Passive Recon"
    tools:
      - tool: subfinder
        tags_emitted:
          - has_subdomains
  phase_2_active:
    label: "Active Recon"
    conditional_tools:
      - tool: httpx
        if_tag: has_subdomains
        tags_emitted:
          - has_live_hosts

3. The "tools" or "conditional_tools" list MUST contain flat objects with a "tool" key (the binary name).
4. Do NOT nest "tools" inside conditional_tools objects.
5. Use ONLY these HuntForge tool names: subfinder, crtsh, httpx, naabu, whatweb, katana, gau, paramspider, ffuf, nuclei, subjack, dalfox, sqlmap.
"""


class MethodologyEngine:
    def __init__(self, model: str = None):
        self.helper = OpenRouterHelper(model=model)

    def generate(self, prompt: str) -> dict:
        """
        Calls OpenRouter to generate a HuntForge methodology YAML and parses it.
        Falls back to default_methodology.yaml on failure.
        """
        logger.info(f"Asking OpenRouter ({self.helper.model}) to generate methodology for: {prompt}")

        # Check if OpenRouter is reachable (API key is set)
        if not self.helper.is_available():
            logger.error(
                "OpenRouter API key is not set. Make sure to set OPENROUTER_API_KEY. "
                "Falling back to default methodology."
            )
            return self._load_default()

        try:
            output_text = self.helper.generate(
                prompt=f"Generate a HuntForge reconnaissance methodology for:\n{prompt}",
                system=SYSTEM_PROMPT,
            )

            # ── Strip markdown fences if the LLM leaked them ──
            output_text = self._strip_markdown(output_text)

            methodology = yaml.safe_load(output_text)

            # Basic validation
            if not isinstance(methodology, dict) or 'phases' not in methodology:
                raise ValueError("Generated YAML missing 'phases' root key")

            logger.success("Methodology generated successfully via OpenRouter.")
            return methodology

        except Exception as e:
            logger.error(f"Failed to generate methodology via OpenRouter: {e}")
            logger.warning("Falling back to default methodology.")
            return self._load_default()

    # ── Private helpers ──────────────────────────────────────────

    @staticmethod
    def _strip_markdown(text: str) -> str:
        """Remove ```yaml ... ``` fences that local models sometimes add."""
        if "```yaml" in text:
            text = text.split("```yaml", 1)[1].split("```", 1)[0]
        elif "```" in text:
            text = text.split("```", 1)[1].split("```", 1)[0]
        return text.strip()

    @staticmethod
    def _load_default() -> dict:
        with open(os.path.join('config', 'default_methodology.yaml'), 'r') as f:
            return yaml.safe_load(f)


# Wrapper function for the CLI
def generate_methodology(prompt: str) -> dict:
    engine = MethodologyEngine()
    return engine.generate(prompt)
