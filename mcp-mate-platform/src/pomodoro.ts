#!/usr/bin/env node
/**
 * Monitor en tiempo real y notificador de mate-platform.
 *
 * Canales:
 *   - Notificaciones nativas de macOS
 *   - Canales de chat (Slack, Discord, Telegram)
 *   - Consola con sonidos
 */

import { mateClient } from './client.js';
import type { MateStatus } from './config.js';
import { formatStatusSpanish } from './config.js';
import { sendDesktopNotification } from './notifiers/channels.js';

interface Options {
  intervalS: number;
  pomodoroMin: number;
  sound: boolean;
  notifyDesktop: boolean;
  once: boolean;
  verbose: boolean;
}

function parseArgs(argv: string[]): Options {
  const o: Options = {
    intervalS: 5,
    pomodoroMin: 0,
    sound: false,
    notifyDesktop: true,
    once: false,
    verbose: false,
  };

  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const val = () => {
      const v = argv[++i];
      if (v === undefined) throw new Error(`Falta valor para ${a}`);
      return v;
    };
    switch (a) {
      case '--interval':
        o.intervalS = Math.max(1, Number(val()));
        break;
      case '--pomodoro':
        o.pomodoroMin = Math.max(1, Number(val()));
        break;
      case '--sound':
        o.sound = true;
        break;
      case '--no-desktop':
        o.notifyDesktop = false;
        break;
      case '--once':
        o.once = true;
        break;
      case '--verbose':
        o.verbose = true;
        break;
      case '-h':
      case '--help':
        console.log(
          'Uso: node dist/pomodoro.js [--interval S] [--pomodoro MIN] [--sound] [--no-desktop] [--once]\n' +
            '  --interval S     Segundos entre consultas (default: 5)\n' +
            '  --pomodoro MIN   Aviso de mate estancado cada MIN minutos\n' +
            '  --sound          Sonido de alerta en macOS (afplay)\n' +
            '  --no-desktop     Desactivar alertas de escritorio y webhooks\n' +
            '  --once           Imprimir estado actual y salir\n' +
            'Variables de entorno:\n' +
            '  MATE_PLATFORM_URL   (default http://localhost:8180)\n' +
            '  DISCORD_WEBHOOK_URL (Webhook de canal Discord)\n' +
            '  SLACK_WEBHOOK_URL   (Incoming Webhook de Slack)\n' +
            '  TELEGRAM_BOT_TOKEN & TELEGRAM_CHAT_ID (Bot de Telegram)\n',
        );
        process.exit(0);
        break;
      default:
        throw new Error(`Opcion desconocida: ${a}`);
    }
  }
  return o;
}

function stamp(): string {
  return new Date().toLocaleTimeString('es-AR', { hour12: false });
}

function log(msg: string): void {
  console.log(`[${stamp()}] ${msg}`);
}

interface Tracker {
  lastTurn: string | null;
  lastDocked: boolean | null;
  lastAlarm: boolean | null;
  pomodoroStart: number;
}

async function showCurrentStatus(opts: Options): Promise<void> {
  const st = await mateClient.getStatus();
  log(`Estado: ${formatStatusSpanish(st)}`);
  const participants = mateClient
    .describeParticipants(st)
    .map((p) => `  ${p.isCurrentTurn ? '👉' : ' '} ${p.name}`)
    .join('\n');
  log(`Participantes:\n${participants}`);

  if (opts.notifyDesktop) {
    await sendDesktopNotification({
      title: 'Estado del Mate 🧉',
      message: `Turno: ${st.turn} | ${st.isDocked ? 'En la base' : 'Tomando'}`,
    });
  }
}

async function watch(opts: Options): Promise<never> {
  const t: Tracker = {
    lastTurn: null,
    lastDocked: null,
    lastAlarm: null,
    pomodoroStart: Date.now(),
  };

  log(`Monitoreando mate-platform en ${mateClient.baseUrl} cada ${opts.intervalS}s... (Ctrl+C para salir)`);

  while (true) {
    try {
      const st = await mateClient.getStatus();

      // Primer chequeo base
      if (t.lastTurn === null) {
        log(`Estado inicial: ${formatStatusSpanish(st)}`);
        t.lastTurn = st.turn;
        t.lastDocked = st.isDocked;
        t.lastAlarm = st.delayAlarm;
      } else {
        // Evento: Estado de base cambio
        if (t.lastDocked !== st.isDocked) {
          if (!st.isDocked) {
            const msg = `${st.turn} agarro el mate y esta tomando.`;
            log(`[EVENTO] ${msg}`);
            if (opts.notifyDesktop) {
              await sendDesktopNotification({
                title: 'Mate en mano 🧉',
                message: msg,
              });
            }
          } else {
            log(`[EVENTO] Mate devuelto a la base.`);
          }
          t.lastDocked = st.isDocked;
        }

        // Evento: Cambio de turno
        if (t.lastTurn !== st.turn) {
          const msg = `¡Le toca a ${st.turn}! El mate ya esta listo.`;
          log(`[TURNO] Proximo turno: ${st.turn} (Distancia: ${st.distance_cm} cm)`);
          if (opts.notifyDesktop) {
            await sendDesktopNotification({
              title: '¡Te toca el mate! 🧉',
              message: msg,
            });
          }
          t.lastTurn = st.turn;
          t.pomodoroStart = Date.now();
        }

        // Evento: Alarma de mate retenido
        if (!t.lastAlarm && st.delayAlarm) {
          const alertMsg = `⚠️ ¡${st.turn} se durmio con el mate! ¡Larga el mate!`;
          log(`[ALARMA] ${alertMsg}`);
          if (opts.notifyDesktop) {
            await sendDesktopNotification({
              title: '¡ALARMA DEL MATE! ⏰',
              message: alertMsg,
            });
          }
          t.lastAlarm = true;
        } else if (t.lastAlarm && !st.delayAlarm) {
          log(`[ALARMA DESACTIVADA] Mate liberado.`);
          t.lastAlarm = false;
        }
      }

      // Pomodoro matero
      if (opts.pomodoroMin > 0) {
        const elapsedMin = (Date.now() - t.pomodoroStart) / 60000;
        if (elapsedMin >= opts.pomodoroMin) {
          const pomoMsg = `Pasaron ${opts.pomodoroMin} minutos. ¡Hora de hacer circular el mate!`;
          log(`[RECORDATORIO] ${pomoMsg}`);
          if (opts.notifyDesktop) {
            await sendDesktopNotification({
              title: 'Recordatorio Matero 🧉',
              message: pomoMsg,
            });
          }
          t.pomodoroStart = Date.now();
        }
      }
    } catch (err) {
      if (opts.verbose) {
        log(`[AVISO] Error de conexion con el ESP32: ${err instanceof Error ? err.message : String(err)}`);
      }
    }

    await new Promise((resolve) => setTimeout(resolve, opts.intervalS * 1000));
  }
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (opts.once) {
    await showCurrentStatus(opts);
    process.exit(0);
  }
  await watch(opts);
}

main().catch((err) => {
  console.error('[mate-platform-notify] Error:', err);
  process.exit(1);
});
