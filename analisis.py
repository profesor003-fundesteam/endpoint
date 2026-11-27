"""Análisis de datos con Pandas (persistencia en CSV)."""
import json
import os
import pandas as pd

COLS = ["id", "fecha", "turno", "material", "kg", "co2", "origen", "producto"]


class Analista:
    def __init__(self, ruta):
        self.ruta = ruta
        self.df = pd.read_csv(ruta) if os.path.exists(ruta) else pd.DataFrame(columns=COLS)
        self._tipos()

    def _tipos(self):                      # evita columnas 'object' (rompe describe y las gráficas)
        self.df = self.df.astype({"id": int, "kg": float, "co2": float})

    def siguiente_id(self):
        return int(self.df["id"].max()) + 1 if len(self.df) else 1

    def agregar(self, reg):
        self.df = pd.concat([self.df, pd.DataFrame([reg.to_dict()])[COLS]], ignore_index=True)
        self._tipos()
        self._guardar()

    def quitar(self, reg_id):
        self.df = self.df[self.df["id"] != reg_id].reset_index(drop=True)
        self._guardar()

    def _guardar(self):
        self.df.to_csv(self.ruta, index=False)

    # ---- análisis ----
    def resumen(self):
        d = self.df
        if d.empty:
            return None
        return {"registros": len(d), "kg_total": round(d.kg.sum(), 2), "co2_total": round(d.co2.sum(), 2),
                "kg_promedio": round(d.kg.mean(), 3), "material_top": d.groupby("material").kg.sum().idxmax()}

    def por_material(self):
        g = self.df.groupby("material").agg(registros=("id", "count"), kg=("kg", "sum"), co2=("co2", "sum"))
        g["%_kg"] = (g.kg / g.kg.sum() * 100).round(1)
        return g.sort_values("kg", ascending=False).round(3)

    def por_dia(self):
        d = self.df.assign(dia=pd.to_datetime(self.df["fecha"]).dt.date)
        return d.groupby("dia").agg(registros=("id", "count"), kg=("kg", "sum"), co2=("co2", "sum")).round(3)

    def por_origen(self):
        return self.df.groupby("origen").size().rename("registros").to_frame()

    def estadistica(self):
        k = self.df["kg"]
        if k.empty:
            return None
        return {"media": round(k.mean(), 3), "mediana": round(k.median(), 3),
                "desviacion": round(k.std(), 3) if len(k) > 1 else 0.0, "minimo": k.min(), "q1": round(k.quantile(.25), 3),
                "q3": round(k.quantile(.75), 3), "maximo": k.max(), "material_mas_frecuente": self.df["material"].mode()[0]}

    def describe_por_material(self):
        return self.df.groupby("material")["kg"].describe().round(3)

    def datos_para_informe(self):
        """Datos AGREGADOS (sin nombres de personas) que se envían a la IA."""
        pm = json.loads(self.por_material().reset_index().to_json(orient="records"))
        dia = self.por_dia().reset_index(); dia["dia"] = dia["dia"].astype(str)
        return {"resumen": json.loads(json.dumps(self.resumen(), default=float)), "por_material": pm,
                "por_dia": json.loads(dia.to_json(orient="records")),
                "estadistica_peso_kg": json.loads(json.dumps(self.estadistica(), default=float))}

    def informe_local(self):
        """Informe en texto armado solo con Pandas (respaldo si no hay IA)."""
        if self.df.empty:
            return "Aún no hay registros."
        r, pm, dia, e = self.resumen(), self.por_material(), self.por_dia(), self.estadistica()
        return "\n".join([
            f"Se registraron {r['registros']} entregas que suman {r['kg_total']} kg y evitaron {r['co2_total']} kg de CO2.",
            f"El material con más volumen es {pm.index[0]} ({pm['%_kg'].iloc[0]}% de los kg).",
            f"El material que más CO2 evitó es {pm['co2'].idxmax()} ({pm['co2'].max()} kg de CO2).",
            f"El día con más kilos fue {dia['kg'].idxmax()} ({dia['kg'].max()} kg).",
            f"Cada entrega pesa en promedio {e['media']} kg (mediana {e['mediana']} kg).",
            f"Recomendación: reservar espacio y transporte para {pm.index[0]}, que es el material más frecuente."])

    def vaciar(self):
        self.df = self.df.iloc[0:0]
        self._guardar()

    def exportar(self, ruta):
        pm, pd_ = self.por_material().reset_index(), self.por_dia().reset_index()
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("# POR MATERIAL\n"); pm.to_csv(f, index=False)
            f.write("\n# POR DIA\n"); pd_.to_csv(f, index=False)
