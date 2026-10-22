# ms-asignaciones

Microservicio de **Asignaciones** de la plataforma **FleetOps** (FleetCorp S.A.), proyecto del curso Desarrollo de Software III (750027C) de la Universidad del Valle. Lo desarrolla el **Grupo 02**.

Asignaciones es la única autoridad sobre la relación vehículo-conductor. Recibe las solicitudes de los empleados, busca un vehículo y un conductor aptos (activos y con su documentación vigente) que no tengan otra asignación en las mismas fechas, y crea la asignación. Después sigue su ciclo de vida a partir de los eventos de Telemetría y Rutas e Incidentes, y publica sus propios eventos para el resto del sistema.

## Stack

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.12 |
| Framework web | Flask |
| Arquitectura | Hexagonal (puertos y adaptadores) |
| Base de datos | PostgreSQL |
| Caché | Redis |
| Mensajería | Broker de eventos (Kafka o RabbitMQ, por definir entre los equipos) |
| Calidad | ruff, mypy, pytest + pytest-cov, SonarCloud |
| Contenedores | Docker |
| CI | GitHub Actions |

## Arquitectura

El código sigue la arquitectura hexagonal: la lógica de negocio vive en el núcleo y no depende de Flask, de la base de datos ni del broker. Todo lo externo se conecta a través de puertos (interfaces definidas por el núcleo) implementados por adaptadores.

```
src/asignaciones/
├── domain/          # Entidades, reglas de negocio y máquina de estados
├── application/     # Casos de uso y puertos (interfaces)
├── adapters/
│   ├── inbound/     # Controladores REST (Flask) y consumidores de eventos
│   └── outbound/    # Repositorios (PostgreSQL), clientes HTTP, caché (Redis), publicador outbox
└── main.py          # Punto de entrada: construye los adaptadores y los inyecta
```

## Estados de una asignación

| Transición | Disparador |
|---|---|
| (inicio) → `PENDIENTE` | `POST /asignaciones` |
| `PENDIENTE` → `EN_CURSO` | Evento `RutaIniciadaEvent` |
| `EN_CURSO` → `FINALIZADA` | Evento `RutaFinalizadaEvent` |
| `EN_CURSO` → `INTERRUMPIDA_POR_INCIDENTE` | Evento de incidente de Incidentes |
| `PENDIENTE` → `PENDIENTE` (reasignación) | `PUT /asignaciones/{id}/reasignar` |

Ningún registro se elimina: las asignaciones solo cambian de estado.

## API REST

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/asignaciones` | Crea una asignación a partir de la solicitud del empleado |
| `GET` | `/asignaciones/{id}` | Consulta una asignación |
| `GET` | `/asignaciones` | Lista paginada con filtros y resumen por estado |
| `GET` | `/asignaciones/activas` | Asignaciones en `PENDIENTE` o `EN_CURSO` de un vehículo o conductor |
| `PUT` | `/asignaciones/{id}/reasignar` | Reemplaza el vehículo o el conductor de una asignación pendiente |
| `GET` | `/health`, `/ready`, `/metrics` | Salud del servicio y métricas para Prometheus |

La documentación completa de cada endpoint estará en Swagger (OpenAPI) cuando el servicio esté en marcha.

## Integración con otros microservicios

**Consume por HTTP**

| Servicio | Llamada |
|---|---|
| Vehículos | `GET /vehiculos?estado=ACTIVO&tipo={tipo}&vigencia_hasta={fecha}` |
| Conductores | `GET /conductores?estado=ACTIVO&vigencia_hasta={fecha}` |

**Eventos que publica**

| Evento | Cuándo |
|---|---|
| `assignment_created_event` | Se crea una asignación |
| `interrupted_assignment_event` | Una asignación se interrumpe por un incidente |
| `modified_assignment_event` | Se reasigna el vehículo o el conductor |

**Eventos que consume**

| Evento | Publica |
|---|---|
| `RutaIniciadaEvent` | Telemetría y Rutas |
| `RutaFinalizadaEvent` | Telemetría y Rutas |
| Evento de incidente reportado | Incidentes |

## Desarrollo local

Requisitos: Python 3.12, Docker y Git.

```bash
# Clonar el repositorio
git clone <url-del-repositorio>
cd ms-asignaciones

# Crear y activar el entorno virtual
python -m venv .venv
source .venv/bin/activate        # Linux / Mac
.venv\Scripts\activate           # Windows

# Instalar dependencias (incluidas las de desarrollo)
python -m pip install -e ".[dev]"
```

## Calidad de código

Antes de cada commit:

```bash
ruff format src tests            # Formato
ruff check src tests --fix       # Linting
mypy src                         # Tipos estáticos
pytest --cov=src --cov-fail-under=80   # Pruebas con cobertura mínima del 80 %
```

Las pruebas unitarias no requieren Docker. Las de integración levantan un PostgreSQL real con Testcontainers, así que Docker debe estar corriendo.

## Flujo de trabajo

- `main`: código estable.
- `develop`: rama de integración.
- Ramas personales o de funcionalidad (`feat/...`, `fix/...`): todo cambio sale de aquí.

Todo cambio entra por pull request. Cada PR hacia `develop` ejecuta el pipeline de CI: ruff, mypy, pruebas con cobertura y análisis de SonarCloud.

## Configuración

La configuración se lee de variables de entorno o de un archivo `.env`, que nunca se sube al repositorio.

| Variable | Descripción |
|---|---|
| `DATABASE_URL` | Conexión a PostgreSQL |
| `REDIS_URL` | Conexión a Redis |
| `BROKER_URL` | Conexión al broker de eventos |
| `VEHICULOS_URL`, `CONDUCTORES_URL` | URL base de los servicios consumidos |
| `HTTP_TIMEOUT_MS` | Timeout de las llamadas a otros servicios |
