import streamlit as st
import json
from datetime import date
import subprocess
import os
import time
import psutil

# === Funciones auxiliares ===


def fecha_hoy():
    return date.today().strftime("%Y-%m-%d")


def consultar_agenda():
    hoy = fecha_hoy()
    try:
        with open("agenda.json", "r", encoding="utf-8") as f:
            agenda = json.load(f)
        return agenda.get(hoy, {})
    except:
        return {}

def leer_ultimo_comando():
    try:
        with open("last_command.txt", "r", encoding="utf-8") as f:
            contenido = f.read().strip()
            if "|" in contenido:
                comando, respuesta = contenido.split("|", 1)
                return comando, respuesta
            return contenido, ""
    except:
        return "", ""

def is_listening_active():
    try:
        for proc in psutil.process_iter(['name', 'cmdline']):
            if proc.info['cmdline'] and 'python' in proc.info['cmdline'][0] and 'voice_listener.py' in ' '.join(proc.info['cmdline']):
                return True
    except:
        pass
    return False

def start_listening():
    try:
        # Detener procesos anteriores
        for proc in psutil.process_iter(['name', 'cmdline']):
            if proc.info['cmdline'] and 'python' in proc.info['cmdline'][0] and 'voice_listener.py' in ' '.join(proc.info['cmdline']):
                proc.terminate()
        
        # Ejecutar nuevo proceso
        process = subprocess.Popen(["python", "voice_listener.py"])
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False

def mostrar_actividades():
    actividades = consultar_agenda()
    hoy = fecha_hoy()
    
    st.subheader(f"📅 Agenda para hoy ({hoy})")
    
    if not actividades:
        st.info("✅ No hay actividades programadas para hoy")
        return
    
    if 'citas' in actividades and actividades['citas']:
        st.markdown("### 🏥 Citas")
        for i, cita in enumerate(actividades['citas']):
            st.write(f"**⏰ {cita.get('hora', 'Sin hora')}** - {cita.get('actividad', 'Sin nombre')}")
    
    if 'medicamentos' in actividades and actividades['medicamentos']:
        st.markdown("### 💊 Medicamentos")
        for i, med in enumerate(actividades['medicamentos']):
            st.write(f"**⏰ {med.get('hora', 'Sin hora')}** - {med.get('medicamento', 'Sin nombre')} {med.get('dosis', '')}")

# === INTERFAZ PRINCIPAL ===
st.set_page_config(page_title="Asistente de Voz", page_icon="🧓", layout="wide")

st.title("🧓 Asistente de Voz para Personas Mayores")

# === SIDEBAR ===
st.sidebar.header("ℹ️ Información del Sistema")
st.sidebar.info("""
 **Funcionalidades:**
- 🎤 Reconocimiento de voz
- 📅 Gestión de agenda médica
- ⏰ Recordatorios con hora
- 💊 Control de medicamentos
""")

# === COLUMNAS PRINCIPALES ===
col1, col2 = st.columns([2, 1])

with col1:
    # MOSTRAR AGENDA
    mostrar_actividades()
    
    # BOTÓN PARA ACTUALIZAR
    if st.button("🔄 Actualizar Agenda", use_container_width=True):
        st.rerun()

with col2:
    # SECCIÓN DE VOZ
    st.header("🎤 Control por Voz")
    
    # Estado de escucha
    if is_listening_active():
        st.warning("⚠️ El asistente está escuchando...")
    else:
        st.info("🎤 Presiona el botón para hablar")
    
    # BOTÓN PRINCIPAL DE VOZ
    if st.button("🎤 **HABLAR CON EL ASISTENTE**", 
                type="primary", 
                use_container_width=True,
                help="Presiona y habla claramente al micrófono"):
        
        if start_listening():
            st.success("✅ Escuchando... habla ahora")
            # Esperar y actualizar
            time.sleep(3)
            st.rerun()
        else:
            st.error("❌ Error al iniciar el micrófono")
    
    # MOSTRAR ÚLTIMO COMANDO
    comando, respuesta = leer_ultimo_comando()
    
    if comando:
        st.markdown("---")
        st.subheader("Último comando:")
        
        if comando == "no_voice_detected":
            st.error("❌ No se detectó voz. Habla más claro y cerca del micrófono.")
        else:
            st.success(f"**🗣️ Dijiste:** {comando}")
            if respuesta:
                st.info(f"**🔊 Asistente respondió:** {respuesta}")
    
# BOTÓN PARA LEER AGENDA EN VOZ ALTA
if st.button("🔊 Escuchar mi agenda", use_container_width=True):
    st.info("🔊 Reproduciendo agenda...")
    try:
        import pyttsx3
        
        actividades = consultar_agenda()  # Ya devuelve SOLO lo de hoy
        engine = pyttsx3.init()
        
        if actividades:
            mensaje = "Tu agenda para hoy: "
            
            if 'citas' in actividades:
                for cita in actividades['citas']:
                    mensaje += f"Cita a las {cita.get('hora', '')}, {cita.get('actividad', '')}. "
            
            if 'medicamentos' in actividades:
                for med in actividades['medicamentos']:
                    mensaje += f"Medicamento a las {med.get('hora', '')}, {med.get('medicamento', '')}, dosis {med.get('dosis', '')}. "
            
            engine.say(mensaje)
            engine.runAndWait()
        else:
            engine.say("No tienes actividades para hoy")
            engine.runAndWait()
            
    except Exception as e:
        st.error(f"Error al reproducir voz: {e}")

# === INSTRUCCIONES ===
with st.expander("📋 ¿Cómo funciona?"):
    st.write("""
    1. **Presiona 'HABLAR CON EL ASISTENTE'**
    2. **Habla claro y cerca del micrófono**
    3. **Di por ejemplo:**
       - "Medicamento ibuprofeno a las 7"
       - "Cita a las 3 con Juan"
       - "Cita a las 2:30 con el doctor"
    4. **El asistente agregará tu cita y te responderá por voz**
    """)

# === VERIFICACIÓN DE ARCHIVOS ===
if not os.path.exists("agenda.json"):
    st.sidebar.warning("⚠️ Creando archivo agenda.json...")
    with open("agenda.json", "w", encoding="utf-8") as f:
        json.dump({}, f, indent=2)

# === BOTÓN DE EMERGENCIA ===
if st.sidebar.button("🔄 Reiniciar Todo", type="secondary"):
    try:
        # Limpiar archivos temporales
        for archivo in ["last_command.txt"]:
            if os.path.exists(archivo):
                os.remove(archivo)
        st.sidebar.success("✅ Sistema reiniciado")
        st.rerun()
    except:
        st.sidebar.error("❌ Error al reiniciar")