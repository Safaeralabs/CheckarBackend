# Checkar CDA Backend

Base de arquitectura para Checkar CDA construida con Django y Django REST Framework.

## Modulos incluidos

- `accounts`: usuarios, perfiles, roles y bitacora.
- `vehicles`: vehiculos registrados por clientes.
- `scheduling`: citas, sedes, servicios, horarios y tarifas.
- `inspections`: flujo tecnico de inspeccion, evidencias y certificados.
- `billing`: facturas y pagos.
- `notifications`: notificaciones transaccionales.
- `operations`: recepcion operativa y trazabilidad de planta.
- `administration`: reportes globales y configuracion administrativa.

## Puesta en marcha

1. Crear entorno virtual.
2. Instalar dependencias con `py -m pip install -r requirements.txt`.
3. Copiar `.env.example` a `.env`.
4. Ejecutar migraciones con `py manage.py migrate`.
5. Crear superusuario con `py manage.py createsuperuser`.
6. Iniciar servidor con `py manage.py runserver`.

## Auth API

- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/auth/logout/`
- `GET /api/auth/session/`

## Estructura

La arquitectura funcional y de API esta documentada en [docs/system-architecture.md](./docs/system-architecture.md).
