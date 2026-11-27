"""EcoEndpoint Lite - menú de consola. Ejecuta: python main.py"""
import random
from datetime import datetime, timedelta
from centro import CentroAcopio
import api_off
from groq_client import recomendar, generar_informe
import graficas
from ordenamiento import burbuja, merge_sort, busqueda_binaria, busqueda_lineal, cargar_camion

MATERIALES = ["plastico", "vidrio", "metal", "papel", "carton", "organico", "otros"]
MENU = """
===== EcoEndpoint Lite =====
1. Agregar persona a la cola de turnos
2. Ver cola de turnos
3. Atender siguiente turno y registrar residuo
4. Deshacer último registro (Pila)
5. Ver historial de esta sesión (Pila)
6. Reporte de análisis (Pandas)
7. Exportar reporte a CSV
8. Cargar datos de ejemplo (30 registros)
9. Ranking de materiales (ordenamiento: burbuja vs merge sort)
10. Buscar registro por ID (búsqueda binaria vs lineal)
11. Plan de carga del camión (algoritmo voraz)
12. Estadística descriptiva (media, mediana, desviación...)
13. Gráficas (Matplotlib)
14. Informe del analista (Pandas calcula + Groq interpreta)
0. Salir"""


def leer_kg(defecto):
    while True:
        txt = input(f"Peso en kg (Enter = {defecto} estimado): ").strip().replace(",", ".")
        if not txt:
            return defecto
        try:
            kg = float(txt)
            if kg > 0:
                return kg
        except ValueError:
            pass
        print("  Escribe un número mayor a 0.")


def elegir_material():
    for i, m in enumerate(MATERIALES, 1):
        print(f"  {i}. {m}")
    while True:
        op = input("Material: ").strip()
        if op.isdigit() and 1 <= int(op) <= len(MATERIALES):
            return MATERIALES[int(op) - 1]
        print("  Opción inválida.")


def atender_y_registrar(c):
    t = c.atender()
    if not t:
        return print("No hay turnos en espera.")
    print(f"Atendiendo a: {t.nombre}")
    material, origen, producto = None, "manual", ""
    codigo = input("Código de barras del producto (Enter = elegir material a mano): ").strip()
    if codigo:
        info = api_off.consultar(codigo)                              # API Open Food Facts
        if info and info["material"]:
            material, origen, producto = info["material"], "api", info["producto"]
            print(f"  API -> {producto} | empaque: {material}" + (" (desde caché)" if info.get('cache') else ""))
        else:
            print("  No se pudo obtener el material (sin internet, producto no encontrado o sin datos). Elígelo tú:")
    material = material or elegir_material()
    kg = leer_kg(c.factores[material]["peso_kg"])
    r = c.registrar(material, kg, t.nombre, origen, producto)
    print(f"Registrado: {r.material} {r.kg} kg | CO2 evitado {r.co2} kg")
    rec = recomendar(material)
    print(f"Recomendación ({'IA Groq' if rec['fuente'] == 'groq' else 'respaldo local'}): {rec['recomendacion']}")


def reporte(c):
    s = c.analista.resumen()
    if not s:
        return print("Aún no hay registros.")
    print(f"\nRegistros: {s['registros']} | Total: {s['kg_total']} kg | CO2 evitado: {s['co2_total']} kg | "
          f"Promedio: {s['kg_promedio']} kg | Material líder: {s['material_top']}")
    print("\n-- Por material --\n", c.analista.por_material().to_string())
    print("\n-- Por día --\n", c.analista.por_dia().to_string())
    print("\n-- Origen del dato --\n", c.analista.por_origen().to_string())


def datos_ejemplo(c):
    random.seed(7)
    for i in range(30):
        mat = random.choices(MATERIALES, weights=[30, 15, 12, 15, 15, 8, 5])[0]
        kg = round(random.uniform(0.5, 6) if mat != "metal" else random.uniform(0.2, 2), 2)
        f = (datetime.now() - timedelta(days=random.randint(0, 6), hours=random.randint(0, 8))).isoformat(timespec="seconds")
        c.registrar(mat, kg, f"Ejemplo {i+1}", "manual", "", fecha=f)
    print("30 registros de ejemplo agregados.")


def ranking(c):
    if c.analista.df.empty: return print("Aún no hay registros.")
    items = list(c.analista.por_material()["kg"].items())
    b, cb = burbuja(items, clave=lambda t: t[1], reverso=True)
    m, cm = merge_sort(items, clave=lambda t: t[1], reverso=True)
    print("\nRanking por kg (mayor a menor):")
    for i, (mat, kg) in enumerate(m, 1): print(f"  {i}. {mat}: {kg:.2f} kg")
    print(f"Comparaciones -> burbuja: {cb} | merge sort: {cm} | coinciden: {b == m}")


def buscar(c):
    regs, _ = merge_sort(c.analista.df.to_dict("records"), clave=lambda r: r["id"])
    if not regs: return print("Aún no hay registros.")
    txt = input(f"ID del registro (1 a {regs[-1]['id']}): ").strip()
    if not txt.isdigit(): return print("  Escribe un número.")
    i, pb = busqueda_binaria(regs, int(txt), clave=lambda r: r["id"])
    _, pl = busqueda_lineal(regs, int(txt), clave=lambda r: r["id"])
    print(f"Pasos -> binaria: {pb} | lineal: {pl}")
    print(f"Encontrado: {regs[i]['material']} {regs[i]['kg']} kg ({regs[i]['fecha']})" if i >= 0 else "No existe ese ID.")


def camion(c):
    if c.analista.df.empty: return print("Aún no hay registros.")
    cap = input("Capacidad del camión en kg (Enter = 20): ").strip().replace(",", ".")
    cap = float(cap) if cap.replace(".", "", 1).isdigit() else 20.0
    stock = c.analista.por_material()["kg"]
    items = [{"material": m, "kg": float(kg), "co2_kg": c.factores[m]["co2"]} for m, kg in stock.items()]
    plan, kg, co2 = cargar_camion(items, cap)
    print(f"\nPlan de carga (prioriza el material que más CO2 evita por kg):")
    for p in plan: print(f"  {p['material']}: {p['kg']} kg -> {p['co2']} kg de CO2")
    print(f"Carga total: {kg} de {cap} kg | CO2 evitado: {co2} kg")


def estadistica(c):
    e = c.analista.estadistica()
    if not e: return print("Aún no hay registros.")
    print("\nEstadística descriptiva del peso (kg):")
    for k, v in e.items(): print(f"  {k}: {v}")
    print("\n", c.analista.describe_por_material().to_string())


def informe(c):
    a = c.analista
    if a.df.empty: return print("Aún no hay registros.")
    r = generar_informe(a.datos_para_informe(), a.informe_local())
    print(f"\nInforme del analista ({'IA Groq' if r['fuente'] == 'groq' else 'generado con Pandas, sin IA'}):\n{r['informe']}")


def main():
    c = CentroAcopio()
    while True:
        print(MENU)
        op = input("Opción: ").strip()
        if op == "1":
            n = input("Nombre: ").strip()
            if n: print(f"Turno #{c.nuevo_turno(n).id} para {n}. En espera: {len(c.cola)}")
        elif op == "2":
            print("Cola:", [f"{t.nombre} ({t.creado})" for t in c.cola.to_list()] or "vacía")
        elif op == "3": atender_y_registrar(c)
        elif op == "4":
            r = c.deshacer(); print(f"Deshecho: {r.material} {r.kg} kg" if r else "No hay nada que deshacer.")
        elif op == "5":
            for r in c.pila.to_list(): print(f"  #{r.id} {r.material} {r.kg} kg ({r.turno})")
            if not len(c.pila): print("  (vacío)")
        elif op == "6": reporte(c)
        elif op == "7":
            c.analista.exportar("reporte.csv"); print("Guardado: reporte.csv")
        elif op == "8": datos_ejemplo(c)
        elif op == "9": ranking(c)
        elif op == "10": buscar(c)
        elif op == "11": camion(c)
        elif op == "12": estadistica(c)
        elif op == "14": informe(c)
        elif op == "13":
            if c.analista.df.empty: print("Aún no hay registros.")
            else: print("Gráficas guardadas en:", *graficas.generar(c.analista), sep="\n  ")
        elif op == "0": break
        else: print("Opción inválida.")


if __name__ == "__main__":
    main()
