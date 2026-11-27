"""EcoEndpoint Lite - BACKEND (Flask, API REST). El FRONTEND está en la carpeta frontend/.
Ejecución:  python app.py   y abrir  http://localhost:5000"""
import os
import threading
import matplotlib
matplotlib.use("Agg")                       # gráficas sin ventana (se envían al navegador)
from flask import Flask, jsonify, request, send_from_directory, abort
from flask.json.provider import DefaultJSONProvider
from centro import CentroAcopio
from structures import Pila, Cola
import api_off
from groq_client import recomendar, generar_informe
import graficas
from ordenamiento import burbuja, merge_sort, busqueda_binaria, busqueda_lineal, cargar_camion
from main import MATERIALES, datos_ejemplo

FRONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")


class Proveedor(DefaultJSONProvider):       # permite enviar números de Pandas/NumPy en JSON
    @staticmethod
    def default(o):
        return o.item() if hasattr(o, "item") else DefaultJSONProvider.default(o)


app = Flask(__name__, static_folder=FRONT, static_url_path="/static")
app.json = Proveedor(app)
c, estado, candado = CentroAcopio(), {"actual": None}, threading.Lock()


def snapshot():
    return {"cola": [{"id": t.id, "nombre": t.nombre, "hora": t.creado} for t in c.cola.to_list()],
            "historial": [r.to_dict() for r in c.pila.to_list()],          # la Pila: lo último primero
            "actual": estado["actual"], "resumen": c.analista.resumen(), "materiales": MATERIALES}


def tabla(df):
    return df.reset_index().to_dict("records")


def error(msg, code=400):
    return jsonify(error=msg), code


@app.get("/")
def index():
    return send_from_directory(FRONT, "index.html")


@app.get("/api/estado")
def ver_estado():
    return jsonify(snapshot())


@app.post("/api/cola")                      # Cola FIFO: entra al final
def agregar_turno():
    nombre = (request.get_json() or {}).get("nombre", "").strip()
    if not nombre:
        return error("Escribe un nombre.")
    c.nuevo_turno(nombre)
    return jsonify(snapshot())


@app.post("/api/atender")                   # Cola FIFO: sale el primero
def atender():
    t = c.atender()
    if not t:
        return error("No hay turnos en espera.")
    estado["actual"] = {"id": t.id, "nombre": t.nombre}
    return jsonify(snapshot())


@app.get("/api/consultar")                  # API externa Open Food Facts
def consultar():
    codigo = request.args.get("codigo", "").strip()
    if not codigo:
        return error("Escribe un código de barras.")
    info = api_off.consultar(codigo)
    if not info or not info.get("material"):
        return jsonify(encontrado=False)
    return jsonify(encontrado=True, **info)


@app.get("/api/recomendar")                 # API de Groq (con respaldo local)
def recomendacion():
    material = request.args.get("material", "")
    if material not in c.factores:
        return error("Elige un material.")
    return jsonify(recomendar(material))


@app.get("/api/informe")                    # Pandas calcula + Groq interpreta
def informe():
    a = c.analista
    if a.df.empty:
        return error("Aún no hay registros.")
    return jsonify(generar_informe(a.datos_para_informe(), a.informe_local()))


@app.post("/api/registrar")
def registrar():
    d = request.get_json() or {}
    mat = d.get("material")
    if mat not in c.factores:
        return error("Elige un material.")
    try:
        kg = float(d.get("kg") or c.factores[mat]["peso_kg"])
        if kg <= 0:
            raise ValueError
    except ValueError:
        return error("El peso debe ser un número mayor a 0.")
    turno = estado["actual"]["nombre"] if estado["actual"] else d.get("turno", "")
    reg = c.registrar(mat, kg, turno, d.get("origen", "manual"), d.get("producto", ""))
    estado["actual"] = None
    return jsonify(registro=reg.to_dict(), **snapshot())


@app.post("/api/deshacer")                  # Pila LIFO: sale el último
def deshacer():
    r = c.deshacer()
    return jsonify(deshecho=r.to_dict() if r else None, **snapshot())


@app.post("/api/ejemplo")
def ejemplo():
    datos_ejemplo(c)
    return jsonify(snapshot())


@app.post("/api/reiniciar")
def reiniciar():
    c.analista.vaciar(); c.pila, c.cola, estado["actual"] = Pila(), Cola(), None
    return jsonify(snapshot())


@app.get("/api/reporte")                    # Pandas
def reporte():
    a = c.analista
    if a.df.empty:
        return jsonify(vacio=True)
    dia = a.por_dia().reset_index(); dia["dia"] = dia["dia"].astype(str)
    return jsonify(vacio=False, resumen=a.resumen(), por_material=tabla(a.por_material()), por_dia=dia.to_dict("records"),
                   origen=tabla(a.por_origen()), estadistica=a.estadistica(), describe=tabla(a.describe_por_material()))


@app.get("/api/ranking")                    # Ordenamiento
def ranking():
    if c.analista.df.empty:
        return error("Aún no hay registros.")
    items = list(c.analista.por_material()["kg"].items())
    b, cb = burbuja(items, clave=lambda t: t[1], reverso=True)
    m, cm = merge_sort(items, clave=lambda t: t[1], reverso=True)
    return jsonify(ranking=[{"material": k, "kg": round(v, 2)} for k, v in m], burbuja=cb, merge=cm, coinciden=(b == m))


@app.get("/api/buscar")                     # Búsqueda binaria vs lineal
def buscar():
    regs, _ = merge_sort(c.analista.df.to_dict("records"), clave=lambda r: r["id"])
    if not regs:
        return error("Aún no hay registros.")
    try:
        objetivo = int(request.args.get("id", ""))
    except ValueError:
        return error("Escribe un ID numérico.")
    i, pb = busqueda_binaria(regs, objetivo, clave=lambda r: r["id"])
    _, pl = busqueda_lineal(regs, objetivo, clave=lambda r: r["id"])
    return jsonify(encontrado=i >= 0, registro=regs[i] if i >= 0 else None, binaria=pb, lineal=pl, total=len(regs))


@app.post("/api/camion")                    # Algoritmo voraz
def camion():
    if c.analista.df.empty:
        return error("Aún no hay registros.")
    try:
        cap = float((request.get_json() or {}).get("capacidad") or 20)
        if cap <= 0:
            raise ValueError
    except ValueError:
        return error("La capacidad debe ser un número mayor a 0.")
    stock = c.analista.por_material()["kg"]
    items = [{"material": m, "kg": float(kg), "co2_kg": c.factores[m]["co2"]} for m, kg in stock.items()]
    plan, kg, co2 = cargar_camion(items, cap)
    return jsonify(plan=[p for p in plan if p["kg"] > 0], kg=kg, capacidad=cap, co2=co2)


@app.get("/api/graficas")                   # Matplotlib
def generar_graficas():
    if c.analista.df.empty:
        return error("Aún no hay registros.")
    with candado:
        rutas = graficas.generar(c.analista, mostrar=False)
    return jsonify(archivos=[os.path.basename(r) for r in rutas])


@app.get("/graficas/<archivo>")
def ver_grafica(archivo):
    if not archivo.endswith(".png"):
        abort(404)
    return send_from_directory(graficas.CARPETA, archivo)


if __name__ == "__main__":
    print("EcoEndpoint Lite en http://localhost:5000  (Ctrl+C para detener)")
    app.run(host="127.0.0.1", port=5000, debug=False)
