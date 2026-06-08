import streamlit as st
import google.generativeai as genai
from PIL import Image
import datetime

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="KimikaLab Birtuala", page_icon="🧪", layout="wide")

# 2. CONEXIÓN SEGURA A LA API (Usando los Secretos)
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"Modelo disponible: {m.name}")
except KeyError:
    st.info("Nota técnica: Añade tu GEMINI_API_KEY en los secretos de Streamlit Cloud.")

model = genai.GenerativeModel("gemini-1.5-flash-latest")
# 3. DISEÑO DEL MENÚ LATERAL
with st.sidebar:
    st.title("🧪 KimikaLab")
    st.header("Atalak / Saberes Básicos")
    opcion = st.radio(
        "Aukeratu praktika bat / Elige una práctica:",
        (
            "1. Eredu Zientifikoa / Método Científico", 
            "2. Egitura atomikoa / Estructura atómica", 
            "3. Disoluzioak / Disoluciones", 
            "4. Estekiometria / Estequiometría", 
            "5. Zinetika / Cinética", 
            "📷 Arazoen Ebazpena / Resolución por Foto"
        )
    )
    
    st.markdown("---")
    if st.button("🔄 BERRIA / REINICIAR", use_container_width=True):
        st.session_state.mensajes = []
        st.rerun()

# 4. INSTRUCCIONES DEL SISTEMA (El "Cerebro" del simulador)
instrucciones_base = f"""
Eres un Simulador de Laboratorio de Química interactivo y tutor bilingüe para 1º Bachillerato (LOMLOE).
Práctica actual elegida por el alumno: {opcion}.

Reglas Estrictas:
1. NUNCA muestres código JSON, etiquetas internas o comandos. Solo texto natural.
2. Saluda en euskera y castellano. Tras la primera respuesta del alumno, detecta su idioma y responde ÚNICAMENTE en ese idioma.
3. PRÁCTICAS 1-5: Inventa variables químicas nuevas. Presenta el entorno y espera a que el alumno decida qué instrumental usar y qué cálculos hacer. No resuelvas el experimento por él.
4. TUTOR FOTO (Opción 6): Transcribe los datos de la foto mentalmente, pregunta qué pide el problema y guía paso a paso mediante el método socrático.
5. SEGURIDAD: Si propone una mezcla peligrosa, detén la simulación y explica la norma de seguridad.
"""

# 5. INICIALIZAR MEMORIA DEL CHAT
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []
    mensaje_bienvenida = f"Kaixo! Ongi etorri. Has aukeratu duzun praktika: **{opcion}**.\n\n¡Hola! Bienvenido/a. Has elegido la práctica: **{opcion}**.\n\n¿Estás preparado/a para comenzar? / Hasteko prest?"
    st.session_state.mensajes.append({"role": "assistant", "content": mensaje_bienvenida})

# 6. INTERFAZ PRINCIPAL
st.title("🧪 KimikaLab Birtuala")

# Lógica especial para analizar fotos
if "Foto" in opcion:
    st.info("Sube la imagen del problema o examen para que el simulador te guíe paso a paso.")
    archivo_foto = st.file_uploader("Carga una imagen (JPG/PNG)", type=["jpg", "png", "jpeg"])
    
    if archivo_foto is not None:
        imagen = Image.open(archivo_foto)
        st.image(imagen, caption="Irudia / Imagen subida", width=350)
        
        if st.button("Aztertu Irudia / Analizar Imagen"):
            with st.spinner("Analizando variables del problema..."):
                respuesta_vision = model.generate_content([instrucciones_base + "\nEl alumno ha subido esta imagen. Pregúntale qué datos logra identificar en ella para empezar a resolverlo.", imagen])
                st.session_state.mensajes.append({"role": "assistant", "content": respuesta_vision.text})
                st.rerun()

st.markdown("---")

# Renderizar el historial de conversación
for msg in st.session_state.mensajes:
    avatar_icon = "🧑‍🔬" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar_icon):
        st.markdown(msg["content"])

# 7. CHAT INTERACTIVO
entrada_alumno = st.chat_input("Idatzi hemen... / Escribe aquí tu respuesta...")

if entrada_alumno:
    st.session_state.mensajes.append({"role": "user", "content": entrada_alumno})
    with st.chat_message("user", avatar="🧑‍🔬"):
        st.markdown(entrada_alumno)
    
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Kalkulatzen / Procesando en el laboratorio..."):
            historial_texto = instrucciones_base + "\n\nHistorial de la conversación:\n"
            for m in st.session_state.mensajes:
                historial_texto += f"{m['role']}: {m['content']}\n"
            
            respuesta_ia = model.generate_content(historial_texto)
            st.markdown(respuesta_ia.text)
            
    st.session_state.mensajes.append({"role": "assistant", "content": respuesta_ia.text})

# 8. GENERACIÓN DEL INFORME DE EVALUACIÓN
st.markdown("---")
if st.button("📊 GENERAR INFORME / TXOSTENA"):
    if len(st.session_state.mensajes) > 2:
        with st.spinner("Generando evaluación pedagógica..."):
            historial = str(st.session_state.mensajes)
            prompt_eval = f"Actúa como profesor evaluador. Analiza este historial de sesión de química: {historial}. Genera un informe breve estructurado en: 1. Conceptos dominados (Aciertos), 2. Errores cometidos y cómo se solucionaron, 3. Nota cualitativa general."
            reporte = model.generate_content(prompt_eval).text
            
            st.subheader("Irakaslearentzako Txostena / Informe de Evaluación")
            st.info(reporte)
            st.download_button(
                label="Descargar Informe (.txt)", 
                data=reporte, 
                file_name=f"informe_kimikalab_{datetime.date.today()}.txt"
            )
    else:
        st.error("Aún no hay suficiente actividad en el laboratorio para generar un informe.")
