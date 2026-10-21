import torch
import numpy as np
import logging

logger = logging.getLogger(__name__)

class SileroVAD:
    def __init__(self, threshold=0.5, sampling_rate=16000):
        self.threshold = threshold
        self.sampling_rate = sampling_rate
        self.model = None
        self._load_model()

    def _load_model(self):
        try:
            logger.info("Loading Silero VAD model...")
            # Silero VAD requires torch
            self.model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                trust_repo=True
            )
            self.model.eval()
            logger.info("Silero VAD loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load Silero VAD: {e}")
            raise

    def is_speech(self, audio_chunk_float32: np.ndarray) -> bool:
        """
        Takes a chunk of float32 audio (between -1 and 1) 
        and returns True if speech probability exceeds threshold.
        """
        if self.model is None:
            return False
            
        try:
            # Convert numpy array to torch tensor
            tensor_chunk = torch.from_numpy(audio_chunk_float32)
            
            # Silero expects shape (batch_size, sequence_length)
            tensor_chunk = torch.unsqueeze(tensor_chunk, 0)
            
            # Get speech probability
            with torch.no_grad():
                speech_prob = self.model(tensor_chunk, self.sampling_rate).item()
                
            return speech_prob >= self.threshold
        except Exception as e:
            logger.error(f"VAD Error: {e}")
            return False
