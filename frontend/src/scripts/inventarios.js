import { TabulatorFull as Tabulator } from 'tabulator-tables';
import QRCode from 'qrcode';

const $ = (selector) => document.querySelector(selector);
const apiBase = $('meta[name="api-base"]').content;

const TIPOS = [
  { valor: 'a', etiqueta: 'Parte A' },
  { valor: 'b', etiqueta: 'Contraparte B' },
  { valor: 'unico', etiqueta: 'Conteo único' },
];

let csrf = '';
let inventoryRows = [];
let inventoryPage = 1;
let inventoryHasMore = false;
let selected = null;
let devices = [];
let analysisTable = null;
let deviceTable = null;
let toastTimer = null;

function toast(message, variant = 'info') {
  const element = $('#toast');
  if (!element) return;
  const text = $('#toast-message');
  if (text) text.textContent = message;
  const icon = $('#toast-icon');
  if (icon) icon.setAttribute('href', { success: '#icon-check', error: '#icon-alerta', info: '#icon-info' }[variant] || '#icon-info');
  element.dataset.variant = variant;
  element.hidden = false;
  if (window.clearTimeout) window.clearTimeout(toastTimer);
  if (window.setTimeout) toastTimer = window.setTimeout(() => { element.hidden = true; }, 6000);
}

function abrirDialogo(id) {
  const dialogo = $(`#${id}`);
  if (!dialogo) return;
  if (typeof dialogo.showModal === 'function') dialogo.showModal();
  else dialogo.open = true;
}

function cerrarDialogo(id) {
  const dialogo = $(`#${id}`);
  if (!dialogo) return;
  if (typeof dialogo.close === 'function') dialogo.close();
  else dialogo.open = false;
}

function nodo(tag, clase = '', texto = '') {
  const elemento = document.createElement(tag);
  if (clase) elemento.className = clase;
  if (texto) elemento.textContent = texto;
  return elemento;
}

function boton(texto, clase, alPulsar) {
  const elemento = nodo('button', clase, texto);
  elemento.type = 'button';
  elemento.addEventListener('click', alPulsar);
  return elemento;
}

function chip(texto, variante) {
  return nodo('span', `chip chip-${variante}`, texto);
}

function escapar(valor) {
  return String(valor ?? '').replace(/[&<>"']/g, (caracter) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[caracter]));
}

function etiquetaTipo(tipo) {
  return TIPOS.find((item) => item.valor === tipo)?.etiqueta ?? tipo;
}

function fechaCorta(iso) {
  if (!iso) return '';
  const fecha = new Date(iso);
  if (Number.isNaN(fecha.getTime())) return '';
  return fecha.toLocaleDateString('es-CL', { day: '2-digit', month: 'short', year: 'numeric' });
}

async function readJson(response, route) {
  if (!(response.headers.get('content-type') || '').toLowerCase().includes('application/json')) {
    throw new Error(`La API respondió con una página en lugar de JSON (${response.status}, ${route}). Comprueba el proxy, el servidor y las migraciones de inventario.`);
  }
  try {
    return await response.json();
  } catch {
    throw new Error(`La API devolvió JSON incompleto (${response.status}, ${route}).`);
  }
}

async function api(path, data) {
  const response = await fetch(`${apiBase}/api/v1/inventarios/${path}`, {
    credentials: apiBase ? 'include' : 'same-origin',
    method: data === undefined ? 'GET' : 'POST',
    headers: data === undefined ? {} : { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
    body: data === undefined ? undefined : JSON.stringify(data),
  });
  const result = await readJson(response, `/api/v1/inventarios/${path}`);
  if (!response.ok) throw new Error(result.error || `Error HTTP ${response.status} al consultar inventarios.`);
  return result;
}

/* ---------------------------------------------------------------- datos --- */

async function cargarBodegas() {
  const bodegas = [];
  let pagina = 1;
  while (true) {
    const response = await fetch(`${apiBase}/api/v1/informat/bodegas/?pagina=${pagina}`, {
      credentials: apiBase ? 'include' : 'same-origin',
    });
    const data = await readJson(response, '/api/v1/informat/bodegas/');
    if (!response.ok) throw new Error(data.error || `Error HTTP ${response.status} al consultar bodegas.`);
    bodegas.push(...data.bodegas);
    if (!data.hay_mas) break;
    pagina += 1;
  }
  const select = $('#inventory-warehouse');
  select.replaceChildren();
  if (bodegas.length === 0) {
    const option = document.createElement('option');
    option.value = '';
    option.textContent = 'No hay bodegas disponibles';
    select.append(option);
    return;
  }
  for (const bodega of bodegas) {
    const option = document.createElement('option');
    option.value = bodega.codigo;
    option.textContent = `${bodega.codigo} · ${bodega.nombre}`;
    select.append(option);
  }
}

async function cargarInventarios(reiniciar = false) {
  if (reiniciar) {
    inventoryPage = 1;
    inventoryRows = [];
  }
  const data = await api(`?pagina=${inventoryPage}&tamano=25`);
  inventoryRows.push(...data.inventarios);
  inventoryHasMore = Boolean(data.hay_mas);
  inventoryPage += 1;
  renderInventarios();
}

async function cargarDetalle(id) {
  selected = await api(`${id}/`);
  renderDetalle();
}

async function cargarCapturadores() {
  const data = await api('capturadores/');
  devices = data.capturadores;
  renderCapturadores();
}

/* ------------------------------------------------------------- renders --- */

function renderInventarios() {
  const lista = $('#inventory-list');
  lista.replaceChildren();
  for (const row of inventoryRows) {
    const item = nodo('li');
    const activo = selected && selected.id === row.id;
    const enlace = nodo('button', `w-full rounded-lg p-3 text-left transition-colors hover:bg-surface-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary${activo ? ' bg-primary-soft' : ''}`);
    enlace.type = 'button';
    const titulo = nodo('div', 'flex items-start justify-between gap-2');
    titulo.append(nodo('span', 'font-medium text-ink', row.nombre));
    titulo.append(chip(row.estado === 'abierto' ? 'Abierto' : 'Cerrado', row.estado === 'abierto' ? 'chip-success' : 'chip-neutral'));
    const meta = nodo('p', 'mt-1 text-xs text-ink-subtle', `Bodega ${row.bodega} · ${fechaCorta(row.creado_en)}`);
    enlace.append(titulo, meta);
    enlace.addEventListener('click', () => {
      cargarDetalle(row.id).catch((error) => toast(error.message, 'error'));
    });
    item.append(enlace);
    lista.append(item);
  }
  $('#inventory-count').textContent = String(inventoryRows.length);
  $('#inventory-empty').hidden = inventoryRows.length > 0;
  $('#inventory-more').hidden = !inventoryHasMore;
}

function renderDetalle() {
  const vacio = $('#detail-empty');
  const contenido = $('#detail-content');
  if (!selected) {
    vacio.hidden = false;
    contenido.hidden = true;
    return;
  }
  vacio.hidden = true;
  contenido.hidden = false;
  $('#detail-name').textContent = selected.nombre;
  const estado = $('#detail-state');
  estado.textContent = selected.estado === 'abierto' ? 'Abierto' : 'Cerrado';
  estado.className = `chip ${selected.estado === 'abierto' ? 'chip-success' : 'chip-neutral'}`;
  $('#detail-meta').textContent = `Bodega ${selected.bodega} · ${selected.bodega_nombre} · creado el ${fechaCorta(selected.creado_en)}`;
  $('#detail-close').hidden = selected.estado !== 'abierto';
  renderTurnos();
  renderAnalisis();
}

/**
 * Los turnos A/B de un inventario comparten zona y no repiten tipo. La web
 * propone la combinación legal para que el supervisor no choque con la regla;
 * el backend la valida igualmente.
 */
function sugerirTurno(turnos) {
  if (turnos.length === 0) {
    return { zona: '', tipo: 'a', disponible: true,
      pista: 'Sin conteos todavía. Define la zona de conteo: el capturador la recibe configurada y no la escribe.' };
  }
  const zona = turnos[0].zona || '';
  const usados = new Set(turnos.map((turno) => turno.tipo));
  const detalle = turnos.map((turno) => `${turno.usuario} · ${turno.zona} · ${etiquetaTipo(turno.tipo)}`).join(' · ');
  if (usados.has('unico')) {
    return { zona, tipo: 'unico', disponible: false,
      pista: `Conteo único (${detalle}): este inventario no admite un segundo turno.` };
  }
  const libre = !usados.has('a') ? 'a' : !usados.has('b') ? 'b' : null;
  if (!libre) {
    return { zona, tipo: '', disponible: false,
      pista: `La contraprova está completa (${detalle}). Cierra el inventario cuando los capturadores terminen.` };
  }
  return { zona, tipo: libre, disponible: true,
    pista: `Conteos actuales: ${detalle}. El siguiente conteo usa la zona ${zona} y el tipo ${etiquetaTipo(libre)}: los conteos se comparan dentro de la misma zona.` };
}

function aplicarSugerenciaTurno(turnos, campos) {
  const sugerencia = sugerirTurno(turnos);
  campos.zona.value = sugerencia.zona;
  campos.zona.readOnly = !sugerencia.disponible;
  if (sugerencia.tipo) campos.tipo.value = sugerencia.tipo;
  campos.tipo.disabled = !sugerencia.disponible;
  if (campos.boton) campos.boton.disabled = !sugerencia.disponible;
  campos.pista.textContent = sugerencia.pista;
}

function renderTurnos() {
  const lista = $('#assignments-list');
  lista.replaceChildren();
  const turnos = (selected && selected.asignaciones) || [];
  for (const turno of turnos) {
    lista.append(filaTurno({
      id: turno.id,
      zona: turno.zona,
      tipo: turno.tipo,
      operador: turno.usuario,
      finalizado: turno.finalizado,
      capturador: turno.capturador,
      inventarioId: selected.id,
      bodega: selected.bodega_nombre ? `${selected.bodega} · ${selected.bodega_nombre}` : selected.bodega,
    }));
  }
  $('#assignments-empty').hidden = turnos.length > 0;
}

function renderAnalisis() {
  const resultados = selected ? selected.resultados : [];
  const resumen = $('#analysis-summary');
  resumen.replaceChildren();
  const conteos = { coincidente: 0, diferencia: 0, faltante: 0, pendiente: 0 };
  for (const fila of resultados) {
    conteos[fila.estado] = (conteos[fila.estado] ?? 0) + 1;
  }
  if (resultados.length > 0) {
    if (conteos.coincidente) resumen.append(chip(`${conteos.coincidente} coincidentes`, 'chip-success'));
    if (conteos.diferencia) resumen.append(chip(`${conteos.diferencia} diferencias`, 'chip-warning'));
    if (conteos.faltante) resumen.append(chip(`${conteos.faltante} faltantes`, 'chip-danger'));
    if (conteos.pendiente) resumen.append(chip(`${conteos.pendiente} pendientes`, 'chip-neutral'));
  }
  $('#analysis-empty').hidden = resultados.length > 0;
  if (analysisTable) analysisTable.setData(resultados);
}

function renderCapturadores() {
  if (!deviceTable) return;
  deviceTable.setData(devices.map((device) => {
    const turnos = (device.turnos || []).map((turno) => ({ ...turno, capturador_id: device.id }));
    return {
      ...device,
      busqueda: textoBusqueda(device),
      turnos,
      zonas: turnos.map((turno) => turno.zona || '—'),
      tipos: turnos.map((turno) => turno.tipo_nombre || etiquetaTipo(turno.tipo)),
      estadosConteo: turnos.map((turno) => ({ finalizado: turno.finalizado })),
    };
  }));
  actualizarContadorCapturadores();
}

function textoBusqueda(device) {
  const partes = [device.nombre, device.activo ? 'activo' : 'revocado', device.vinculado ? 'vinculación emitida' : 'sin vincular'];
  for (const turno of device.turnos || []) {
    partes.push(turno.inventario_nombre, turno.bodega, turno.bodega_nombre, turno.zona,
      turno.zona_nombre, turno.tipo, turno.tipo_nombre);
  }
  return partes.filter(Boolean).join(' ').toLowerCase();
}

function actualizarContadorCapturadores() {
  const visibles = deviceTable ? deviceTable.getData('active').length : devices.length;
  $('#device-count').textContent = String(visibles);
  $('#tab-capturadores-count').textContent = String(devices.length);
}

function zonasHtml(zonas) {
  if (!zonas || zonas.length === 0) return '<span class="text-sm text-ink-subtle">Sin zonas</span>';
  return `<div class="flex flex-wrap gap-1">${zonas.map((zona) => `<span class="chip chip-neutral">${escapar(zona)}</span>`).join('')}</div>`;
}

function tiposHtml(tipos) {
  if (!tipos || tipos.length === 0) return '<span class="text-sm text-ink-subtle">Sin tipos</span>';
  return `<div class="flex flex-wrap gap-1">${tipos.map((tipo) => `<span class="chip chip-primary">${escapar(tipo)}</span>`).join('')}</div>`;
}

function estadosConteoHtml(estados) {
  if (!estados || estados.length === 0) return '<span class="text-sm text-ink-subtle">Sin conteos</span>';
  return `<div class="flex flex-wrap gap-1">${estados.map((estado) => `<span class="chip ${estado.finalizado ? 'chip-success' : 'chip-warning'}">${estado.finalizado ? 'Finalizado' : 'En curso'}</span>`).join('')}</div>`;
}

function qrHtml(device) {
  if (device.activo === false) return '<span class="text-sm text-ink-subtle">—</span>';
  const turnos = device.turnos || [];
  if (turnos.length === 0) return '<span class="text-sm text-ink-subtle">Sin conteo</span>';
  const turno = turnos[0];
  return `<button type="button" class="btn btn-soft btn-sm whitespace-nowrap" data-accion="qr" data-capturador="${escapar(device.id)}" data-turno="${escapar(turno.turno)}" data-inventario="${escapar(turno.inventario)}">Generar QR</button>`;
}

function accionesHtml(device) {
  const partes = [];
  for (const turno of device.turnos || []) {
    if (device.activo === false) continue;
    partes.push(`<button type="button" class="btn btn-ghost btn-sm whitespace-nowrap" data-accion="editar" data-turno="${escapar(turno.turno)}" data-zona="${escapar(turno.zona)}" data-tipo="${escapar(turno.tipo)}" data-inventario="${escapar(turno.inventario)}">Editar</button>`);
  }
  if (device.activo) {
    partes.push(`<button type="button" class="btn btn-secondary btn-sm whitespace-nowrap" data-accion="revocar" data-id="${escapar(device.id)}">Revocar</button>`);
  }
  partes.push(`<button type="button" class="btn btn-ghost btn-sm whitespace-nowrap text-danger hover:bg-danger/10 hover:text-danger" data-accion="eliminar" data-id="${escapar(device.id)}">Eliminar</button>`);
  return `<div class="flex flex-nowrap items-center gap-1">${partes.join('')}</div>`;
}

/**
 * Fila de un turno con su configuración (operador, bodega, zona y tipo) y las
 * acciones para emitir el QR o corregir la zona y el tipo.
 */
function filaTurno({ id, zona, tipo, operador, finalizado, capturador, inventarioId, inventarioNombre, bodega }) {
  const item = nodo('li', 'rounded-xl border border-line p-4');
  const cabecera = nodo('div', 'flex flex-wrap items-start justify-between gap-3');
  const datos = nodo('div', 'min-w-0');
  datos.append(nodo('p', 'font-medium text-ink', operador || 'Sin operador'));
  const configuracion = nodo('p', 'mt-1 text-sm text-ink-muted');
  configuracion.append(nodo('span', '', `Zona ${zona || '—'}`));
  configuracion.append(nodo('span', '', ` · ${etiquetaTipo(tipo)}`));
  if (bodega) configuracion.append(nodo('span', '', ` · Bodega ${bodega}`));
  datos.append(configuracion);
  if (inventarioNombre) datos.append(nodo('p', 'mt-1 text-xs text-ink-subtle', `Inventario: ${inventarioNombre}`));

  const acciones = nodo('div', 'flex flex-wrap items-center gap-2');
  acciones.append(chip(finalizado ? 'Finalizado' : 'Pendiente', finalizado ? 'chip-success' : 'chip-warning'));
  if (capturador) {
    acciones.append(boton('Generar QR', 'btn btn-secondary btn-sm', () => {
      generarQr(capturador, id, inventarioId);
    }));
  }
  acciones.append(boton('Editar', 'btn btn-ghost btn-sm', () => {
    abrirModalTurno({ id, zona, tipo, inventarioId });
  }));
  cabecera.append(datos, acciones);
  item.append(cabecera);
  return item;
}

function abrirModalTurno({ id, zona, tipo, inventarioId }) {
  $('#turn-id').value = id;
  $('#turn-zone').value = zona === 'Todas' ? '' : zona || '';
  $('#turn-type').value = tipo;
  $('#turn-form').dataset.inventario = inventarioId;
  abrirDialogo('modal-turno');
}

async function guardarTurno() {
  const id = $('#turn-id').value;
  const zona = $('#turn-zone').value.trim();
  const tipo = $('#turn-type').value;
  const inventarioId = $('#turn-form').dataset.inventario;
  try {
    const resultado = await api(`asignaciones/${id}/turno/`, { zona, tipo });
    cerrarDialogo('modal-turno');
    toast(`Conteo actualizado: zona ${resultado.zona} · ${etiquetaTipo(resultado.tipo)}.`, 'success');
    await cargarCapturadores();
    if (selected && (!inventarioId || selected.id === inventarioId)) await cargarDetalle(selected.id);
  } catch (error) {
    toast(error.message, 'error');
  }
}

function revocarCapturador(id) {
  if (!confirm('¿Revocar este capturador? Sincroniza primero sus conteos pendientes.')) return;
  api(`capturadores/${id}/revocar/`, {})
    .then(async () => {
      await cargarCapturadores();
      toast('Capturador revocado.', 'success');
    })
    .catch((error) => toast(error.message, 'error'));
}

function eliminarCapturador(id) {
  const device = devices.find((item) => item.id === id);
  const nombre = device ? device.nombre : 'el capturador';
  if (!confirm(`¿Eliminar a ${nombre}? Se borran sus conteos y su cuenta interna.`)) return;
  api(`capturadores/${id}/eliminar/`, {})
    .then(async () => {
      await cargarCapturadores();
      if (selected) await cargarDetalle(selected.id);
      toast('Capturador eliminado.', 'success');
    })
    .catch((error) => toast(error.message, 'error'));
}

/* ------------------------------------------------------------ acciones --- */

async function generarQr(capturadorId, asignacionId, inventarioId) {
  try {
    const resultado = await api(`capturadores/${capturadorId}/qr/`, {
      inventario: inventarioId,
      asignacion: asignacionId,
    });
    await mostrarQr(resultado);
    toast('QR generado. Escanea el código en el equipo antes de que venza.', 'success');
  } catch (error) {
    toast(error.message, 'error');
  }
}

async function mostrarQr(resultado) {
  const contenido = resultado.contenido_qr;
  let configuracion = resultado.configuracion;
  if (!configuracion) {
    try {
      configuracion = JSON.parse(contenido);
    } catch {
      configuracion = {};
    }
  }
  $('#qr-operador').textContent = configuracion.operador || configuracion.usuario || '';
  $('#qr-bodega').textContent = configuracion.bodega_nombre && configuracion.bodega_nombre !== configuracion.bodega
    ? `${configuracion.bodega} · ${configuracion.bodega_nombre}`
    : configuracion.bodega || '';
  $('#qr-zona').textContent = configuracion.zona_nombre && configuracion.zona_nombre !== configuracion.zona
    ? `${configuracion.zona} · ${configuracion.zona_nombre}`
    : configuracion.zona || '';
  $('#qr-tipo').textContent = configuracion.tipo_nombre || etiquetaTipo(configuracion.tipo);
  $('#qr-inventario').textContent = configuracion.inventario_nombre || configuracion.inventario || '';
  const area = $('#pairing-content');
  area.value = contenido;
  await QRCode.toCanvas($('#pairing-canvas'), contenido, { width: 260, margin: 2 });
  abrirDialogo('modal-qr');
}

function activarPestana(tabActivo, panelActivo) {
  for (const tab of document.querySelectorAll('[role="tab"]')) {
    const activo = tab.id === tabActivo;
    tab.classList.toggle('is-active', activo);
    tab.setAttribute('aria-selected', String(activo));
    tab.tabIndex = activo ? 0 : -1;
  }
  for (const panel of document.querySelectorAll('[role="tabpanel"]')) {
    panel.hidden = panel.id !== panelActivo;
  }
}

/* ---------------------------------------------------------------- init --- */

async function init() {
  const sessionResponse = await fetch(`${apiBase}/api/v1/sesion/`, { credentials: apiBase ? 'include' : 'same-origin' });
  const session = await readJson(sessionResponse, '/api/v1/sesion/');
  if (!sessionResponse.ok) throw new Error(session.error || `Error HTTP ${sessionResponse.status} al consultar la sesión.`);
  if (!session.puede_supervisar_inventario) { window.location.assign('/'); return; }
  csrf = session.csrf;
  $('#username').textContent = session.usuario || '';
  $('#user-initials').textContent = (session.usuario || '?').slice(0, 2).toUpperCase();

  analysisTable = new Tabulator('#analysis-table', {
    layout: 'fitColumns',
    responsiveLayout: 'collapse',
    pagination: true,
    paginationSize: 25,
    columns: [
      { title: 'Zona', field: 'zona' },
      { title: 'Ubicación', field: 'ubicacion_codigo' },
      { title: 'Producto', field: 'producto' },
      { title: 'A', field: 'a' },
      { title: 'B', field: 'b' },
      { title: 'Único', field: 'unico' },
      {
        title: 'Resultado',
        field: 'estado',
        formatter: (cell) => {
          const estado = cell.getValue();
          const variantes = { coincidente: 'chip-success', diferencia: 'chip-warning', faltante: 'chip-danger', pendiente: 'chip-neutral' };
          const textos = { coincidente: 'Coincidente', diferencia: 'Diferencia', faltante: 'Faltante', pendiente: 'Pendiente' };
          return `<span class="chip ${variantes[estado] ?? 'chip-neutral'}">${textos[estado] ?? estado}</span>`;
        },
      },
    ],
  });

  deviceTable = new Tabulator('#device-table', {
    layout: 'fitColumns',
    responsiveLayout: 'collapse',
    pagination: true,
    paginationSize: 25,
    placeholder: () => (devices.length > 0
      ? 'Ningún capturador coincide con la búsqueda.'
      : 'No hay capturadores registrados. Usa «Registrar capturador» para dar de alta un equipo.'),
    columns: [
      {
        title: 'Operador',
        field: 'nombre',
        headerSort: true,
        minWidth: 300,
        responsive: 0,
        formatter: (cell) => {
          const device = cell.getRow().getData();
          return `<div class="flex items-center justify-between gap-3"><span class="font-semibold">${escapar(device.nombre)}</span>${qrHtml(device)}</div>`;
        },
        cellClick: (event) => {
          const botonQr = event.target.closest('button[data-accion="qr"]');
          if (!botonQr) return;
          generarQr(botonQr.getAttribute('data-capturador'), botonQr.getAttribute('data-turno'),
            botonQr.getAttribute('data-inventario'));
        },
      },
      {
        title: 'Estado',
        field: 'activo',
        width: 120,
        headerSort: false,
        formatter: (cell) => (cell.getValue()
          ? '<span class="chip chip-success">Activo</span>'
          : '<span class="chip chip-danger">Revocado</span>'),
      },
      {
        title: 'Vinculación',
        field: 'vinculado',
        width: 140,
        headerSort: false,
        formatter: (cell) => (cell.getValue()
          ? '<span class="chip chip-primary" title="Se emitió una vinculación; el equipo puede haberse desvinculado localmente">Vinculación emitida</span>'
          : '<span class="chip chip-neutral">Sin vincular</span>'),
      },
      {
        title: 'Zona',
        field: 'zonas',
        width: 150,
        headerSort: false,
        formatter: (cell) => zonasHtml(cell.getValue()),
      },
      {
        title: 'Tipo',
        field: 'tipos',
        width: 160,
        headerSort: false,
        formatter: (cell) => tiposHtml(cell.getValue()),
      },
      {
        title: 'Estado del conteo',
        field: 'estadosConteo',
        width: 180,
        headerSort: false,
        formatter: (cell) => estadosConteoHtml(cell.getValue()),
      },
      {
        title: 'Acciones',
        field: 'acciones',
        width: 220,
        headerSort: false,
        formatter: (cell) => accionesHtml(cell.getRow().getData()),
        cellClick: (event) => {
          const botonAccion = event.target.closest('button[data-accion]');
          if (!botonAccion) return;
          const accion = botonAccion.getAttribute('data-accion');
          if (accion === 'qr') {
            generarQr(botonAccion.getAttribute('data-capturador'), botonAccion.getAttribute('data-turno'),
              botonAccion.getAttribute('data-inventario'));
          } else if (accion === 'editar') {
            abrirModalTurno({
              id: botonAccion.getAttribute('data-turno'),
              zona: botonAccion.getAttribute('data-zona'),
              tipo: botonAccion.getAttribute('data-tipo'),
              inventarioId: botonAccion.getAttribute('data-inventario'),
            });
          } else if (accion === 'revocar') {
            revocarCapturador(botonAccion.getAttribute('data-id'));
          } else if (accion === 'eliminar') {
            eliminarCapturador(botonAccion.getAttribute('data-id'));
          }
        },
      },
    ],
  });
  deviceTable.on('dataFiltered', actualizarContadorCapturadores);

  await Promise.all([cargarBodegas(), cargarInventarios(true), cargarCapturadores()]);
}

document.addEventListener?.('DOMContentLoaded', () => {});
function arrancar() {
  init().catch((error) => toast(error.message, 'error'));
}
if (document.readyState === 'loading') document.addEventListener?.('DOMContentLoaded', arrancar);
else arrancar();

$('#open-inventory-modal').addEventListener('click', () => abrirDialogo('modal-inventario'));
// El alta del capturador puede incluir su turno: el supervisor elige inventario,
// zona y tipo en el mismo paso. Si el turno choca con las reglas, la API rechaza
// la operación completa y el equipo no queda creado.
let deviceTurnoToken = 0;

async function prepararNuevoCapturador() {
  const select = $('#device-inventory');
  select.replaceChildren();
  const sinTurno = document.createElement('option');
  sinTurno.value = '';
  sinTurno.textContent = 'Sin conteo por ahora';
  select.append(sinTurno);
  let abiertos = [];
  try {
    const data = await api('?pagina=1&tamano=100');
    abiertos = data.inventarios.filter((item) => item.estado === 'abierto');
  } catch (error) {
    toast(error.message, 'error');
  }
  for (const item of abiertos) {
    const option = document.createElement('option');
    option.value = item.id;
    option.textContent = `${item.nombre} · bodega ${item.bodega}`;
    select.append(option);
  }
  if (selected && abiertos.some((item) => item.id === selected.id)) select.value = selected.id;
  else if (abiertos.length > 0) select.value = abiertos[0].id;
  await actualizarTurnoNuevo();
}

async function actualizarTurnoNuevo() {
  const id = $('#device-inventory').value;
  const zona = $('#device-zone');
  const tipo = $('#device-type');
  const pista = $('#device-hint');
  const boton = $('#create-device button[type="submit"]');
  const token = (deviceTurnoToken += 1);
  if (!id) {
    zona.value = '';
    zona.readOnly = true;
    zona.required = false;
    tipo.disabled = true;
    boton.disabled = false;
    pista.textContent = 'Sin inventario: el capturador queda registrado y podrás asignarle su conteo cuando lo necesites.';
    return;
  }
  zona.readOnly = false;
  zona.required = true;
  tipo.disabled = false;
  boton.disabled = true;
  pista.textContent = 'Leyendo los conteos del inventario…';
  try {
    const detalle = await api(`${id}/`);
    if (token !== deviceTurnoToken) return;
    aplicarSugerenciaTurno(detalle.asignaciones || [], { zona, tipo, pista, boton });
  } catch (error) {
    if (token !== deviceTurnoToken) return;
    toast(error.message, 'error');
    boton.disabled = true;
    pista.textContent = 'No se pudo leer la configuración del inventario.';
  }
}

$('#open-device-modal').addEventListener('click', () => {
  prepararNuevoCapturador().catch((error) => toast(error.message, 'error'));
  abrirDialogo('modal-device');
});
$('#device-inventory').addEventListener('change', () => {
  actualizarTurnoNuevo().catch((error) => toast(error.message, 'error'));
});
$('#close-inventory-modal').addEventListener('click', () => cerrarDialogo('modal-inventario'));
$('#close-device-modal').addEventListener('click', () => cerrarDialogo('modal-device'));
$('#close-qr-modal').addEventListener('click', () => cerrarDialogo('modal-qr'));
$('#close-turn-modal').addEventListener('click', () => cerrarDialogo('modal-turno'));
$('#device-search').addEventListener('input', (event) => {
  const termino = event.target.value.trim().toLowerCase();
  if (!deviceTable) return;
  deviceTable.setFilter((row) => !termino || row.busqueda.includes(termino));
  // `dataFiltered` se emite antes de que el filtro surta efecto; contar aquí ya es fiable.
  actualizarContadorCapturadores();
});
$('#toast-close').addEventListener('click', () => { $('#toast').hidden = true; });
$('#more-inventories').addEventListener('click', () => {
  cargarInventarios().catch((error) => toast(error.message, 'error'));
});

$('#tab-inventarios').addEventListener('click', () => activarPestana('tab-inventarios', 'vista-inventarios'));
$('#tab-capturadores').addEventListener('click', () => activarPestana('tab-capturadores', 'vista-capturadores'));
$('#tab-turnos').addEventListener('click', () => activarPestana('tab-turnos', 'panel-turnos'));
$('#tab-analisis').addEventListener('click', () => {
  activarPestana('tab-analisis', 'panel-analisis');
  if (analysisTable) analysisTable.redraw(true);
});

$('#create-inventory').addEventListener('submit', async (event) => {
  event.preventDefault();
  const nombre = $('#inventory-name').value.trim();
  const bodega = $('#inventory-warehouse').value;
  try {
    const creado = await api('crear/', { nombre, bodega });
    cerrarDialogo('modal-inventario');
    $('#create-inventory').reset();
    await cargarInventarios(true);
    await cargarDetalle(creado.id);
    toast(`Inventario «${nombre}» creado. Registra capturadores con su zona y tipo para empezar.`, 'success');
  } catch (error) {
    toast(error.message, 'error');
  }
});

$('#create-device').addEventListener('submit', async (event) => {
  event.preventDefault();
  const nombre = $('#device-name').value.trim();
  const inventario = $('#device-inventory').value;
  const datos = { nombre };
  if (inventario) {
    datos.inventario = inventario;
    datos.zona = $('#device-zone').value.trim();
    datos.tipo = $('#device-type').value;
  }
  try {
    const creado = await api('capturadores/crear/', datos);
    cerrarDialogo('modal-device');
    $('#create-device').reset();
    await cargarCapturadores();
    if (creado.turno) {
      toast(`Capturador «${creado.nombre}» registrado con su conteo: zona ${creado.turno.zona} · ${etiquetaTipo(creado.turno.tipo)}. Genera su QR para vincular el equipo.`, 'success');
      if (selected && selected.id === inventario) await cargarDetalle(selected.id);
    } else {
      toast(`Capturador «${creado.nombre}» registrado sin conteo. Asígnale inventario, zona y tipo cuando lo necesites.`, 'success');
    }
  } catch (error) {
    toast(error.message, 'error');
  }
});

$('#turn-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  await guardarTurno();
});

$('#detail-close').addEventListener('click', () => {
  if (!selected) return;
  if (!confirm('¿Cerrar este inventario? No se admitirán nuevos conteos.')) return;
  api(`${selected.id}/cerrar/`, {})
    .then(async () => {
      await Promise.all([cargarDetalle(selected.id), cargarInventarios(true), cargarCapturadores()]);
      toast('Inventario cerrado.', 'success');
    })
    .catch((error) => toast(error.message, 'error'));
});

$('#copy-pairing').addEventListener('click', () => {
  const area = $('#pairing-content');
  if (!navigator.clipboard) {
    toast('El navegador no permite copiar. Selecciona el texto manualmente.', 'error');
    return;
  }
  navigator.clipboard.writeText(area.value)
    .then(() => toast('Contenido del QR copiado.', 'success'))
    .catch(() => toast('No se pudo copiar el contenido del QR.', 'error'));
});

/* Navegación lateral y tema, en línea con el resto del portal. */
function esEscritorio() {
  const media = window.matchMedia ? window.matchMedia('(min-width: 768px)') : null;
  return Boolean(media && media.matches);
}

function fijarSidebar(abierto) {
  const sidebar = $('#sidebar');
  if (!sidebar) return;
  sidebar.dataset.state = abierto ? 'open' : 'closed';
  const backdrop = $('#sidebar-backdrop');
  if (backdrop) backdrop.hidden = !abierto;
  const toggle = $('#menu-toggle');
  if (toggle) toggle.setAttribute('aria-expanded', String(abierto));
}

$('#menu-toggle').addEventListener('click', () => {
  const sidebar = $('#sidebar');
  fijarSidebar(sidebar.dataset.state !== 'open');
});
$('#sidebar-backdrop').addEventListener('click', () => fijarSidebar(false));
$('#sidebar-collapse').addEventListener('click', () => {
  const sidebar = $('#sidebar');
  const contraido = sidebar.dataset.collapsed !== 'true';
  sidebar.dataset.collapsed = String(contraido);
  const botonColapsar = $('#sidebar-collapse');
  botonColapsar.setAttribute('aria-expanded', String(!contraido));
  botonColapsar.setAttribute('aria-label', contraido ? 'Expandir el menú' : 'Contraer el menú');
});

const temaGuardado = localStorage.getItem('inet-ivs:tema');
document.documentElement.classList.toggle('dark', temaGuardado === 'dark'
  || (!temaGuardado && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches));

$('#theme-toggle').addEventListener('click', () => {
  document.documentElement.classList.toggle('dark');
  localStorage.setItem('inet-ivs:tema', document.documentElement.classList.contains('dark') ? 'dark' : 'light');
});

if (esEscritorio()) fijarSidebar(false);
