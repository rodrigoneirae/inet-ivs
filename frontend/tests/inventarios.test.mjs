import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import vm from 'node:vm';

const CONFIGURACION = {
  inventario: 'inventario-uuid',
  inventario_nombre: 'TEST',
  bodega: '10',
  bodega_nombre: 'Principal',
  zona: 'Z1',
  zona_nombre: 'Zona norte',
  operador: 'Equipo',
  usuario: 'Equipo',
  tipo: 'a',
  tipo_nombre: 'Parte A',
  turno: 'turno-uuid',
};

function textoDe(elemento) {
  let texto = elemento.textContent || '';
  for (const hijo of elemento.children || []) texto += ` ${textoDe(hijo)}`;
  return texto;
}

async function setup() {
  const elementos = new Map();
  const tablas = [];
  const element = selector => {
    if (!elementos.has(selector)) {
      elementos.set(selector, {
        content: '', textContent: '', value: '', hidden: false, dataset: {}, listeners: {}, children: [],
        addEventListener(type, callback) { this.listeners[type] = callback; },
        setAttribute() {},
        replaceChildren(...children) { this.children = children; },
        append(...children) { this.children.push(...children); },
        reset() { this.resetCalled = true; },
      });
    }
    return elementos.get(selector);
  };
  const response = data => ({ ok: true, status: 200,
    headers: { get: () => 'application/json' }, json: async () => data });
  const llamadas = [];
  const context = {
    document: {
      readyState: 'complete',
      querySelector: element,
      querySelectorAll: () => [],
      documentElement: { classList: { toggle() {}, contains: () => false } },
      createElement: tag => ({ tag, children: [], listeners: {}, value: '',
        append(...children) { this.children.push(...children); },
        addEventListener(type, handler) { this.listeners[type] = handler; } }),
    },
    localStorage: { getItem: () => null, setItem() {} },
    matchMedia: () => ({ matches: false }),
    window: { location: { assign() {} } },
    navigator: {},
    confirm: () => true,
    FormData: class { constructor() { return new Map([['nombre', 'TEST'], ['bodega', '10']]); } },
    Tabulator: class {
      constructor(selector, options) { this.selector = selector; this.options = options; this.data = []; this.filters = []; tablas.push(this); }
      replaceData(data) { this.data = data; }
      setData(data) { this.data = data; }
      redraw() {}
      getData(tipo) { return tipo === 'active' && this.filters.length ? this.data.filter(this.filters[0]) : this.data; }
      setFilter(filtro) { this.filters = [filtro]; }
      on() {}
    },
    QRCode: { async toCanvas(canvas, content) { canvas.scannedContent = content; } },
    fetch: async (url, options) => {
      llamadas.push({ url, method: options?.method ?? 'GET', body: options?.body });
      if (url.endsWith('/sesion/')) return response({ puede_supervisar_inventario: true, csrf: 'csrf', usuario: 'sup' });
      if (url.includes('/informat/bodegas/')) return response({ bodegas: [{ codigo: '10', nombre: 'Principal' }], hay_mas: false });
      if (url.includes('/capturadores/') && url.endsWith('/qr/')) {
        return response({ contenido_qr: JSON.stringify({ v: 1, codigo: 'codigo-de-prueba', ...CONFIGURACION }),
          configuracion: CONFIGURACION, vence_en: '2026-01-01T00:00:00Z' });
      }
      if (url.includes('/capturadores/') && url.endsWith('/eliminar/')) return response({ eliminado: true });
      if (url.includes('/capturadores/crear/')) return response({ id: 'device-uuid', nombre: 'Equipo' });
      if (url.includes('/capturadores/')) {
        return response({ capturadores: [{
          id: 'device-uuid', nombre: 'Equipo', activo: true, vinculado: false,
          turnos: [{ ...CONFIGURACION, finalizado: false, inventario_estado: 'abierto' }],
        }] });
      }
      if (url.includes('/asignaciones/') && url.endsWith('/turno/')) {
        return response({ id: 'turno-uuid', zona: 'Z2', tipo: 'a', turnos_movidos: 1 });
      }
      if (url.includes('/inventarios/crear/')) return response({ id: 'inventario-uuid' });
      if (url.includes('/inventarios/inventario-uuid/')) {
        return response({ id: 'inventario-uuid', nombre: 'TEST', estado: 'abierto', bodega: '10',
          bodega_nombre: 'Principal', creado_en: '2026-11-17T14:00:00Z',
          asignaciones: [{ id: 'turno-uuid', zona: 'Z1', tipo: 'a', usuario: 'Equipo',
            capturador: 'device-uuid', finalizado: false }], resultados: [] });
      }
      if (url.includes('/inventarios/?')) {
        return response({ inventarios: [{ id: 'inventario-uuid', nombre: 'TEST', bodega: '10',
          bodega_nombre: 'Principal', estado: 'abierto', creado_en: '2026-11-17T14:00:00Z' }], hay_mas: false });
      }
      return response({ inventarios: [], hay_mas: false });
    },
  };
  const script = (await readFile(new URL('../src/scripts/inventarios.js', import.meta.url), 'utf8'))
    .replace("import { TabulatorFull as Tabulator } from 'tabulator-tables';", '')
    .replace("import QRCode from 'qrcode';", '');
  vm.runInNewContext(script, context);
  await new Promise(resolve => setImmediate(resolve));
  return { element, llamadas, tablas };
}

function columna(tabla, titulo) {
  return tabla.options.columns.find((item) => item.title === titulo);
}

test('la lista de inventarios se pinta con bodega y estado', async () => {
  const { element } = await setup();
  assert.equal(element('#inventory-count').textContent, '1');
  assert.match(textoDe(element('#inventory-list')), /TEST/);
  assert.match(textoDe(element('#inventory-list')), /Bodega 10/);
  assert.equal(element('#detail-empty').hidden, false);
});

test('los capturadores se listan con zona, tipo y estado separados', async () => {
  const { tablas } = await setup();
  const tabla = tablas.find((item) => item.selector === '#device-table');
  assert.ok(tabla);
  assert.equal(tabla.data.length, 1);
  const fila = tabla.data[0];
  assert.equal(fila.nombre, 'Equipo');
  assert.equal(fila.turnos[0].zona, 'Z1');
  assert.equal(fila.turnos[0].tipo, 'a');
  const zonas = columna(tabla, 'Zona').formatter({ getValue: () => fila.zonas });
  const tipos = columna(tabla, 'Tipo').formatter({ getValue: () => fila.tipos });
  const estados = columna(tabla, 'Estado del conteo').formatter({ getValue: () => fila.estadosConteo });
  assert.match(zonas, /Z1/);
  assert.match(tipos, /Parte A/);
  assert.match(estados, /En curso/);
});

test('el QR queda junto al operador para seguir visible en pantallas pequeñas', async () => {
  const { tablas } = await setup();
  const tabla = tablas.find((item) => item.selector === '#device-table');
  const operador = columna(tabla, 'Operador');
  const qr = operador.formatter({ getRow: () => ({ getData: () => tabla.data[0] }) });
  assert.equal(operador.responsive, 0);
  assert.match(qr, /Equipo/);
  const acciones = columna(tabla, 'Acciones').formatter({ getRow: () => ({ getData: () => tabla.data[0] }) });
  assert.match(qr, /data-accion="qr"/);
  assert.doesNotMatch(acciones, /data-accion="qr"/);
  assert.match(acciones, /data-accion="editar"/);
  assert.match(acciones, /data-accion="revocar"/);
  assert.match(acciones, /data-accion="eliminar"/);
});

test('un capturador revocado no ofrece QR ni edición de turnos', async () => {
  const { tablas } = await setup();
  const tabla = tablas.find((item) => item.selector === '#device-table');
  const revocado = { ...tabla.data[0], activo: false };
  const qr = columna(tabla, 'Operador').formatter({ getRow: () => ({ getData: () => revocado }) });
  const html = columna(tabla, 'Acciones').formatter({ getRow: () => ({ getData: () => revocado }) });
  assert.doesNotMatch(qr, /data-accion="qr"/);
  assert.doesNotMatch(html, /data-accion="editar"/);
  assert.doesNotMatch(html, /data-accion="revocar"/);
  assert.match(html, /data-accion="eliminar"/);
});

test('el buscador filtra por operador, bodega, zona o inventario', async () => {
  const { element, tablas } = await setup();
  const tabla = tablas.find((item) => item.selector === '#device-table');
  const buscador = element('#device-search');
  buscador.listeners.input({ target: { value: 'Z1' } });
  assert.equal(tabla.getData('active').length, 1);
  buscador.listeners.input({ target: { value: 'Z9' } });
  assert.equal(tabla.getData('active').length, 0);
  buscador.listeners.input({ target: { value: '' } });
  assert.equal(tabla.getData('active').length, 1);
});

test('la tabla ofrece revocar y eliminar el capturador', async () => {
  const { tablas } = await setup();
  const tabla = tablas.find((item) => item.selector === '#device-table');
  const html = columna(tabla, 'Acciones').formatter({ getRow: () => ({ getData: () => tabla.data[0] }) });
  assert.match(html, /data-accion="revocar"/);
  assert.match(html, /data-accion="eliminar"/);
});

test('registrar un capturador envía inventario, zona y tipo', async () => {
  const { element, llamadas } = await setup();
  element('#device-name').value = 'Nuevo';
  element('#device-inventory').value = 'inventario-uuid';
  element('#device-zone').value = 'Z1';
  element('#device-type').value = 'b';
  await element('#create-device').listeners.submit({ preventDefault() {} });
  await new Promise(resolve => setImmediate(resolve));
  const llamada = llamadas.find(item => item.url.includes('/capturadores/crear/'));
  assert.deepEqual(JSON.parse(llamada.body),
    { nombre: 'Nuevo', inventario: 'inventario-uuid', zona: 'Z1', tipo: 'b' });
});

test('el modal de alta propone la zona y el tipo que faltan en el inventario', async () => {
  const { element } = await setup();
  element('#open-device-modal').listeners.click();
  await new Promise(resolve => setImmediate(resolve));
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(element('#device-inventory').value, 'inventario-uuid');
  assert.equal(element('#device-zone').value, 'Z1');
  assert.equal(element('#device-type').value, 'b');
  assert.match(element('#device-hint').textContent, /Contraparte B/);
});

test('eliminar un capturador llama a la API y recarga la tabla', async () => {
  const { tablas, llamadas } = await setup();
  const tabla = tablas.find((item) => item.selector === '#device-table');
  const atributos = { 'data-accion': 'eliminar', 'data-id': 'device-uuid' };
  const botonAccion = { getAttribute: (nombre) => atributos[nombre] };
  columna(tabla, 'Acciones').cellClick({ target: { closest: () => botonAccion } }, {});
  await new Promise(resolve => setImmediate(resolve));
  await new Promise(resolve => setImmediate(resolve));
  const peticion = llamadas.find((llamada) => llamada.url.endsWith('/eliminar/'));
  assert.ok(peticion);
  assert.equal(peticion.method, 'POST');
});

test('generar el QR por turno pide el turno exacto y muestra la configuración', async () => {
  const { element, llamadas, tablas } = await setup();
  const tabla = tablas.find((item) => item.selector === '#device-table');
  const atributos = { 'data-accion': 'qr', 'data-capturador': 'device-uuid',
    'data-turno': 'turno-uuid', 'data-inventario': 'inventario-uuid' };
  const botonAccion = { getAttribute: (nombre) => atributos[nombre] };
  tabla.options.columns.find((item) => item.title === 'Operador')
    .cellClick({ target: { closest: () => botonAccion } }, {});
  await new Promise(resolve => setImmediate(resolve));
  await new Promise(resolve => setImmediate(resolve));
  const peticion = llamadas.find((llamada) => llamada.url.endsWith('/qr/'));
  assert.ok(peticion);
  assert.equal(peticion.method, 'POST');
  const cuerpo = JSON.parse(peticion.body);
  assert.equal(cuerpo.inventario, 'inventario-uuid');
  assert.equal(cuerpo.asignacion, 'turno-uuid');
  assert.equal(element('#qr-operador').textContent, 'Equipo');
  assert.equal(element('#qr-bodega').textContent, '10 · Principal');
  assert.equal(element('#qr-zona').textContent, 'Z1 · Zona norte');
  assert.equal(element('#qr-tipo').textContent, 'Parte A');
  assert.match(element('#pairing-content').value, /codigo-de-prueba/);
});

test('editar un turno abre el modal con la zona y el tipo actuales', async () => {
  const { element, tablas } = await setup();
  const tabla = tablas.find((item) => item.selector === '#device-table');
  const atributos = { 'data-accion': 'editar', 'data-turno': 'turno-uuid',
    'data-zona': 'Z1', 'data-tipo': 'a', 'data-inventario': 'inventario-uuid' };
  const botonAccion = { getAttribute: (nombre) => atributos[nombre] };
  tabla.options.columns.find((item) => item.title === 'Acciones')
    .cellClick({ target: { closest: () => botonAccion } }, {});
  assert.equal(element('#turn-id').value, 'turno-uuid');
  assert.equal(element('#turn-zone').value, 'Z1');
  assert.equal(element('#turn-type').value, 'a');
});

test('el modal de turno guarda la zona y el tipo nuevos', async () => {
  const { element, llamadas } = await setup();
  element('#turn-id').value = 'turno-uuid';
  element('#turn-zone').value = 'Z2';
  element('#turn-type').value = 'b';
  await element('#turn-form').listeners.submit({ preventDefault() {} });
  await new Promise(resolve => setImmediate(resolve));
  const peticion = llamadas.find((llamada) => llamada.url.endsWith('/turno/'));
  assert.ok(peticion);
  const cuerpo = JSON.parse(peticion.body);
  assert.equal(cuerpo.zona, 'Z2');
  assert.equal(cuerpo.tipo, 'b');
});

test('registrar un capturador mantiene la referencia del formulario', async () => {
  const { element } = await setup();
  const form = element('#create-device');
  await form.listeners.submit({ preventDefault() {} });
  assert.equal(form.resetCalled, true);
  assert.match(element('#toast-message').textContent, /registrado/);
});
