# Perfiles y permisos

La autorización de los módulos se basa en permisos Django en servidor; ocultar
una opción del menú no reemplaza la validación de cada API.

Para crear el grupo inicial de administradores, después de aplicar migraciones:

```bash
python manage.py configurar_perfiles
```

El grupo `Administrador` recibe permisos para pedidos (consulta y acciones),
stock, catálogo I-NET, administración del token y catálogo web. Asigna al grupo
solo las cuentas autorizadas desde el nuevo módulo `/usuarios/`, disponible
únicamente para superusuarios. El módulo permite buscar cuentas y asignar o
retirar el grupo; el endpoint vuelve a comprobar el superusuario y registra los
cambios. Ser miembro del grupo Administrador no concede acceso a Django Admin:
para eso se requiere además `is_staff`; las cuentas `is_superuser` conservan el
comportamiento estándar de Django.

Los usuarios no reciben permisos por defecto. Antes de producción, revisa y
retira permisos directos o de otros grupos en cuentas existentes; el comando
configura el grupo `Administrador` y no modifica esos permisos existentes.
