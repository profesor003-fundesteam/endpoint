"""API de Groq (modelo openai/gpt-oss-120b): recomendación de reciclaje por material.
Si no hay internet, clave o respuesta válida, usa el diccionario local datos/recomendaciones.json (try/except)."""
import json
import os
from dotenv import load_dotenv

load_dotenv()                                   # lee GROQ_API_KEY del archivo .env
BASE = os.path.dirname(os.path.abspath(__file__))
MODELO = "openai/gpt-oss-120b"
PROMPT = ("Eres asesor de un centro de acopio de reciclaje. Responde SOLO un JSON con la clave "
          "'recomendacion': un consejo corto en español (máximo 20 palabras) para manejar ese material.")


PROMPT_INFORME = ("Eres analista de datos de un centro de acopio. Recibes datos agregados en JSON. Redacta un informe en español de "
                  "máximo 5 líneas con los hallazgos principales y una recomendación. No inventes cifras que no estén en los datos. "
                  "Responde SOLO un JSON con la clave 'informe'.")


def _crear_cliente(timeout):
    if not os.getenv("GROQ_API_KEY"):
        return None
    try:
        from groq import Groq
        return Groq(timeout=timeout, max_retries=0)
    except Exception as e:
        print("Groq no disponible:", e)
        return None


def crear_analista(timeout=15, _cliente=None):
    """Clausura: devuelve generar_informe(datos, informe_local). Groq interpreta los datos que calculó Pandas."""
    cliente = _cliente or _crear_cliente(timeout)

    def generar_informe(datos, informe_local):
        if cliente:
            try:
                r = cliente.chat.completions.create(
                    model=MODELO, temperature=0.3, reasoning_effort="low", response_format={"type": "json_object"},
                    messages=[{"role": "system", "content": PROMPT_INFORME},
                              {"role": "user", "content": json.dumps(datos, ensure_ascii=False, default=float)}])
                texto = str(json.loads(r.choices[0].message.content)["informe"]).strip()
                return {"informe": texto, "fuente": "groq"}
            except Exception as e:
                print(f"[Groq falló: {type(e).__name__}] usando informe local")
        return {"informe": informe_local, "fuente": "local"}

    return generar_informe


def crear_asesor(timeout=10, _cliente=None):
    """Clausura: devuelve recomendar(material), que recuerda el cliente de Groq y las respuestas ya pedidas (caché)."""
    cache, cliente = {}, _cliente or _crear_cliente(timeout)
    with open(os.path.join(BASE, "datos", "recomendaciones.json"), encoding="utf-8") as f:
        respaldo = json.load(f)

    def recomendar(material):
        if material in cache:
            return {**cache[material], "cache": True}
        if cliente:
            try:
                r = cliente.chat.completions.create(
                    model=MODELO, temperature=0.2, reasoning_effort="low", response_format={"type": "json_object"},
                    messages=[{"role": "system", "content": PROMPT}, {"role": "user", "content": f"Material: {material}"}])
                res = {"recomendacion": str(json.loads(r.choices[0].message.content)["recomendacion"]).strip(), "fuente": "groq"}
                cache[material] = res
                return res
            except Exception as e:              # sin internet, clave inválida, límite de uso, JSON inválido...
                print(f"[Groq falló: {type(e).__name__}] usando respaldo local")
        return {"recomendacion": respaldo.get(material, respaldo["otros"]), "fuente": "local"}

    return recomendar


recomendar = crear_asesor()
generar_informe = crear_analista()
