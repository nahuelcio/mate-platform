import { BASE_URL, type MateStatus, type Participant } from './config.js';

const TIMEOUT_MS = 4000;

export class MatePlatformError extends Error {
  constructor(
    message: string,
    readonly status?: number,
    readonly body?: string,
  ) {
    super(message);
    this.name = 'MatePlatformError';
  }
}

export class MatePlatformClient {
  constructor(readonly baseUrl: string = BASE_URL) {}

  private async request(
    path: string,
    init?: { method?: string; query?: Record<string, string>; bodyJson?: unknown },
  ): Promise<unknown> {
    const method = init?.method ?? 'GET';
    const url = new URL(`${this.baseUrl}${path}`);

    if (init?.query) {
      for (const [k, v] of Object.entries(init.query)) {
        if (v !== undefined && v !== '') url.searchParams.set(k, v);
      }
    }

    const headers: Record<string, string> = { Accept: 'application/json' };
    let body: string | undefined;
    if (init?.bodyJson !== undefined) {
      body = JSON.stringify(init.bodyJson);
      headers['Content-Type'] = 'application/json';
    }

    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
    let res: Response;
    try {
      res = await fetch(url.toString(), { method, headers, body, signal: ctrl.signal });
    } catch (err) {
      const cause = err instanceof Error ? err.message : String(err);
      throw new MatePlatformError(
        `Sin respuesta del ESP32 en ${this.baseUrl} (${cause}). Revisá que esté prendido o corriendo en Wokwi.`,
      );
    } finally {
      clearTimeout(timer);
    }

    const text = await res.text();
    if (!res.ok) {
      throw new MatePlatformError(
        `El ESP32 respondió ${res.status} en ${path}`,
        res.status,
        text,
      );
    }

    if (text.length === 0) return null;
    try {
      return JSON.parse(text);
    } catch {
      return text;
    }
  }

  async getStatus(): Promise<MateStatus> {
    return (await this.request('/status')) as MateStatus;
  }

  async configureRound(names: string[]): Promise<unknown> {
    return this.request('/round/config', {
      method: 'POST',
      bodyJson: { names },
    });
  }

  async registerThanks(name?: string): Promise<unknown> {
    return this.request('/round/thanks', {
      method: 'POST',
      query: name ? { name } : {},
    });
  }

  async nextTurn(): Promise<unknown> {
    return this.request('/round/next', {
      method: 'POST',
    });
  }

  async tiltServo(angle: number): Promise<unknown> {
    return this.request('/servo/tilt', {
      method: 'POST',
      query: { angle: String(angle) },
    });
  }

  describeParticipants(s: MateStatus): Participant[] {
    return (s.participants ?? []).map((name) => ({
      name,
      isCurrentTurn: name.toLowerCase() === (s.turn ?? '').toLowerCase(),
    }));
  }
}

export const mateClient = new MatePlatformClient();
