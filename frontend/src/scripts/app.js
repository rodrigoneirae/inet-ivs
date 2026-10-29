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
  for (const selector of ['#nav-home', '#nav-orders']) {
    const element = $(selector);
    if (!element) continue;
    if (selector === current) element.setAttribute('aria-current', 'page');
    else element.removeAttribute('aria-current');
  }
}

function displaySession(data) {
  csrf = data.csrf;
  $('#login-screen').hidden = Boolean(data.usuario);
  $('#app').hidden = !data.usuario;
  if (data.usuario) {
    $('#username').textContent = data.usuario;
    const avatar = $('#user-initials');
    if (avatar) avatar.textContent = initials(data.usuario);
    $('#greeting').textContent = `Hola, ${data.usuario}`;
    $('#nav-orders').hidden = !data.puede_ver_pedidos;
    const hero = $('#hero-orders');
    if (hero) hero.hidden = !data.puede_ver_pedidos;
    $('#sync').hidden = !data.puede_sincronizar;
    if (window.location.pathname === '/pedidos/' && data.puede_ver_pedidos) {
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
    columns: columns.map(([label, field, minWidth]) => ({
      title: `${label}${order === field ? (direction === 'asc' ? ' ▲' : ' ▼') : ''}`,
      field, minWidth,
      ...(field === 'canal' ? { headerFilter: filterHeader(field, data.canales, canal), headerFilterFunc: () => true } : {}),
      ...(field === 'estado' ? { headerFilter: filterHeader(field, data.estados, estado), headerFilterFunc: () => true } : {}),
    })),
  });
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
  try {
    const selected = keep ? new URLSearchParams(applied) : params();
    selected.set('page', String(next));
    const data = await (await request(`/api/v1/pedidos/?${selected}`)).json();
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
$('#previous').addEventListener('click', () => loadOrders(page - 1, true));
$('#next').addEventListener('click', () => loadOrders(page + 1, true));
$('#sync').addEventListener('click', async () => { try { toast((await post('/api/v1/pedidos/sincronizar/')).mensaje, 'success'); } catch (error) { toast(error.message, 'error'); } });
$('#export').addEventListener('click', async () => {
  try {
    const response = await request(`/api/v1/pedidos/exportar/?${applied}`);
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url; link.download = 'pedidos.xlsx'; link.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 60000);
    toast('Archivo generado correctamente.', 'success');
  } catch (error) { toast(error.message, 'error'); }
});

setSidebar(false);
setSidebarCollapsed(readStorage(SIDEBAR_KEY) === 'collapsed');
applyTheme(currentTheme());
if (window.Litepicker) {
  for (const input of form.querySelectorAll('input[type="date"]')) {
    new window.Litepicker({ element: input, singleMode: true, format: 'YYYY-MM-DD', lang: 'es-ES' });
  }
}
request('/api/v1/sesion/').then(response => response.json()).then(displaySession).catch(error => toast(error.message, 'error'));
