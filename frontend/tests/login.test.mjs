import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import vm from 'node:vm';

test('el formulario muestra la sesión tras una respuesta asíncrona', async () => {
  const elements = new Map();
  const element = (selector) => {
    if (!elements.has(selector)) {
      elements.set(selector, {
        hidden: true,
        listeners: {},
        addEventListener(type, callback) { this.listeners[type] = callback; },
        querySelectorAll() { return []; },
        reset() { this.wasReset = true; },
        click() { this.wasClicked = true; },
      });
    }
    return elements.get(selector);
  };
  const session = { csrf: 'token', usuario: null, puede_ver_pedidos: false };
  const loggedIn = { csrf: 'nuevo', usuario: 'usuario', puede_ver_pedidos: true };
  const context = {
    document: { querySelector: element, documentElement: { classList: { add() {} } } },
    window: { matchMedia: () => ({ matches: false }), location: { hash: '#pedidos' } },
    FormData: class { constructor() { return new Map([['username', 'usuario'], ['password', 'clave']]); } },
    URLSearchParams,
    fetch: async (path) => ({ ok: true, json: async () => path.includes('ingresar') ? loggedIn : session }),
  };
  const script = (await readFile(new URL('../src/scripts/app.js', import.meta.url), 'utf8'))
    .replace("import { TabulatorFull as Tabulator } from 'tabulator-tables';", '');
  vm.runInNewContext(script, context);
  await new Promise(resolve => setImmediate(resolve));
  const form = element('#login-form');
  const event = { currentTarget: form, preventDefault() {} };
  const result = form.listeners.submit(event);
  event.currentTarget = null;
  await result;
  assert.equal(form.wasReset, true);
  assert.equal(element('#app').hidden, false);
  assert.equal(element('#username').textContent, 'usuario');
  assert.equal(element('#nav-orders').wasClicked, true);
});
