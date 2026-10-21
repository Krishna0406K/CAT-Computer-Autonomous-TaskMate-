import os
import wave
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache the voice model
_piper_voice = None

def get_piper_voice(model_path: str = "en_US-lessac-medium.onnx"):
    global _piper_voice
    if _piper_voice is None:
        try:
            from piper.voice import PiperVoice
            if not os.path.exists(model_path):
                logger.error(f"Voice model {model_path} not found. Please download a Piper ONNX model.")
                return None
            logger.info("Loading Piper TTS model on strictly CPU...")
            _piper_voice = PiperVoice.load(model_path)
        except ImportError:
            logger.error("piper-tts is not installed.")
            raise
    return _piper_voice

def synthesize_speech(text: str, output_path: str = "tts_output.wav", model_path: str = "en_US-lessac-medium.onnx") -> str:
    """
    Uses Piper-TTS to synthesize speech strictly on CPU.
    Returns the path to the generated wav file.
    """
    try:
        voice = get_piper_voice(model_path)
        if not voice:
            return ""
            
        with wave.open(output_path, "wb") as wav_file:
            voice.synthesize(text, wav_file)
            
        return output_path
    except Exception as e:
        logger.error(f"TTS synthesis failed: {str(e)}")
        return ""

def play_audio(file_path: str):
    """
    Plays an audio file locally using sounddevice.
    """
    if not os.path.exists(file_path):
        return
        
    try:
        import soundfile as sf
        import sounddevice as sd
        
        data, fs = sf.read(file_path, dtype='float32')
        sd.play(data, fs)
        sd.wait() # Block until audio is finished playing
    except ImportError:
        logger.error("sounddevice or soundfile not installed.")
    except Exception as e:
        logger.error(f"Failed to play audio: {str(e)}")

def play_completion_sound():
    """
    Plays the custom CAT reply sound (MP3) for task completion feedback.
    This is triggered only during Agent Work verification, not normal chat.
    """
    # Use absolute path to the uploaded sound file
    sound_path = r"D:\CAT\sound\CAT reply sound.mp3"
    
    if os.path.exists(sound_path):
        try:
            # MP3s require pygame or playsound since soundfile primarily supports WAV/OGG
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(sound_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        except ImportError:
            logger.error("pygame is required to play MP3 files. Please run: pip install pygame")
        except Exception as e:
            logger.error(f"Failed to play completion sound: {str(e)}")
    else:
        logger.warning(f"*MEOW* (Audio file not found at {sound_path}, but task completed!)")
