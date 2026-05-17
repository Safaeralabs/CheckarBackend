# Arquitectura Web Checkar CDA

## 1. Arquitectura de carpetas

```text
checkar_cda_backend/
├── config/
├── apps/
│   ├── common/
│   ├── accounts/
│   ├── vehicles/
│   ├── scheduling/
│   ├── inspections/
│   ├── billing/
│   ├── notifications/
│   ├── operations/
│   └── administration/
├── docs/
├── manage.py
├── requirements.txt
└── .env.example
```

## 2. Portales conectados

### Portal Cliente

- Autenticacion, registro y perfil.
- Registro y gestion de vehiculos.
- Agenda de citas por sede, servicio y franja.
- Consulta de estado de inspeccion.
- Historial de inspecciones y certificados.
- Pagos, facturas y notificaciones.

### Portal Operador

- Recepcion del vehiculo.
- Validacion de cita, cliente y placa.
- Pre-chequeo documental.
- Inspeccion visual y fotografica.
- Registro de resultados.
- Seguimiento de cola, trazabilidad y bitacora.

### Panel Admin

- Usuarios y roles.
- Catalogo de servicios.
- Tarifas por sede.
- Horarios y cupos.
- Sedes.
- Reportes globales.

## 3. Rutas principales

### Cliente

- `/cliente/login`
- `/cliente/registro`
- `/cliente/dashboard`
- `/cliente/perfil`
- `/cliente/vehiculos`
- `/cliente/citas`
- `/cliente/citas/nueva`
- `/cliente/inspecciones`
- `/cliente/certificados`
- `/cliente/pagos`
- `/cliente/facturas`
- `/cliente/notificaciones`

### Operador

- `/operador/login`
- `/operador/dashboard`
- `/operador/recepcion`
- `/operador/recepcion/:placa`
- `/operador/inspecciones`
- `/operador/inspecciones/:id/documentos`
- `/operador/inspecciones/:id/visual`
- `/operador/inspecciones/:id/resultados`
- `/operador/bitacora`
- `/operador/reportes`

### Admin

- `/admin-panel/dashboard`
- `/admin-panel/usuarios`
- `/admin-panel/roles`
- `/admin-panel/servicios`
- `/admin-panel/tarifas`
- `/admin-panel/horarios`
- `/admin-panel/sedes`
- `/admin-panel/reportes`

## 4. Modelos de datos

### Cuentas

- `User`: identidad, credenciales, rol, telefono, documento.
- `CustomerProfile`: direccion, ciudad, sede preferida.
- `OperatorProfile`: sede, codigo interno, capacidades operativas.
- `AuditLog`: eventos sensibles y trazabilidad.

### Vehiculos

- `Vehicle`: placa, tipo, marca, linea, modelo, combustible, VIN, kilometraje.

### Agenda

- `Branch`: sedes.
- `ServiceType`: revision por tipo de vehiculo.
- `Tariff`: tarifa por sede y vigencia.
- `ScheduleSlot`: ventana horaria y capacidad.
- `Appointment`: reserva de revision.

### Inspeccion

- `InspectionRecord`: inspeccion principal.
- `DocumentCheck`: pre-evaluacion documental.
- `InspectionChecklistItem`: hallazgos por item tecnico.
- `InspectionPhoto`: evidencia visual.
- `InspectionCertificate`: certificado emitido.

### Facturacion

- `Invoice`: factura.
- `PaymentTransaction`: transaccion de pago.

### Operacion

- `VehicleReception`: recepcion y cola.
- `SystemLogEntry`: bitacora tecnica del sistema.

### Administracion

- `GlobalReport`: exportables y reportes agregados.

## 5. Roles y permisos

- `customer`: administra su perfil, vehiculos, citas, pagos, certificados y notificaciones propias.
- `operator`: valida citas, recepciona vehiculos, consulta agenda operativa y registra chequeos iniciales.
- `inspector`: captura evidencias, checklist tecnico y resultados de inspeccion.
- `supervisor`: puede revisar resultados, aprobar flujo operativo y escalar incidencias.
- `admin`: acceso global, catalogos, configuracion, tarifas, sedes, horarios y reportes.

## 6. Flujo de estados

### Cita

`created -> confirmed -> checked_in -> in_progress -> completed`

Flujos alternos:

- `created -> cancelled`
- `confirmed -> no_show`
- `in_progress -> rejected`

### Inspeccion

`pending -> documents_validated -> visual_review -> mechanical_test -> results_recorded -> approved/rejected -> certified`

### Pago

`pending -> authorized -> paid`

Flujos alternos:

- `pending -> failed`
- `paid -> refunded`

## 7. Componentes principales

### Cliente

- `AuthShell`
- `CustomerDashboard`
- `CustomerProfileCard`
- `VehicleRegistryForm`
- `VehicleList`
- `AppointmentWizard`
- `InspectionStatusTimeline`
- `InspectionHistoryTable`
- `CertificateDownloadCard`
- `InvoiceList`
- `PaymentCheckout`
- `NotificationCenter`

### Operador

- `OperatorDashboard`
- `ReceptionQueueBoard`
- `PlateLookup`
- `AppointmentValidator`
- `DocumentChecklist`
- `TechnicalDataForm`
- `PhotoCapturePanel`
- `InspectionChecklistBoard`
- `ResultsSummary`
- `SystemLogFeed`
- `OperationalReportsPanel`

### Admin

- `AdminDashboard`
- `UserRoleTable`
- `ServiceCatalogManager`
- `TariffManager`
- `SchedulePlanner`
- `BranchManager`
- `GlobalReportsBoard`

## 8. API endpoints

### Auth y usuarios

- `GET /api/auth/users/me/`
- `GET /api/auth/users/`
- `GET /api/auth/customers/`
- `GET /api/auth/operators/`
- `GET /api/auth/audit-logs/`

### Vehiculos

- `GET /api/vehicles/`
- `POST /api/vehicles/`
- `GET /api/vehicles/{id}/`
- `PATCH /api/vehicles/{id}/`

### Agenda

- `GET /api/scheduling/branches/`
- `GET /api/scheduling/services/`
- `GET /api/scheduling/tariffs/`
- `GET /api/scheduling/slots/`
- `GET /api/scheduling/appointments/`
- `POST /api/scheduling/appointments/`
- `POST /api/scheduling/appointments/{id}/cancel/`

### Inspeccion

- `GET /api/inspections/records/`
- `POST /api/inspections/records/`
- `POST /api/inspections/records/{id}/advance_status/`
- `GET|POST /api/inspections/documents/`
- `GET|POST /api/inspections/checklist/`
- `GET|POST /api/inspections/photos/`
- `GET /api/inspections/certificates/`

### Facturacion

- `GET /api/billing/invoices/`
- `GET|POST /api/billing/transactions/`
- `POST /api/billing/transactions/{id}/confirm/`

### Notificaciones

- `GET /api/notifications/`
- `GET|POST /api/notifications/devices/`

### Operacion

- `GET|POST /api/operations/receptions/`
- `GET /api/operations/logs/`

### Administracion

- `GET /api/admin-panel/dashboard-summary/`
- `GET|POST /api/admin-panel/global-reports/`

## 9. Reglas de seguridad

- Autenticacion obligatoria en toda la API.
- Autorizacion por rol y por pertenencia de recurso.
- Segregacion de datos: el cliente solo puede ver su informacion.
- Bitacora de acciones sensibles: cambios de estado, pagos, certificados, roles.
- Validacion estricta de transiciones de estado.
- Cifrado HTTPS obligatorio en produccion.
- Almacenamiento seguro de archivos con rutas no publicas si contienen evidencia sensible.
- Proteccion CSRF para sesiones web y estrategia token si se expone a apps moviles.
- Politicas de contraseñas robustas y recuperacion auditada.
- Rate limiting para login, consultas de placa y pagos.
- Sanitizacion de archivos, metadatos y entradas JSON.
- Backups, retencion de auditoria y monitoreo de errores.

## 10. Lineamientos UI responsive

- Mobile-first desde 360px.
- Header compacto con accesos rapidos a cita, estado y soporte.
- Navegacion inferior en cliente para movil.
- Sidebar colapsable en operador y admin.
- Tablas operativas con vistas tipo cards en movil.
- Color principal de marca: azul.
- Tokens sugeridos:
  - `--color-primary: #0B5FFF`
  - `--color-primary-dark: #0847BF`
  - `--color-primary-soft: #EAF2FF`
  - `--color-success: #1F9D55`
  - `--color-warning: #D97706`
  - `--color-danger: #C0392B`

## 11. Siguiente fase recomendada

- Agregar JWT o session auth segun canal.
- Crear migraciones.
- Implementar pruebas de permisos y transiciones.
- Conectar frontend responsive sobre esta API.
- Integrar pasarela de pagos y servicio de notificaciones.
