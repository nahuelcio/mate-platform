#!/usr/bin/env node
/**
 * Mock del webserver del ESP32 yMate para desarrollo y tests.
 * Replica el comportamiento de /Proyectos/esp32/src/main.cpp:
 *   - /status            GET  -> JSON de estado
 *   - /ronda/config      POST -> body JSON { nombres: [...] }
 *   - /ronda/gracias     POST -> lee "nombre" del query (igual que server.arg())
 *   - /servo/mover       POST/GET -> lee "angulo" del query (igual que server.arg())
 *
 * Uso:  npm run mock        (escucha en http://localhost:8180)
 *       PORT=9999 npm run mock
 */

import { createServer } from 'node:http';

const PORT = Number(process.env.PORT ?? 8180);

// --- Estado espejo del firmware ---
let participantes = ['Nahuel', 'Santi', 'Flor', 'Mati'];
let turnoActual = 0;
let mateEnBase = true;
let alertaActiva = false;
let tiempoLevantado = 0;
let angulo = 0;
const TIEMPO_LIMITE_MS = 15000;

function avanzarTurno() {
  if (participantes.length === 0) return;
  turnoActual = (turnoActual + 1) % participantes.length;
}

function sacarParticipante(nombre) {
  const idx = participantes.findIndex(
    (n) => n.toLowerCase() === nombre.toLowerCase(),
  );
  if (idx === -1) return;
  participantes.splice(idx, 1);
  if (turnoActual >= participantes.length) turnoActual = 0;
}

function send(res, code, obj) {
  const body = typeof obj === 'string' ? obj : JSON.stringify(obj);
  res.writeHead(code, { 'Content-Type': 'application/json' });
  res.end(body);
}

function readQuery(url) {
  return new URL(url, `http://localhost:${PORT}`).searchParams;
}

async function readBody(req) {
  const chunks = [];
  for await (const c of req) chunks.push(c);
  return Buffer.concat(chunks).toString('utf8');
}

const server = createServer(async (req, res) => {
  const url = new URL(req.url ?? '/', `http://localhost:${PORT}`);
  const path = url.pathname;
  const query = url.searchParams;

  if (req.method === 'GET' && path === '/status') {
    const status = {
      turno: participantes[turnoActual] ?? 'Nadie',
      mateEnBase,
      alertaDemora: alertaActiva,
      distancia_cm: mateEnBase ? 8.2 : 3.1,
      mic_amplitud: 120,
      sg90_angulo: angulo,
      participantes,
    };
    send(res, 200, status);
    return;
  }

  if (req.method === 'POST' && path === '/ronda/config') {
    const body = await readBody(req);
    try {
      const { nombres } = JSON.parse(body);
      participantes = Array.isArray(nombres) ? nombres.map(String) : [];
      turnoActual = 0;
      send(res, 200, { status: 'ok' });
    } catch {
      send(res, 400, { error: 'JSON Invalido' });
    }
    return;
  }

  if (req.method === 'POST' && path === '/ronda/gracias') {
    // Igual que server.arg("nombre") en el firmware: el query tiene prioridad.
    const nombre = query.get('nombre') ?? participantes[turnoActual];
    if (nombre) sacarParticipante(nombre);
    send(res, 200, { status: 'eliminado', nombre });
    return;
  }

  if ((req.method === 'POST' || req.method === 'GET') && path === '/servo/mover') {
    const raw = query.get('angulo');
    const ang = raw ? Number(raw) : 45;
    angulo = Math.max(0, Math.min(90, Number.isFinite(ang) ? ang : 45));
    send(res, 200, { status: 'ok', angulo });
    return;
  }

  send(res, 404, { error: `No existe ${path}` });
});

// Simulación del lazo del firmware: el mate vuelve a la base y avanza el turno
setInterval(() => {
  if (!mateEnBase && Date.now() - tiempoLevantado > TIEMPO_LIMITE_MS) {
    alertaActiva = true;
  }
  if (Math.random() < 0.004) {
    // El botón de base cambia solo (para probar detección de eventos)
    if (mateEnBase) {
      mateEnBase = false;
      tiempoLevantado = Date.now();
      alertaActiva = false;
      angulo = 45;
    } else {
      mateEnBase = true;
      alertaActiva = false;
      angulo = 0;
      avanzarTurno();
    }
  }
}, 500);

server.listen(PORT, () => {
  console.log(`[mock-ymate] ESP32 simulado en http://localhost:${PORT}`);
  console.log(`[mock-ymate] Participantes: ${participantes.join(', ')}`);
});
