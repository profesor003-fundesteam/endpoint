"""Cliente de la API pública Open Food Facts (sin clave): código de barras -> material del empaque."""
import requests

URL = "https://world.openfoodfacts.org/api/v2/product/{}.json"
CAMPOS = "product_name,brands,packagings,packaging_tags"
# palabra del empaque (inglés) -> material del centro de acopio
MAPA = {"plastic": "plastico", "pet": "plastico", "glass": "vidrio", "aluminium": "metal", "aluminum": "metal",
        "steel": "metal", "metal": "metal", "can": "metal", "paper": "papel", "cardboard": "carton", "carton": "carton"}


def material_desde_texto(textos):
    for t in textos:
        for clave, mat in MAPA.items():
            if clave in t.lower():
                return mat
    return None


def extraer(data):
    """Recibe el JSON de la API y devuelve {producto, marca, material} (o None si no hay producto)."""
    p = data.get("product")
    if data.get("status") == 0 or not p:
        return None
    textos = []
    for e in p.get("packagings", []) or []:
        m = e.get("material")
        textos.append(m.get("id", "") if isinstance(m, dict) else str(m or ""))
    textos += p.get("packaging_tags", []) or []
    return {"producto": p.get("product_name") or "(sin nombre)", "marca": p.get("brands", ""),
            "material": material_desde_texto(textos)}


def crear_consultor(timeout=6):
    """Clausura: devuelve la función consultar() que recuerda (caché) los códigos ya consultados."""
    cache = {}

    def consultar(codigo):
        """Devuelve {producto, marca, material} o None si no hay internet / no existe / falla la API."""
        codigo = codigo.strip()
        if codigo in cache:
            return {**cache[codigo], "cache": True}
        try:
            r = requests.get(URL.format(codigo), params={"fields": CAMPOS}, timeout=timeout,
                             headers={"User-Agent": "EcoEndpoint-SIC/1.0 (proyecto educativo)"})
            r.raise_for_status()
            info = extraer(r.json())
        except (requests.RequestException, ValueError):
            return None
        if info:
            cache[codigo] = info
        return info

    return consultar


consultar = crear_consultor()
