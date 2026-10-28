# Instrucciones para agentes de desarrollo

Estas reglas se aplican a todo el repositorio y a cualquier código generado o modificado. Antes de trabajar, revisa las instrucciones aplicables, el código existente y la documentación del proyecto. Sigue las instrucciones de mayor prioridad; comunica cualquier conflicto o excepción necesaria. No afirmes haber ejecutado verificaciones que no realizaste.

## Estructura y arquitectura

- Crea cada nueva aplicación Django dentro de `modulo/<nombre_app>/`. Usa nombres descriptivos en minúsculas y `snake_case`. Configura el paquete, `AppConfig.name` e `INSTALLED_APPS` con la ruta completa `modulo.<nombre_app>`; verifica que Django descubra modelos, migraciones y pruebas.
- `inet_ivs/` contiene la configuración del proyecto. `theme/` es una aplicación existente: no la muevas ni reestructures aplicaciones existentes sin una solicitud explícita y un plan de migración.
- Organiza cada aplicación por dominio y responsabilidad. Mantén vistas, tareas y consumidores delgados; ubica la lógica de negocio reutilizable en servicios o componentes apropiados. Evita dependencias circulares y abstracciones innecesarias.
- Usa las capacidades de Django y las dependencias existentes antes de añadir bibliotecas. Justifica dependencias nuevas y comprueba compatibilidad y mantenimiento.
- No introduzcas cambios ajenos a la tarea. Conserva la compatibilidad existente salvo que se solicite lo contrario.

## Identificadores y URL

- Nunca expongas identificadores enteros de registros en URL nuevas, incluidas rutas de administración, API, archivos y WebSockets propios. Usa UUID como identificador público, tanto en rutas como en enlaces, redirecciones y referencias públicas relacionadas.
- Para modelos nuevos expuestos públicamente, usa preferentemente un `UUIDField` único con `default=uuid.uuid4` y `editable=False`; puede ser clave primaria o campo público separado. Define rutas con el conversor `<uuid:...>` y consulta por ese campo.
- Para modelos existentes con clave entera, añade un UUID público mediante una migración segura; no cambies la clave primaria ni rompas URL existentes sin evaluar dependencias, datos y compatibilidad. No expongas el ID interno en respuestas públicas cuando no sea necesario.
- Un UUID no es un secreto ni reemplaza la autorización. Comprueba permisos y alcance del objeto en cada operación. Las rutas de administración de Django existentes requieren evaluación específica antes de modificarlas.

## Seguridad y privacidad

- Aplica mínimo privilegio y denegación por defecto. Verifica autenticación y autorización por acción y objeto en vistas, API, administración, tareas y WebSockets. Limita consultas al ámbito autorizado para evitar acceso entre usuarios u organizaciones.
- Valida entradas en el servidor con formularios, validadores o serializers. Limita campos editables, tamaños, formatos y cargas de archivos. No confíes en datos del cliente ni en validaciones exclusivas del frontend.
- Mantén las protecciones de Django contra CSRF, XSS y SQL injection. Usa ORM o consultas parametrizadas; evita HTML no confiable, `mark_safe` y excepciones CSRF sin justificación y controles equivalentes.
- No incluyas secretos, credenciales ni datos personales en código, repositorio, errores o logs. Usa variables de entorno o un gestor de secretos. No expongas trazas al usuario.
- Para producción, exige `DEBUG=False`, secretos seguros, hosts y orígenes permitidos explícitos, HTTPS, cookies seguras y cabeceras de seguridad adecuadas. No debilites la configuración para facilitar pruebas.
- Protege operaciones sensibles con controles apropiados: límites de frecuencia, validación de origen en WebSockets, tiempos de espera y tratamiento seguro de archivos y servicios externos. Evita revelar si existen recursos no autorizados.

## Datos, rendimiento y concurrencia

- Diseña modelos con restricciones de base de datos, nulabilidad, índices y relaciones acordes al dominio. Usa migraciones versionadas, compatibles con datos existentes y reversibles cuando sea posible. Nunca edites migraciones ya aplicadas sin una estrategia explícita.
- Evita consultas N+1 con `select_related` y `prefetch_related` cuando corresponda. Pagina listados y limita consultas y cargas de datos. Añade índices según consultas reales y mide antes de optimizar.
- Usa transacciones para operaciones que deban ser atómicas y controles de concurrencia cuando correspondan. Programa tareas posteriores al commit con `transaction.on_commit` cuando dependan de datos recién guardados.
- Usa Celery para trabajo costoso o externo cuando corresponda. Diseña tareas idempotentes, con reintentos y tiempos de espera limitados; no envíes secretos ni datos sensibles innecesarios al broker.
- Usa caché solo cuando aporte valor. Define expiración, invalidación y aislamiento por usuario u organización cuando aplique. No almacenes datos sensibles sin una evaluación de seguridad.

## Calidad y verificación

- Usa siempre anotaciones de tipos (type hints) en el código Python nuevo o modificado, incluidos parámetros, valores de retorno y variables cuando aporten claridad. Conserva la compatibilidad con la versión de Python del proyecto.
- Sigue las convenciones del proyecto y PEP 8. Mantén funciones cohesivas, nombres claros y manejo explícito de errores. Documenta decisiones no evidentes y cambios de configuración o despliegue.
- Añade o actualiza pruebas para funcionalidades y regresiones: casos correctos, entradas inválidas, permisos, aislamiento entre usuarios y acceso mediante UUID. Prueba restricciones y concurrencia cuando sean relevantes.
- Ejecuta las verificaciones pertinentes al cambio, como pruebas de Django, `python manage.py check` y `python manage.py makemigrations --check --dry-run`, cuando el entorno lo permita. Informa resultados y cualquier verificación omitida o bloqueada.
- Registra eventos operativos y de auditoría relevantes sin datos sensibles. Evita errores silenciosos y mensajes que filtren detalles internos.
- Antes de operaciones destructivas o migraciones con riesgo de pérdida de datos, explica el impacto y solicita confirmación. No modifiques archivos ajenos ni reviertas cambios existentes del usuario.
