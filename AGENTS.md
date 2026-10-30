# Instrucciones para agentes de desarrollo

Estas reglas se aplican a todo el repositorio y a cualquier código generado o modificado. Antes de trabajar, revisa las instrucciones aplicables, el código existente y la documentación del proyecto. Sigue las instrucciones de mayor prioridad; comunica cualquier conflicto o excepción necesaria. No afirmes haber ejecutado verificaciones que no realizaste.

## Estructura y arquitectura

- Crea cada nueva aplicación Django dentro de `modulo/<nombre_app>/`. Usa nombres descriptivos en minúsculas y `snake_case`. Configura el paquete, `AppConfig.name` e `INSTALLED_APPS` con la ruta completa `modulo.<nombre_app>`; verifica que Django descubra modelos, migraciones y pruebas.
- `inet_ivs/` contiene la configuración del proyecto. `theme/` es una aplicación existente: no la muevas ni reestructures aplicaciones existentes sin una solicitud explícita y un plan de migración.
- Organiza cada aplicación por dominio y responsabilidad. Mantén vistas, tareas y consumidores delgados; ubica la lógica de negocio reutilizable en servicios o componentes apropiados. Evita dependencias circulares y abstracciones innecesarias.
- Agrupa modelos, vistas, rutas, servicios y pruebas en paquetes `models/`, `views/`, `urls/`, `services/` y `tests/`, con archivos descriptivos por responsabilidad. Cuando corresponda, usa también `forms/`, `backends/` y `tasks/`. Conserva `apps.py`, `migrations/`, `admin.py` y `management/` según las convenciones y necesidades de Django.
- Exporta los modelos desde `models/__init__.py` y los backends usados en la configuración desde su paquete. Para Celery, importa las tareas en `tasks/__init__.py` y conserva nombres explícitos estables que coincidan con Beat y los mensajes existentes; verifica el descubrimiento de Django y Celery después de reorganizar archivos.
- Usa las capacidades de Django y las dependencias existentes antes de añadir bibliotecas. Justifica dependencias nuevas y comprueba compatibilidad y mantenimiento.
- No introduzcas cambios ajenos a la tarea. Conserva la compatibilidad existente salvo que se solicite lo contrario.

## Diseño e interfaz

- Diseña siempre interfaces responsivas, adaptadas a móviles, tabletas y escritorio. Comprueba la navegación, los formularios y las tablas en distintos tamaños de pantalla.
- Usa Tailwind CSS para los estilos y mantén un sistema de colores coherente con temas claro y oscuro. Como paleta inicial, usa azul `#2563EB` para acciones principales, verde `#16A34A` para éxito, ámbar `#D97706` para advertencias y rojo `#DC2626` para errores; en el tema claro usa fondo `#F8FAFC`, superficies `#FFFFFF` y texto `#0F172A`, y en el oscuro fondo `#0F172A`, superficies `#1E293B` y texto `#F8FAFC`. Ajusta los tonos cuando sea necesario para garantizar contraste y legibilidad.
- Organiza la interfaz principal como un dashboard con menú lateral y menú superior. El menú lateral debe poder ocultarse o minimizarse y disponer de un control accesible para volver a mostrarlo o expandirlo. En pantallas pequeñas, adáptalo para que sea accesible sin ocultar permanentemente el contenido principal.
- Separa la lógica JavaScript del HTML: utiliza archivos JavaScript independientes y evita scripts y manejadores de eventos en línea. No uses jQuery; emplea JavaScript nativo y las capacidades disponibles del proyecto.
- Usa Tabulator para las tablas de datos, con presentación responsiva y paginación apropiada para el volumen de información. Integra sus estilos con los temas claro y oscuro.
- Usa Litepicker para la selección de fechas y rangos de fechas en las interfaces. Utiliza los archivos compartidos locales en `static/vendor/litepicker/`, mantén la validación en el servidor y contempla accesibilidad, temas claro y oscuro y funcionamiento alternativo cuando JavaScript no esté disponible.
- Usa notificaciones tipo toast para comunicar resultados y errores; nunca uses `alert()`. Garantiza que las notificaciones sean accesibles y legibles en ambos temas.
- Mantén accesibilidad mediante HTML semántico, navegación por teclado, estados de foco visibles y contraste adecuado. No dependas únicamente del color para transmitir información.

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
- Para producción, exige `DEBUG=False`, secretos seguros, hosts y orígenes permitidos explícitos, HTTPS, cookies seguras y cabeceras de seguridad adecuadas. No debilites la configuración para facilitar pruebas. Excepción autorizada: la conexión SQL Server de I-NET puede usar `TrustServerCertificate=yes` cuando se habilite explícitamente en la configuración del entorno.
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
