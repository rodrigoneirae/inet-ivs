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
let puedeDescargarCatalogo = false;
let perfilesPagina = 1;
let perfilesBusqueda = '';
let perfilesRequest = 0;
let perfilesDisponibles = [];
let permisosDisponibles = [];

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
  const body = new URLSearchParams();
  if (data instanceof FormData || data instanceof URLSearchParams) {
    for (const [key, value] of data.entries()) body.append(key, value);
  } else {
    for (const [key, value] of Object.entries(data)) {
      if (Array.isArray(value)) value.forEach(item => body.append(key, item));
      else if (value !== undefined && value !== null) body.append(key, value);
    }
  }
  const response = await request(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': csrf },
    body,
  });
  return response.json();
}

function initials(name) {
  const parts = String(name || '').trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return '–';
  return (parts[0][0] + (parts[1] ? parts[1][0] : '')).toUpperCase();
}

function setCurrentNav(current) {
  for (const selector of ['#nav-home', '#nav-orders', '#nav-stock', '#nav-catalogo', '#nav-configuracion']) {
    const element = $(selector);
    if (!element) continue;
    if (selector === current) element.setAttribute('aria-current', 'page');
    else element.removeAttribute('aria-current');
  }
}

function displaySession(data) {
  csrf = data.csrf;
  puedeCrearInet = Boolean(data.puede_sincronizar);
  puedeDescargarCatalogo = Boolean(data.puede_ver_catalogo_web && data.puede_descargar_catalogo);
  $('#login-screen').hidden = Boolean(data.usuario);
  $('#app').hidden = !data.usuario;
  if (data.usuario) {
    $('#username').textContent = data.usuario;
    const avatar = $('#user-initials');
    if (avatar) avatar.textContent = initials(data.usuario);
  $('#greeting').textContent = `Hola, ${data.usuario}`;
    $('#nav-orders').hidden = !data.puede_ver_pedidos;
    $('#nav-stock').hidden = !data.puede_ver_stock;
    $('#nav-catalogo').hidden = !data.puede_ver_catalogo_web;
    const puedeConfigurar = Boolean(data.puede_configurar_usuarios || data.puede_administrar_token);
    $('#nav-configuracion').hidden = !puedeConfigurar;
    $('#config-informat').hidden = !data.puede_administrar_token;
    $('#config-acceso').hidden = !data.puede_configurar_usuarios;
    const hero = $('#hero-orders');
    if (hero) hero.hidden = !data.puede_ver_pedidos;
    $('#sync').hidden = !data.puede_sincronizar;
    const rutaActual = window.location.pathname || '/';
    if (rutaActual === '/configuracion/' && puedeConfigurar) {
      $('#home').hidden = true;
      $('#stock').hidden = true;
      $('#orders').hidden = true;
      $('#catalogo-web').hidden = true;
      $('#user-profiles').hidden = true;
      $('#configuracion').hidden = false;
      $('#page-title').textContent = 'Configuración';
      setCurrentNav('#nav-configuracion');
    } else if (rutaActual === '/usuarios/' && data.puede_configurar_usuarios) {
      $('#home').hidden = true;
      $('#stock').hidden = true;
      $('#orders').hidden = true;
      $('#catalogo-web').hidden = true;
      $('#user-profiles').hidden = false;
      $('#configuracion').hidden = true;
      $('#page-title').textContent = 'Perfiles de usuario';
      setCurrentNav('#nav-users');
      selectUsersTab('usuarios');
      loadUserProfiles(1, $('#perfiles-filtro').value.trim());
    } else if (rutaActual.startsWith('/catalogo/') && data.puede_ver_catalogo_web) {
      $('#home').hidden = true;
      $('#stock').hidden = true;
      $('#orders').hidden = true;
      $('#catalogo-web').hidden = false;
      $('#page-title').textContent = 'Catálogo';
      setCurrentNav('#nav-catalogo');
      renderCatalogoWebRoute();
    } else if (rutaActual.startsWith('/catalogo/') && !data.puede_ver_catalogo_web) {
      toast('No tienes permiso para consultar el catálogo.', 'error');
      setCurrentNav('#nav-home');
    } else if (rutaActual === '/stock/' && data.puede_ver_stock) {
      $('#home').hidden = true;
      $('#stock').hidden = false;
      $('#configuracion').hidden = true;
      $('#page-title').textContent = 'Stock Informat';
      setCurrentNav('#nav-stock');
      $('#catalogo').hidden = !data.puede_ver_catalogo;
      $('#token-informat').hidden = !data.puede_administrar_token;
      if (data.puede_ver_catalogo) loadCatalogo(1);
    } else if (rutaActual === '/pedidos/' && data.puede_ver_pedidos) {
      $('#home').hidden = true;
      $('#orders').hidden = false;
      $('#configuracion').hidden = true;
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
      ...(field === 'fulfillment' ? { formatter: cell => {
        const row = cell.getRow().getData();
        const span = document.createElement('span');
        const documento = row.inet_estado === 'creado'
          ? `Tipo: ${row.inet_tipo_documento || 'No disponible'} · N.º: ${row.inet_numero}` : '';
        span.textContent = [row.fulfillment, documento].filter(Boolean).join(' · ');
        return span;
      } } : {}),
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
        status.textContent = row.inet_estado === 'creado' ? 'Creado'
          : row.fulfillment ? 'No aplica · Fulfillment' : (row.inet_estado || 'pendiente');
        container.append(status);
        if (puedeCrearInet && !row.fulfillment && ['pendiente', 'error'].includes(row.inet_estado)) {
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
        if (puedeCrearInet) {
          const history = document.createElement('button');
          history.type = 'button'; history.className = 'btn btn-secondary btn-sm ml-2'; history.textContent = 'Historial I-NET';
          history.addEventListener('click', async event => {
            event.stopPropagation();
            try {
              const data = await (await request(`/api/v1/pedidos/${row.uuid}/inet/errores/`)).json();
              showInetHistory(data.intentos, row.pedido, row.uuid);
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

function showInetHistory(intentos, pedido, pedidoUuid) {
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
    if (intento.uuid && pedidoUuid) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'btn btn-secondary btn-sm mt-3';
      button.textContent = 'Ver solicitud y respuesta';
      const messages = document.createElement('div');
      messages.className = 'mt-3 space-y-3';
      messages.hidden = true;
      button.addEventListener('click', async () => {
        if (!messages.hidden) { messages.hidden = true; return; }
        button.disabled = true;
        try {
          const data = await (await request(`/api/v1/pedidos/${pedidoUuid}/inet/intentos/${intento.uuid}/`)).json();
          messages.replaceChildren();
          for (const [label, value] of [['Solicitud', data.solicitud], ['Respuesta', data.respuesta]]) {
            const section = document.createElement('section');
            const heading = document.createElement('h3');
            heading.className = 'text-sm font-semibold text-ink';
            heading.textContent = label;
            const pre = document.createElement('pre');
            pre.className = 'mt-2 max-h-64 overflow-auto whitespace-pre-wrap break-all rounded-lg bg-surface p-3 text-xs text-ink';
            pre.textContent = value === null ? 'No disponible para este intento.' : JSON.stringify(value, null, 2);
            section.append(heading, pre);
            messages.append(section);
          }
          messages.hidden = false;
        } catch (error) { toast(error.message, 'error'); }
        finally { button.disabled = false; }
      });
      item.append(button, messages);
    }
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
$('#nav-catalogo').addEventListener('click', () => { window.location.assign('/catalogo/'); });
$('#nav-configuracion').addEventListener('click', () => { window.location.assign('/configuracion/'); });
$('#config-informat-abrir').addEventListener('click', () => {
  $('#configuracion-inicio').hidden = true;
  $('#configuracion-informat-detalle').hidden = false;
  $('#token-valor').focus();
});
$('#config-informat-volver').addEventListener('click', () => {
  $('#configuracion-informat-detalle').hidden = true;
  $('#configuracion-inicio').hidden = false;
});

function renderPermissionChoices(seleccionados = []) {
  const opciones = $('#perfil-permisos');
  opciones.replaceChildren();
  const seleccion = new Set(seleccionados);
  permisosDisponibles.forEach((permiso, indice) => {
    const label = catalogoElemento('label', 'flex cursor-pointer items-start gap-2 rounded-lg border border-line p-2.5 text-sm text-ink hover:bg-surface-muted');
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.name = 'permisos';
    checkbox.value = permiso.clave;
    checkbox.checked = seleccion.has(permiso.clave);
    checkbox.className = 'mt-0.5 size-4 shrink-0 rounded accent-primary';
    checkbox.id = `permiso-perfil-${indice}`;
    label.htmlFor = checkbox.id;
    label.append(checkbox, document.createTextNode(permiso.nombre));
    opciones.append(label);
  });
}

function renderProfilesList() {
  const lista = $('#perfiles-lista');
  lista.replaceChildren();
  for (const perfil of perfilesDisponibles) {
    const tarjeta = catalogoElemento('article', 'rounded-lg border border-line p-3');
    const encabezado = catalogoElemento('div', 'flex flex-wrap items-center justify-between gap-2');
    encabezado.append(catalogoElemento('h4', 'font-semibold text-ink', perfil.nombre));
    encabezado.append(catalogoElemento('span', 'chip chip-neutral',
      perfil.administrador ? 'Perfil protegido' : `${perfil.usuarios_asignados} usuarios`));
    tarjeta.append(encabezado);
    const permisos = catalogoElemento('div', 'mt-2 flex flex-wrap gap-1.5');
    const etiquetas = perfil.permisos.map(clave => permisosDisponibles.find(opcion => opcion.clave === clave)?.nombre || clave);
    if (etiquetas.length) {
      for (const etiqueta of etiquetas) permisos.append(catalogoElemento('span', 'chip chip-neutral text-xs', etiqueta));
    } else {
      permisos.append(catalogoElemento('span', 'text-sm text-ink-muted', 'Sin permisos asignados'));
    }
    tarjeta.append(permisos);
    if (!perfil.administrador) {
      const acciones = catalogoElemento('div', 'mt-3 flex gap-2');
      const editar = catalogoElemento('button', 'btn btn-secondary btn-sm', 'Editar');
      editar.type = 'button';
      editar.dataset.editarPerfil = perfil.clave;
      const eliminar = catalogoElemento('button', 'btn btn-danger btn-sm', 'Eliminar');
      eliminar.type = 'button';
      eliminar.dataset.eliminarPerfil = perfil.clave;
      eliminar.disabled = perfil.usuarios_asignados > 0;
      eliminar.title = eliminar.disabled ? 'Retira el perfil de los usuarios antes de eliminarlo.' : '';
      acciones.append(editar, eliminar);
      tarjeta.append(acciones);
    }
    lista.append(tarjeta);
  }
  if (!perfilesDisponibles.length) {
    lista.append(catalogoElemento('p', 'text-sm text-ink-muted', 'Aún no hay perfiles configurados.'));
  }
}

function selectUsersTab(tabName, focus = false) {
  const mostrarPerfiles = tabName === 'perfiles';
  const tabPerfiles = $('#tab-perfiles');
  const tabUsuarios = $('#tab-usuarios');
  tabPerfiles.classList.toggle('is-active', mostrarPerfiles);
  tabUsuarios.classList.toggle('is-active', !mostrarPerfiles);
  tabPerfiles.setAttribute('aria-selected', String(mostrarPerfiles));
  tabUsuarios.setAttribute('aria-selected', String(!mostrarPerfiles));
  tabPerfiles.tabIndex = mostrarPerfiles ? 0 : -1;
  tabUsuarios.tabIndex = mostrarPerfiles ? -1 : 0;
  $('#panel-perfiles').hidden = !mostrarPerfiles;
  $('#panel-usuarios').hidden = mostrarPerfiles;
  if (focus) (mostrarPerfiles ? tabPerfiles : tabUsuarios).focus();
}

$('#tab-perfiles').addEventListener('click', () => selectUsersTab('perfiles'));
$('#tab-usuarios').addEventListener('click', () => selectUsersTab('usuarios'));
for (const [selector, nombre] of [['#tab-usuarios', 'usuarios'], ['#tab-perfiles', 'perfiles']]) {
  $(selector).addEventListener('keydown', event => {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    const destino = event.key === 'Home' ? 'usuarios'
      : event.key === 'End' ? 'perfiles'
        : nombre === 'perfiles' ? 'usuarios' : 'perfiles';
    selectUsersTab(destino, true);
  });
}

async function loadUserProfiles(pagina = 1, busqueda = '') {
  const solicitud = ++perfilesRequest;
  $('#perfiles-estado').textContent = 'Cargando usuarios…';
  $('#perfiles-anterior').disabled = true;
  $('#perfiles-siguiente').disabled = true;
  try {
    const query = new URLSearchParams({ pagina: String(pagina), busqueda });
    const respuesta = await request(`/api/v1/acceso/perfiles/usuarios/?${query}`);
    const datos = await respuesta.json();
    if (solicitud !== perfilesRequest) return;
    perfilesPagina = datos.pagina;
    perfilesBusqueda = busqueda;
    perfilesDisponibles = datos.perfiles;
    permisosDisponibles = datos.permisos_disponibles;
    renderProfilesList();
    renderPermissionChoices();
    $('#perfiles-total').textContent = `${datos.total} usuarios`;
    $('#tab-usuarios-count').textContent = datos.total;
    $('#tab-perfiles-count').textContent = datos.perfiles.length;
    $('#perfiles-sin-configurar').hidden = datos.grupo_configurado;
    const filas = $('#perfiles-usuarios');
    filas.replaceChildren();
    if (!datos.usuarios.length) {
      const filaVacia = catalogoElemento('tr', '');
      const celdaVacia = catalogoElemento('td', 'px-4 py-6 text-center text-ink-muted', 'No se encontraron usuarios.');
      celdaVacia.colSpan = 4;
      filaVacia.append(celdaVacia);
      filas.append(filaVacia);
    }
    let indiceFila = 0;
    for (const usuario of datos.usuarios) {
      const fila = catalogoElemento('tr', 'align-middle');
      fila.append(catalogoElemento('th', 'px-4 py-3 font-medium text-ink', usuario.username));
      fila.append(catalogoElemento('td', 'px-4 py-3 text-ink-muted', usuario.activo ? 'Activo' : 'Inactivo'));
      const perfil = catalogoElemento('td', 'px-4 py-3');
      if (usuario.superusuario) {
        perfil.append(catalogoElemento('span', 'chip chip-neutral', 'Superusuario · acceso total'));
      } else {
        const formulario = catalogoElemento('form', 'flex flex-wrap gap-2');
        formulario.dataset.perfilUsuario = 'true';
        formulario.id = `perfil-usuario-form-${indiceFila}`;
        const nombre = document.createElement('input');
        nombre.type = 'hidden';
        nombre.name = 'username';
        nombre.value = usuario.username;
        formulario.append(nombre);
        const gruposAsignados = new Set(usuario.perfiles);
        for (const perfilDisponible of perfilesDisponibles) {
          const label = catalogoElemento('label', 'inline-flex cursor-pointer items-center gap-1.5 rounded-full border border-line px-2.5 py-1 text-xs text-ink hover:bg-surface-muted');
          const checkbox = document.createElement('input');
          checkbox.type = 'checkbox';
          checkbox.name = 'perfiles';
          checkbox.value = perfilDisponible.clave;
          checkbox.checked = gruposAsignados.has(perfilDisponible.clave);
          checkbox.className = 'size-3.5 rounded accent-primary';
          label.append(checkbox, document.createTextNode(perfilDisponible.nombre));
          formulario.append(label);
        }
        perfil.append(formulario);
      }
      fila.append(perfil);
      const accion = catalogoElemento('td', 'px-4 py-3 text-right');
      if (!usuario.superusuario) {
        const guardar = catalogoElemento('button', 'btn btn-secondary btn-sm', 'Guardar');
        guardar.type = 'submit';
        guardar.disabled = !perfilesDisponibles.length;
        guardar.setAttribute('form', `perfil-usuario-form-${indiceFila}`);
        indiceFila += 1;
        accion.append(guardar);
      }
      fila.append(accion);
      filas.append(fila);
    }
    $('#perfiles-estado').textContent = datos.usuarios.length
      ? 'Solo los superusuarios pueden cambiar este perfil. Los cambios se aplican inmediatamente.'
      : '';
    $('#perfiles-pagina').textContent = `Página ${datos.pagina} de ${datos.paginas}`;
    $('#perfiles-anterior').disabled = !datos.hay_anterior;
    $('#perfiles-siguiente').disabled = !datos.hay_siguiente;
  } catch (error) {
    if (solicitud !== perfilesRequest) return;
    $('#perfiles-estado').textContent = 'No se pudieron cargar los usuarios.';
    toast(error.message, 'error');
  }
}

$('#perfiles-busqueda').addEventListener('submit', event => {
  event.preventDefault();
  loadUserProfiles(1, $('#perfiles-filtro').value.trim());
});
$('#perfiles-usuarios').addEventListener('submit', async event => {
  const formulario = event.target.closest('form[data-perfil-usuario]');
  if (!formulario) return;
  event.preventDefault();
  const guardar = event.submitter instanceof HTMLButtonElement
    ? event.submitter
    : document.querySelector(`button[form="${formulario.id}"]`);
  if (guardar) guardar.disabled = true;
  try {
    const datos = new FormData(formulario);
    const actualizado = await post('/api/v1/acceso/perfiles/usuario/', {
      username: datos.get('username'),
      perfiles: datos.getAll('perfiles'),
    });
    toast(`Perfiles de ${actualizado.username} actualizados.`, 'success');
    await loadUserProfiles(perfilesPagina, perfilesBusqueda);
  } catch (error) {
    toast(error.message, 'error');
  } finally {
    if (guardar) guardar.disabled = false;
  }
});
$('#perfil-editor').addEventListener('submit', async event => {
  event.preventDefault();
  const editor = event.currentTarget;
  const boton = $('#perfil-guardar');
  boton.disabled = true;
  try {
    const datos = new FormData(editor);
    const resultado = await post('/api/v1/acceso/perfiles/guardar/', {
      nombre: datos.get('nombre'),
      nombre_original: datos.get('nombre_original'),
      permisos: datos.getAll('permisos'),
    });
    toast(resultado.mensaje, 'success');
    editor.reset();
    editor.elements.nombre_original.value = '';
    $('#perfil-editor-titulo').textContent = 'Crear perfil';
    boton.textContent = 'Crear perfil';
    $('#perfil-cancelar').hidden = true;
    await loadUserProfiles(perfilesPagina, perfilesBusqueda);
  } catch (error) {
    toast(error.message, 'error');
  } finally {
    boton.disabled = false;
  }
});
$('#perfil-cancelar').addEventListener('click', () => {
  const editor = $('#perfil-editor');
  editor.reset();
  editor.elements.nombre_original.value = '';
  $('#perfil-editor-titulo').textContent = 'Crear perfil';
  $('#perfil-guardar').textContent = 'Crear perfil';
  $('#perfil-cancelar').hidden = true;
});
$('#perfiles-lista').addEventListener('click', async event => {
  const editar = event.target.closest('[data-editar-perfil]');
  if (editar) {
    const perfil = perfilesDisponibles.find(item => item.clave === editar.dataset.editarPerfil);
    if (!perfil) return;
    const editor = $('#perfil-editor');
    editor.elements.nombre.value = perfil.nombre;
    editor.elements.nombre_original.value = perfil.nombre;
    renderPermissionChoices(perfil.permisos);
    $('#perfil-editor-titulo').textContent = `Editar perfil: ${perfil.nombre}`;
    $('#perfil-guardar').textContent = 'Guardar cambios';
    $('#perfil-cancelar').hidden = false;
    editor.scrollIntoView({ behavior: 'smooth', block: 'start' });
    return;
  }
  const eliminar = event.target.closest('[data-eliminar-perfil]');
  if (!eliminar) return;
  try {
    const resultado = await post('/api/v1/acceso/perfiles/eliminar/', { clave: eliminar.dataset.eliminarPerfil });
    toast(resultado.mensaje, 'success');
    await loadUserProfiles(perfilesPagina, perfilesBusqueda);
  } catch (error) {
    toast(error.message, 'error');
  }
});
$('#perfiles-anterior').addEventListener('click', () => loadUserProfiles(perfilesPagina - 1, perfilesBusqueda));
$('#perfiles-siguiente').addEventListener('click', () => loadUserProfiles(perfilesPagina + 1, perfilesBusqueda));
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

let catalogoWebRequest = 0;
let catalogoWebPagina = 1;
let catalogoWebFacetas = [];
let catalogoWebFacetasCargando;
const catalogoWebClavesAtributo = ['ATTUNO', 'ATTDOS', 'ATTTRE', 'ATTCUA', 'ATTCIN'];

function catalogoElemento(etiqueta, clases, texto) {
  const elemento = document.createElement(etiqueta);
  if (clases) elemento.className = clases;
  if (texto !== undefined) elemento.textContent = String(texto);
  return elemento;
}

function catalogoImagen(src, alt, clases = 'aspect-square w-full rounded-lg bg-white object-contain') {
  if (!src) return catalogoElemento('div', `${clases} grid place-items-center text-sm text-slate-500`, 'Imagen no disponible');
  const imagen = catalogoElemento('img', clases);
  imagen.src = src;
  imagen.alt = alt;
  imagen.loading = 'lazy';
  imagen.addEventListener('error', () => {
    imagen.replaceWith(catalogoElemento('div', `${clases} grid place-items-center text-sm text-slate-500`, 'Imagen no disponible'));
  }, { once: true });
  return imagen;
}

function filtrosCatalogoSeleccionados() {
  return Object.fromEntries(catalogoWebClavesAtributo.map(clave => [
    clave,
    [...document.querySelectorAll(`input[name="${clave}"]:checked`)].map(input => input.value),
  ]));
}

function filtrosCatalogoDesdeUrl(params) {
  return Object.fromEntries(catalogoWebClavesAtributo.map(clave => [clave, params.getAll(clave)]));
}

function actualizarContadorFiltrosCatalogo() {
  const seleccionados = filtrosCatalogoSeleccionados();
  const cantidad = Object.values(seleccionados).reduce((total, valores) => total + valores.length, 0);
  const boton = $('#catalogo-web-filtros-toggle');
  boton.textContent = cantidad ? `Filtros (${cantidad})` : 'Filtros';
  boton.setAttribute('aria-label', cantidad ? `Filtros, ${cantidad} activos` : 'Abrir filtros por atributos');

  const contenedor = $('#catalogo-web-filtros-activos');
  contenedor.replaceChildren();
  for (const [clave, valores] of Object.entries(seleccionados)) {
    const nombreGrupo = catalogoWebFacetas.find(grupo => grupo.clave === clave)?.nombre || `Atributo ${clave}`;
    for (const valor of valores) {
      const chip = catalogoElemento('span', 'chip chip-neutral inline-flex items-center gap-1.5', `${nombreGrupo}: ${valor}`);
      const quitar = catalogoElemento('button', 'ml-1 inline-grid h-5 w-5 place-items-center rounded-full text-ink-muted hover:bg-surface-muted hover:text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary', '×');
      quitar.type = 'button';
      quitar.setAttribute('aria-label', `Quitar filtro ${nombreGrupo}: ${valor}`);
      quitar.addEventListener('click', () => {
        const checkbox = [...document.querySelectorAll(`input[name="${clave}"]`)]
          .find(input => input.value === valor);
        if (checkbox) {
          checkbox.checked = false;
          aplicarFiltrosCatalogo();
        }
      });
      chip.append(quitar);
      contenedor.append(chip);
    }
  }
}

function aplicarFiltrosCatalogo() {
  const busqueda = $('#catalogo-web-busqueda').value.trim();
  const filtros = filtrosCatalogoSeleccionados();
  const query = new URLSearchParams();
  for (const [clave, valores] of Object.entries(filtros)) {
    for (const valor of valores) query.append(clave, valor);
  }
  if (busqueda) query.set('busqueda', busqueda);
  window.history.pushState({}, '', `/catalogo/${query.size ? `?${query}` : ''}`);
  $('#catalogo-web-facetas-panel').hidden = true;
  $('#catalogo-web-filtros-toggle').setAttribute('aria-expanded', 'false');
  actualizarContadorFiltrosCatalogo();
  loadCatalogoWebListado(1, busqueda, filtros);
}

function renderCatalogoWebRoute() {
  const params = new URLSearchParams(window.location.search);
  const rutaDetalle = window.location.pathname.match(/^\/catalogo\/producto\/([0-9a-f-]+)\/?$/i);
  const publicId = params.get('producto') || (rutaDetalle ? rutaDetalle[1] : null);
  if (publicId) loadCatalogoWebDetalle(publicId);
  else {
    const filtros = filtrosCatalogoDesdeUrl(params);
    loadCatalogoWebListado(Number(params.get('pagina')) || 1, params.get('busqueda') || '', filtros);
    cargarFacetasCatalogo();
  }
}

async function cargarFacetasCatalogo() {
  if (catalogoWebFacetasCargando) return catalogoWebFacetasCargando;
  catalogoWebFacetasCargando = (async () => {
    try {
      const respuesta = await request('/api/v1/catalogo/atributos/');
      catalogoWebFacetas = (await respuesta.json()).atributos || [];
      const formulario = $('#catalogo-web-facetas');
      formulario.replaceChildren();
      for (const grupo of catalogoWebFacetas) {
        const campo = catalogoElemento('fieldset', 'max-h-40 min-w-0 overflow-y-auto rounded-lg border border-line p-2');
        const etiqueta = catalogoElemento('legend', 'px-1 text-sm font-semibold text-ink', grupo.nombre);
        const seleccionados = new Set(new URLSearchParams(window.location.search).getAll(grupo.clave));
        grupo.valores.forEach((valor, indice) => {
          const id = `filtro-${grupo.clave}-${indice}`;
          const fila = catalogoElemento('label', 'flex cursor-pointer items-center gap-2 rounded-md px-1.5 py-1 text-sm text-ink hover:bg-surface-muted');
          const opcion = catalogoElemento('input', 'h-4 w-4 rounded border-line text-primary focus:ring-primary');
          opcion.type = 'checkbox';
          opcion.id = id;
          opcion.name = grupo.clave;
          opcion.value = valor.nombre;
          opcion.checked = seleccionados.has(valor.nombre);
          fila.htmlFor = id;
          fila.append(opcion, document.createTextNode(`${valor.nombre} (${valor.cantidad})`));
          campo.append(fila);
        });
        campo.prepend(etiqueta);
        formulario.append(campo);
      }
      actualizarContadorFiltrosCatalogo();
      $('#catalogo-web-facetas-estado').textContent = catalogoWebFacetas.length
        ? 'Marca una o varias opciones por atributo.'
        : 'Los filtros se poblarán a medida que se carguen los atributos de los productos.';
    } catch (error) {
      $('#catalogo-web-facetas-estado').textContent = 'No se pudieron cargar los filtros.';
      toast(error.message, 'error');
      catalogoWebFacetasCargando = null;
    }
  })();
  return catalogoWebFacetasCargando;
}

async function loadCatalogoWebListado(pagina, busqueda, filtros = {}) {
  const solicitud = ++catalogoWebRequest;
  const listado = $('#catalogo-web-listado');
  const detalle = $('#catalogo-web-detalle');
  listado.hidden = false;
  detalle.hidden = true;
  $('#catalogo-web-busqueda').value = busqueda;
  for (const clave of catalogoWebClavesAtributo) {
    const valores = new Set(Array.isArray(filtros[clave]) ? filtros[clave] : (filtros[clave] ? [filtros[clave]] : []));
    for (const opcion of document.querySelectorAll(`input[name="${clave}"]`)) opcion.checked = valores.has(opcion.value);
  }
  $('#catalogo-web-estado').textContent = 'Cargando productos…';
  const query = new URLSearchParams({ pagina: String(pagina), tamano: '24', busqueda });
  for (const clave of catalogoWebClavesAtributo) {
    const valores = Array.isArray(filtros[clave]) ? filtros[clave] : (filtros[clave] ? [filtros[clave]] : []);
    for (const valor of valores) query.append(clave, valor);
  }
  try {
    const respuesta = await request(`/api/v1/catalogo/productos/?${query}`);
    const datos = await respuesta.json();
    if (solicitud !== catalogoWebRequest) return;
    catalogoWebPagina = datos.pagina;
    const tarjetas = $('#catalogo-web-tarjetas');
    tarjetas.replaceChildren();
    for (const producto of datos.productos) {
      const tarjeta = catalogoElemento('article', 'card flex flex-col gap-3 p-3');
      const enlace = catalogoElemento('a', 'block text-ink no-underline');
      const detalleQuery = new URLSearchParams(window.location.search);
      detalleQuery.set('producto', producto.public_id);
      enlace.href = `/catalogo/?${detalleQuery}`;
      enlace.dataset.catalogoProducto = producto.public_id;
      enlace.append(catalogoImagen(producto.imagen, `Imagen de ${producto.sku}`));
      const sku = catalogoElemento('p', 'mt-3 text-sm font-bold', producto.sku);
      const descripcion = catalogoElemento('h3', 'mt-1 min-h-12 text-sm font-semibold', producto.descripcion || 'Sin descripción');
      enlace.append(sku, descripcion);
      const acciones = catalogoElemento('div', 'mt-auto flex items-center justify-center gap-3 pt-2');
      const ver = catalogoElemento('a', 'btn btn-secondary inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm');
      ver.href = enlace.href;
      ver.dataset.catalogoProducto = producto.public_id;
      ver.append(catalogoElemento('span', 'text-base', '◎'), document.createTextNode('Ver detalle'));
      acciones.append(ver);
      if (puedeDescargarCatalogo) {
        const descargas = catalogoElemento('details', 'relative');
        const abrirDescargas = catalogoElemento('summary', 'inline-flex cursor-pointer list-none items-center gap-2 whitespace-nowrap rounded-full bg-primary px-4 py-2 text-sm font-semibold text-primary-contrast hover:bg-primary-hover focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary');
        abrirDescargas.append(catalogoElemento('span', 'text-base', '↓'), document.createTextNode('Descargar'));
        const opciones = catalogoElemento('div', 'absolute bottom-full right-0 z-10 mb-2 min-w-48 overflow-hidden rounded-xl border border-line bg-surface p-1 shadow-elevated');
        for (const [etiqueta, tamano] of [['Alta (original)', 'alta'], ['1500 × 1500', '1500'], ['800 × 800', '800']]) {
          const opcion = catalogoElemento('a', 'block rounded-lg px-3 py-2.5 text-sm font-semibold text-ink no-underline hover:bg-surface-muted', etiqueta);
          opcion.href = `/api/v1/catalogo/productos/${encodeURIComponent(producto.public_id)}/descargar/${tamano}/`;
          opciones.append(opcion);
        }
        descargas.append(abrirDescargas, opciones);
        acciones.append(descargas);
      }
      tarjeta.append(enlace, acciones);
      tarjetas.append(tarjeta);
    }
    $('#catalogo-web-total').textContent = `${datos.total} productos`;
    $('#catalogo-web-estado').textContent = datos.productos.length ? `${datos.productos.length} productos en esta página.` : 'No se encontraron productos.';
    $('#catalogo-web-pagina').textContent = `Página ${datos.pagina} de ${datos.paginas}`;
    $('#catalogo-web-anterior').disabled = !datos.hay_anterior;
    $('#catalogo-web-siguiente').disabled = !datos.hay_siguiente;
  } catch (error) {
    if (solicitud !== catalogoWebRequest) return;
    $('#catalogo-web-estado').textContent = 'No se pudo cargar el catálogo.';
    toast(error.message, 'error');
  }
}

async function loadCatalogoWebDetalle(publicId) {
  const solicitud = ++catalogoWebRequest;
  $('#catalogo-web-listado').hidden = true;
  const contenedor = $('#catalogo-web-detalle');
  contenedor.hidden = false;
  contenedor.replaceChildren(catalogoElemento('p', 'text-sm text-ink-muted', 'Cargando producto…'));
  try {
    const respuesta = await request(`/api/v1/catalogo/productos/${encodeURIComponent(publicId)}/`);
    const producto = await respuesta.json();
    if (solicitud !== catalogoWebRequest) return;
    contenedor.replaceChildren();
    const volver = catalogoElemento('button', 'btn btn-secondary', '← Volver al catálogo');
      volver.type = 'button';
      volver.addEventListener('click', () => {
      const query = new URLSearchParams(window.location.search);
      query.delete('producto');
      window.history.pushState({}, '', `/catalogo/${query.size ? `?${query}` : ''}`);
      renderCatalogoWebRoute();
    });
    const detalleWs = producto.detalle_ws || {};
    const venta = detalleWs.venta || {};
    const existencias = detalleWs.existencias || {};
    const metricas = detalleWs.metricas || {};
    const titulo = catalogoElemento('h2', 'mt-1 text-xl font-bold leading-snug tracking-tight text-ink',
      venta.descripcion_larga || producto.descripcion || 'Producto');
    const sku = catalogoElemento('p', 'text-sm font-semibold text-primary', producto.sku);
    const columnas = catalogoElemento('div', 'mt-5 grid items-start gap-5 xl:grid-cols-2');
    const galeria = catalogoElemento('div', 'space-y-3');
    const informacion = catalogoElemento('div', 'space-y-4');
    const ficha = catalogoElemento('dl', 'space-y-2');
    informacion.append(sku, titulo);
    const codigosBarra = (venta.codigos_barra || []).join(', ') || producto.codigo_barra || '—';
    const estado = existencias.estado === null || existencias.estado === undefined
      ? (producto.estado === null ? '—' : String(producto.estado)) : String(existencias.estado);
    const filas = [
      ['Estado I-NET', estado],
      ['Descripción corta', venta.descripcion_corta || producto.descripcion_corta || '—'],
      ['Unidad', [existencias.unidad, existencias.unidad_abreviada].filter(Boolean).join(' · ') || '—'],
      ['Clasificación', existencias.clasificacion || '—'],
      ['Largo', metricas.largo ? `${metricas.largo} cm` : '—'],
      ['Ancho', metricas.ancho ? `${metricas.ancho} cm` : '—'],
      ['Alto', metricas.alto ? `${metricas.alto} cm` : '—'],
      ['Peso', metricas.peso ? `${metricas.peso} kg` : '—'],
      ['EAN / código de barras', codigosBarra],
    ];
    for (const [etiqueta, valor] of filas) {
      const fila = catalogoElemento('div', 'flex items-center gap-3 rounded-lg border border-line bg-surface-muted/40 px-3 py-2');
      fila.append(catalogoElemento('span', 'grid h-8 w-8 shrink-0 place-items-center rounded-full bg-primary/10 text-sm text-primary', '✧'));
      fila.append(catalogoElemento('dt', 'min-w-0 flex-1 text-sm font-medium text-ink', etiqueta));
      fila.append(catalogoElemento('dd', 'm-0 text-right text-sm font-semibold text-ink', valor));
      ficha.append(fila);
    }
    if (detalleWs.atributos?.length) {
      const tarjetaAtributos = catalogoElemento('section', 'flex flex-wrap gap-2');
      for (const atributo of detalleWs.atributos) {
        tarjetaAtributos.append(catalogoElemento('span', 'chip chip-neutral text-xs font-semibold uppercase', `• ${atributo.nombre}`));
      }
      informacion.append(tarjetaAtributos);
    }
    informacion.append(ficha);
    if (puedeDescargarCatalogo) {
      const descargasProducto = catalogoElemento('section', 'flex flex-wrap items-center gap-2 border-t border-line pt-3');
      descargasProducto.append(catalogoElemento('span', 'mr-1 text-sm font-semibold text-ink', 'Descargar todas:'));
      for (const [texto, tamano] of [['Alta calidad', 'alta'], ['1500 × 1500', '1500'], ['800 × 800', '800']]) {
        const enlace = catalogoElemento('a', 'btn btn-primary btn-sm', `↓ ${texto}`);
        enlace.href = `/api/v1/catalogo/productos/${encodeURIComponent(producto.public_id)}/descargar/${tamano}/`;
        descargasProducto.append(enlace);
      }
      informacion.append(descargasProducto);
    }
    if (producto.detalle_ws_actualizado_en) {
      const fechaActualizacion = new Date(producto.detalle_ws_actualizado_en);
      informacion.append(catalogoElemento('p', 'text-xs text-ink-subtle',
        `Información de I-NET actualizada: ${fechaActualizacion.toLocaleString('es-CL')}`));
    } else if (!Object.keys(detalleWs).length) {
      informacion.append(catalogoElemento('p', 'text-sm text-ink-muted',
        'El detalle ampliado de I-NET no está disponible por ahora; se muestran los datos locales.'));
    }
    if (producto.imagenes.length) {
      let indiceActivo = Math.max(0, producto.imagenes.findIndex(imagen => imagen.portada));
      const imagenPrincipal = catalogoImagen(
        producto.imagenes[indiceActivo].preview,
        `${producto.sku}, imagen ${indiceActivo + 1}`,
        'h-72 w-full rounded-lg bg-white object-contain sm:h-80 xl:h-[28rem]',
      );
      const marco = catalogoElemento('div', 'card relative m-0 overflow-hidden p-3');
      marco.append(imagenPrincipal);
      const anterior = catalogoElemento('button', 'btn btn-secondary absolute left-5 top-1/2 -translate-y-1/2 rounded-full', '←');
      anterior.type = 'button';
      anterior.setAttribute('aria-label', 'Imagen anterior');
      const siguiente = catalogoElemento('button', 'btn btn-secondary absolute right-5 top-1/2 -translate-y-1/2 rounded-full', '→');
      siguiente.type = 'button';
      siguiente.setAttribute('aria-label', 'Imagen siguiente');
      marco.append(anterior, siguiente);
      const miniaturas = catalogoElemento('div', 'flex gap-2 overflow-x-auto pb-1');
      let enlacesDescarga = [];
      if (puedeDescargarCatalogo) {
        const descargas = catalogoElemento('details', 'relative inline-block');
        const menuDescargas = catalogoElemento('summary', 'inline-flex cursor-pointer list-none items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white');
        menuDescargas.append(catalogoElemento('span', '', '↓'), document.createTextNode('Imagen activa'));
        const opcionesImagenActiva = catalogoElemento('div', 'absolute bottom-full left-0 z-10 mb-2 min-w-48 overflow-hidden rounded-xl border border-line bg-surface p-1 shadow-elevated');
        enlacesDescarga = [
          ['Alta calidad', 'original'],
          ['1500 × 1500', 'resolucion_1500'],
          ['800 × 800', 'resolucion_800'],
        ].map(([texto, campo]) => {
          const enlace = catalogoElemento('a', 'block rounded-lg px-3 py-2.5 text-sm font-semibold text-ink no-underline hover:bg-surface-muted', texto);
          enlace.href = producto.imagenes[indiceActivo][campo];
          opcionesImagenActiva.append(enlace);
          return { enlace, campo };
        });
        descargas.append(menuDescargas, opcionesImagenActiva);
        galeria.append(descargas);
      }
      const leyenda = catalogoElemento('p', 'text-xs text-ink-muted');
      const botonesMiniatura = producto.imagenes.map((imagen, indice) => {
        const boton = catalogoElemento('button', 'shrink-0 rounded-lg border-2 border-transparent p-1 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary');
        boton.type = 'button';
        boton.setAttribute('aria-label', `Mostrar imagen ${indice + 1} de ${producto.imagenes.length}`);
        boton.append(catalogoImagen(imagen.miniatura, `${producto.sku}, miniatura ${indice + 1}`, 'h-20 w-20 rounded-md bg-white object-contain'));
        boton.addEventListener('click', () => actualizarImagenActiva(indice));
        miniaturas.append(boton);
        return boton;
      });
      function actualizarImagenActiva(indice) {
        indiceActivo = (indice + producto.imagenes.length) % producto.imagenes.length;
        const imagen = producto.imagenes[indiceActivo];
        imagenPrincipal.src = imagen.preview;
        imagenPrincipal.alt = `${producto.sku}, imagen ${indiceActivo + 1}`;
        leyenda.textContent = `${imagen.nombre}${imagen.portada ? ' · Portada' : ''} · ${indiceActivo + 1} de ${producto.imagenes.length}`;
        for (const { enlace, campo } of enlacesDescarga) enlace.href = imagen[campo];
        botonesMiniatura.forEach((boton, posicion) => {
          boton.classList.toggle('border-primary', posicion === indiceActivo);
          boton.setAttribute('aria-pressed', String(posicion === indiceActivo));
        });
      }
      anterior.addEventListener('click', () => actualizarImagenActiva(indiceActivo - 1));
      siguiente.addEventListener('click', () => actualizarImagenActiva(indiceActivo + 1));
      actualizarImagenActiva(indiceActivo);
      galeria.prepend(marco, leyenda, miniaturas);
    } else {
      galeria.append(catalogoElemento('p', 'text-sm text-ink-muted', 'No hay imágenes importadas para este producto.'));
    }
    columnas.append(galeria, informacion);
    contenedor.append(volver, columnas);
  } catch (error) {
    if (solicitud !== catalogoWebRequest) return;
    contenedor.replaceChildren(catalogoElemento('p', 'text-sm text-danger', 'No se pudo cargar el detalle del producto.'));
    toast(error.message, 'error');
  }
}

$('#catalogo-web-filtros').addEventListener('submit', event => {
  event.preventDefault();
  aplicarFiltrosCatalogo();
});
$('#catalogo-web-facetas').addEventListener('change', () => {
  actualizarContadorFiltrosCatalogo();
});
$('#catalogo-web-aplicar-filtros').addEventListener('click', aplicarFiltrosCatalogo);
$('#catalogo-web-limpiar-atributos').addEventListener('click', () => {
  for (const opcion of document.querySelectorAll('#catalogo-web-facetas input[type="checkbox"]')) opcion.checked = false;
  aplicarFiltrosCatalogo();
});
$('#catalogo-web-filtros-toggle').addEventListener('click', event => {
  const panel = $('#catalogo-web-facetas-panel');
  panel.hidden = !panel.hidden;
  event.currentTarget.setAttribute('aria-expanded', String(!panel.hidden));
});
$('#catalogo-web-anterior').addEventListener('click', () => {
  const query = new URLSearchParams(window.location.search);
  const page = catalogoWebPagina - 1;
  query.set('pagina', String(page));
  window.history.pushState({}, '', `/catalogo/?${query}`);
  loadCatalogoWebListado(page, $('#catalogo-web-busqueda').value, filtrosCatalogoDesdeUrl(query));
});
$('#catalogo-web-siguiente').addEventListener('click', () => {
  const query = new URLSearchParams(window.location.search);
  const page = catalogoWebPagina + 1;
  query.set('pagina', String(page));
  window.history.pushState({}, '', `/catalogo/?${query}`);
  loadCatalogoWebListado(page, $('#catalogo-web-busqueda').value, filtrosCatalogoDesdeUrl(query));
});
$('#catalogo-web-tarjetas').addEventListener('click', event => {
  const enlace = event.target.closest('[data-catalogo-producto]');
  if (!enlace) return;
  event.preventDefault();
  const publicId = enlace.dataset.catalogoProducto;
  window.history.pushState({}, '', `/catalogo/?producto=${encodeURIComponent(publicId)}`);
  loadCatalogoWebDetalle(publicId);
});
if (window.addEventListener) {
  window.addEventListener('popstate', () => {
    if (window.location.pathname.startsWith('/catalogo/')) renderCatalogoWebRoute();
  });
}

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
