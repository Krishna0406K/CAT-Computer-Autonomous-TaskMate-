import re
import logging

logger = logging.getLogger(__name__)

class TranscriptionValidator:
    def __init__(self):
        # Known whisper hallucinations when it processes silence/breathing
        self.hallucinations = [
            "you", "thank you.", "thank you", "thanks.", 
            "subs by", "subtitles by", "amara.org",
            "silence", "[silence]", "(silence)",
            "bye.", "bye", "goodbye.",
            "the end.", "end of transcript."
        ]

    def is_valid(self, text: str) -> tuple[bool, str]:
        """
        Validates transcribed text.
        Returns (is_valid, failure_reason)
        """
        if not text:
            return False, "empty"
            
        clean_text = text.lower().strip()
        
        # Remove punctuation for strict hallucination matching
        stripped_text = re.sub(r'[^\w\s]', '', clean_text)
        
        if not stripped_text:
            return False, "empty_after_punctuation_strip"
            
        if clean_text in self.hallucinations or stripped_text in self.hallucinations:
            return False, "hallucination_matched"
            
        # Too short, probably just a breath or mic pop
        if len(stripped_text) <= 2:
            return False, "too_short"
            
        return True, ""
