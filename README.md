# mate-platform 🧉

IoT platform for smart mate sharing sessions powered by ESP32, embedded sensors, web server API, and MCP notification agent for Claude Code and chat channels.

---

## Overview

`mate-platform` automates round management for drinking mate:
- **Automatic turn passing:** When the mate is picked up from the dock base, a timer starts. Once placed back on the dock, the round advances automatically to the next person.
- **Hold alarm:** If a participant retains the mate longer than the allowed duration, an acoustic alarm sounds through the buzzer and displays a warning on the OLED screen.
- **Automated tilt mechanism:** An SG90 micro-servo tilts the base to 45° to assist with water pouring and herbal infusion positioning.
- **Voice integration ("Thanks" detection):** When someone says *"gracias"*, they leave the round, and the turn advances.
- **Notifications & Chat:** Multi-channel notification watcher (macOS native banners, Discord, Slack, Telegram) and Model Context Protocol (MCP) server for Claude Code.

---

## Hardware Components & Pinout

ESP32 DOIT 30-PIN Dev Board configuration:

| Component | Function | ESP32 Pins | Protocol / Mode |
| :--- | :--- | :--- | :--- |
| **SSD1306 (0.96" OLED)** | Turn display, timer & alert banner | `SDA: GPIO 21`, `SCL: GPIO 22` | I2C (`0x3C`) |
| **GY-521 (MPU6050)** | Accelerometer & gyro for tilt detection | `SDA: GPIO 21`, `SCL: GPIO 22` | I2C (`0x68`) |
| **SG90 Micro Servo** | Automatic 45° tilt mechanism | `PWM: GPIO 13`, `VIN (5V)`, `GND` | PWM |
| **HC-SR04** | Ultrasonic proximity sensor | `TRIG: GPIO 5`, `ECHO: GPIO 18` | Digital I/O |
| **GY-MAX9814** | Microphone with automatic gain | `OUT: GPIO 35` (ADC1), `3V3`, `GND` | Analog (ADC1 safe with Wi-Fi) |
| **Active Buzzer** | Acoustic anti-delay alarm | `GPIO 19`, `GND` | Digital / PWM `tone()` |
| **Base Dock Switch** | Mate present / lifted detection | `GPIO 4`, `GND` | Digital In (`INPUT_PULLUP`) |

---

## REST API (ESP32 Web Server)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/status` | Returns round status, current turn, dock state, distance, and participant list |
| `POST` | `/round/config` | Sets participant names: `{"names": ["Nahuel", "Santi", "Flor"]}` |
| `POST` | `/round/thanks` | Removes participant who said thanks: `?name=Nahuel` |
| `POST` | `/round/next` | Manually advances to the next turn |
| `POST` | `/servo/tilt` | Adjusts SG90 tilt angle: `?angle=45` |

---

## Claude Code MCP Integration (`mcp-mate-platform`)

The included MCP server exposes tools directly to Claude Code.

### Available Tools:
1. `mate_status`: Consultar estado del mate y a quién le toca.
2. `mate_tilt_pour`: Inclinar el mate a 45° con el servo para cebar.
3. `mate_thanks`: Registrar que alguien dijo "gracias" y retirarlo de la ronda.
4. `mate_next`: Pasar el turno manualmente.
5. `mate_configure`: Configurar la lista de personas de la ronda.

### Registering with Claude Code:

```bash
claude mcp add mate-platform -- node /path/to/mate-platform/mcp-mate-platform/dist/index.js
```

For real hardware over local Wi-Fi, specify the target IP:
```bash
claude mcp add mate-platform -- node /path/to/mate-platform/mcp-mate-platform/dist/index.js --env MATE_PLATFORM_URL=http://192.168.1.50
```

### Notifications & Chat Watcher (macOS, Discord, Slack, Telegram):

Run in a background terminal:
```bash
cd mcp-mate-platform

# With optional Chat Webhooks:
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."

npm run notify -- --sound --pomodoro 3
```

---

## Simulation with Wokwi

1. Open `diagram.json` in VS Code.
2. Press `F1` / `Cmd + Shift + P` and select **`Wokwi: Start Simulator`**.
3. Ports are forwarded automatically to `http://localhost:8180`.

---

## License

MIT
