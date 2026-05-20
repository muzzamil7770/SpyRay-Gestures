import os
import time
import random
import subprocess
from PySide6.QtCore import QThread, Signal
import win32com.client
import pythoncom

class SAPIEventHandler:
    """Event handler for native Windows SAPI Speech Recognition."""
    def __init__(self):
        self.callback = None
        self.log_callback = None
    
    def OnRecognition(self, StreamNum, StreamPos, RecogType, Result):
        try:
            phrase = Result.PhraseInfo.GetText()
            if self.callback:
                self.callback(phrase)
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"Error parsing SAPI recognition result: {e}")


class VoiceAssistantThread(QThread):
    # Signals for communicating with GUI
    status_updated = Signal(str)      # IDLE, LISTENING, PROCESSING, SPEAKING
    speech_detected = Signal(str)     # Raw transcribed text
    command_executed = Signal(str, str, str) # Trigger, Action, Speech Response
    assistant_spoke = Signal(str)     # Jarvis reply text
    log_message = Signal(str)         # Debug logs

    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.running = False
        self.listening = False
        self.tts = None
        
        # Core conversational memory (local chatbot brain)
        self.default_responses = {
            "what is your name": "I am JARVIS, your systems assistant. FRIDAY's modules are also available on my memory subgrid, sir.",
            "who are you": "I am your personal AI interface, sir. Ready to optimize your system parameters.",
            "how are you": "All processors are optimal, sir. Power levels are at maximum capacity.",
            "are you there": "At your service, sir. Core registers are stable.",
            "tell me a joke": "Why did the computer squeak, sir? Because it had a byte-size mouse!",
            "thank you": "Always a pleasure, sir. Happy to assist.",
            "who is iron man": "That would be Tony Stark, sir. A brilliant engineer indeed.",
            "self destruct": "Self destruct sequence initiated. Just kidding, sir. Core registers are safe."
        }
        
        self.init_tts()

    def init_tts(self):
        try:
            self.tts = win32com.client.Dispatch("SAPI.SpVoice")
            self.log_message.emit("Asynchronous speech synthesis engine ready.")
        except Exception as e:
            self.log_message.emit(f"TTS init error: {e}")

    def speak(self, text):
        """Speaks text asynchronously using SAPI."""
        if self.tts:
            self.status_updated.emit("SPEAKING")
            self.assistant_spoke.emit(text)
            self.log_message.emit(f"[Jarvis Voice] Speaking: {text}")
            # Flag 1 represents SPF_ASYNC
            self.tts.Speak(text, 1)
        else:
            self.assistant_spoke.emit(f"[TTS Offline] {text}")

    def stop_speech(self):
        if self.tts:
            # SPF_PURGEBEFORESPEAK (2)
            self.tts.Speak("", 2)

    def run(self):
        # Initialize COM on this background thread
        pythoncom.CoInitialize()
        
        self.running = True
        self.log_message.emit("Initializing instant local Windows SAPI voice recognition...")
        
        try:
            # Create local shared speech recognizer
            recognizer = win32com.client.Dispatch("SAPI.SpSharedRecognizer")
            context = recognizer.CreateRecoContext()
            
            # Setup Event Handler
            event_sink = win32com.client.WithEvents(context, SAPIEventHandler)
            event_sink.callback = self.on_speech_heard
            event_sink.log_callback = lambda msg: self.log_message.emit(msg)
            
            # Create default dictation grammar
            grammar = context.CreateGrammar(1)
            grammar.DictationSetState(1)
            
            self.log_message.emit("Instant local voice recognition engine started. Zero-latency listening active.")
            
            # Welcome greeting
            assistant_name = self.config.get("assistant_name", "JARVIS")
            self.speak(f"Systems online, sir. I am {assistant_name}, at your command.")
            
            # COM Message Pump Loop
            while self.running:
                if self.listening:
                    self.status_updated.emit("LISTENING")
                else:
                    self.status_updated.emit("IDLE")
                
                # Check for native Windows SAPI COM events
                pythoncom.PumpWaitingMessages()
                self.msleep(30)  # Low CPU overhead, highly responsive
                
        except Exception as e:
            self.log_message.emit(f"SAPI voice recognition initialization error: {e}. Falling back to command input.")
            # Keep thread alive to allow simulated/typed command execution if SAPI fails
            while self.running:
                self.msleep(100)
        finally:
            pythoncom.CoUninitialize()
            self.log_message.emit("Voice Assistant core thread stopped.")

    def on_speech_heard(self, text):
        if not self.listening:
            return
            
        phrase = text.strip().lower()
        if not phrase:
            return
            
        self.speech_detected.emit(phrase)
        self.status_updated.emit("PROCESSING")
        self.log_message.emit(f"[SAPI Voice Heard]: \"{phrase}\"")
        
        # 1. Process custom dynamics commands
        matched = self.process_system_command(phrase)
        if matched:
            return
            
        # 2. Process learning / teach instructions
        learned = self.process_learning_commands(phrase)
        if learned:
            return
            
        # 3. Process conversational responses
        self.process_conversational(phrase)

    def process_system_command(self, text) -> bool:
        commands = self.config.get("voice_commands", {})
        for trigger_phrase, cmd_info in commands.items():
            trigger = trigger_phrase.lower().strip()
            if trigger in text:
                action = cmd_info.get("action", "")
                speech_options = cmd_info.get("speech_responses", ["Command executed, sir."])
                response = random.choice(speech_options)
                
                self.speak(response)
                self.command_executed.emit(trigger, action, response)
                return True
        return False

    def process_learning_commands(self, text) -> bool:
        """
        Dynamically learns conversational responses on the fly.
        Triggers:
        - "teach [assistant_name] [question] response [answer]"
        - "remember [question] is [answer]"
        """
        name = self.config.get("assistant_name", "JARVIS").lower()
        
        # Parse: "teach jarvis what is your home response stark tower"
        if "teach " in text and " response " in text:
            try:
                # Remove "teach " part
                content = text.replace("teach ", "").strip()
                # Remove assistant name if present
                if content.startswith(name):
                    content = content[len(name):].strip()
                    
                question, answer = content.split(" response ", 1)
                question = question.strip()
                answer = answer.strip()
                
                if question and answer:
                    memory = self.config.get("conversational_memory", {})
                    memory[question] = answer
                    self.config.set("conversational_memory", memory)
                    
                    self.speak(f"Core registers updated, sir. I have learned to reply to \"{question}\" with \"{answer}\".")
                    self.command_executed.emit("teach", "save_memory", f"Learned: {question} -> {answer}")
                    return True
            except Exception as e:
                self.log_message.emit(f"Failed to parse teach instruction: {e}")
                
        # Parse: "remember [question] is [answer]"
        elif "remember " in text and " is " in text:
            try:
                content = text.replace("remember ", "").strip()
                question, answer = content.split(" is ", 1)
                question = question.strip()
                answer = answer.strip()
                
                if question and answer:
                    memory = self.config.get("conversational_memory", {})
                    memory[question] = answer
                    self.config.set("conversational_memory", memory)
                    
                    self.speak(f"Understood, sir. I'll remember that {question} is {answer}.")
                    self.command_executed.emit("remember", "save_memory", f"Learned: {question} is {answer}")
                    return True
            except Exception as e:
                self.log_message.emit(f"Failed to parse remember instruction: {e}")
                
        return False

    def process_conversational(self, text):
        """Conversational response generator using learned memory or defaults."""
        # 1. Check custom learned memories
        memory = self.config.get("conversational_memory", {})
        for q, a in memory.items():
            if q in text:
                self.speak(a)
                return
                
        # 2. Check defaults
        for q, a in self.default_responses.items():
            if q in text:
                self.speak(a)
                return
                
        # 3. Default fallback if assistant was mentioned
        name = self.config.get("assistant_name", "JARVIS").lower()
        if name in text:
            options = [
                "Always listening, sir.",
                "How can I help you optimize your gesture engine?",
                "Systems are active, sir. Ready to assist.",
                "SPyRaw core values are stable, sir. Awaiting instructions."
            ]
            self.speak(random.choice(options))
        else:
            # Silent fallback if assistant was not directly invoked
            pass
