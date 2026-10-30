import subprocess
import sys

from django.test import SimpleTestCase


class DescubrimientoTasksTests(SimpleTestCase):
    def test_worker_descubre_tareas_con_nombres_compatibles(self) -> None:
        codigo = """
from inet_ivs.celery import app
app.loader.import_default_modules()
esperadas = {
    'modulo.acceso.tasks.sincronizar_usuarios_ivs',
    'modulo.anymarket.tasks.sincronizar_pedidos',
    'modulo.anymarket.tasks.reconciliar_pedidos',
}
faltantes = esperadas - set(app.tasks)
if faltantes:
    raise SystemExit(f'Tareas no registradas: {sorted(faltantes)}')
"""
        resultado = subprocess.run(
            [sys.executable, '-c', codigo], capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)
