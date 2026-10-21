import pyaudio
import numpy as np
import logging
import time

logger = logging.getLogger(__name__)

class AudioCapture:
    def __init__(self, sample_rate=16000, chunk_size=512, device_index=None):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.device_index = device_index
        self.pyaudio = pyaudio.PyAudio()
        self.stream = None
        
        self.diagnose_devices()

    def diagnose_devices(self):
        """Logs available microphone devices to help with setup."""
        info = self.pyaudio.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')
        logger.info("--- Voice Pipeline: Available Microphones ---")
        for i in range(0, num_devices):
            if (self.pyaudio.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                name = self.pyaudio.get_device_info_by_host_api_device_index(0, i).get('name')
                logger.info(f"Input Device id {i} - {name}")
                if self.device_index is None and ("wo mic" in name.lower() or "droidcam" in name.lower()):
                    self.device_index = i
                    logger.info(f"Auto-selected Virtual Mic: {name}")

    def start(self):
        """Starts the PyAudio stream."""
        if self.stream is not None:
            return
            
        try:
            self.stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                input_device_index=self.device_index
            )
            logger.info("Microphone stream opened successfully.")
        except Exception as e:
            logger.error(f"Failed to open microphone: {e}")
            raise

    def read_chunk(self) -> np.ndarray:
        """Reads a chunk of audio and returns a normalized float32 numpy array."""
        if not self.stream:
            raise RuntimeError("Stream is not open")
            
        # Read raw bytes (exception_on_overflow=False prevents crashes if we process too slowly)
        raw_data = self.stream.read(self.chunk_size, exception_on_overflow=False)
        
        # Convert to int16 numpy array
        audio_data = np.frombuffer(raw_data, dtype=np.int16)
        
        # Convert to float32 normalized between -1.0 and 1.0 (Required for Silero/Whisper)
        audio_float32 = audio_data.astype(np.float32) / 32768.0
        
        return audio_float32

    def stop(self):
        """Stops and closes the stream."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

    def terminate(self):
        self.stop()
        self.pyaudio.terminate()
