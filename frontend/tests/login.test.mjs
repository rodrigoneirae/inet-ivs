import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import vm from 'node:vm';

class ClassList {
  constructor() { this.values = new Set(); }
  add(...names) { for (const name of names) this.values.add(name); }
  remove(...names) { for (const name of names) this.values.delete(name); }
  contains(name) { return this.values.has(name); }
  toggle(name, force) {
    const active = force === undefined ? !this.values.has(name) : Boolean(force);
    if (active) this.values.add(name);
    else this.values.delete(name);
    return active;
  }
}

function createContext(opciones = {}) {
  const elements = new Map();
  const enlaces = [];
  const element = (selector) => {
    if (!elements.has(selector)) {
      elements.set(selector, {
        hidden: true,
        dataset: {},
        attributes: {},
        listeners: {},
        textContent: '',
        classList: new ClassList(),
        addEventListener(type, callback) { this.listeners[type] = callback; },
        setAttribute(name, value) { this.attributes[name] = value; },
        removeAttribute(name) { delete this.attributes[name]; },
        querySelectorAll() { return []; },
        reset() { this.wasReset = true; },
        click() { this.wasClicked = true; },
      });
    }
    return elements.get(selector);
  };
  const storage = new Map();
  const session = { csrf: 'token', usuario: null, puede_ver_pedidos: false };
  const loggedIn = { csrf: 'nuevo', usuario: 'usuario', puede_ver_pedidos: true };
  const context = {
    document: {
      querySelector: element,
      documentElement: { classList: new ClassList() },
      addEventListener() {},
      createElement(tag) {
        const nodo = { tag, attributes: {}, click() { this.wasClicked = true; } };
        if (tag === 'a') enlaces.push(nodo);
        return nodo;
      },
    },
    window: {
      matchMedia: () => ({ matches: false }),
      location: { hash: '#pedidos' },
      localStorage: {
        getItem: key => (storage.has(key) ? storage.get(key) : null),
        setItem: (key, value) => storage.set(key, value),
      },
      setTimeout: (callback, delay) => {
        const handle = setTimeout(callback, delay);
        handle.unref?.();
        return handle;
      },
      clearTimeout: handle => clearTimeout(handle),
    },
    FormData: class { constructor() { return new Map([['username', 'usuario'], ['password', 'clave']]); } },
    URLSearchParams,
    URL: { createObjectURL: () => 'blob:mock', revokeObjectURL: () => {} },
    btoa: data => Buffer.from(data, 'binary').toString('base64'),
    fetch: async path => ({ ok: true, json: async () => (path.includes('ingresar') ? loggedIn : session) }),
    ...opciones,
  };
  return { context, element, storage, enlaces };
}

async function run(context) {
  const script = (await readFile(new URL('../src/scripts/app.js', import.meta.url), 'utf8'))
    .replace("import { TabulatorFull as Tabulator } from 'tabulator-tables';", '');
  vm.runInNewContext(script, context);
  await new Promise(resolve => setImmediate(resolve));
}

test('el formulario muestra la sesión tras una respuesta asíncrona', async () => {
  const { context, element } = createContext();
  await run(context);
  const form = element('#login-form');
  const event = { currentTarget: form, preventDefault() {} };
  const result = form.listeners.submit(event);
  event.currentTarget = null;
  await result;
  assert.equal(form.wasReset, true);
  assert.equal(element('#app').hidden, false);
  assert.equal(element('#username').textContent, 'usuario');
  assert.equal(element('#user-initials').textContent, 'U');
  assert.equal(element('#nav-orders').wasClicked, true);
});

test('el tema se alterna y queda guardado en el navegador', async () => {
  const { context, element, storage } = createContext();
  await run(context);
  assert.equal(context.document.documentElement.classList.contains('dark'), false);
  element('#theme-toggle').listeners.click({ currentTarget: element('#theme-toggle') });
  assert.equal(context.document.documentElement.classList.contains('dark'), true);
  assert.equal(storage.get('inet-ivs:tema'), 'dark');
  element('#theme-toggle').listeners.click({ currentTarget: element('#theme-toggle') });
  assert.equal(context.document.documentElement.classList.contains('dark'), false);
  assert.equal(storage.get('inet-ivs:tema'), 'light');
});

test('el menú lateral se contrae en escritorio y se guarda el estado', async () => {
  const { context, element, storage } = createContext();
  await run(context);
  assert.equal(element('#sidebar').dataset.collapsed, 'false');
  element('#sidebar-collapse').listeners.click({ currentTarget: element('#sidebar-collapse') });
  assert.equal(element('#sidebar').dataset.collapsed, 'true');
  assert.equal(storage.get('inet-ivs:menu'), 'collapsed');
});

test('el menú lateral se abre y se cierra en pantallas pequeñas', async () => {
  const { context, element } = createContext();
  await run(context);
  const toggle = element('#menu-toggle');
  toggle.listeners.click({ currentTarget: toggle });
  assert.equal(element('#sidebar').dataset.state, 'open');
  assert.equal(element('#sidebar-backdrop').hidden, false);
  assert.equal(toggle.attributes['aria-expanded'], 'true');
  element('#sidebar-backdrop').listeners.click({ currentTarget: element('#sidebar-backdrop') });
  assert.equal(element('#sidebar').dataset.state, 'closed');
  assert.equal(element('#sidebar-backdrop').hidden, true);
});

test('en el navegador la exportación se descarga con un enlace', async () => {
  const { context, element, enlaces } = createContext({
    fetch: async () => ({
      ok: true,
      json: async () => ({}),
      blob: async () => ({ arrayBuffer: async () => new Uint8Array([80, 75, 3, 4]).buffer }),
    }),
  });
  await run(context);
  element('#export').listeners.click({ currentTarget: element('#export') });
  await new Promise(resolve => setTimeout(resolve, 50));
  assert.equal(enlaces.length, 1);
  assert.equal(enlaces[0].download, 'pedidos.xlsx');
});

test('en la aplicación de escritorio la exportación se guarda con el comando nativo', async () => {
  const invocaciones = [];
  const { context, element } = createContext({
    fetch: async () => ({
      ok: true,
      json: async () => ({}),
      blob: async () => ({ arrayBuffer: async () => new Uint8Array([80, 75, 3, 4]).buffer }),
    }),
  });
  context.window.__TAURI__ = {
    core: {
      invoke: async (comando, argumentos) => {
        invocaciones.push([comando, argumentos]);
        return '/tmp/pedidos.xlsx';
      },
    },
  };
  await run(context);
  element('#export').listeners.click({ currentTarget: element('#export') });
  await new Promise(resolve => setTimeout(resolve, 50));
  assert.equal(invocaciones.length, 1);
  assert.equal(invocaciones[0][0], 'guardar-archivo');
  assert.equal(invocaciones[0][1].nombre, 'pedidos.xlsx');
  assert.equal(invocaciones[0][1].contenido, btoa('PK'));
});
