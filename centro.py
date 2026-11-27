"""CentroAcopio: une Cola (turnos), Pila (deshacer) y Analista (Pandas)."""
import json
import os
from structures import Pila, Cola
from models import Turno, Registro
from analisis import Analista

def fabricar_calculadora_co2(factores):
    """Clausura: la tabla de factores y devuelve una función que calcula el CO2 evitado."""
    def calcular(material, kg):
        return round(float(kg) * factores.get(material, factores["otros"])["co2"], 3)
    return calcular


BASE = os.path.dirname(os.path.abspath(__file__))


class CentroAcopio:
    def __init__(self):
        with open(os.path.join(BASE, "datos", "factores.json"), encoding="utf-8") as f:
            self.factores = json.load(f)
        self.calcular_co2 = fabricar_calculadora_co2(self.factores)
        self.cola, self.pila = Cola(), Pila()
        self.analista = Analista(os.path.join(BASE, "datos", "registro.csv"))

    def nuevo_turno(self, nombre):
        t = Turno(nombre); self.cola.enqueue(t); return t           # FIFO: entra al final

    def atender(self):
        return self.cola.dequeue()                                    # FIFO: sale el primero

    def registrar(self, material, kg, turno="", origen="manual", producto="", fecha=None):
        material = material if material in self.factores else "otros"
        reg = Registro(material=material, kg=round(float(kg), 3), co2=self.calcular_co2(material, kg),
                       turno=turno, origen=origen, producto=producto, id=self.analista.siguiente_id())
        if fecha:
            reg.fecha = fecha
        self.pila.push(reg); self.analista.agregar(reg)               # LIFO: historial para deshacer
        return reg

    def deshacer(self):
        reg = self.pila.pop()                                         # LIFO: sale el último
        if reg:
            self.analista.quitar(reg.id)
        return reg
