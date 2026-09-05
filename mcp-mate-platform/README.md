# mcp-ymate 🧉

Servidor **MCP** para que **Claude Code** (y Claude Desktop) controlen el **ESP32 yMate** — el mate con ronda automática, sensor de apoyo, servo de cebado y alerta de demora.

Habla con el webserver del ESP32 (proyecto en `../esp32`, simulado con Wokwi):

| Endpoint del ESP32 | Uso |
|---|---|
| `GET /status` | Estado de la ronda |
| `POST /ronda/config` | Armar ronda: `{ "nombres": [...] }` |
| `POST /ronda/gracias` | Sacar a quien dijo gracias (`?nombre=` o el actual) |
| `POST /servo/mover` | Inclinar el servo (`?angulo=`, 0–90, default 45) |

> Importante: el firmware lee los parámetros con `server.arg()`, que se resuelve
> con el **query string**. Este cliente manda los parámetros por query y además
> repite el body JSON para máxima compatibilidad.

## Requisitos

- Node.js ≥ 18 (probado con Node 26)
- La simulación de Wokwi corriendo con el reenvío `localhost:8180 → target:80`,
  o el ESP32 real en tu red (usá `YMATE_BASE_URL`)

## Instalación

```bash
cd /Users/nahuelcioffi/Proyectos/esp32/mcp-ymate
npm install
npm run build     # genera dist/
```

## Registrarlo en Claude Code

### Opción A: `claude mcp add` (recomendada)

```bash
# Si el ESP32 está simulado en localhost:8180 (Wokwi):
claude mcp add ymate -- node /Users/nahuelcioffi/Proyectos/esp32/mcp-ymate/dist/index.js

# Si el ESP32 real está en tu red:
claude mcp add ymate --env YMATE_BASE_URL=http://192.168.1.50 -- node /Users/nahuelcioffi/Proyectos/esp32/mcp-ymate/dist/index.js

# Alcance: --scope local (solo este proyecto) o --scope user (todos tus proyectos)
```

### Opción B: `.mcp.json` en la raíz del proyecto

```json
{
  "mcpServers": {
    "ymate": {
      "command": "node",
      "args": ["/Users/nahuelcioffi/Proyectos/esp32/mcp-ymate/dist/index.js"],
      "env": { "YMATE_BASE_URL": "http://localhost:8180" }
    }
  }
}
```

### Opción C: config global de Claude Code

```bash
claude mcp add --scope user ymate -- node /Users/nahuelcioffi/Proyectos/esp32/mcp-ymate/dist/index.js
```

### Registrarlo en Claude Desktop

`claude_desktop_config.json` (macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "ymate": {
      "command": "node",
      "args": ["/Users/nahuelcioffi/Proyectos/esp32/mcp-ymate/dist/index.js"],
      "env": { "YMATE_BASE_URL": "http://localhost:8180" }
    }
  }
}
```

Verificá con `claude mcp list` (Claude Code) o reiniciá Claude Desktop.

## Herramientas MCP

| Herramienta | Qué hace |
|---|---|
| `mate_status` | Estado de la ronda: quién tiene el turno, si el mate está apoyado o en mano, alerta de demora, distancia y participantes |
| `mate_cebar` | Inclina el servo (ceba el mate). `{ angulo?: 0–90 }`, default 45 |
| `mate_gracias` | Registra el "gracias" de alguien y lo saca de la ronda. `{ nombre?: string }`, default: el actual |
| `mate_siguiente` | Pasa el turno al siguiente (rota la lista vía `/ronda/config`) |
| `mate_configurar` | Arma una ronda nueva. `{ nombres: string[] }` (máx. 10) |

Después de registrarlo, decile a Claude algo como:

> Usá `mate_status`, pasale el turno a Santi con `mate_siguiente` y cebá con `mate_cebar`.

## Notificador / Pomodoro matero (terminal)

Un proceso aparte que vigila `/status` cada pocos segundos y avisa por consola
cuando alguien levanta el mate, lo devuelve, cambia el turno o salta la alerta
de demora. Con `--pomodoro MIN` recuerda pasar el mate cada `MIN` minutos.

```bash
npm run notify                                  # vigila cada 5 s
npm run notify -- --interval 10 --pomodoro 3 --sound
npm run notify -- --once                        # imprime el estado y sale (útil para hooks)
YMATE_BASE_URL=http://192.168.1.50 npm run notify
```

### Como hook de Claude Code

Para que un agente "matero" vigile la ronda en background, agregá esto a tu
`.claude/settings.json` (o la config de tu proyecto):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash(npm run notify|node .*pomodoro)",
        "hooks": [
          {
            "type": "command",
            "command": "node /Users/nahuelcioffi/Proyectos/esp32/mcp-ymate/dist/pomodoro.js --once"
          }
        ]
      }
    ]
  }
}
```

O simplemente dejalo corriendo en otra pestaña de la terminal con `npm run notify`.

## Desarrollo y verificación

```bash
npm run mock      # mock del ESP32 en http://localhost:8180 (replica main.cpp)
npm run smoke     # test E2E: mock + handshake MCP por stdio + las 5 herramientas
npm run notify -- --once   # prueba el notificador contra el mock
```

La base URL se resuelve así: `YMATE_BASE_URL` → `ESP32_URL` → `http://localhost:8180`.

## Estructura

```
mcp-ymate/
├── src/
│   ├── index.ts       # servidor MCP (stdio) con las 5 herramientas
│   ├── client.ts      # cliente HTTP contra el ESP32 (query + body)
│   ├── config.ts      # resolución de YMATE_BASE_URL y tipos
│   └── pomodoro.ts    # notificador / pomodoro matero en terminal
├── scripts/
│   ├── mock-esp32.js  # mock fiel del firmware para desarrollo
│   └── smoke.mjs      # smoke test end-to-end por stdio
├── package.json
└── tsconfig.json
```

## Solución de problemas

- **"No hay respuesta del ESP32"**: la simulación de Wokwi no está corriendo, o el
  ESP32 real está en otra IP. Ajustá `YMATE_BASE_URL`.
- **No aparecen las herramientas**: reiniciá Claude Code / Claude Desktop después
  de registrar el server, y verificá con `claude mcp list`.
- **El ángulo no cambia con body JSON**: el firmware usa `server.arg()`, que
  prioriza el query string; este cliente siempre manda `?angulo=` también.
