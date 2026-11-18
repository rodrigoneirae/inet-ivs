import json
import uuid
from datetime import timedelta
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from modulo.inventario.models import Asignacion, Bodega, Conteo, Inventario, ProductoSnapshot, TokenMovil, Ubicacion, Zona
from modulo.inventario.services.capturadores import huella
from modulo.inventario.services.catalogo import CatalogoNoDisponible


class InventarioApiTests(TestCase):
    def setUp(self) -> None:
        usuario = get_user_model()
        self.supervisor = usuario.objects.create_user(username='supervisor')
        self.a = usuario.objects.create_user(username='contador-a')
        self.b = usuario.objects.create_user(username='contador-b')
        permiso_supervisor = Permission.objects.get(codename='supervisar_inventario')
        permiso_contador = Permission.objects.get(codename='contar_inventario')
        self.supervisor.user_permissions.add(permiso_supervisor)
        self.a.user_permissions.add(permiso_contador)
        self.b.user_permissions.add(permiso_contador)
        self.bodega = Bodega.objects.create(codigo='01', nombre='Principal')
        self.zona = Zona.objects.create(bodega=self.bodega, codigo='Z', nombre='Zona')
        self.ubicacion = Ubicacion.objects.create(zona=self.zona, codigo='U')
        self.inventario = Inventario.objects.create(bodega=self.bodega, nombre='Ciclo 1', creado_por=self.supervisor)
        ProductoSnapshot.objects.create(codigo='SKU1', descripcion='Prueba', codigo_barra='BARRA')

    def post(self, user: object, url: str, data: dict[str, object]) -> object:
        client = Client()
        client.force_login(user)
        return client.post(url, data=json.dumps(data), content_type='application/json')

    def assign(self, user: object, tipo: str) -> Asignacion:
        return Asignacion.objects.create(inventario=self.inventario, ubicacion=self.ubicacion, usuario=user, tipo=tipo)

    @override_settings(INVENTARIO_APP_TOKEN='a' * 48,
                       CACHES={'api_rate_limit': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
    def test_vinculacion_capturador_turnos_aislamiento_y_revocacion(self) -> None:
        mobile = Client(enforce_csrf_checks=True)
        url = '/api/v1/inventarios/capturadores/crear/'
        self.assertEqual(Client().post(url, json.dumps({'nombre': 'Equipo'}), content_type='application/json').status_code, 401)
        self.assertEqual(mobile.post(url, json.dumps({'nombre': 'Equipo'}), content_type='application/json').status_code, 403)
        created = self.post(self.supervisor, url, {'nombre': 'Equipo'})
        self.assertEqual(created.status_code, 201)
        device_id = created.json()['id']
        device = TokenMovil.objects.get(public_id=device_id)
        self.assertIsNone(device.vinculacion_hash)
        self.assertEqual(device.usuario.has_usable_password(), False)
        qr_url = f'/api/v1/inventarios/capturadores/{device_id}/qr/'
        inventory_id = str(self.inventario.public_id)
        self.assertEqual(self.post(self.supervisor, qr_url, {'inventario': inventory_id}).status_code, 409)
        assign_url = f'/api/v1/inventarios/{inventory_id}/asignar/'
        self.assertEqual(self.post(self.supervisor, assign_url, {'dispositivo': device_id, 'tipo': 'unico'}).status_code, 400)
        turno = self.post(self.supervisor, assign_url, {'dispositivo': device_id, 'tipo': 'unico', 'zona': 'Z1'})
        self.assertEqual(turno.status_code, 201)
        qr = self.post(self.supervisor, qr_url, {'inventario': inventory_id})
        self.assertEqual(qr.status_code, 200)
        contenido = json.loads(qr.json()['contenido_qr'])
        self.assertEqual({key: contenido[key] for key in ('bodega', 'zona', 'usuario', 'tipo')},
                         {'bodega': '01', 'zona': 'Z1', 'usuario': 'Equipo', 'tipo': 'unico'})
        code = contenido['codigo']
        device.refresh_from_db()
        self.assertNotEqual(device.vinculacion_hash, code)
        device.vinculacion_vence = timezone.now() - timedelta(seconds=1)
        device.save(update_fields=['vinculacion_vence'])
        pairing = '/api/v1/inventarios/movil/vincular/'
        app_auth = {'HTTP_AUTHORIZATION': f"Bearer {'a' * 48}"}
        self.assertEqual(mobile.post(pairing, json.dumps({'codigo': code}),
                                     content_type='application/json', **app_auth).status_code, 400)
        renewed = self.post(self.supervisor, qr_url, {'inventario': inventory_id})
        self.assertEqual(renewed.status_code, 200)
        code = json.loads(renewed.json()['contenido_qr'])['codigo']
        self.assertNotEqual(code, contenido['codigo'])
        self.assertEqual(mobile.post(pairing, json.dumps({'codigo': 'inválido'}),
                                     content_type='application/json', **app_auth).status_code, 400)
        response = mobile.post(pairing, json.dumps({'codigo': code}),
                               content_type='application/json', **app_auth)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['configuracion']['zona'], 'Z1')
        self.assertEqual(response.json()['configuracion']['operador'], 'Equipo')
        self.assertEqual(response.json()['configuracion']['tipo_nombre'], 'Conteo único')
        # La re-emisión es válida: el equipo puede volver a vincularse.
        reemitido = self.post(self.supervisor, qr_url, {'inventario': inventory_id})
        self.assertEqual(reemitido.status_code, 200)
        nuevo_codigo = json.loads(reemitido.json()['contenido_qr'])['codigo']
        self.assertNotEqual(nuevo_codigo, code)
        token = response.json()['token']
        self.assertNotEqual(device.token_hash, token)
        self.assertEqual(mobile.post(pairing, json.dumps({'codigo': code}),
                                     content_type='application/json', **app_auth).status_code, 400)
        # El token del equipo sigue vigente tras reemitir el QR.
        headers = {'HTTP_AUTHORIZATION': f'Bearer {token}'}
        own_config = '/api/v1/inventarios/movil/equipo/'
        self.assertEqual(mobile.get(own_config).status_code, 401)
        self.assertEqual(mobile.get(own_config, **app_auth).status_code, 401)
        recovered = mobile.get(own_config, **headers)
        self.assertEqual(recovered.status_code, 200)
        self.assertEqual(recovered.json()['nombre'], 'Equipo')
        self.assertEqual(recovered.json()['configuracion'], response.json()['configuracion'])
        listing = '/api/v1/inventarios/movil/'
        self.assertEqual(mobile.get(listing, **headers).json()['inventarios'][0]['id'], inventory_id)
        self.assertEqual(Client().get('/api/v1/inventarios/capturadores/').status_code, 401)
        client = Client()
        client.force_login(self.supervisor)
        self.assertEqual(client.get(f'/api/v1/inventarios/{self.inventario.public_id}/')
                         .json()['asignaciones'][0]['usuario'], 'Equipo')
        other = self.post(self.supervisor, '/api/v1/inventarios/capturadores/crear/', {'nombre': 'Otro'})
        other_inventory = Inventario.objects.create(bodega=self.bodega, nombre='Otro', creado_por=self.supervisor)
        self.assertEqual(self.post(self.supervisor, f'/api/v1/inventarios/{other_inventory.public_id}/asignar/',
                                   {'dispositivo': other.json()['id'], 'tipo': 'unico', 'zona': 'Z2'}).status_code, 201)
        other_qr = self.post(self.supervisor, f"/api/v1/inventarios/capturadores/{other.json()['id']}/qr/",
                             {'inventario': str(other_inventory.public_id)}).json()
        other_pair = mobile.post(pairing, json.dumps({'codigo': json.loads(other_qr['contenido_qr'])['codigo']}),
                                  content_type='application/json', **app_auth).json()['token']
        other_config = mobile.get(own_config, HTTP_AUTHORIZATION=f'Bearer {other_pair}')
        self.assertEqual(other_config.status_code, 200)
        self.assertEqual(other_config.json()['configuracion']['inventario'], str(other_inventory.public_id))
        self.assertEqual(mobile.get(listing, **headers).json()['inventarios'][0]['id'], str(self.inventario.public_id))
        self.assertEqual(mobile.get(listing, HTTP_AUTHORIZATION=f'Bearer {other_pair}').json()['inventarios'][0]['id'],
                         str(other_inventory.public_id))
        config = f'/api/v1/inventarios/movil/{self.inventario.public_id}/configuracion/'
        self.assertEqual(mobile.get(config, **headers).json()['turnos'][0]['id'], turno.json()['id'])
        self.assertEqual(mobile.get(config, HTTP_AUTHORIZATION=f'Bearer {other_pair}').status_code, 404)
        self.assertEqual(mobile.get(config, HTTP_AUTHORIZATION=f"Bearer {'a' * 48}",
                                    HTTP_X_CONTADOR=device.usuario.username).status_code, 403)
        event = {'evento': str(uuid.uuid4()), 'zona': 'Z1', 'ubicacion': 'U1', 'producto': 'SKU1', 'cantidad': '1'}
        sync = f"/api/v1/inventarios/movil/asignaciones/{turno.json()['id']}/sincronizar/"
        self.assertEqual(mobile.post(sync, json.dumps({'eventos': [event]}),
                                     content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {other_pair}').status_code, 404)
        self.assertEqual(mobile.post(sync, json.dumps({'eventos': [event]}),
                                     content_type='application/json', **headers).json()['confirmados'], [event['evento']])
        self.assertEqual(self.post(self.supervisor, f'/api/v1/inventarios/capturadores/{device_id}/revocar/', {}).status_code, 200)
        self.assertEqual(mobile.get(listing, **headers).status_code, 401)
        self.assertEqual(mobile.get(own_config, **headers).status_code, 401)
        self.assertEqual(mobile.post(sync, json.dumps({'eventos': [event]}),
                                     content_type='application/json', **headers).status_code, 401)

    def test_ficha_de_capturador_expone_la_configuracion(self) -> None:
        device = self.post(self.supervisor, '/api/v1/inventarios/capturadores/crear/',
                           {'nombre': 'Equipo'}).json()['id']
        url = f'/api/v1/inventarios/{self.inventario.public_id}/asignar/'
        turno = self.post(self.supervisor, url, {'dispositivo': device, 'tipo': 'a', 'zona': 'Z1'}).json()
        client = Client()
        client.force_login(self.supervisor)
        ficha = next(item for item in client.get('/api/v1/inventarios/capturadores/').json()['capturadores']
                     if item['id'] == device)
        self.assertEqual(ficha['nombre'], 'Equipo')
        self.assertEqual(ficha['vinculado'], False)
        self.assertEqual(len(ficha['turnos']), 1)
        configuracion = ficha['turnos'][0]
        self.assertEqual(configuracion['operador'], 'Equipo')
        self.assertEqual(configuracion['bodega'], '01')
        self.assertEqual(configuracion['bodega_nombre'], 'Principal')
        self.assertEqual(configuracion['zona'], 'Z1')
        self.assertEqual(configuracion['tipo'], 'a')
        self.assertEqual(configuracion['tipo_nombre'], 'Parte A')
        self.assertEqual(configuracion['inventario'], str(self.inventario.public_id))
        self.assertEqual(configuracion['turno'], turno['id'])

    def test_qr_por_turno_rechaza_un_turno_ajeno(self) -> None:
        device = self.post(self.supervisor, '/api/v1/inventarios/capturadores/crear/',
                           {'nombre': 'Equipo'}).json()['id']
        otro = self.post(self.supervisor, '/api/v1/inventarios/capturadores/crear/',
                         {'nombre': 'Otro'}).json()['id']
        url = f'/api/v1/inventarios/{self.inventario.public_id}/asignar/'
        turno = self.post(self.supervisor, url, {'dispositivo': device, 'tipo': 'a', 'zona': 'Z1'}).json()
        ajeno = self.post(self.supervisor, url, {'dispositivo': otro, 'tipo': 'b', 'zona': 'Z1'}).json()
        qr_url = f'/api/v1/inventarios/capturadores/{device}/qr/'
        generado = self.post(self.supervisor, qr_url, {'inventario': str(self.inventario.public_id),
                                                        'asignacion': turno['id']})
        self.assertEqual(generado.status_code, 200)
        self.assertEqual(generado.json()['configuracion']['turno'], turno['id'])
        self.assertEqual(generado.json()['configuracion']['zona'], 'Z1')
        # El turno de otro capturador no habilita el QR de este equipo.
        self.assertEqual(self.post(self.supervisor, qr_url, {'inventario': str(self.inventario.public_id),
                                                              'asignacion': ajeno['id']}).status_code, 409)
        self.assertEqual(self.post(self.supervisor, qr_url, {'inventario': str(self.inventario.public_id),
                                                              'asignacion': 'no-uuid'}).status_code, 400)

    def test_reconfigurar_turno_zona_tipo_y_conflictos(self) -> None:
        device = self.post(self.supervisor, '/api/v1/inventarios/capturadores/crear/',
                           {'nombre': 'Equipo'}).json()['id']
        url = f'/api/v1/inventarios/{self.inventario.public_id}/asignar/'
        a = self.post(self.supervisor, url, {'dispositivo': device, 'tipo': 'a', 'zona': 'Z1'}).json()
        route = f'/api/v1/inventarios/asignaciones/{a["id"]}/turno/'
        # Solo el supervisor reconfigura.
        self.assertEqual(self.post(self.a, route, {'zona': 'Z2', 'tipo': 'a'}).status_code, 403)
        # Cambiar el tipo a uno ya usado en la misma zona es un conflicto.
        otro = self.post(self.supervisor, '/api/v1/inventarios/capturadores/crear/',
                         {'nombre': 'Otro'}).json()['id']
        b = self.post(self.supervisor, url, {'dispositivo': otro, 'tipo': 'b', 'zona': 'Z1'}).json()
        self.assertEqual(self.post(self.supervisor, route, {'zona': 'Z1', 'tipo': 'b'}).status_code, 409)
        # Un conteo único no puede compartir zona con otro turno.
        self.assertEqual(self.post(self.supervisor, route, {'zona': 'Z1', 'tipo': 'unico'}).status_code, 409)
        # Mover la zona arrastra al turno homólogo: los A/B siguen compartiendo zona.
        movido = self.post(self.supervisor, route, {'zona': 'Z2', 'tipo': 'a'})
        self.assertEqual(movido.status_code, 200)
        self.assertEqual(movido.json()['zona'], 'Z2')
        self.assertEqual(movido.json()['turnos_movidos'], 2)
        self.assertEqual(Asignacion.objects.get(public_id=b['id']).zona.codigo, 'Z2')
        # Con conteos registrados la configuración ya no se toca.
        evento = {'evento': str(uuid.uuid4()), 'zona': 'Z2', 'ubicacion': 'E1',
                  'producto': 'SKU1', 'cantidad': '1'}
        operador = TokenMovil.objects.get(public_id=device).usuario
        self.assertEqual(self.post(operador, f'/api/v1/inventarios/asignaciones/{a["id"]}/sincronizar/',
                                   {'eventos': [evento]}).status_code, 200)
        self.assertEqual(self.post(self.supervisor, route, {'zona': 'Z3', 'tipo': 'a'}).status_code, 409)
        self.assertEqual(self.post(self.supervisor, route, {'zona': '', 'tipo': 'a'}).status_code, 400)

    @override_settings(INVENTARIO_APP_TOKEN='d' * 48,
                       CACHES={'api_rate_limit': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
    def test_configuracion_movil_incluye_nombres_de_la_configuracion(self) -> None:
        device = self.post(self.supervisor, '/api/v1/inventarios/capturadores/crear/',
                           {'nombre': 'Equipo'}).json()['id']
        url = f'/api/v1/inventarios/{self.inventario.public_id}/asignar/'
        turno = self.post(self.supervisor, url, {'dispositivo': device, 'tipo': 'a', 'zona': 'Z1'}).json()
        qr_url = f'/api/v1/inventarios/capturadores/{device}/qr/'
        codigo = json.loads(self.post(self.supervisor, qr_url,
                                      {'inventario': str(self.inventario.public_id)}).json()['contenido_qr'])['codigo']
        mobile = Client()
        app_auth = {'HTTP_AUTHORIZATION': 'Bearer ' + 'd' * 48}
        respuesta = mobile.post('/api/v1/inventarios/movil/vincular/', json.dumps({'codigo': codigo}),
                                 content_type='application/json', **app_auth)
        self.assertEqual(respuesta.status_code, 200)
        token = respuesta.json()['token']
        headers = {'HTTP_AUTHORIZATION': f'Bearer {token}'}
        config = mobile.get(f'/api/v1/inventarios/movil/{self.inventario.public_id}/configuracion/', **headers)
        self.assertEqual(config.status_code, 200)
        datos = config.json()
        self.assertEqual(datos['inventario_nombre'], self.inventario.nombre)
        self.assertEqual(datos['bodega_nombre'], 'Principal')
        self.assertEqual(datos['contador'], 'Equipo')
        self.assertEqual(datos['turnos'][0]['tipo_nombre'], 'Parte A')
        self.assertEqual(datos['turnos'][0]['zona'], 'Z1')
        self.assertEqual(datos['turnos'][0]['id'], turno['id'])

    def test_eliminar_capturador_exige_supervisor_y_libera_su_historial(self) -> None:
        device = self.post(self.supervisor, '/api/v1/inventarios/capturadores/crear/',
                           {'nombre': 'Equipo'}).json()['id']
        url = f'/api/v1/inventarios/{self.inventario.public_id}/asignar/'
        turno = self.post(self.supervisor, url, {'dispositivo': device, 'tipo': 'a', 'zona': 'Z1'}).json()
        eliminar = f'/api/v1/inventarios/capturadores/{device}/eliminar/'
        self.assertEqual(self.post(self.a, eliminar, {}).status_code, 403)
        self.assertEqual(self.post(self.supervisor, eliminar, {}).status_code, 200)
        self.assertFalse(TokenMovil.objects.filter(public_id=device).exists())
        self.assertFalse(Asignacion.objects.filter(public_id=turno['id']).exists())
        self.assertEqual(self.post(self.supervisor, eliminar, {}).status_code, 404)

    def test_eliminar_capturador_con_qr_emitido(self) -> None:
        """El turno referenciado por el token no debe bloquear la eliminación."""
        url = '/api/v1/inventarios/capturadores/crear/'
        creado = self.post(self.supervisor, url, {'nombre': 'Equipo', 'inventario': str(self.inventario.public_id),
                                                  'zona': 'Z1', 'tipo': 'unico'}).json()
        qr = self.post(self.supervisor, f'/api/v1/inventarios/capturadores/{creado["id"]}/qr/',
                       {'inventario': str(self.inventario.public_id)})
        self.assertEqual(qr.status_code, 200)
        self.assertIsNotNone(TokenMovil.objects.get(public_id=creado['id']).vinculacion_asignacion_id)
        self.assertEqual(self.post(self.supervisor, f'/api/v1/inventarios/capturadores/{creado["id"]}/eliminar/',
                                   {}).status_code, 200)
        self.assertFalse(TokenMovil.objects.filter(public_id=creado['id']).exists())
        self.assertFalse(Asignacion.objects.filter(public_id=creado['turno']['id']).exists())

    def test_capturador_con_conteos_no_se_elimina(self) -> None:
        device = self.post(self.supervisor, '/api/v1/inventarios/capturadores/crear/',
                           {'nombre': 'Equipo'}).json()['id']
        url = f'/api/v1/inventarios/{self.inventario.public_id}/asignar/'
        turno = self.post(self.supervisor, url, {'dispositivo': device, 'tipo': 'a', 'zona': 'Z1'}).json()
        evento = {'evento': str(uuid.uuid4()), 'zona': 'Z1', 'ubicacion': 'U1',
                  'producto': 'SKU1', 'cantidad': '1'}
        operador = TokenMovil.objects.get(public_id=device).usuario
        self.assertEqual(self.post(operador, f'/api/v1/inventarios/asignaciones/{turno["id"]}/sincronizar/',
                                   {'eventos': [evento]}).status_code, 200)
        self.assertEqual(self.post(self.supervisor, f'/api/v1/inventarios/capturadores/{device}/eliminar/', {}).status_code, 409)
        self.assertTrue(TokenMovil.objects.filter(public_id=device).exists())

    def test_alta_de_capturador_asigna_turno_con_zona_y_tipo(self) -> None:
        url = '/api/v1/inventarios/capturadores/crear/'
        inventario = str(self.inventario.public_id)
        # El turno exige zona y tipo cuando se registra con inventario.
        self.assertEqual(self.post(self.supervisor, url,
                                   {'nombre': 'Equipo', 'inventario': inventario, 'tipo': 'a'}).status_code, 400)
        self.assertEqual(self.post(self.supervisor, url,
                                   {'nombre': 'Equipo', 'inventario': inventario, 'zona': 'Z1'}).status_code, 400)
        creado = self.post(self.supervisor, url,
                           {'nombre': 'Equipo', 'inventario': inventario, 'zona': 'Z1', 'tipo': 'a'})
        self.assertEqual(creado.status_code, 201)
        datos = creado.json()
        self.assertEqual(datos['turno']['zona'], 'Z1')
        self.assertEqual(datos['turno']['tipo'], 'a')
        self.assertEqual(datos['turno']['operador'], 'Equipo')
        self.assertEqual(datos['turno']['inventario'], inventario)
        turno = Asignacion.objects.get(public_id=datos['turno']['id'])
        self.assertEqual(turno.inventario, self.inventario)
        self.assertEqual(turno.zona.codigo, 'Z1')
        # Un segundo tipo A choca con la regla y no deja capturador huérfano.
        antes = TokenMovil.objects.count()
        choque = self.post(self.supervisor, url,
                           {'nombre': 'Choca', 'inventario': inventario, 'zona': 'Z1', 'tipo': 'a'})
        self.assertEqual(choque.status_code, 409)
        self.assertIn('Parte A', choque.json()['error'])
        self.assertEqual(TokenMovil.objects.count(), antes)
        # Sin inventario solo se registra el equipo.
        sin_turno = self.post(self.supervisor, url, {'nombre': 'Solo'})
        self.assertEqual(sin_turno.status_code, 201)
        self.assertNotIn('turno', sin_turno.json())
        self.assertFalse(Asignacion.objects.filter(
            usuario__username__startswith='capturador_',
            usuario__capturador_inventario__nombre='Solo').exists())

    def test_importar_catalogo_movil_exige_token_de_equipo(self) -> None:
        """La importación desde I-NET se hace desde la app, no desde la web."""
        url = '/api/v1/inventarios/movil/catalogo/importar/'
        self.assertEqual(self.post(self.supervisor, url, {'pagina': 1}).status_code, 401)
        with override_settings(INVENTARIO_APP_TOKEN='a' * 48):
            aplicacion = Client(enforce_csrf_checks=True).post(
                url, json.dumps({'pagina': 1}), content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer {"a" * 48}',
            )
        self.assertEqual(aplicacion.status_code, 401)
        creado = self.post(self.supervisor, '/api/v1/inventarios/capturadores/crear/',
                           {'nombre': 'Equipo'}).json()
        token = 'k' * 48
        TokenMovil.objects.filter(public_id=creado['id']).update(token_hash=huella(token))
        client = Client(enforce_csrf_checks=True)
        auth = {'HTTP_AUTHORIZATION': f'Bearer {token}'}
        self.assertEqual(client.post(url, json.dumps({'pagina': 0}), content_type='application/json',
                                     **auth).status_code, 400)
        with patch('modulo.inventario.views.api.importar_pagina', Mock(return_value=(150, True))) as importar:
            respuesta = client.post(url, json.dumps({'pagina': 2, 'tamano': 150}),
                                    content_type='application/json', **auth)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json(), {'importados': 150, 'pagina': 2, 'hay_mas': True})
        importar.assert_called_once_with(2, 150)
        with patch('modulo.inventario.views.api.importar_pagina',
                   Mock(side_effect=CatalogoNoDisponible('No se pudo consultar I-NET.'))):
            caido = client.post(url, json.dumps({'pagina': 1}), content_type='application/json', **auth)
        self.assertEqual(caido.status_code, 503)
        self.assertEqual(caido.json()['error'], 'No se pudo consultar I-NET.')

    def test_permisos_y_asignacion_cruzada(self) -> None:
        url = f'/api/v1/inventarios/{self.inventario.public_id}/asignar/'
        body = {'usuario': self.a.username, 'tipo': 'a'}
        self.assertEqual(self.post(self.a, url, body).status_code, 403)
        self.assertEqual(self.post(self.supervisor, url, body).status_code, 201)
        self.assertEqual(self.post(self.supervisor, url, {**body, 'tipo': 'b'}).status_code, 409)
        self.assertEqual(self.post(self.supervisor, url, {**body, 'usuario': self.b.username, 'tipo': 'b'}).status_code, 201)
        self.assertEqual(self.post(self.supervisor, url, {**body, 'usuario': self.b.username, 'tipo': 'unico'}).status_code, 409)
        self.assertEqual(self.post(self.supervisor, url, {**body, 'usuario': ''}).status_code, 400)

    def test_capturador_exige_zona_y_no_mezcla_zonas(self) -> None:
        device = self.post(self.supervisor, '/api/v1/inventarios/capturadores/crear/',
                           {'nombre': 'Equipo'}).json()['id']
        url = f'/api/v1/inventarios/{self.inventario.public_id}/asignar/'
        self.assertEqual(self.post(self.supervisor, url, {'dispositivo': device, 'tipo': 'a'}).status_code, 400)
        self.assertEqual(self.post(self.supervisor, url, {'dispositivo': device, 'tipo': 'a', 'zona': 'Z1'}).status_code, 201)
        otro = self.post(self.supervisor, '/api/v1/inventarios/capturadores/crear/',
                         {'nombre': 'Otro'}).json()['id']
        self.assertEqual(self.post(self.supervisor, url, {'dispositivo': otro, 'tipo': 'b', 'zona': 'Z2'}).status_code, 409)
        self.assertEqual(self.post(self.supervisor, url, {'dispositivo': otro, 'tipo': 'b', 'zona': 'Z1'}).status_code, 201)
        self.assertEqual(Zona.objects.filter(codigo='Z1', bodega=self.bodega).count(), 1)
        self.assertFalse(Zona.objects.filter(codigo='Z2', bodega=self.bodega).exists())

    def test_reintento_mismo_evento_y_conflicto(self) -> None:
        turno = self.assign(self.a, 'unico')
        url = f'/api/v1/inventarios/asignaciones/{turno.public_id}/sincronizar/'
        evento = {'evento': str(uuid.uuid4()), 'producto': 'BARRA', 'cantidad': '2.500'}
        self.assertEqual(self.post(self.a, url, {'eventos': [evento]}).status_code, 200)
        self.assertEqual(self.post(self.a, url, {'eventos': [evento]}).status_code, 200)
        self.assertEqual(Conteo.objects.count(), 1)
        self.assertEqual(self.post(self.b, url, {'eventos': [evento]}).status_code, 404)
        self.assertEqual(self.post(self.a, url, {'eventos': [{**evento, 'cantidad': '3'}]}).status_code, 409)
        self.assertEqual(self.post(self.a, url, {'eventos': [{**evento, 'evento': 'invalido'}]}).status_code, 400)

    def test_analisis_diferencias_faltantes_unico_y_cierre(self) -> None:
        a = self.assign(self.a, 'a')
        b = self.assign(self.b, 'b')
        for turno, user, quantity in ((a, self.a, '2'), (b, self.b, '3')):
            url = f'/api/v1/inventarios/asignaciones/{turno.public_id}/sincronizar/'
            self.assertEqual(self.post(user, url, {'eventos': [{'evento': str(uuid.uuid4()),
                                                                 'producto': 'SKU1', 'cantidad': quantity}]}).status_code, 200)
        detail = f'/api/v1/inventarios/{self.inventario.public_id}/'
        client = Client()
        client.force_login(self.supervisor)
        self.assertEqual(client.get(detail).json()['resultados'][0]['estado'], 'pendiente')
        self.assertEqual(self.post(self.supervisor, f'{detail}cerrar/', {}).status_code, 409)
        for turno, user in ((a, self.a), (b, self.b)):
            self.assertEqual(self.post(user, f'/api/v1/inventarios/asignaciones/{turno.public_id}/finalizar/', {}).status_code, 200)
        self.assertEqual(client.get(detail).json()['resultados'][0]['estado'], 'diferencia')
        self.assertEqual(self.post(self.supervisor, f'{detail}cerrar/', {}).status_code, 200)
        self.assertEqual(client.get(detail).json()['resultados'][0]['estado'], 'diferencia')
        self.assertEqual(self.post(self.a, f'/api/v1/inventarios/asignaciones/{a.public_id}/sincronizar/',
                                   {'eventos': [{'evento': str(uuid.uuid4()), 'producto': 'SKU1', 'cantidad': '1'}]}).status_code, 409)

    def test_solo_conteo_coincide_y_ausencia_en_b_es_faltante(self) -> None:
        solo = self.assign(self.a, 'unico')
        self.post(self.a, f'/api/v1/inventarios/asignaciones/{solo.public_id}/sincronizar/',
                  {'eventos': [{'evento': str(uuid.uuid4()), 'producto': 'SKU1', 'cantidad': '1'}]})
        self.post(self.a, f'/api/v1/inventarios/asignaciones/{solo.public_id}/finalizar/', {})
        client = Client()
        client.force_login(self.supervisor)
        url = f'/api/v1/inventarios/{self.inventario.public_id}/'
        self.assertEqual(client.get(url).json()['resultados'][0]['estado'], 'coincidente')
        second = Inventario.objects.create(bodega=self.bodega, nombre='Otro ciclo', creado_por=self.supervisor)
        a = Asignacion.objects.create(inventario=second, ubicacion=self.ubicacion, usuario=self.a, tipo='a')
        b = Asignacion.objects.create(inventario=second, ubicacion=self.ubicacion, usuario=self.b, tipo='b')
        self.post(self.a, f'/api/v1/inventarios/asignaciones/{a.public_id}/sincronizar/',
                  {'eventos': [{'evento': str(uuid.uuid4()), 'producto': 'SKU1', 'cantidad': '1'}]})
        for turno, user in ((a, self.a), (b, self.b)):
            self.post(user, f'/api/v1/inventarios/asignaciones/{turno.public_id}/finalizar/', {})
        self.assertEqual(client.get(f'/api/v1/inventarios/{second.public_id}/').json()['resultados'][0]['estado'], 'faltante')

    @patch('modulo.inventario.views.api.buscar_bodega')
    def test_csrf_y_bodega_de_inet(self, buscar: Mock) -> None:
        buscar.return_value = {'codigo': '2', 'nombre': 'Bodega I-NET'}
        url = '/api/v1/inventarios/crear/'
        self.assertEqual(self.post(self.supervisor, url, {'nombre': 'Otro', 'bodega': '2'}).status_code, 201)
        self.assertEqual(Bodega.objects.get(codigo='2').nombre, 'Bodega I-NET')
        buscar.assert_called_once_with('2')
        buscar.return_value = None
        self.assertEqual(self.post(self.supervisor, url, {'nombre': 'Inválido', 'bodega': '3'}).status_code, 400)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.supervisor)
        self.assertEqual(client.post(url, json.dumps({
            'nombre': 'Sin CSRF', 'bodega': '1',
        }), content_type='application/json').status_code, 403)

    def test_sincronizacion_todo_o_nada_y_codigo_barra_ambiguo(self) -> None:
        turno = self.assign(self.a, 'unico')
        url = f'/api/v1/inventarios/asignaciones/{turno.public_id}/sincronizar/'
        valid = {'evento': str(uuid.uuid4()), 'producto': 'SKU1', 'cantidad': '1'}
        invalid = {'evento': str(uuid.uuid4()), 'producto': 'DESCONOCIDO', 'cantidad': '1'}
        self.assertEqual(self.post(self.a, url, {'eventos': [valid, invalid]}).status_code, 400)
        self.assertEqual(Conteo.objects.count(), 0)
        ProductoSnapshot.objects.create(codigo='SKU2', descripcion='Otro', codigo_barra='BARRA')
        self.assertEqual(self.post(self.a, url, {'eventos': [{**valid, 'producto': 'BARRA'}]}).status_code, 409)
        self.assertEqual(Conteo.objects.count(), 0)

    @override_settings(INVENTARIO_APP_TOKEN='a' * 48)
    def test_token_env_conteo_zona_y_revocacion_por_configuracion(self) -> None:
        headers = {'HTTP_AUTHORIZATION': f"Bearer {'a' * 48}", 'HTTP_X_CONTADOR': self.a.username}
        mobile = Client(enforce_csrf_checks=True)
        self.assertEqual(mobile.get('/api/v1/inventarios/movil/', **headers).status_code, 200)
        self.assertEqual(mobile.get('/api/v1/inventarios/movil/').status_code, 401)
        turno = Asignacion.objects.create(inventario=self.inventario, usuario=self.a, tipo='unico')
        config = mobile.get(f'/api/v1/inventarios/movil/{self.inventario.public_id}/configuracion/', **headers)
        self.assertIsNone(config.json()['turnos'][0]['zona'])
        url = f'/api/v1/inventarios/movil/asignaciones/{turno.public_id}/sincronizar/'
        event = {'evento': str(uuid.uuid4()), 'zona': 'NUEVA-ZONA', 'ubicacion': 'ESCANEADA',
                 'producto': 'SKU1', 'cantidad': '2'}
        self.assertEqual(mobile.post(url, json.dumps({'eventos': [event]}), content_type='application/json', **headers).status_code, 200)
        self.assertEqual(Conteo.objects.get().ubicacion.codigo, 'ESCANEADA')
        self.assertEqual(Conteo.objects.get().ubicacion.zona.codigo, 'NUEVA-ZONA')
        self.assertEqual(Conteo.objects.get().ubicacion.zona.bodega, self.bodega)
        self.assertEqual(mobile.post(url, json.dumps({'eventos': [event]}), content_type='application/json', **headers).status_code, 200)
        other = {**headers, 'HTTP_X_CONTADOR': self.b.username}
        self.assertEqual(mobile.post(url, json.dumps({'eventos': [event]}), content_type='application/json', **other).status_code, 404)
        with override_settings(INVENTARIO_APP_TOKEN='b' * 48):
            self.assertEqual(mobile.get('/api/v1/inventarios/movil/', **headers).status_code, 401)
        with override_settings(INVENTARIO_APP_TOKEN=''):
            self.assertEqual(mobile.get('/api/v1/inventarios/movil/', **headers).status_code, 401)

    def test_zona_compara_ubicaciones_escaneadas_sin_registrarlas_previamente(self) -> None:
        a = Asignacion.objects.create(inventario=self.inventario, zona=self.zona, usuario=self.a, tipo='a')
        b = Asignacion.objects.create(inventario=self.inventario, zona=self.zona, usuario=self.b, tipo='b')
        self.assertFalse(Ubicacion.objects.filter(codigo='NUEVA').exists())
        for turno, user, location, amount in ((a, self.a, 'NUEVA', '2'),
                                              (b, self.b, 'NUEVA', '2'),
                                              (a, self.a, 'FALTA', '1')):
            url = f'/api/v1/inventarios/asignaciones/{turno.public_id}/sincronizar/'
            event = {'evento': str(uuid.uuid4()), 'ubicacion': location, 'producto': 'SKU1', 'cantidad': amount}
            self.assertEqual(self.post(user, url, {'eventos': [event]}).status_code, 200)
        for turno, user in ((a, self.a), (b, self.b)):
            self.post(user, f'/api/v1/inventarios/asignaciones/{turno.public_id}/finalizar/', {})
        client = Client()
        client.force_login(self.supervisor)
        rows = client.get(f'/api/v1/inventarios/{self.inventario.public_id}/').json()['resultados']
        self.assertEqual({row['ubicacion_codigo']: row['estado'] for row in rows},
                         {'NUEVA': 'coincidente', 'FALTA': 'faltante'})

    def test_lote_invalido_no_crea_ubicacion(self) -> None:
        a = Asignacion.objects.create(inventario=self.inventario, zona=self.zona, usuario=self.a, tipo='unico')
        url = f'/api/v1/inventarios/asignaciones/{a.public_id}/sincronizar/'
        event = {'evento': str(uuid.uuid4()), 'ubicacion': 'NO-GUARDAR',
                 'producto': 'DESCONOCIDO', 'cantidad': '1'}
        self.assertEqual(self.post(self.a, url, {'eventos': [event]}).status_code, 400)
        self.assertFalse(Ubicacion.objects.filter(codigo='NO-GUARDAR').exists())

    @override_settings(INVENTARIO_APP_TOKEN='c' * 48)
    def test_turnos_globales_comparan_zona_ubicacion_y_producto(self) -> None:
        ruta = f'/api/v1/inventarios/{self.inventario.public_id}/asignar/'
        self.assertEqual(self.post(self.supervisor, ruta, {'usuario': self.a.username, 'tipo': 'a'}).status_code, 201)
        self.assertEqual(self.post(self.supervisor, ruta, {'usuario': self.b.username, 'tipo': 'b'}).status_code, 201)
        turnos = {turno.tipo: turno for turno in Asignacion.objects.filter(inventario=self.inventario)}
        mobile = Client(enforce_csrf_checks=True)
        for tipo, usuario, zona, ubicacion, cantidad in (
            ('a', self.a, 'Z1', 'E1', '2'), ('b', self.b, 'Z1', 'E1', '2'),
            ('a', self.a, 'Z2', 'E1', '1'), ('b', self.b, 'Z2', 'E2', '1'),
        ):
            headers = {'HTTP_AUTHORIZATION': f"Bearer {'c' * 48}", 'HTTP_X_CONTADOR': usuario.username}
            url = f'/api/v1/inventarios/movil/asignaciones/{turnos[tipo].public_id}/sincronizar/'
            event = {'evento': str(uuid.uuid4()), 'zona': zona, 'ubicacion': ubicacion,
                     'producto': 'SKU1', 'cantidad': cantidad}
            self.assertEqual(mobile.post(url, json.dumps({'eventos': [event]}), content_type='application/json',
                                         **headers).status_code, 200)
        client = Client()
        client.force_login(self.supervisor)
        detalle = f'/api/v1/inventarios/{self.inventario.public_id}/'
        self.assertTrue(all(row['estado'] == 'pendiente' for row in client.get(detalle).json()['resultados']))
        for tipo, usuario in (('a', self.a), ('b', self.b)):
            headers = {'HTTP_AUTHORIZATION': f"Bearer {'c' * 48}", 'HTTP_X_CONTADOR': usuario.username}
            url = f'/api/v1/inventarios/movil/asignaciones/{turnos[tipo].public_id}/finalizar/'
            self.assertEqual(mobile.post(url, '{}', content_type='application/json', **headers).status_code, 200)
        resultados = client.get(detalle).json()['resultados']
        self.assertEqual({(r['zona'], r['ubicacion_codigo']): r['estado'] for r in resultados}, {
            ('Z1', 'E1'): 'coincidente', ('Z2', 'E1'): 'faltante', ('Z2', 'E2'): 'faltante',
        })
        self.assertEqual(self.post(self.supervisor, f'{detalle}cerrar/', {}).status_code, 200)

    def test_usuario_no_puede_tomar_dos_turnos_globales(self) -> None:
        ruta = f'/api/v1/inventarios/{self.inventario.public_id}/asignar/'
        self.assertEqual(self.post(self.supervisor, ruta, {'usuario': self.a.username, 'tipo': 'a'}).status_code, 201)
        self.assertEqual(self.post(self.supervisor, ruta, {'usuario': self.a.username, 'tipo': 'b'}).status_code, 409)
