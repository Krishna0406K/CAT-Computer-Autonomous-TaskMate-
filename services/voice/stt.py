import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache the model so it doesn't reload into RAM on every request
_whisper_model = None

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            logger.info("Loading faster-whisper model on strictly CPU...")
            # Using 'base.en' for fast CPU transcription. 
            # compute_type="int8" optimizes memory and CPU usage.
            _whisper_model = WhisperModel("base.en", device="cpu", compute_type="int8")
        except ImportError:
            logger.error("faster-whisper is not installed.")
            raise
    return _whisper_model

def transcribe_audio(audio_source) -> str:
    """
    Transcribes spoken audio to text using faster-whisper entirely on the CPU.
    audio_source can be a string (file path) or a numpy array (float32).
    """
    try:
        model = get_whisper_model()
        logger.debug("Transcribing audio buffer...")
        
        # We explicitly set language="en" to improve speed and accuracy if known
        segments, info = model.transcribe(audio_source, beam_size=5, language="en", condition_on_previous_text=False)
        
        text = " ".join([segment.text for segment in segments])
        return text.strip()
    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}")
        return ""
