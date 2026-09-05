import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';
import { mateClient } from './client.js';

const server = new McpServer({
  name: 'mate-platform',
  version: '1.0.0',
});

// ---------------------------------------------------------------------------
// Tool: mate_status
// ---------------------------------------------------------------------------
server.registerTool(
  'mate_status',
  {
    title: 'Consultar estado del mate',
    description: 'Devuelve quién tiene el turno de la ronda, si el mate está apoyado o en mano, alerta de demora y distancia.',
    inputSchema: z.object({}),
  },
  async () => {
    try {
      const st = await mateClient.getStatus();
      const list = mateClient
        .describeParticipants(st)
        .map((p) => `- ${p.isCurrentTurn ? '👉 TURNO ACTUAL:' : ' '} ${p.name}`)
        .join('\n');

      const text = [
        `Turno actual: ${st.turn}`,
        `Estado del mate: ${st.isDocked ? 'Apoyado en la base (disponible)' : 'En mano (tomando)'}`,
        `Alerta de demora: ${st.delayAlarm ? '¡SÍ, SE COLGARON! ⏰' : 'No'}`,
        `Distancia sensor: ${st.distance_cm} cm`,
        `Ronda (${st.participants.length} participantes):`,
        list || '  (sin participantes)',
      ].join('\n');

      return { content: [{ type: 'text', text }] };
    } catch (err) {
      return {
        isError: true,
        content: [{ type: 'text', text: err instanceof Error ? err.message : String(err) }],
      };
    }
  },
);

// ---------------------------------------------------------------------------
// Tool: mate_tilt_pour
// ---------------------------------------------------------------------------
server.registerTool(
  'mate_tilt_pour',
  {
    title: 'Inclinar mate para cebar',
    description: 'Mueve el microservo SG90 a 45 grados (o el ángulo indicado) para cebar el mate.',
    inputSchema: z.object({
      angle: z
        .number()
        .int()
        .min(0)
        .max(90)
        .optional()
        .describe('Ángulo en grados (0-90). Por defecto: 45.'),
    }),
  },
  async ({ angle }) => {
    try {
      const target = angle ?? 45;
      await mateClient.tiltServo(target);
      return {
        content: [{ type: 'text', text: `Mate inclinado a ${target}° para cebar.` }],
      };
    } catch (err) {
      return {
        isError: true,
        content: [{ type: 'text', text: err instanceof Error ? err.message : String(err) }],
      };
    }
  },
);

// ---------------------------------------------------------------------------
// Tool: mate_thanks
// ---------------------------------------------------------------------------
server.registerTool(
  'mate_thanks',
  {
    title: 'Alguien dijo gracias',
    description: 'Registra que una persona dijo "gracias" y la saca de la ronda de mate.',
    inputSchema: z.object({
      name: z
        .string()
        .optional()
        .describe('Nombre de la persona que se retira. Si se omite, saca al del turno actual.'),
    }),
  },
  async ({ name }) => {
    try {
      const res = (await mateClient.registerThanks(name)) as { name?: string };
      const removed = res?.name ?? name ?? 'participante actual';
      const st = await mateClient.getStatus();
      return {
        content: [
          {
            type: 'text',
            text: `¡${removed} dijo gracias y se fue de la ronda! Quedan ${st.participants.length} personas. Le toca a: ${st.turn}.`,
          },
        ],
      };
    } catch (err) {
      return {
        isError: true,
        content: [{ type: 'text', text: err instanceof Error ? err.message : String(err) }],
      };
    }
  },
);

// ---------------------------------------------------------------------------
// Tool: mate_next
// ---------------------------------------------------------------------------
server.registerTool(
  'mate_next',
  {
    title: 'Pasar turno',
    description: 'Avanza manualmente al siguiente participante de la ronda.',
    inputSchema: z.object({}),
  },
  async () => {
    try {
      await mateClient.nextTurn();
      const st = await mateClient.getStatus();
      return {
        content: [{ type: 'text', text: `Turno pasado. ¡Ahora le toca a ${st.turn}!` }],
      };
    } catch (err) {
      return {
        isError: true,
        content: [{ type: 'text', text: err instanceof Error ? err.message : String(err) }],
      };
    }
  },
);

// ---------------------------------------------------------------------------
// Tool: mate_configure
// ---------------------------------------------------------------------------
server.registerTool(
  'mate_configure',
  {
    title: 'Configurar ronda',
    description: 'Configura la lista de personas para la ronda de mate.',
    inputSchema: z.object({
      names: z.array(z.string()).min(1).max(10).describe('Lista de nombres de los participantes.'),
    }),
  },
  async ({ names }) => {
    try {
      await mateClient.configureRound(names);
      return {
        content: [{ type: 'text', text: `Ronda armada con ${names.length} personas: ${names.join(', ')}.` }],
      };
    } catch (err) {
      return {
        isError: true,
        content: [{ type: 'text', text: err instanceof Error ? err.message : String(err) }],
      };
    }
  },
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((err) => {
  console.error('[mate-platform-mcp] Error fatal:', err);
  process.exit(1);
});
