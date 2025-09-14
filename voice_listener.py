import speech_recognition as sr
import pyttsx3
import json
from datetime import datetime, date
import re
import os

class VoiceAssistant:
    def __init__(self):
        print("🎧 Iniciando asistente de voz...")
        self.setup_tts()
        self.setup_recognizer()
    
    def setup_recognizer(self):
        """Configura el reconocimiento de voz"""
        self.recognizer = sr.Recognizer()
        try:
            # Listar micrófonos disponibles
            print("Buscando micrófonos...")
            mic_list = sr.Microphone.list_microphone_names()
            print(f"Micrófonos encontrados: {mic_list}")
            
            self.microphone = sr.Microphone()
            print("✅ Micrófono configurado")
            
        except Exception as e:
            print(f"❌ Error con micrófono: {e}")
            self.microphone = None
    
    def setup_tts(self):
        """Configura el sintetizador de voz"""
        try:
            self.tts_engine = pyttsx3.init()
            print("✅ Sintetizador de voz listo")
        except Exception as e:
            print(f"❌ Error con sintetizador: {e}")
    
    def speak(self, text):
        """Reproduce texto como voz"""
        print(f"🔊 ASISTENTE: {text}")
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"❌ Error al hablar: {e}")
    
    def listen(self):
        """Escucha y devuelve el texto reconocido"""
        if not self.microphone:
            return "Error: No se encontró micrófono"
        
        try:
            print("🎤 ESCUCHANDO... Habla ahora (5 segundos)")
            
            with self.microphone as source:
                # Ajustar para ruido ambiental
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=8)
            
            print("✅ Procesando audio...")
            
            # Intentar reconocimiento
            try:
                text = self.recognizer.recognize_google(audio, language='es-ES')
                print(f"✅ Reconocido: {text}")
                return text
            except sr.UnknownValueError:
                return "No entendí"
            except sr.RequestError:
                return "Error de conexión"
                
        except sr.WaitTimeoutError:
            return "No escuché nada"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def process_command(self, command):
        """Procesa el comando"""
        if not command or "no entendí" in command.lower():
            return "No te escuché bien. ¿Puedes repetir?"
        
        command_lower = command.lower()
        
        # Comandos simples
        if any(word in command_lower for word in ['hola', 'buenos días']):
            return "¡Hola! ¿En qué puedo ayudarte?"
        
        elif any(word in command_lower for word in ['qué tengo hoy', 'agenda']):
            return self.get_daily_summary()
        
        elif any(word in command_lower for word in ['cita', 'agendar']):
            return self.add_appointment(command)
        
        elif 'gracias' in command_lower:
            return "¡De nada! ¿Algo más?"
        
        else:
            return f"Entendí: {command}. ¿Quieres agregarlo como cita?"
    
    def get_daily_summary(self):
        """Obtiene resumen del día"""
        try:
            with open("agenda.json", "r", encoding="utf-8") as f:
                agenda = json.load(f)
            
            today = str(date.today())
            if today not in agenda:
                return "Hoy no tienes nada programado"
            
            activities = agenda[today]
            summary = "Hoy tienes: "
            
            if 'citas' in activities:
                for cita in activities['citas']:
                    summary += f"Cita a las {cita.get('hora', '')} {cita.get('actividad', '')}. "
            
            return summary
            
        except:
            return "No pude leer la agenda"
    
    def add_appointment(self, command):
        """Agrega cita simple"""
        try:
            # Extraer hora
            hora_match = re.search(r'(\d{1,2})', command)
            hora = hora_match.group(1) + ":00" if hora_match else "10:00"
            
            # Extraer actividad
            actividad = "Cita importante"
            if ' con ' in command:
                actividad = command.split(' con ')[1]
            elif ' para ' in command:
                actividad = command.split(' para ')[1]
            
            # Guardar en agenda
            try:
                with open("agenda.json", "r", encoding="utf-8") as f:
                    agenda = json.load(f)
            except:
                agenda = {}
            
            today = str(date.today())
            if today not in agenda:
                agenda[today] = {"citas": [], "medicamentos": []}
            
            agenda[today]["citas"].append({
                "hora": hora,
                "actividad": actividad,
                "tipo": "personal"
            })
            
            with open("agenda.json", "w", encoding="utf-8") as f:
                json.dump(agenda, f, indent=2)
            
            return f"✅ Listo. Cita a las {hora} para {actividad}"
            
        except Exception as e:
            return f"Error: {str(e)}"
    def process_command(self, command):
        """Procesa el comando y guarda automáticamente en la agenda si es recordatorio"""
        if not command or "no entendí" in command.lower():
            return "No te escuché bien. ¿Puedes repetir?"
        
        command_lower = command.lower()

        # --- Comandos que NO son recordatorios ---
        if any(word in command_lower for word in ['hola', 'buenos días']):
            return "¡Hola! ¿En qué puedo ayudarte?"
        
        elif any(word in command_lower for word in ['gracias']):
            return "¡De nada! ¿Algo más?"

        elif any(word in command_lower for word in ['qué tengo hoy', 'agenda']):
            return self.get_daily_summary()
        
        # --- Todo lo demás se guarda en la agenda ---
        return self.add_appointment(command)


    def add_appointment(self, command):
        """Agrega cualquier frase como cita/recordatorio en la agenda"""
        try:
            # Buscar una hora en formato HH o HH:MM
            hora_match = re.search(r'(\d{1,2}(:\d{2})?)', command)
            hora = hora_match.group(1) if hora_match else "Sin hora"
            
            # Guardar el resto como actividad
            actividad = command
            
            # Cargar agenda existente
            try:
                with open("agenda.json", "r", encoding="utf-8") as f:
                    agenda = json.load(f)
            except:
                agenda = {}
            
            today = str(date.today())
            if today not in agenda:
                agenda[today] = {"citas": [], "medicamentos": []}
            
            # Agregar cita
            agenda[today]["citas"].append({
                "hora": hora,
                "actividad": actividad,
                "tipo": "recordatorio"
            })
            
            # Guardar en archivo
            with open("agenda.json", "w", encoding="utf-8") as f:
                json.dump(agenda, f, indent=2, ensure_ascii=False)
            
            return f"✅ Guardé tu recordatorio: '{actividad}' a las {hora}"
        
        except Exception as e:
            return f"Error al guardar recordatorio: {str(e)}"

def main():
    print("=== INICIANDO ASISTENTE ===")
    
    assistant = VoiceAssistant()
    
    if assistant.microphone is None:
        print("❌ Conecta un micrófono")
        return
    
    print("🎤 HABLA AHORA...")
    command = assistant.listen()
    
    if command and "no entendí" not in command.lower():
        print(f"🗣️ Tú: {command}")
        response = assistant.process_command(command)
        print(f"🔊 Asistente: {response}")
        assistant.speak(response)
        
        # Guardar para la app
        with open("last_command.txt", "w", encoding="utf-8") as f:
            f.write(f"{command}|{response}")
    else:
        error_msg = "No te escuché. Habla más fuerte."
        print(f"❌ {error_msg}")
        with open("last_command.txt", "w", encoding="utf-8") as f:
            f.write(f"error|{error_msg}")

if __name__ == "__main__":
    main()