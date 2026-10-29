import { TabulatorFull as Tabulator } from 'tabulator-tables';

const $ = (selector) => document.querySelector(selector);
const form = $('#filters');
let csrf = '';
let page = 1;
let pages = 1;
let order = 'fecha';
let direction = 'desc';
let canal = '';
let estado = '';
let table;
let applied = new URLSearchParams();

function toast(message) {
  const element = $('#toast');
  element.textContent = message;
  element.hidden = false;
  window.clearTimeout(toast.timer);
  toast.timer = window.setTimeout(() => { element.hidden = true; }, 6000);
}

async function request(path, options = {}) {
  const response = await fetch(path, { credentials: 'same-origin', ...options });
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

function displaySession(data) {
  csrf = data.csrf;
  $('#login-screen').hidden = Boolean(data.usuario);
  $('#app').hidden = !data.usuario;
  if (data.usuario) {
    $('#username').textContent = data.usuario;
    $('#greeting').textContent = `Hola, ${data.usuario}`;
    $('#nav-orders').hidden = !data.puede_ver_pedidos;
    $('#sync').hidden = !data.puede_sincronizar;
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
    ['Canal', 'canal'], ['OC', 'pedido'], ['Cliente', 'cliente'], ['Fecha', 'fecha'],
    ['Ítems', 'items'], ['Venta', 'total'], ['Status', 'estado'], ['Estado', 'fulfillment'],
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
    columns: columns.map(([label, field]) => ({
      title: `${label}${order === field ? (direction === 'asc' ? ' ▲' : ' ▼') : ''}`,
      field, minWidth: field === 'cliente' ? 180 : 120,
      ...(field === 'canal' ? { headerFilter: filterHeader(field, data.canales, canal), headerFilterFunc: () => true } : {}),
      ...(field === 'estado' ? { headerFilter: filterHeader(field, data.estados, estado), headerFilterFunc: () => true } : {}),
    })),
  });
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
    renderTable(data);
  } catch (error) { toast(error.message); }
}

$('#login-form').addEventListener('submit', async event => {
  event.preventDefault();
  try {
    const formData = new FormData(event.currentTarget);
    const result = await post('/api/v1/ingresar/', Object.fromEntries(formData));
    event.currentTarget.reset();
    displaySession(result);
  } catch (error) { toast(error.message); }
});
$('#logout').addEventListener('click', async () => {
  try { const data = await post('/api/v1/salir/'); displaySession({ ...data, usuario: null }); }
  catch (error) { toast(error.message); }
});
$('#nav-home').addEventListener('click', () => { $('#home').hidden = false; $('#orders').hidden = true; $('#page-title').textContent = 'Inicio'; });
$('#nav-orders').addEventListener('click', () => { $('#home').hidden = true; $('#orders').hidden = false; $('#page-title').textContent = 'Pedidos AnyMarket'; loadOrders(); });
$('#menu-toggle').addEventListener('click', event => { const side = $('#sidebar'); side.hidden = !side.hidden; event.currentTarget.setAttribute('aria-expanded', String(!side.hidden)); });
$('#theme-toggle').addEventListener('click', () => { document.documentElement.classList.toggle('dark'); });
form.addEventListener('submit', event => { event.preventDefault(); loadOrders(); });
$('#previous').addEventListener('click', () => loadOrders(page - 1, true));
$('#next').addEventListener('click', () => loadOrders(page + 1, true));
$('#sync').addEventListener('click', async () => { try { toast((await post('/api/v1/pedidos/sincronizar/')).mensaje); } catch (error) { toast(error.message); } });
$('#export').addEventListener('click', async () => {
  try {
    const response = await request(`/api/v1/pedidos/exportar/?${applied}`);
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url; link.download = 'pedidos.xlsx'; link.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 60000);
  } catch (error) { toast(error.message); }
});

if (window.matchMedia('(prefers-color-scheme: dark)').matches) document.documentElement.classList.add('dark');
if (window.Litepicker) {
  for (const input of form.querySelectorAll('input[type="date"]')) {
    new window.Litepicker({ element: input, singleMode: true, format: 'YYYY-MM-DD', lang: 'es-ES' });
  }
}
request('/api/v1/sesion/').then(response => response.json()).then(displaySession).catch(error => toast(error.message));
