import { TabulatorFull as Tabulator } from 'tabulator-tables';

const $ = (selector) => document.querySelector(selector);
const form = $('#filters');
const THEME_KEY = 'inet-ivs:tema';
const SIDEBAR_KEY = 'inet-ivs:menu';
const apiMeta = document.querySelector('meta[name="api-base"]');
const API_BASE = (apiMeta && apiMeta.content ? String(apiMeta.content) : '').replace(/\/$/, '');
const CREDENTIALS = API_BASE ? 'include' : 'same-origin';
let csrf = '';
let page = 1;
let pages = 1;
let order = 'fecha';
let direction = 'desc';
let canal = '';
let estado = '';
let table;
let applied = new URLSearchParams();
let ordersRequest = 0;
let searchTimer;
let puedeCrearInet = false;

function readStorage(key) {
  try {
    return window.localStorage ? window.localStorage.getItem(key) : null;
  } catch {
    return null;
  }
}

function writeStorage(key, value) {
  try {
    if (window.localStorage) window.localStorage.setItem(key, value);
  } catch {
    /* El navegador puede bloquear el almacenamiento local. */
  }
}

function toast(message, variant = 'info') {
  const element = $('#toast');
  if (!element) return;
  const text = $('#toast-message');
  if (text) text.textContent = message;
  const icon = $('#toast-icon');
  if (icon) icon.setAttribute('href', { success: '#icon-check', error: '#icon-alerta', info: '#icon-info' }[variant] || '#icon-info');
  element.dataset.variant = variant;
  element.hidden = false;
  window.clearTimeout(toast.timer);
  toast.timer = window.setTimeout(() => { element.hidden = true; }, 6000);
}

function prefersDark() {
  const media = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;
  return Boolean(media && media.matches);
}

function applyTheme(theme) {
  document.documentElement.classList.toggle('dark', theme === 'dark');
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.setAttribute('content', theme === 'dark' ? '#0f172a' : '#2563eb');
}

function currentTheme() {
  const stored = readStorage(THEME_KEY);
  if (stored === 'light' || stored === 'dark') return stored;
  return prefersDark() ? 'dark' : 'light';
}

function isDesktop() {
  const media = window.matchMedia ? window.matchMedia('(min-width: 768px)') : null;
  return Boolean(media && media.matches);
}

function syncBodyScroll() {
  if (!document.body) return;
  const sidebar = $('#sidebar');
  const drawerOpen = Boolean(sidebar) && sidebar.dataset.state === 'open' && !isDesktop();
  document.body.style.overflow = drawerOpen ? 'hidden' : '';
}

function setSidebar(open) {
  const sidebar = $('#sidebar');
  if (!sidebar) return;
  sidebar.dataset.state = open ? 'open' : 'closed';
  const backdrop = $('#sidebar-backdrop');
  if (backdrop) backdrop.hidden = !open;
  const toggle = $('#menu-toggle');
  if (toggle) toggle.setAttribute('aria-expanded', String(open));
  syncBodyScroll();
}

function setSidebarCollapsed(collapsed) {
  const sidebar = $('#sidebar');
  if (!sidebar) return;
  sidebar.dataset.collapsed = String(collapsed);
  const button = $('#sidebar-collapse');
  if (button) {
    button.setAttribute('aria-expanded', String(!collapsed));
    button.setAttribute('aria-label', collapsed ? 'Expandir el menú' : 'Contraer el menú');
  }
  writeStorage(SIDEBAR_KEY, collapsed ? 'collapsed' : 'expanded');
}

function apiUrl(path) {
  return `${API_BASE}${path}`;
}

function enTauri() {
  return Boolean(window.__TAURI__ && window.__TAURI__.core && window.__TAURI__.core.invoke);
}

function aBase64(buffer) {
  const bytes = new Uint8Array(buffer);
  let binario = '';
  const bloque = 0x8000;
  for (let indice = 0; indice < bytes.length; indice += bloque) {
    binario += String.fromCharCode.apply(null, bytes.subarray(indice, indice + bloque));
  }
  return btoa(binario);
}

/**
 * Guarda el archivo generado. En la aplicación de escritorio el visor web no
 * puede descargar por sí solo, así que los bytes se envían a la aplicación
 * nativa, que muestra el diálogo de guardado.
 */
async function guardarArchivo(nombre, blob) {
  if (enTauri()) {
    const contenido = aBase64(await blob.arrayBuffer());
    const ruta = await window.__TAURI__.core.invoke('guardar-archivo', { nombre, contenido });
    return { cancelado: ruta === null, ruta };
  }
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = nombre;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 60000);
  return { cancelado: false, ruta: null };
}

async function request(path, options = {}) {
  const response = await fetch(apiUrl(path), { credentials: CREDENTIALS, ...options });
  if (!response.ok) {
    let message = 'No se pudo completar la operación.';
    try { message = (await response.json()).error || message; } catch { /* Respuesta no JSON. */ }
    throw new Error(message);
  }
  return response;
}

async function post(path, data = {}) {
  const response = await request(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': csrf },
    body: new URLSearchParams(data),
  });
  return response.json();
}

function initials(name) {
  const parts = String(name || '').trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return '–';
  return (parts[0][0] + (parts[1] ? parts[1][0] : '')).toUpperCase();
}

function setCurrentNav(current) {
  for (const selector of ['#nav-home', '#nav-orders', '#nav-stock']) {
    const element = $(selector);
    if (!element) continue;
    if (selector === current) element.setAttribute('aria-current', 'page');
    else element.removeAttribute('aria-current');
  }
}

function displaySession(data) {
  csrf = data.csrf;
  puedeCrearInet = Boolean(data.puede_sincronizar);
  $('#login-screen').hidden = Boolean(data.usuario);
  $('#app').hidden = !data.usuario;
  if (data.usuario) {
    $('#username').textContent = data.usuario;
    const avatar = $('#user-initials');
    if (avatar) avatar.textContent = initials(data.usuario);
    $('#greeting').textContent = `Hola, ${data.usuario}`;
    $('#nav-orders').hidden = !data.puede_ver_pedidos;
    $('#nav-stock').hidden = !data.puede_ver_stock;
    const hero = $('#hero-orders');
    if (hero) hero.hidden = !data.puede_ver_pedidos;
    $('#sync').hidden = !data.puede_sincronizar;
    if (window.location.pathname === '/stock/' && data.puede_ver_stock) {
      $('#home').hidden = true;
      $('#stock').hidden = false;
      $('#page-title').textContent = 'Stock Informat';
      setCurrentNav('#nav-stock');
      $('#catalogo').hidden = !data.puede_ver_catalogo;
      $('#token-informat').hidden = !data.puede_administrar_token;
      if (data.puede_ver_catalogo) loadCatalogo(1);
    } else if (window.location.pathname === '/pedidos/' && data.puede_ver_pedidos) {
      $('#home').hidden = true;
      $('#orders').hidden = false;
      $('#page-title').textContent = 'Pedidos AnyMarket';
      setCurrentNav('#nav-orders');
      loadOrders();
    } else if (window.location.hash === '#pedidos' && data.puede_ver_pedidos) {
      $('#nav-orders').click();
    } else {
      setCurrentNav('#nav-home');
    }
  }
}

function channel(value) {
  return ({ mercado_livre: 'MERCADO LIBRE', shopify: 'PORTOMENAJE', 'c52434-09': 'YAKU' })[String(value || '').toLowerCase()] || value || '—';
}

function params() {
  const result = new URLSearchParams(new FormData(form));
  result.set('canal', canal);
  result.set('estado', estado);
  result.set('orden', order);
  result.set('direccion', direction);
  return result;
}

function filterHeader(field, values, selected) {
  return () => {
    const select = document.createElement('select');
    select.setAttribute('aria-label', `Filtrar por ${field === 'canal' ? 'canal' : 'status'}`);
    for (const value of ['', ...new Set([...values.filter(v => typeof v === 'string' && v), selected].filter(Boolean))]) {
      select.add(new Option(value ? (field === 'canal' ? channel(value) : value) : 'Todos', value));
    }
    select.value = selected;
    select.addEventListener('change', () => {
      if (field === 'canal') canal = select.value; else estado = select.value;
      loadOrders();
    });
    ['click', 'keydown', 'pointerdown'].forEach(type => select.addEventListener(type, event => event.stopPropagation()));
    return select;
  };
}

function renderTable(data) {
  const columns = [
    ['Canal', 'canal', 140], ['OC', 'pedido', 120], ['Cliente', 'cliente', 170], ['Fecha', 'fecha', 140],
    ['Ítems', 'items', 80], ['Venta', 'total', 110], ['Status', 'estado', 110], ['Estado', 'fulfillment', 110],
  ];
  if (table) table.destroy();
  table = new Tabulator('#orders-table', {
    data: data.resultados.map(row => ({
      canal: channel(row.canal), pedido: row.numero ?? '—', cliente: row.cliente ?? '—',
      fecha: row.fecha_local ?? '—', items: row.items, total: row.total ?? '—',
      estado: row.estado ?? '—', fulfillment: row.fulfillment ? 'Fulfillment' : '',
      uuid: row.uuid, inet_estado: row.inet_estado, inet_numero: row.inet_numero,
      inet_tipo_documento: row.inet_tipo_documento,
      documento_solicitado: row.documento_solicitado === 'factura' ? 'Factura'
        : row.documento_solicitado === 'boleta' ? 'Boleta' : 'Por confirmar',
    })),
    layout: 'fitColumns', responsiveLayout: 'collapse', placeholder: 'No hay pedidos que coincidan con los filtros.',
    columnDefaults: {
      headerSort: false,
      formatter: cell => { const span = document.createElement('span'); span.textContent = String(cell.getValue() ?? ''); return span; },
      headerClick: (_event, column) => {
        const field = column.getField();
        direction = order === field && direction === 'asc' ? 'desc' : 'asc';
        order = field;
        loadOrders();
      },
    },
    columns: [...columns.map(([label, field, minWidth]) => ({
      title: `${label}${order === field ? (direction === 'asc' ? ' ▲' : ' ▼') : ''}`,
      field, minWidth,
      ...(field === 'canal' ? { headerFilter: filterHeader(field, data.canales, canal), headerFilterFunc: () => true } : {}),
      ...(field === 'estado' ? { headerFilter: filterHeader(field, data.estados, estado), headerFilterFunc: () => true } : {}),
    })), {
      title: 'Documento solicitado', field: 'documento_solicitado', minWidth: 155,
      headerSort: false, headerClick: () => {},
    }, {
      title: 'I-NET', field: 'inet_estado', minWidth: 190, headerSort: false,
      formatter: cell => {
        const row = cell.getRow().getData();
        const container = document.createElement('div');
        const status = document.createElement('span');
        status.textContent = row.inet_estado === 'creado'
          ? `Tipo: ${row.inet_tipo_documento || 'No disponible'} · N.º: ${row.inet_numero}`
          : (row.inet_estado || 'pendiente');
        container.append(status);
        if (puedeCrearInet && ['pendiente', 'error'].includes(row.inet_estado)) {
          const button = document.createElement('button');
          button.type = 'button'; button.className = 'btn btn-secondary btn-sm ml-2';
          button.textContent = row.inet_estado === 'error' ? 'Reintentar' : 'Crear';
          button.addEventListener('click', async event => {
            event.stopPropagation(); button.disabled = true;
            try {
              const result = await post(`/api/v1/pedidos/${row.uuid}/inet/`);
              toast(`${result.mensaje} Tipo: ${result.tipo_documento || 'No disponible'} · N.º: ${result.numero}`, 'success');
            } catch (error) { showInetModal(error.message, row.pedido); }
            finally { await loadOrders(page, true); }
          });
          container.append(button);
        }
        if (puedeCrearInet && ['error', 'revision'].includes(row.inet_estado)) {
          const history = document.createElement('button');
          history.type = 'button'; history.className = 'btn btn-secondary btn-sm ml-2'; history.textContent = 'Ver errores';
          history.addEventListener('click', async event => {
            event.stopPropagation();
            try {
              const data = await (await request(`/api/v1/pedidos/${row.uuid}/inet/errores/`)).json();
              showInetHistory(data.intentos, row.pedido);
            } catch (error) { showInetModal(error.message, row.pedido); }
          });
          container.append(history);
        }
        return container;
      },
    }],
  });
}

function openModal(id, title, description, content) {
  const modal = document.getElementById(id);
  document.getElementById(`${id}-title`).textContent = title;
  document.getElementById(`${id}-description`).textContent = description;
  document.getElementById(`${id}-content`).replaceChildren(content);
  if (!modal.open) modal.showModal();
}

function showInetModal(message, pedido) {
  const detail = document.createElement('div');
  detail.className = 'rounded-xl border border-danger/20 bg-danger-soft p-4 text-sm leading-relaxed text-danger-ink whitespace-pre-wrap break-words';
  detail.textContent = message;
  openModal('inet-modal', 'No se pudo crear el pedido', `Pedido ${pedido} · Detalle de la operación en I-NET`, detail);
}

function showInetHistory(intentos, pedido) {
  const list = document.createElement('ol');
  list.className = 'space-y-3';
  if (!intentos.length) {
    const empty = document.createElement('li');
    empty.className = 'rounded-xl bg-surface-muted p-4 text-sm text-ink-muted';
    empty.textContent = 'No hay intentos registrados para este pedido.';
    list.append(empty);
  }
  for (const intento of intentos) {
    const item = document.createElement('li');
    item.className = 'rounded-xl border border-line bg-surface-muted p-4';
    const header = document.createElement('div');
    header.className = 'flex flex-wrap items-center justify-between gap-2';
    const status = document.createElement('span');
    const labels = { error: 'Error', revision: 'Requiere revisión', creado: 'Creado' };
    status.className = intento.resultado === 'error' ? 'chip chip-danger' : 'chip chip-neutral';
    status.textContent = labels[intento.resultado] || intento.resultado;
    const date = document.createElement('time');
    date.className = 'text-xs text-ink-muted';
    const parsedDate = new Date(intento.fecha);
    date.textContent = Number.isNaN(parsedDate.getTime()) ? 'Fecha no disponible' : parsedDate.toLocaleString('es-CL');
    if (!Number.isNaN(parsedDate.getTime())) date.dateTime = parsedDate.toISOString();
    header.append(status, date);
    const detail = document.createElement('p');
    detail.className = 'mt-3 whitespace-pre-wrap break-words text-sm leading-relaxed text-ink';
    detail.textContent = intento.detalle || 'Sin detalle adicional.';
    item.append(header, detail);
    list.append(item);
  }
  openModal('inet-modal', 'Historial de envíos', `Pedido ${pedido} · Intentos registrados en I-NET`, list);
}

function renderSyncStatus(data) {
  const container = $('#sync-status');
  if (!container) return;
  container.replaceChildren();
  const format = value => value ? new Intl.DateTimeFormat('es-CL', {
    timeZone: data.zona_horaria, dateStyle: 'short', timeStyle: 'medium',
  }).format(new Date(value)) : 'Sin registro';
  for (const [key, label] of [['pedidos', 'Sincronización'], ['reconciliacion', 'Reconciliación']]) {
    const state = data.sincronizaciones[key] || {};
    const item = document.createElement('div');
    item.className = state.ultimo_error ? 'chip chip-danger' : 'chip chip-success';
    item.textContent = `${label}: ${format(state.ultimo_exito)}`;
    if (state.ultimo_error) {
      const error = document.createElement('span');
      error.textContent = `Error: ${state.ultimo_error}${state.ultimo_error_en ? ` (${format(state.ultimo_error_en)})` : ''}`;
      item.append(error);
    }
    container.append(item);
  }
}

async function loadOrders(next = 1, keep = false) {
  const requestId = ++ordersRequest;
  try {
    const selected = keep ? new URLSearchParams(applied) : params();
    selected.set('page', String(next));
    const data = await (await request(`/api/v1/pedidos/?${selected}`)).json();
    if (requestId !== ordersRequest) return;
    selected.delete('page');
    applied = selected;
    page = data.pagina;
    pages = data.paginas;
    $('#pagination').textContent = `${data.total} pedidos · Página ${page} de ${pages}`;
    $('#previous').disabled = page <= 1;
    $('#next').disabled = page >= pages;
    renderSyncStatus(data);
    renderTable(data);
  } catch (error) {
    if (requestId !== ordersRequest) return;
    $('#pagination').textContent = 'Sin datos';
    toast(error.message, 'error');
  }
}

$('#login-form').addEventListener('submit', async event => {
  event.preventDefault();
  const loginForm = event.currentTarget;
  try {
    const formData = new FormData(loginForm);
    const result = await post('/api/v1/ingresar/', Object.fromEntries(formData));
    loginForm.reset();
    displaySession(result);
  } catch (error) { toast(error.message, 'error'); }
});
$('#logout').addEventListener('click', async () => {
  try { const data = await post('/api/v1/salir/'); displaySession({ ...data, usuario: null }); }
  catch (error) { toast(error.message, 'error'); }
});
$('#nav-home').addEventListener('click', () => { window.location.assign('/'); });
$('#nav-orders').addEventListener('click', () => { window.location.assign('/pedidos/'); });
$('#nav-stock').addEventListener('click', () => { window.location.assign('/stock/'); });
$('#token-informat-form').addEventListener('submit', async event => {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form.querySelector('button[type="submit"]');
  button.disabled = true;
  try {
    const result = await post('/api/v1/informat/token/', new FormData(form));
    form.reset();
    toast(result.mensaje, 'success');
  } catch (error) {
    toast(error.message, 'error');
  } finally {
    button.disabled = false;
  }
});
let catalogoTable;
let catalogoPagina = 1;
let catalogoHayMas = false;
let catalogoRequest = 0;
async function loadCatalogo(pagina) {
  const id = ++catalogoRequest;
  $('#catalogo-estado').textContent = 'Cargando productos…';
  $('#catalogo-anterior').disabled = true;
  $('#catalogo-siguiente').disabled = true;
  try {
    const query = new URLSearchParams({ busqueda: $('#catalogo-busqueda').value, pagina: String(pagina), tamano: '25' });
    const data = await (await request(`/api/v1/informat/productos/?${query}`)).json();
    if (id !== catalogoRequest) return;
    catalogoPagina = data.pagina;
    catalogoHayMas = data.hay_mas;
    $('#catalogo-pagina').textContent = `Página ${catalogoPagina}`;
    $('#catalogo-estado').textContent = data.productos.length ? `${data.productos.length} producto(s) en esta página.` : 'No se encontraron productos.';
    if (catalogoTable) catalogoTable.destroy();
    catalogoTable = new Tabulator('#catalogo-tabla', {
      data: data.productos, layout: 'fitColumns', responsiveLayout: 'collapse',
      columns: [
        { title: 'Código', field: 'codigo', formatter: 'plaintext' },
        { title: 'Descripción', field: 'descripcion', formatter: 'plaintext' },
        { title: 'Código de barras', field: 'codigo_barra', formatter: 'plaintext' },
      ],
    });
  } catch (error) {
    if (id !== catalogoRequest) return;
    $('#catalogo-estado').textContent = 'No se pudo cargar el catálogo.';
    catalogoHayMas = false;
    toast(error.message, 'error');
  } finally {
    if (id === catalogoRequest) {
      $('#catalogo-anterior').disabled = catalogoPagina <= 1;
      $('#catalogo-siguiente').disabled = !catalogoHayMas;
    }
  }
}
$('#catalogo-filtros').addEventListener('submit', event => { event.preventDefault(); loadCatalogo(1); });
$('#catalogo-anterior').addEventListener('click', () => loadCatalogo(catalogoPagina - 1));
$('#catalogo-siguiente').addEventListener('click', () => loadCatalogo(catalogoPagina + 1));
let stockTable;
let stockRequest = 0;
$('#stock-filters').addEventListener('submit', async event => {
  event.preventDefault();
  const id = ++stockRequest;
  const button = event.currentTarget.querySelector('button[type="submit"]');
  button.disabled = true;
  $('#stock-status').textContent = 'Consultando…';
  if (stockTable) { stockTable.destroy(); stockTable = null; }
  try {
    const query = new URLSearchParams(new FormData(event.currentTarget));
    const data = await (await request(`/api/v1/informat/stock/?${query}`)).json();
    if (id !== stockRequest) return;
    const rows = data.productos.flatMap(producto => {
      const bodegas = producto.bodegas.length ? producto.bodegas : [{}];
      return bodegas.map(bodega => ({ ...producto, bodega: bodega.bodega, disponible_bodega: bodega.disponible }));
    });
    $('#stock-status').textContent = rows.length ? `${data.productos.length} producto(s) encontrado(s).` : 'No se encontraron productos.';
    stockTable = new Tabulator('#stock-table', {
      data: rows, layout: 'fitColumns', responsiveLayout: 'collapse', pagination: true, paginationSize: 20,
      columns: [
        { title: 'Producto', field: 'producto', formatter: 'plaintext' },
        { title: 'Descripción', field: 'descripcion', formatter: 'plaintext' },
        { title: 'Stock actual general', field: 'stock_actual', formatter: 'plaintext' },
        { title: 'Disponible general', field: 'stock_disponible', formatter: 'plaintext' },
        { title: 'Bodega', field: 'bodega', formatter: 'plaintext' },
        { title: 'Disponible en bodega', field: 'disponible_bodega', formatter: 'plaintext' },
      ],
    });
  } catch (error) {
    if (id === stockRequest) { $('#stock-status').textContent = 'No se pudo obtener el stock.'; toast(error.message, 'error'); }
  } finally { if (id === stockRequest) button.disabled = false; }
});
$('#hero-orders').addEventListener('click', () => { window.location.assign('/pedidos/'); });
$('#menu-toggle').addEventListener('click', () => {
  const sidebar = $('#sidebar');
  setSidebar(sidebar.dataset.state !== 'open');
});
$('#sidebar-backdrop').addEventListener('click', () => setSidebar(false));
$('#sidebar-collapse').addEventListener('click', () => {
  const sidebar = $('#sidebar');
  setSidebarCollapsed(sidebar.dataset.collapsed !== 'true');
});
$('#theme-toggle').addEventListener('click', () => {
  const theme = currentTheme() === 'dark' ? 'light' : 'dark';
  writeStorage(THEME_KEY, theme);
  applyTheme(theme);
});
$('#toast-close').addEventListener('click', () => { $('#toast').hidden = true; });
document.addEventListener('keydown', event => {
  if (event.key === 'Escape') {
    const sidebar = $('#sidebar');
    if (sidebar.dataset.state === 'open') setSidebar(false);
  }
});
if (window.addEventListener) window.addEventListener('resize', syncBodyScroll);
form.addEventListener('submit', event => { event.preventDefault(); loadOrders(); });
$('#filtro-busqueda').addEventListener('input', () => {
  ordersRequest++;
  window.clearTimeout(searchTimer);
  searchTimer = window.setTimeout(() => loadOrders(), 350);
});
$('#previous').addEventListener('click', () => loadOrders(page - 1, true));
$('#next').addEventListener('click', () => loadOrders(page + 1, true));
$('#sync').addEventListener('click', async () => { try { toast((await post('/api/v1/pedidos/sincronizar/')).mensaje, 'success'); } catch (error) { toast(error.message, 'error'); } });
$('#export').addEventListener('click', async () => {
  try {
    const response = await request(`/api/v1/pedidos/exportar/?${applied}`);
    const blob = await response.blob();
    const resultado = await guardarArchivo('pedidos.xlsx', blob);
    if (resultado.cancelado) toast('Se canceló el guardado del archivo.', 'info');
    else toast(resultado.ruta ? `Archivo guardado en ${resultado.ruta}` : 'Archivo generado correctamente.', 'success');
  } catch (error) { toast(error.message, 'error'); }
});

setSidebar(false);
setSidebarCollapsed(readStorage(SIDEBAR_KEY) === 'collapsed');
applyTheme(currentTheme());
if (window.Litepicker) {
  const desde = $('#filtro-desde');
  const hasta = $('#filtro-hasta');
  const picker = new window.Litepicker({
    element: $('#filtro-rango'),
    singleMode: false,
    format: 'DD-MM-YYYY',
    delimiter: ' - ',
    lang: 'es-ES',
    setup(instance) {
      instance.on('selected', (inicio, fin) => {
        desde.value = inicio.format('YYYY-MM-DD');
        hasta.value = fin.format('YYYY-MM-DD');
        window.clearTimeout(searchTimer);
        loadOrders();
      });
    },
  });
  $('#limpiar-rango').addEventListener('click', () => {
    picker.clearSelection();
    desde.value = '';
    hasta.value = '';
    window.clearTimeout(searchTimer);
    loadOrders();
  });
  $('#fechas-alternativas').hidden = true;
  $('#rango-fechas').hidden = false;
} else {
  for (const input of [$('#filtro-desde'), $('#filtro-hasta')]) {
    input.addEventListener('change', () => loadOrders());
  }
}
request('/api/v1/sesion/').then(response => response.json()).then(displaySession).catch(error => toast(error.message, 'error'));
