# EcoEndpoint Lite

Analista de datos para centros de acopio · Samsung Innovation Campus · Equipo **Endpoint**

**Integrantes:** Lince Ávila · Gustavo Almanza · Juan Meneses · Isaías Domínguez

## Planteamiento

Los centros de acopio reciben residuos de muchas personas, pero casi nunca registran de forma ordenada qué material llega, cuánto pesa ni cuánto CO₂ se evita al reciclarlo. Sin datos no se pueden tomar decisiones.

## Objetivos

- Ordenar la atención al público con una Cola (FIFO) de turnos.
- Permitir corregir errores del operador con una Pila (LIFO) que deshace el último registro.
- Consultar el material del empaque de un producto con una API pública (Open Food Facts) a partir de su código de barras.
- Obtener una recomendación de reciclaje por material con la API de Groq (modelo de lenguaje), con respaldo local si no hay internet.
- Analizar los datos con Pandas: kg y CO₂ por material, por día y ranking de materiales.
- Generar un informe del analista: Pandas calcula las cifras y Groq las interpreta (solo datos agregados, sin nombres de personas). Sin internet se genera un informe con plantilla.

## Herramientas

Python 3 (POO, clausuras, listas, diccionarios, `dataclasses`, `try/except`) · Flask · Pandas · Matplotlib · Requests · HTML, CSS y JavaScript · API Open Food Facts · API de Groq (modelo `gpt-oss-120b`) · JSON y CSV.

## Arquitectura (frontend + backend, 100 % local)

- **Backend (Python + Flask):** `app.py` expone una API REST y usa los demás módulos.
- **Frontend (HTML + CSS + JavaScript):** carpeta `frontend/`. Panel web con turnos, registro, historial, reportes, algoritmos y gráficas. Solo muestra datos y llama a la API del backend.
- **Consola:** también es posible usar el sistema sin navegador con `python main.py`.

## Requisitos

- Python 3.10 o superior
- Navegador web (Chrome o Edge)
- Internet (opcional): solo para las dos APIs

## Cómo ejecutar

1. Instalar las dependencias:

```
python -m pip install -r requirements.txt
```

2. Iniciar el servidor:

```
python app.py
```

3. Abrir http://localhost:5000 en el navegador. El botón «Cargar datos de ejemplo» permite ver los reportes y las gráficas.

**Activar Groq (opcional):** crear un archivo llamado `.env` en la misma carpeta que `app.py`, usando como guía `env_example.txt`. El contenido debe ser esta línea con la clave real:

```
GROQ_API_KEY=tu_clave_de_groq
```

Sin clave o sin internet, el sistema usa textos de respaldo y sigue funcionando. Si falla la API de códigos de barras, el material se elige a mano.

## Resultado

Una aplicación web local que registra turnos, residuos y pesos, calcula el CO₂ evitado (factor del material × kg) y genera reportes, gráficas y un informe con Pandas. Los reportes se pueden exportar a CSV. Los factores de CO₂ de `datos/factores.json` son valores de referencia ajustables.

## Estructura del proyecto

```
app.py              Backend Flask (API REST)
main.py             Menú de consola
centro.py           Clase CentroAcopio
structures.py       Pila (LIFO) y Cola (FIFO)
models.py           Clases Turno y Registro
api_off.py          Cliente de la API Open Food Facts
groq_client.py      Cliente de la API de Groq
analisis.py         Análisis de datos con Pandas
ordenamiento.py     Algoritmos de ordenamiento, búsqueda y planificación
graficas.py         Gráficas con Matplotlib
frontend/           Interfaz web (HTML, CSS y JavaScript)
datos/              Factores, recomendaciones de respaldo y registros
env_example.txt     Plantilla del archivo .env (sin clave real)
requirements.txt    Dependencias del proyecto
```

## Limitaciones

- Los factores de CO₂ son valores de referencia y deben calibrarse con una fuente oficial.
- Open Food Facts es una base colaborativa: no todos los productos incluyen el material del empaque. En ese caso se elige a mano.
- La recomendación y el informe con IA requieren internet y una clave de Groq.

---

Datos de productos: Open Food Facts (licencia ODbL).
