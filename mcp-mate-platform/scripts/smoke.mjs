/**
 * Smoke test: boots mock ESP32 server with pure English endpoints,
 * initializes MCP server over stdio, and exercises tools.
 */
import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { resolve } from 'node:path';

function createMockEsp32() {
  const state = {
    turn: 'Nahuel',
    isDocked: true,
    delayAlarm: false,
    distance_cm: 8.2,
    mic_amplitude: 42,
    tilt_angle: 0,
    participants: ['Nahuel', 'Santi', 'Flor', 'Mati'],
  };

  const server = createServer((req, res) => {
    const url = new URL(req.url ?? '/', 'http://localhost');
    const sendJson = (code, data) => {
      res.writeHead(code, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(data));
    };

    if (req.method === 'GET' && url.pathname === '/status') {
      return sendJson(200, state);
    }
    if (req.method === 'POST' && url.pathname === '/servo/tilt') {
      const ang = Number(url.searchParams.get('angle') || 45);
      state.tilt_angle = ang;
      return sendJson(200, { status: 'ok', angle: ang });
    }
    if (req.method === 'POST' && url.pathname === '/round/thanks') {
      const nom = url.searchParams.get('name') || state.turn;
      state.participants = state.participants.filter((p) => p !== nom);
      return sendJson(200, { status: 'removed', name: nom });
    }
    if (req.method === 'POST' && url.pathname === '/round/next') {
      return sendJson(200, { status: 'ok', turn: state.turn });
    }
    if (req.method === 'POST' && url.pathname === '/round/config') {
      return sendJson(200, { status: 'ok' });
    }

    res.writeHead(404);
    res.end('Not found');
  });

  return new Promise((resolve) => {
    server.listen(0, '127.0.0.1', () => {
      const port = server.address().port;
      resolve({ server, port, url: `http://127.0.0.1:${port}` });
    });
  });
}

async function main() {
  const mock = await createMockEsp32();
  const serverPath = resolve('dist/index.js');
  const child = spawn(process.execPath, [serverPath], {
    env: { ...process.env, MATE_PLATFORM_URL: mock.url },
    stdio: ['pipe', 'pipe', 'inherit'],
  });

  let buffer = '';
  const responses = new Map();

  child.stdout.on('data', (chunk) => {
    buffer += chunk.toString('utf8');
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';
    for (const line of lines) {
      if (!line.trim()) continue;
      const json = JSON.parse(line);
      if (json.id !== undefined) responses.set(json.id, json);
    }
  });

  let idCounter = 1;
  const send = (method, params) => {
    const id = idCounter++;
    child.stdin.write(JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n');
    return new Promise((res, rej) => {
      const check = setInterval(() => {
        if (responses.has(id)) {
          clearInterval(check);
          res(responses.get(id));
        }
      }, 20);
      setTimeout(() => {
        clearInterval(check);
        rej(new Error(`Timeout waiting for response to ${method}`));
      }, 3000);
    });
  };

  try {
    await send('initialize', {
      protocolVersion: '2024-11-05',
      capabilities: {},
      clientInfo: { name: 'smoke-test', version: '1.0' },
    });

    const toolsRes = await send('tools/list', {});
    const tools = toolsRes.result.tools.map((t) => t.name);
    console.log('[OK] Tools registradas:', tools.join(', '));

    const statusCall = await send('tools/call', { name: 'mate_status', arguments: {} });
    console.log('[OK] mate_status respuesta:', statusCall.result.content[0].text);

    console.log('Smoke test completado con éxito!');
  } finally {
    child.kill();
    mock.server.close();
  }
}

main().catch((err) => {
  console.error('Smoke test fallo:', err);
  process.exit(1);
});
