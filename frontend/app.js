/* Frontend de EcoEndpoint Lite: solo muestra datos y llama a la API del backend (Flask). */
const $ = id => document.getElementById(id);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const num = n => (typeof n === "number" ? Math.round(n * 1000) / 1000 : n);
let origen = "manual", producto = "";

async function api(url, metodo = "GET", cuerpo) {
  const r = await fetch(url, {method: metodo, headers: {"Content-Type": "application/json"}, body: cuerpo ? JSON.stringify(cuerpo) : undefined});
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(d.error || "Error del servidor");
  return d;
}
const decir = (id, txt, error = false) => { $(id).textContent = txt; $(id).className = "nota" + (error ? " error" : ""); };
const tabla = (filas, cols) => `<div class="tabla-scroll"><table><tr>${cols.map(c => `<th>${esc(c)}</th>`).join("")}</tr>` +
  filas.map(f => `<tr>${cols.map(c => `<td>${esc(num(f[c]))}</td>`).join("")}</tr>`).join("") + "</table></div>";

function pintar(s) {
  const r = s.resumen;
  $("kRegistros").textContent = r ? r.registros : 0; $("kKg").textContent = r ? r.kg_total : 0;
  $("kCo2").textContent = r ? r.co2_total : 0; $("kTop").textContent = r ? r.material_top : "—";
  $("cola").innerHTML = s.cola.map(t => `<li>${esc(t.nombre)} <small>(${esc(t.hora)})</small></li>`).join("") || "<li>Sin turnos en espera</li>";
  $("historial").innerHTML = s.historial.slice(0, 8).map(h => `<li>#${h.id} ${esc(h.material)} · ${num(h.kg)} kg · ${esc(h.turno)}</li>`).join("") || "<li>Aún no hay registros en esta sesión</li>";
  $("actual").textContent = s.actual ? `Atendiendo a: ${s.actual.nombre}` : "Atiende un turno para registrar.";
  if (!$("material").options.length) $("material").innerHTML = s.materiales.map(m => `<option>${m}</option>`).join("");
  const activa = document.querySelector(".tab.activa").dataset.tab; if (activa === "reporte" || activa === "estadistica") cargarReporte();
}
async function estado() { pintar(await api("/api/estado")); }
async function accion(fn, idMsg = "msg") { try { return await fn(); } catch (e) { decir(idMsg, e.message, true); } }

$("btnTurno").onclick = () => accion(async () => { pintar(await api("/api/cola", "POST", {nombre: $("nombre").value})); $("nombre").value = ""; decir("msg", ""); });
$("nombre").onkeydown = e => { if (e.key === "Enter") $("btnTurno").click(); };
$("btnAtender").onclick = () => accion(async () => { pintar(await api("/api/atender", "POST")); decir("msg", ""); });
$("btnConsultar").onclick = () => accion(async () => {
  decir("msgApi", "Consultando…");
  const d = await api("/api/consultar?codigo=" + encodeURIComponent($("codigo").value));
  if (d.encontrado) { $("material").value = d.material; origen = "api"; producto = d.producto; decir("msgApi", `API: ${d.producto} → ${d.material}${d.cache ? " (caché)" : ""}`); }
  else { origen = "manual"; producto = ""; decir("msgApi", "No se obtuvo el material (sin internet o producto sin datos). Elígelo tú.", true); }
}, "msgApi");
$("btnRegistrar").onclick = () => accion(async () => {
  const d = await api("/api/registrar", "POST", {material: $("material").value, kg: $("kg").value, origen, producto});
  pintar(d); decir("msg", `Registrado: ${d.registro.material} ${d.registro.kg} kg · CO₂ evitado ${d.registro.co2} kg`);
  mostrarReco(d.registro.material);
  $("kg").value = ""; $("codigo").value = ""; decir("msgApi", ""); origen = "manual"; producto = "";
});
async function mostrarReco(material) {
  $("reco").hidden = false; $("reco").textContent = "Consultando recomendación…";
  try {
    const d = await api("/api/recomendar?material=" + encodeURIComponent(material));
    $("reco").textContent = `${d.fuente === "groq" ? "IA Groq" : "Respaldo local"} · ${material}: ${d.recomendacion}`;
  } catch (e) { $("reco").textContent = e.message; }
}
$("btnReco").onclick = () => mostrarReco($("material").value);
$("btnDeshacer").onclick = async () => { const d = await api("/api/deshacer", "POST"); pintar(d); decir("msg", d.deshecho ? `Deshecho: ${d.deshecho.material} ${d.deshecho.kg} kg` : "No hay nada que deshacer.", !d.deshecho); };
$("btnEjemplo").onclick = async () => { pintar(await api("/api/ejemplo", "POST")); decir("msg", "30 registros de ejemplo agregados."); };
$("btnReiniciar").onclick = async () => { if (confirm("¿Borrar todos los registros?")) { pintar(await api("/api/reiniciar", "POST")); decir("msg", "Datos reiniciados."); } };

document.querySelectorAll(".tab").forEach(b => b.onclick = () => {
  document.querySelectorAll(".tab").forEach(x => x.classList.toggle("activa", x === b));
  document.querySelectorAll(".contenido").forEach(c => c.hidden = c.id !== b.dataset.tab);
  if (b.dataset.tab === "reporte" || b.dataset.tab === "estadistica") cargarReporte();
});

async function cargarReporte() {
  const d = await api("/api/reporte");
  if (d.vacio) { $("reporte").innerHTML = $("estadistica").innerHTML = "<p class='nota'>Aún no hay registros. Usa «Cargar datos de ejemplo» o registra residuos.</p>"; return; }
  $("reporte").innerHTML = "<h3>Por material</h3>" + tabla(d.por_material, ["material", "registros", "kg", "co2", "%_kg"]) +
    "<h3>Por día</h3>" + tabla(d.por_dia, ["dia", "registros", "kg", "co2"]) + "<h3>Origen del dato</h3>" + tabla(d.origen, ["origen", "registros"]);
  const e = d.estadistica;
  $("estadistica").innerHTML = "<h3>Estadística descriptiva del peso (kg)</h3>" + tabla([e], ["media", "mediana", "desviacion", "minimo", "q1", "q3", "maximo", "material_mas_frecuente"]) +
    "<h3>Por material</h3>" + tabla(d.describe, ["material", "count", "mean", "std", "min", "25%", "50%", "75%", "max"]);
}
$("btnRanking").onclick = () => accion(async () => {
  const d = await api("/api/ranking");
  $("outRanking").innerHTML = tabla(d.ranking.map((r, i) => ({pos: i + 1, ...r})), ["pos", "material", "kg"]) +
    `<p class="nota">Comparaciones: burbuja ${d.burbuja} · merge sort ${d.merge} · mismo resultado: ${d.coinciden ? "sí" : "no"}</p>`;
}, "outRanking");
$("btnBuscar").onclick = () => accion(async () => {
  const d = await api("/api/buscar?id=" + encodeURIComponent($("idBuscar").value));
  $("outBuscar").innerHTML = (d.encontrado ? `<p>#${d.registro.id}: ${esc(d.registro.material)} · ${num(d.registro.kg)} kg · ${esc(d.registro.fecha)}</p>` : "<p>No existe ese ID.</p>") +
    `<p class="nota">Pasos: binaria ${d.binaria} · lineal ${d.lineal} (de ${d.total} registros)</p>`;
}, "outBuscar");
$("btnCamion").onclick = () => accion(async () => {
  const d = await api("/api/camion", "POST", {capacidad: $("capacidad").value});
  $("outCamion").innerHTML = tabla(d.plan, ["material", "kg", "co2"]) + `<p class="nota">Carga: ${d.kg} de ${d.capacidad} kg · CO₂ evitado: ${d.co2} kg (prioriza lo que más CO₂ evita por kg)</p>`;
}, "outCamion");
$("btnGraficas").onclick = () => accion(async () => {
  const d = await api("/api/graficas"), t = Date.now();
  $("outGraficas").innerHTML = d.archivos.map(a => `<img src="/graficas/${a}?t=${t}" alt="${a}">`).join("");
}, "outGraficas");

$("btnInforme").onclick = () => accion(async () => {
  $("outInforme").innerHTML = "<p class='nota'>Generando informe…</p>";
  const d = await api("/api/informe");
  $("outInforme").innerHTML = `<p class="nota">${d.fuente === "groq" ? "Interpretado por IA (Groq)" : "Generado con Pandas (sin IA)"}</p>` +
    d.informe.split("\n").filter(l => l.trim()).map(l => `<p>${esc(l)}</p>`).join("");
}, "outInforme");

estado(); cargarReporte();
