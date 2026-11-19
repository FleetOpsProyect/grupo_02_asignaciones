# Arquitectura hexagonal en ms-asignaciones

Este documento explica, con ejemplos reales del código, cómo está aplicada la
arquitectura hexagonal (puertos y adaptadores) en este microservicio: qué va
en cada capa, qué puede importar a qué, y cómo viaja una petición HTTP desde
que entra hasta que toca el dominio y vuelve. Cierra con lo que falta por
integrar con otros microservicios, dónde iría y por qué todavía no está.

## 1. Las capas y sus carpetas

```
src/assignments/
├── domain/          Entidades y reglas de negocio puras
├── application/     Casos de uso + puertos (interfaces)
│   ├── ports/           <- Protocol: lo que application necesita de afuera
│   └── use_cases/        <- orquestan domain + ports
├── adapters/
│   ├── inbound/      Entran al sistema desde afuera
│   │   ├── http/         Flask: controladores REST
│   │   └── messaging/     consumidores de eventos (vacío todavía)
│   └── outbound/      El sistema sale hacia afuera
│       ├── persistence/   PostgreSQL (SQLAlchemy)
│       ├── http_clients/  HTTP a Vehiculos/Conductores
│       ├── messaging/     publicador de eventos
│       └── cache/         Redis
└── main.py          Composition root: conecta adapters concretos con puertos
```

| Carpeta | Qué contiene | Ejemplo en este repo |
|---|---|---|
| `domain/` | Entidades y las reglas que ellas mismas garantizan, sin ayuda externa | `Assignment`, `AssignmentStatus`, excepciones de negocio |
| `application/ports/` | Interfaces (`Protocol`) que describen lo que un caso de uso necesita de afuera (I/O) | `AssignmentRepository`, `VehicleDirectoryPort`, `DriverDirectoryPort`, `AssignmentEventPublisher` |
| `application/use_cases/` | Orquestan: usan `domain/` + los puertos para cumplir un escenario completo | `CreateAssignmentUseCase`, `GetAssignmentUseCase`, `ListAssignmentsUseCase` |
| `adapters/inbound/http/` | Traduce HTTP ↔ casos de uso | `assignments.py` (blueprint `/assignment`) |
| `adapters/outbound/*` | Implementan los puertos con tecnología real | `SqlAlchemyAssignmentRepository`, `HttpVehicleDirectory`, `LoggingAssignmentEventPublisher` |
| `main.py` | El único módulo que conoce casos de uso **y** adapters concretos a la vez | `create_app()` |

## 2. La regla de dependencias (quién puede importar a quién)

```
adapters/inbound  ──┐
                     ├──>  application  ──>  domain
adapters/outbound ──┘           ▲
                                 │
                              main.py
                     (conoce TODO; cablea adapters <-> ports)
```

- `domain/` no importa nada de Flask, SQLAlchemy, Redis, `requests` ni de
  `adapters/`. Es Python puro.
- `application/` solo importa `domain/` y sus propios `ports/` (interfaces).
  Nunca importa una clase concreta de `adapters/`.
- `adapters/*` importan `application/` (para implementar sus puertos o para
  llamar a sus casos de uso), y pueden importar lo que necesiten de
  infraestructura (Flask, SQLAlchemy, `requests`...).
- `main.py` es el único lugar que importa adapters concretos **y** casos de
  uso al mismo tiempo, y decide "esta clase concreta satisface este puerto".

Esto es lo que permite que el mismo caso de uso funcione en producción (con
Postgres real) y en las pruebas (con un repositorio en memoria) sin cambiar
una línea de `application/`.

## 3. El flujo completo de una petición: `POST /assignment`

Es el caso más completo porque toca las tres cosas: persistencia, llamada a
otro microservicio y publicación de un evento. Paso a paso, con archivo y
función exactos:

```
Cliente HTTP
   │  POST /assignment  {employee_id, vehicle_type, start_date, end_date}
   ▼
① middleware.py → register_correlation_id()
   Asigna/propaga X-Correlation-Id antes de que la peticion llegue al resource.
   ▼
② adapters/inbound/http/assignments.py → AssignmentCollectionResource.post()
   @blp.arguments(AssignmentCreateRequestSchema) ya valido tipos/requeridos
   (marshmallow). Si falta un campo o el tipo no calza, ni siquiera llega aqui.
   ▼
③ El resource arma un DTO de application y llama al caso de uso:
      command = CreateAssignmentCommand(employee_id, vehicle_type,
                                         start_date, end_date)
      use_case = current_app.config["CREATE_ASSIGNMENT_USE_CASE"]
      use_case.execute(command)
   (El resource NO sabe que hay Postgres o SQLAlchemy; solo conoce el caso
   de uso, que a su vez solo conoce los puertos.)
   ▼
④ application/use_cases/create_assignment.py → CreateAssignmentUseCase.execute()
   a) vehicle_directory.find_active(vehicle_type, end_date)   -> puerto
      driver_directory.find_active(end_date)                 -> puerto
      (en main.py esto es HttpVehicleDirectory/HttpDriverDirectory,
       que hacen el GET real a Vehiculos/Conductores)
   b) repository.busy_vehicle_ids(...) / busy_driver_ids(...) -> puerto
      (en main.py esto es SqlAlchemyAssignmentRepository, que consulta
       Postgres por cruces de fecha con asignaciones PENDIENTE/EN_CURSO)
   c) Si no hay candidato libre -> NoAvailabilityError (domain/exceptions.py)
   ▼
⑤ domain/assignment.py → Assignment.request(...)
   AQUI es donde entra el dominio puro: valida end_date > start_date,
   genera el id, y construye la entidad en estado PENDIENTE.
   Si la fecha es invalida, lanza InvalidAssignmentRequestError. El dominio
   no sabe que existe HTTP, Postgres ni Vehiculos: solo sabe sus propias
   reglas.
   ▼
⑥ De vuelta en el caso de uso:
      repository.add(assignment)              -> persiste (puerto)
      event_publisher.assignment_created(...) -> publica el evento (puerto)
      return assignment                       -> devuelve la ENTIDAD de dominio
   ▼
⑦ adapters/inbound/http/assignments.py (de nuevo)
   El resource recibe la entidad `Assignment` y la retorna; flask-smorest la
   serializa con AssignmentResponseSchema -> JSON de respuesta, 201.
   ▼
Cliente HTTP recibe 201 + la asignacion creada
```

Si en cualquier paso ④ se lanza `NoAvailabilityError`,
`InvalidAssignmentRequestError` o `ExternalServiceUnavailableError`, el
resource las atrapa (`try/except` en `post()`) y las convierte en
`Conflict` (409), `BadRequest` (400) o `ServiceUnavailable` (503). Esas
excepciones de Werkzeug las recoge el manejador global de
`adapters/inbound/http/errors.py` (que ya existía en el arquetipo) y les da
el formato de error estándar de FleetOps, con el `correlation_id` incluido.

## 4. Un flujo de solo lectura: `GET /assignment/{id}`

Más corto porque no hay colaboradores externos, solo el repositorio:

```
GET /assignment/{id}
   ▼
AssignmentResource.get(assignment_id)         (adapters/inbound/http)
   ▼
GetAssignmentUseCase.execute(assignment_id)   (application/use_cases)
   ▼
repository.get_by_id(assignment_id)            -> puerto AssignmentRepository
   (en main.py: SqlAlchemyAssignmentRepository -> SELECT en Postgres)
   ▼
Si no existe -> AssignmentNotFoundError (domain/exceptions.py) -> 404
Si existe    -> devuelve la entidad Assignment (domain) tal cual salió de BD
   ▼
AssignmentResponseSchema la serializa -> 200 + JSON
```

`GET /assignment` y `GET /assignment/active` siguen el mismo patrón, pero
usando `ListAssignmentsUseCase`, que además le pide al repositorio
`count_by_status(filters)` para armar el bloque `resumen`.

## 5. Dónde se cablea todo: `main.py`

```python
repository = SqlAlchemyAssignmentRepository(build_session_factory(engine))
vehicle_directory = _build_vehicle_directory(settings)   # Http... o Unconfigured...
driver_directory = _build_driver_directory(settings)
event_publisher = LoggingAssignmentEventPublisher()

app.config["CREATE_ASSIGNMENT_USE_CASE"] = CreateAssignmentUseCase(
    repository, vehicle_directory, driver_directory, event_publisher
)
```

`CreateAssignmentUseCase` nunca ve `SqlAlchemyAssignmentRepository` ni
`HttpVehicleDirectory` por su nombre de clase: los recibe ya construidos,
tipados como los puertos (`AssignmentRepository`, `VehicleDirectoryPort`,
`DriverDirectoryPort`, `AssignmentEventPublisher`). Por eso las pruebas de
`tests/unit/application/` pueden pasarle dobles en memoria
(`FakeAssignmentRepository`, etc.) sin tocar ni una línea del caso de uso.

## 6. Qué falta por integrar con otros microservicios

Todo esto está "planteado" (el puerto y, donde se pudo, el adapter ya
existen) pero no se puede terminar porque depende de informacion o
decisiones que aun no estan en manos del Grupo 02.

| Falta | Por qué no está | Dónde iría |
|---|---|---|
| **Contrato real de `GET /vehiculos` y `GET /conductores`** | Los equipos de Vehículos y Conductores todavía no publicaron la forma exacta de su respuesta JSON (nombres de campos, paginación). `HttpVehicleDirectory`/`HttpDriverDirectory` asumen un arreglo de objetos con campo `id` (ver nota en el código) | Ajustar `extract_ids()` en `adapters/outbound/http_clients/_shared.py`. El puerto (`VehicleDirectoryPort`/`DriverDirectoryPort` en `application/ports/fleet_directory.py`) y el caso de uso **no cambian** |
| **Broker de eventos real (Kafka o RabbitMQ)** | Los equipos de FleetOps todavía no decidieron cuál broker usar entre todos los microservicios | Un adapter nuevo en `adapters/outbound/messaging/` que implemente el puerto `AssignmentEventPublisher` (igual que `LoggingAssignmentEventPublisher`, pero publicando de verdad). Se cablea en `main.py` en vez del publicador de log; `application/` no cambia |
| **Consumidor de `RutaIniciadaEvent`** (`PENDIENTE` → `EN_CURSO`) | Depende del broker (arriba) y de que Telemetría y Rutas ya esté publicando ese evento | Un adapter nuevo en `adapters/inbound/messaging/` (hoy vacío) que reciba el evento, busque la asignación (`repository.get_by_id`) y llame a `assignment.start()` — ese método **ya existe** en `domain/assignment.py`, solo falta quién lo dispare |
| **Consumidor de `RutaFinalizadaEvent`** (`EN_CURSO` → `FINALIZADA`) | Igual que el anterior | Igual que el anterior, pero llamando a `assignment.finish()` (también ya existe en el dominio) |
| **Consumidor del evento de incidente** (`EN_CURSO` → `INTERRUMPIDA_POR_INCIDENTE`) | Depende del broker y de que Incidentes publique ese evento | Igual que los anteriores, llamando a `assignment.interrupt()` (también ya existe) |
| **`PUT /asignaciones/{id}/reasignar`** | Fuera del alcance acordado para este trabajo (se decidió explícitamente no incluirlo) | Un endpoint nuevo en `adapters/inbound/http/assignments.py` + un caso de uso `ReassignAssignmentUseCase` nuevo + el evento `modified_assignment_event` en el publicador |
| **Autenticación/autorización por rol** | Todavía no hay forma de validar un token ni de confiar en headers de un gateway (se decidió explícitamente no implementarlo aún) | Un middleware nuevo en `adapters/inbound/http/`, parecido a `middleware.py`, que llene algo como `g.current_user` antes de que el resource lo use |

En todos los casos la idea es la misma: **el dominio y los casos de uso ya
están listos para esas funcionalidades** (los métodos de transición de
estado existen, los puertos existen); lo único que falta es el adapter
concreto del lado que depende de otro equipo o de una decisión conjunta
todavía no tomada.
