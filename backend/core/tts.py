import asyncio
import edge_tts
import pygame
import os

class TTSEngine:
    def __init__(self):
        # High quality male voice: Christopher Neural (US English)
        # Female option: en-US-AvaNeural
        self.voice = "en-US-ChristopherNeural" 
        self.rate = "+0%"
        self.volume = "+0%"
        pygame.mixer.init()

    def set_voice(self, voice_name_or_gender):
        """Sets the voice based on gender ('male'/'female') or full name."""
        if voice_name_or_gender.lower() == 'male':
            self.voice = "en-US-ChristopherNeural"
        elif voice_name_or_gender.lower() == 'female':
            self.voice = "en-US-AvaNeural"
        else:
            self.voice = voice_name_or_gender
        print(f"TTS Voice set to: {self.voice}")

    async def _generate_audio(self, text, filename):
        """
        Generates audio file from text using Edge TTS.
        """
        communicate = edge_tts.Communicate(text, self.voice, rate=self.rate, volume=self.volume)
        await communicate.save(filename)

    def speak(self, text):
        """
        Converts text to speech using Edge TTS (Online, High Quality).
        """
        print(f"ALIAS: {text}")
        filename = "temp_speech.mp3"
        try:
            # Run async generation in a blocking way
            asyncio.run(self._generate_audio(text, filename))
            
            # Play audio
            if os.path.exists(filename):
                pygame.mixer.music.load(filename)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
            else:
                 print(f"TTS Error: Audio file {filename} was not generated.")
            
            # Unload and clean up
            pygame.mixer.music.unload()
            try:
               os.remove(filename)
            except:
               pass
        except Exception as e:
            print(f"TTS Error: {e}")

    def stop(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
