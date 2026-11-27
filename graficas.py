"""Visualización de datos con Matplotlib. Guarda PNG en graficas/ y las muestra."""
import os
import matplotlib.pyplot as plt

CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graficas")


def generar(analista, mostrar=True):
    os.makedirs(CARPETA, exist_ok=True)
    pm, pdia = analista.por_material(), analista.por_dia()
    rutas = []

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(pm.index, pm["kg"], color="#2E7D5B"); ax.set_title("Kilos recibidos por material"); ax.set_ylabel("kg")
    rutas.append(_guardar(fig, "kg_por_material.png"))

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot([str(d) for d in pdia.index], pdia["co2"], marker="o", color="#1F5FA8")
    ax.set_title("CO2 evitado por día"); ax.set_ylabel("kg de CO2"); ax.tick_params(axis="x", rotation=45)
    rutas.append(_guardar(fig, "co2_por_dia.png"))

    fig, ax = plt.subplots(figsize=(5, 5))
    ax.pie(pm["kg"], labels=pm.index, autopct="%1.1f%%"); ax.set_title("Distribución por material")
    rutas.append(_guardar(fig, "distribucion_material.png"))

    if mostrar:
        plt.show()
    plt.close("all")
    return rutas


def _guardar(fig, nombre):
    fig.tight_layout()
    ruta = os.path.join(CARPETA, nombre)
    fig.savefig(ruta, dpi=120)
    return ruta
