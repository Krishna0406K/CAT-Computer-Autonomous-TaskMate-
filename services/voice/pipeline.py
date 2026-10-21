import threading
import time
import numpy as np
import logging
import httpx
import re

from services.voice.audio_capture import AudioCapture
from services.voice.vad import SileroVAD
from services.voice.quality_gate import TranscriptionValidator
from services.voice.stt import transcribe_audio
from services.voice.telemetry import log_voice_event

logger = logging.getLogger(__name__)

class VoicePipeline:
    def __init__(self, state_callback=None):
        self.state = "IDLE"
        self.state_callback = state_callback
        
        self.capture = AudioCapture()
        self.vad = SileroVAD(threshold=0.5)
        self.validator = TranscriptionValidator()
        
        self.is_running = False
        self.wake_words = ["cat", "hey cat", "hi cat", "okay cat", "ok cat"]
        
        # Audio Buffers
        self.ring_buffer_size = 15 # ~0.5 seconds pre-speech at 512 chunks
        self.ring_buffer = []
        self.current_audio = []
        
        self.silence_chunks = 0
        self.silence_threshold_chunks = 45 # ~1.5 seconds of silence stops command

    def _set_state(self, new_state: str):
        if self.state != new_state:
            self.state = new_state
            logger.info(f"Voice Pipeline State -> {self.state}")
            if self.state_callback:
                self.state_callback(self.state)

    def _play_chime(self):
        try:
            import winsound
            winsound.Beep(1200, 150)
            winsound.Beep(1600, 150)
        except:
            pass

    def start(self):
        self.is_running = True
        self.capture.start()
        threading.Thread(target=self._loop, daemon=True).start()

    def stop(self):
        self.is_running = False
        self.capture.stop()
        self._set_state("IDLE")

    def _route_command(self, command: str):
        self._set_state("PROCESSING")
        try:
            with httpx.Client(timeout=5.0) as client:
                client.post("http://localhost:8000/internal/voice_command", json={"task": command})
        except Exception as e:
            logger.error(f"Failed to route command: {e}")
            log_voice_event("command", self.state, success=False, failure_reason="routing_failed", transcription=command)

    def _process_transcription(self, audio_array: np.ndarray, is_wake_pass: bool = False):
        start_time = time.time()
        text = transcribe_audio(audio_array)
        latency = int((time.time() - start_time) * 1000)
        
        if not text:
            return ""

        text_clean = text.lower().strip().replace(",", "").replace(".", "").replace("!", "").replace("?", "")
        
        if is_wake_pass:
            # Wake word logic
            match = re.search(r'\b(cat|hey cat|okay cat|ok cat)\b', text_clean)
            if match:
                log_voice_event("wake", self.state, latency_ms=latency, success=True, transcription=text)
                return match.group(0)
            return ""
        else:
            # Command logic
            self._set_state("VALIDATING")
            is_valid, reason = self.validator.is_valid(text)
            
            if is_valid:
                log_voice_event("command", self.state, latency_ms=latency, success=True, transcription=text)
                return text
            else:
                logger.warning(f"Transcription rejected by Quality Gate: {reason} ('{text}')")
                log_voice_event("command", self.state, latency_ms=latency, success=False, failure_reason=reason, transcription=text)
                return ""

    def _loop(self):
        while self.is_running:
            try:
                chunk = self.capture.read_chunk()
                is_speech = self.vad.is_speech(chunk)
                
                # Update rolling pre-speech buffer
                self.ring_buffer.append(chunk)
                if len(self.ring_buffer) > self.ring_buffer_size:
                    self.ring_buffer.pop(0)

                if self.state == "IDLE":
                    if is_speech:
                        self._set_state("WAKE_LISTENING")
                        self.current_audio = list(self.ring_buffer)
                        self.silence_chunks = 0
                        
                elif self.state == "WAKE_LISTENING":
                    self.current_audio.append(chunk)
                    if not is_speech:
                        self.silence_chunks += 1
                    else:
                        self.silence_chunks = 0
                        
                    # If they paused speaking, check for wake word
                    if self.silence_chunks > 15: # ~0.5s pause
                        self._set_state("TRANSCRIBING")
                        audio_np = np.concatenate(self.current_audio)
                        wake_word = self._process_transcription(audio_np, is_wake_pass=True)
                        
                        if wake_word:
                            self._set_state("WAKE_DETECTED")
                            self._play_chime()
                            self.current_audio = []
                            self.ring_buffer.clear()
                            self.silence_chunks = 0
                            self._set_state("COMMAND_RECORDING")
                        else:
                            # False alarm / background conversation
                            self._set_state("IDLE")
                            
                elif self.state == "COMMAND_RECORDING":
                    self.current_audio.append(chunk)
                    if not is_speech:
                        self.silence_chunks += 1
                    else:
                        self.silence_chunks = 0
                        
                    # 1.5 seconds of silence ends the command
                    if self.silence_chunks > self.silence_threshold_chunks:
                        self._set_state("TRANSCRIBING")
                        audio_np = np.concatenate(self.current_audio)
                        command_text = self._process_transcription(audio_np, is_wake_pass=False)
                        
                        if command_text:
                            logger.info(f"🎤 Command Captured: '{command_text}'")
                            self._route_command(command_text)
                            
                        self._set_state("IDLE")

            except Exception as e:
                logger.error(f"Pipeline loop error: {e}")
                time.sleep(0.1)
