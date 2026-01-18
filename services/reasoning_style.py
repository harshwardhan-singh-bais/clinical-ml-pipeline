"""
MedCaseReasoning Style Injector
Injects reasoning style and explanation logic into pipeline outputs.
"""
import logging

class ReasoningStyleInjector:
    """
    Applies MedCaseReasoning patterns to explanations and ranking.
    """
    def __init__(self):
        self.patterns = [
            "Most likely",
            "Cannot be ruled out",
            "Less likely given absence of X",
            "Uncertainty remains due to missing evidence"
        ]
        logging.info("MedCaseReasoning style injector initialized.")

    def inject_style(self, explanation: str) -> str:
        # For demonstration, prepend a reasoning pattern
        return f"Most likely: {explanation}"

    def rank_diagnoses(self, diagnoses: list) -> list:
        # Example: sort by confidence, add reasoning pattern
        return [
            {
                **diag,
                "reasoning": self.inject_style(diag.get("justification", ""))
            }
            for diag in diagnoses
        ]
