import speech_recognition as sr

class SpeechEngine:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.is_listening = False

    def listen(self):
        """
        Listens to the microphone and returns the recognized text.
        """
        try:
            with sr.Microphone() as source:
                print("Listening...")
                self.recognizer.adjust_for_ambient_noise(source)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
            print("Recognizing...")
            text = self.recognizer.recognize_google(audio)
            print(f"User said: {text}")
            return text.lower()
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
            return None
        except Exception as e:
            print(f"Error in STT: {e}")
            return None
