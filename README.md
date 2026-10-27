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

Requisitos: Python 3.12, [uv](https://docs.astral.sh/uv/), Docker y Git.

```bash
# Clonar el repositorio
git clone <url-del-repositorio>
cd ms-asignaciones

# Instalar las dependencias (produccion y desarrollo) y crear el entorno
# virtual en .venv; uv tambien instala la version de Python si falta
uv sync

# Copiar las variables de entorno de ejemplo
cp .env.example .env        # Linux / Mac
copy .env.example .env       # Windows
```

`uv run <comando>` ejecuta cualquier herramienta dentro del entorno del proyecto
sin activarlo. Si se prefiere activarlo una sola vez por sesion de terminal:
`source .venv/bin/activate` (Linux/Mac) o `.venv\Scripts\activate` (Windows).

Los valores por defecto de `.env.example` usan `postgres` y `redis` (los
nombres de los servicios en `docker-compose.yml`) como host, para que
funcionen cuando el propio microservicio corre dentro de docker-compose. Si
vas a ejecutar `alembic` o `flask`/`gunicorn` directamente desde tu maquina
(fuera de Docker), cambia esos hosts por `localhost` en tu `.env`, ya que
docker-compose tambien publica esos puertos en el host.

### Levantar el servicio con Docker

El `.env.example` apunta por defecto a los contenedores locales de
`docker-compose.yml`. Hay dos modos:

```bash
# Con PostgreSQL en un contenedor local (no se tiene una base de datos propia)
docker compose --profile local-db up

# Con una base de datos externa (ajusta DATABASE_URL en .env)
docker compose up
```

Redis se levanta siempre como contenedor local de desarrollo. Con cualquiera
de los dos modos, el servicio queda disponible en `http://localhost:8000`:

| Recurso | URL |
|---|---|
| Salud | `http://localhost:8000/health` |
| Disponibilidad | `http://localhost:8000/ready` |
| Metricas (Prometheus) | `http://localhost:8000/metrics` |
| Swagger UI | `http://localhost:8000/swagger-ui` |

### Migraciones

El proyecto usa [Alembic](https://alembic.sqlalchemy.org/) para versionar los
cambios al esquema de PostgreSQL: cada cambio (crear una tabla, agregar una
columna, un indice, etc.) queda como un archivo en `alembic/versions/`, con un
`upgrade()` y un `downgrade()`, para que todo el equipo y el CI apliquen los
mismos cambios en el mismo orden en cualquier ambiente.

`alembic/env.py` ya esta cableado con el proyecto: lee `DATABASE_URL` desde la
configuracion (`.env`) y usa como referencia la `Base` declarativa de
`adapters/outbound/persistence/base.py`. Por eso, el flujo normal es:

1. Crear o modificar un modelo SQLAlchemy heredando de `Base`.
2. Generar la migracion comparando ese modelo contra la base de datos real
   (necesita PostgreSQL corriendo y accesible via `DATABASE_URL`):

   ```bash
   uv run alembic revision --autogenerate -m "crea tabla assignments"
   ```

3. **Revisar el archivo generado en `alembic/versions/`** antes de aplicarlo:
   `--autogenerate` detecta bien tablas y columnas nuevas, pero no siempre
   detecta renombrados, cambios de tipo complejos o constraints.
4. Aplicar la migracion:

   ```bash
   uv run alembic upgrade head
   ```

Otros comandos utiles:

```bash
uv run alembic downgrade -1   # deshace la ultima migracion aplicada
uv run alembic history        # historial de migraciones
uv run alembic current        # revision en la que esta la base conectada
```

Una vez una migracion ya se aplico en `develop`/`main` o en la base de datos
de otro integrante del equipo, no se edita: se crea una migracion nueva
encima. Si todavia esta solo en tu rama, si puedes borrarla y regenerarla.

### Ejecutar el servicio sin Docker

```bash
# Servidor de desarrollo de Flask, con autorecarga
uv run flask --app assignments.main:create_app run --port 8000 --debug

# Servidor de produccion (gunicorn), igual que en el Dockerfile
uv run gunicorn --bind 0.0.0.0:8000 --threads 4 --no-control-socket "assignments.main:create_app()"
```

### Pruebas

```bash
# Unitarias: no requieren Docker
uv run pytest tests/unit

# Integracion: usan Testcontainers, Docker debe estar corriendo
uv run pytest tests/integration

# Todas, con reporte de cobertura (minimo 80 %)
uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=80
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
