# GitMap

**Control de versiones para mapas web de ArcGIS.**

[![CI](https://github.com/14-TR/Git-Map/actions/workflows/ci.yml/badge.svg)](https://github.com/14-TR/Git-Map/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/gitmap-cli.svg)](https://pypi.org/project/gitmap-cli/)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-832%2B-brightgreen)](https://github.com/14-TR/Git-Map/actions)

GitMap lleva los flujos de trabajo familiares de Git a ArcGIS Online y Portal for ArcGIS. Clone un mapa web, realice cambios en una rama, inspeccione exactamente qué cambió, fusione de forma segura y envíe la versión aprobada de vuelta al Portal.

```bash
$ gitmap clone abc123def456
Cloned "County Flood Risk" into county-flood-risk

$ cd county-flood-risk
$ gitmap branch feature/new-basemap
Created branch feature/new-basemap

$ gitmap checkout feature/new-basemap
Switched to branch feature/new-basemap

$ gitmap pull
Pulled latest web map JSON from Portal

$ gitmap diff --format visual
~ operationalLayers[2].visibility: false -> true
+ operationalLayers[5]: "Hydrants"

$ gitmap commit -m "Add hydrants layer and enable parcels"
[feature/new-basemap 8f2a1d9] Add hydrants layer and enable parcels

$ gitmap diff main feature/new-basemap --format visual

$ gitmap checkout main
$ gitmap merge feature/new-basemap
$ gitmap push
Pushed main to Portal
```

## Demo

Un guion de demostración de 60-90 segundos está disponible en [`marketing/demo-script.md`](marketing/demo-script.md). La grabación planeada mostrará el flujo de trabajo seguro de un mapa de prueba: clonar, crear rama, extraer/editar, comparar (diff), confirmar (commit), fusionar (merge) y enviar (push).

Hasta que el video o GIF sea grabado, el guion documenta los comandos exactos, la narración y las notas de seguridad para la primera demo pública.

## Por qué los equipos de GIS utilizan GitMap

Los mapas web de ArcGIS son documentos JSON con un historial real, pero la mayoría de los equipos todavía los gestionan como elementos opacos del Portal. Eso crea problemas conocidos:

- los mapas de producción se sobrescriben sin una pista de auditoría clara
- los experimentos de cartografía, pop-ups, capas y renderizadores son riesgosos
- revisar "¿qué cambió?" generalmente implica una inspección manual del Portal
- promover correcciones entre entornos de pre-producción (staging) y producción es repetitivo
- revertir un cambio erróneo en el mapa es más lento de lo que debería ser

GitMap añade primitivas de control de versiones que los equipos de GIS ya entienden:

- **historial de commits** para cada estado guardado del mapa
- **ramas (branches)** para experimentos seguros y trabajo en paralelo
- **diffs conscientes de ArcGIS** para capas, tablas, renderizadores, pop-ups y propiedades JSON
- **flujos de trabajo de fusión (merge) y reversión (revert)** para lanzamientos y rollbacks más seguros
- **sincronización push/pull** entre repositorios locales y ArcGIS Online o Portal
- **ganchos de automatización (hooks)** para repositorios de mapas masivos, extracciones programadas y flujos de trabajo asistidos por IA

## Instalación

### Requisitos

- Python 3.11, 3.12, 3.13, o 3.14
- Acceso a ArcGIS Online o Portal for ArcGIS
- Un ID de elemento de mapa web para el primer repositorio que desee clonar

### Ruta de instalación soportada actualmente

```bash
git clone https://github.com/14-TR/Git-Map.git
cd Git-Map
/opt/homebrew/bin/python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e "packages/gitmap_core[dev]"
python -m pip install -e apps/cli/gitmap
```

Utilice un intérprete de Python 3.11+ al crear el entorno virtual. En sistemas donde `python3` todavía apunta a Python 3.9 o 3.10, use un ejecutable explícito como `python3.11`, `python3.12` o `python3.13`.

Esto instala el comando de consola `gitmap` desde el checkout actual. Verifique que la CLI esté disponible:

```bash
gitmap --version
gitmap --help
gitmap doctor
```

El paquete PyPI `gitmap-cli` no es actualmente una ruta de instalación soportada para primeros usuarios. Hasta que las instalaciones publicadas sean verificadas para las versiones de Python soportadas, utilice el flujo de instalación desde el código fuente anterior.

## Inicio rápido: primer flujo de trabajo exitoso

Este recorrido comienza con un mapa web de ArcGIS existente y termina enviando un estado de la rama principal (main) aprobado de vuelta al Portal. Para su primera ejecución, utilice un mapa web de prueba que no sea de producción, que sea de su propiedad o que pueda modificar con seguridad.

Antes de comenzar, verifique que el ID del elemento provenga de la URL del elemento del mapa web de ArcGIS y que el mapa sea seguro para realizar pruebas. `gitmap clone` lee desde el Portal y crea un repositorio local; `gitmap push` es el paso que puede actualizar el contenido gestionado por ArcGIS.

### 1. Configurar credenciales del Portal

GitMap puede leer las credenciales de variables de entorno o de un archivo `.env` local. El repositorio incluye una plantilla:

```bash
cp configs/env.example .env
```

Edite `.env` con los detalles de su Portal:

```env
PORTAL_URL=https://your-org.maps.arcgis.com
PORTAL_USER=your_username
PORTAL_PASSWORD=your_password
```

GitMap también acepta los nombres alternativos de usuario/contraseña utilizados por varias herramientas de ArcGIS:

```env
ARCGIS_USERNAME=your_username
ARCGIS_PASSWORD=your_password
```

El archivo `.env` es ignorado por Git y nunca debe ser incluido en los commits.

### 2. Clonar un mapa web

Copie el ID del elemento del mapa web desde ArcGIS Online o Portal, luego clónelo:

- Abra la página del elemento del mapa web en ArcGIS Online o Portal.
- Copie el valor de `id` de la URL, por ejemplo `...?id=abc123def456`.
- Utilice un mapa de prueba primero. `clone`, `status`, `diff`, `log` y `commit` funcionan localmente, pero `push` puede actualizar el contenido de ArcGIS.

```bash
gitmap clone abc123def456
cd YourMapTitle
```

Para elegir el nombre de la carpeta local usted mismo:

```bash
gitmap clone abc123def456 --directory flood-risk-map
cd flood-risk-map
```

El comando clone crea un repositorio local de GitMap que contiene el JSON del mapa web, los metadatos de GitMap y un commit inicial para el estado actual del Portal. No modifica el elemento del Portal.

Si las comprobaciones de instalación, paquete, credenciales o directorio actual no están claras antes de clonar, ejecute:

```bash
gitmap doctor
gitmap doctor --portal
```

`gitmap doctor` verifica el entorno local sin escribir en el Portal. La opción `--portal` intenta realizar una comprobación de conectividad contra la organización de ArcGIS configurada.

### 3. Verificar el estado inicial

```bash
gitmap status
gitmap log --limit 5
```

Debería estar en `main` con un árbol de trabajo limpio después de la clonación inicial.

### 4. Crear una rama de funcionalidad (feature branch)

```bash
gitmap branch feature/hydrology-update
gitmap checkout feature/hydrology-update
```

Realice el cambio del mapa en ArcGIS, o edite los archivos JSON del mapa rastreados localmente si está trabajando a ese nivel.

### 5. Extraer y revisar cambios

Si el cambio se realizó en ArcGIS, extraiga el estado más reciente del Portal en su rama:

```bash
gitmap pull
```

Revise la rama comparándola con `main`:

```bash
gitmap status
gitmap diff --format visual
```

Para generar un artefacto de revisión compartible para los interesados (stakeholders):

```bash
gitmap diff --format html --output hydrology-review.html
```

### 6. Confirmar el cambio aprobado

```bash
gitmap commit -m "Update hydrology layers"
```

Después de confirmar la rama de funcionalidad, puede comparar la punta de la rama guardada con `main`:

```bash
gitmap diff main feature/hydrology-update --format visual
```

Se puede guardar un texto de justificación opcional con el commit:

```bash
gitmap commit -m "Update hydrology layers" -r "Matches the April field-data refresh"
```

### 7. Fusionar y enviar

```bash
gitmap checkout main
gitmap merge feature/hydrology-update
gitmap push
```

`gitmap push` publica el estado de la rama actual de vuelta al elemento de ArcGIS configurado o al elemento de GitMap gestionado por el Portal, dependiendo de la configuración del repositorio. Revise los diffs antes de enviar y utilice un mapa web de prueba hasta que se sienta cómodo con el flujo de trabajo.

Ese es el ciclo principal de GitMap: **clone → branch → pull or edit → diff → commit → merge → push**.

## Flujos de trabajo comunes

### Experimentar de forma segura con un mapa de producción

```bash
gitmap checkout main
gitmap branch feature/try-imagery-basemap
gitmap checkout feature/try-imagery-basemap

# realice el cambio del mapa en ArcGIS, luego sincronícelo localmente
gitmap pull
gitmap diff --format visual
gitmap commit -m "Try imagery basemap"
gitmap diff main feature/try-imagery-basemap --format visual
```

### Revisar cambios antes del lanzamiento

```bash
gitmap diff main feature/try-imagery-basemap --format html --output release-review.html
gitmap log --limit 10
gitmap show HEAD
```

### Revertir un cambio erróneo

```bash
gitmap log --limit 20
gitmap revert <commit-id>
gitmap push
```

### Gestionar muchos mapas a la vez

```bash
gitmap setup-repos --owner myusername --directory repositories
gitmap auto-pull --directory repositories --auto-commit
```

## Referencia rápida de comandos

| Comando | Qué hace |
|---|---|
| `gitmap clone <ITEM_ID>` | Crea un repositorio local a partir de un mapa web de ArcGIS |
| `gitmap clone <ITEM_ID> --directory <PATH>` | Clona en una carpeta local seleccionada |
| `gitmap status` | Muestra la rama actual y el estado del árbol de trabajo |
| `gitmap branch <NAME>` | Crea una rama |
| `gitmap checkout <NAME>` | Cambia de rama |
| `gitmap pull` | Extrae el estado más reciente del Portal en el repositorio actual |
| `gitmap diff [SOURCE] [TARGET]` | Compara el índice, ramas o commits |
| `gitmap diff main feature/x --format visual` | Muestra una comparación de ramas en tabla enriquecida |
| `gitmap diff main feature/x --format html --output review.html` | Exporta un informe de diff compartible |
| `gitmap commit -m "message"` | Guarda el estado actual del mapa como un commit |
| `gitmap log --limit 10` | Ve el historial reciente |
| `gitmap show HEAD` | Inspecciona un commit |
| `gitmap merge <BRANCH>` | Fusiona una rama de funcionalidad en la rama actual |
| `gitmap push` | Publica la rama actual de vuelta en ArcGIS |
| `gitmap revert <COMMIT>` | Restaura un commit anterior sin reescribir el historial |
| `gitmap setup-repos` | Clona muchos mapas de forma masiva |
| `gitmap auto-pull` | Sincroniza muchos repositorios según un horario |
| `gitmap context show` | Visualiza el historial de eventos del repositorio |

Ejecute `gitmap COMMAND --help` para ver las opciones y ejemplos específicos de cada comando.

## Configuración

GitMap admite varias formas de proporcionar credenciales y ajustes de repositorio.

### Variables de entorno

| Variable | Descripción |
|---|---|
| `PORTAL_URL` | URL de ArcGIS Online o Portal |
| `PORTAL_USER` | Nombre de usuario del Portal |
| `PORTAL_PASSWORD` | Contraseña del Portal |
| `ARCGIS_USERNAME` | Variable de nombre de usuario alternativa |
| `ARCGIS_PASSWORD` | Variable de contraseña alternativa |

Las opciones de línea de comandos como `--url` y `--username` tienen prioridad cuando un comando las admite.

### Configuración del repositorio

Cada repositorio almacena los metadatos de GitMap en `.gitmap/config.json`.

```json
{
  "version": "1.0",
  "user_name": "Jane Smith",
  "user_email": "jane@example.com",
  "project_name": "FloodRisk",
  "remote": {
    "name": "origin",
    "url": "https://www.arcgis.com",
    "folder_id": "abc123",
    "item_id": "def456"
  }
}
```

## Documentación y soporte

- Sitio de documentación: <https://14-tr.github.io/Git-Map/>
- Guía de instalación: [docs/getting-started/installation.md](docs/getting-started/installation.md)
- Guía de inicio rápido: [docs/getting-started/quickstart.md](docs/getting-started/quickstart.md)
- Conceptos básicos: [docs/getting-started/concepts.md](docs/getting-started/concepts.md)
- Referencia de comandos CLI: [docs/commands/index.md](docs/commands/index.md)
- Guía del Portal: [docs/guides/portals.md](docs/guides/portals.md)
- Guía de flujo de trabajo: [docs/guides/workflow.md](docs/guides/workflow.md)
- Documento técnico: [docs/technical-paper.md](docs/technical-paper.md)
- Incidencias: <https://github.com/14-TR/Git-Map/issues>

## Desarrollo

```bash
git clone https://github.com/14-TR/Git-Map.git
cd Git-Map
/opt/homebrew/bin/python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e "packages/gitmap_core[dev]"
python -m pip install -e apps/cli/gitmap
python -m pytest packages/gitmap_core/tests integrations/openclaw/tests -x -q
```

Distribución del proyecto:

```text
Git-Map/
├── apps/                         # Paquetes de la CLI, MCP y aplicaciones cliente
├── packages/gitmap_core/         # Librería principal y pruebas principales
├── configs/                      # Configuración de ejemplo
├── docs/                         # Contenido del sitio de documentación MkDocs
├── documentation/                # Material interno de diseño/especificaciones
└── integrations/openclaw/tests/  # Pruebas de integración de OpenClaw
```

## Contribución

Las contribuciones son bienvenidas. Si está corrigiendo un error o añadiendo una funcionalidad:

1. cree una rama
2. añada o actualice las pruebas para los cambios de comportamiento
3. mantenga estable el comportamiento de la CLI a menos que el cambio sea intencionado
4. ejecute el conjunto de pruebas antes de abrir un PR
5. abra un PR con una explicación clara y ejemplos de salida cuando sea útil

## Licencia

MIT — vea [LICENSE](LICENSE).

**GitMap** — el git para GIS.
