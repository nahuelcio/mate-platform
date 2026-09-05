/**
 * Configuration module for mate-platform MCP Server.
 */

export const DEFAULT_BASE_URL = 'http://localhost:8180';

export function resolveBaseUrl(): string {
  const fromEnv =
    process.env.MATE_PLATFORM_URL?.trim() ||
    process.env.YMATE_BASE_URL?.trim() ||
    process.env.ESP32_URL?.trim() ||
    '';
  if (fromEnv) {
    return fromEnv.replace(/\/+$/, '');
  }
  return DEFAULT_BASE_URL;
}

export const BASE_URL = resolveBaseUrl();

export interface Participant {
  name: string;
  isCurrentTurn: boolean;
}

export interface MateStatus {
  turn: string;
  isDocked: boolean;
  delayAlarm: boolean;
  distance_cm: number;
  participants: string[];
  mic_amplitude?: number;
  tilt_angle?: number;
  accel_x?: number;
  accel_y?: number;
  accel_z?: number;
  [key: string]: unknown;
}

export function formatStatusSpanish(s: MateStatus): string {
  const estado = s.delayAlarm
    ? '¡ALARMA! Se colgaron con el mate'
    : s.isDocked
      ? 'apoyado en la base (disponible)'
      : 'en mano (alguien está tomando)';
  return `Turno de: ${s.turn} | Estado: ${estado} | Distancia: ${s.distance_cm} cm`;
}
