
# EcoEndpoint Lite
Analista de datos para centros de acopio · Samsung Innovation Campus · Módulo Python · Equipo **Endpoint**
Lince Ávila, Gustavo Almanza, Juan Meneses, Isaías Domínguez

## Planteamiento
Los centros de acopio reciben residuos de muchas personas, pero casi nunca registran de forma ordenada qué material llega,
cuánto pesa ni cuánto CO₂ se evita al reciclarlo. Sin datos no se pueden tomar decisiones.

## Objetivos
- Ordenar la atención al público con una **Cola (FIFO)** de turnos.
- Permitir corregir errores del operador con una **Pila (LIFO)** que deshace el último registro.
- Consultar el material del empaque de un producto con una **API pública** (Open Food Facts) usando su código de barras.
- Obtener una recomendación de reciclaje por material con la **API de Groq** (modelo de lenguaje), con respaldo local si no hay internet.
- Generar un **informe del analista**: Pandas calcula las cifras y Groq las interpreta (solo datos agregados, sin nombres); sin internet se genera un informe con plantilla.
- Analizar los datos con **Pandas**: kg y CO₂ por material, por día y ranking de materiales.

## Herramientas
Python 3 (POO, clausuras, listas, diccionarios, `dataclasses`, `try/except`) · Pandas · Matplotlib · Requests · API Open Food Facts · API de Groq (modelo gpt-oss-120b) · JSON/CSV.

## Arquitectura (frontend + backend, 100% local)
- **Backend (Python + Flask):** `app.py` expone una API REST y usa `centro.py`, `analisis.py`, `ordenamiento.py`, `api_off.py` y `graficas.py`.
- **Frontend (HTML + CSS + JavaScript):** carpeta `frontend/`. Panel web con turnos, registro, historial, reportes, algoritmos y gráficas. Solo muestra datos y llama a la API del backend.
- También se puede usar sin navegador: `python main.py` (versión de consola).

## Cómo ejecutar
Para la recomendación con Groq, copia `.env.example` como `.env` y pega tu `GROQ_API_KEY`. Sin clave o sin internet, el sistema usa el texto de respaldo.
```
pip install -r requirements.txt
python app.py
```
Abre http://localhost:5000 en el navegador. Usa «Cargar datos de ejemplo» para ver los reportes y las gráficas.
Sin internet funciona igual: si falla la API de códigos de barras, se elige el material a mano.

## Resultado
Un programa de consola que registra turnos, residuos y pesos, calcula el CO₂ evitado (factor del material × kg) y genera
reportes con Pandas, exportables a CSV. Los factores de CO₂ de `datos/factores.json` son valores de referencia ajustables.

## Estructura
`app.py` backend Flask · `frontend/` interfaz web · `main.py` menú de consola · `centro.py` clase CentroAcopio · `structures.py` Pila y Cola · `models.py` Turno y Registro ·
`api_off.py` cliente de la API · `analisis.py` Pandas · `ordenamiento.py` algoritmos · `graficas.py` Matplotlib · `datos/` factores y registro.

Datos de productos: Open Food Facts (ODbL).
