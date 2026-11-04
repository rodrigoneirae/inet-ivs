# Perfiles y permisos

La autorización de los módulos se basa en permisos Django en servidor; ocultar
una opción del menú no reemplaza la validación de cada API.

Para crear el grupo inicial de administradores, después de aplicar migraciones:

```bash
python manage.py configurar_perfiles
```

El grupo `Administrador` recibe todos los permisos operativos disponibles.
Desde `/usuarios/`, los superusuarios pueden crear perfiles personalizados
seleccionando permisos concretos, editarlos, eliminarlos si no están asignados,
y asignar varios perfiles a una cuenta. El módulo y cada endpoint verifican
`is_superuser`; los cambios se registran sin incluir nombres de usuario en los
logs. Ser miembro de un perfil no concede acceso a Django Admin: para eso se
requiere además `is_staff`; las cuentas `is_superuser` conservan el
comportamiento estándar de Django.

Los usuarios no reciben permisos por defecto. Antes de producción, revisa y
retira permisos directos o de otros grupos en cuentas existentes; el comando
configura el grupo `Administrador` y no modifica esos permisos existentes.
