"""Algoritmos del curso (caps. 5 y 6): ordenamiento, búsqueda y algoritmo voraz. Todo hecho a mano."""


def burbuja(datos, clave=lambda x: x, reverso=False):
    """Ordenamiento burbuja. Devuelve (lista_ordenada, comparaciones)."""
    a, comps = list(datos), 0
    for i in range(len(a)):
        hubo_cambio = False
        for j in range(len(a) - 1 - i):
            comps += 1
            x, y = clave(a[j]), clave(a[j + 1])
            if (x < y) if reverso else (x > y):
                a[j], a[j + 1] = a[j + 1], a[j]
                hubo_cambio = True
        if not hubo_cambio:
            break
    return a, comps


def merge_sort(datos, clave=lambda x: x, reverso=False):
    """Ordenamiento por mezcla (divide y vencerás). Devuelve (lista_ordenada, comparaciones)."""
    comparaciones = [0]                                   # la función interna lo recuerda (clausura)

    def mezclar(izq, der):
        res, i, j = [], 0, 0
        while i < len(izq) and j < len(der):
            comparaciones[0] += 1
            x, y = clave(izq[i]), clave(der[j])
            if (x >= y) if reverso else (x <= y):
                res.append(izq[i]); i += 1
            else:
                res.append(der[j]); j += 1
        return res + izq[i:] + der[j:]

    def ordenar(lista):
        if len(lista) <= 1:
            return lista
        m = len(lista) // 2
        return mezclar(ordenar(lista[:m]), ordenar(lista[m:]))

    return ordenar(list(datos)), comparaciones[0]


def busqueda_lineal(lista, objetivo, clave=lambda x: x):
    """Devuelve (índice o -1, pasos)."""
    for i, x in enumerate(lista):
        if clave(x) == objetivo:
            return i, i + 1
    return -1, len(lista)


def busqueda_binaria(lista, objetivo, clave=lambda x: x):
    """La lista debe estar ordenada. Devuelve (índice o -1, pasos)."""
    bajo, alto, pasos = 0, len(lista) - 1, 0
    while bajo <= alto:
        pasos += 1
        medio = (bajo + alto) // 2
        v = clave(lista[medio])
        if v == objetivo:
            return medio, pasos
        bajo, alto = (medio + 1, alto) if v < objetivo else (bajo, medio - 1)
    return -1, pasos


def cargar_camion(items, capacidad_kg):
    """Algoritmo voraz (greedy): llena el camión priorizando el material que más CO2 evita por kg.
    items: [{'material','kg','co2_kg'}]. Devuelve (plan, kg_cargados, co2_total)."""
    ordenados, _ = merge_sort(items, clave=lambda it: it["co2_kg"], reverso=True)
    libre, plan, co2 = capacidad_kg, [], 0.0
    for it in ordenados:
        if libre <= 0:
            break
        kg = round(min(it["kg"], libre), 3)
        plan.append({"material": it["material"], "kg": kg, "co2": round(kg * it["co2_kg"], 3)})
        libre -= kg; co2 += kg * it["co2_kg"]
    return plan, round(capacidad_kg - libre, 3), round(co2, 3)
