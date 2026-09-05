import { exec } from 'node:child_process';

/**
 * Multi-channel notifier:
 * 1. macOS native banner/notification (AppleScript / osascript)
 * 2. Webhooks: Discord / Slack / Telegram (configured via ENV vars)
 * 3. Terminal sound (afplay)
 */

export interface MateNotificationPayload {
  title: string;
  message: string;
  sound?: boolean;
}

export async function sendDesktopNotification(payload: MateNotificationPayload): Promise<void> {
  const { title, message, sound = true } = payload;

  // macOS Native Banner
  if (process.platform === 'darwin') {
    const escapedTitle = title.replace(/"/g, '\\"');
    const escapedMsg = message.replace(/"/g, '\\"');
    const script = `display notification "${escapedMsg}" with title "${escapedTitle}" sound name "Glass"`;
    exec(`osascript -e '${script}'`);
  }

  // Discord Webhook (set DISCORD_WEBHOOK_URL)
  if (process.env.DISCORD_WEBHOOK_URL) {
    try {
      await fetch(process.env.DISCORD_WEBHOOK_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: `🧉 **${title}**\n${message}`,
        }),
      });
    } catch (err) {
      console.error('[Notifier] Discord webhook error:', err);
    }
  }

  // Slack Webhook (set SLACK_WEBHOOK_URL)
  if (process.env.SLACK_WEBHOOK_URL) {
    try {
      await fetch(process.env.SLACK_WEBHOOK_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: `🧉 *${title}*\n${message}`,
        }),
      });
    } catch (err) {
      console.error('[Notifier] Slack webhook error:', err);
    }
  }

  // Telegram Bot (set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
  if (process.env.TELEGRAM_BOT_TOKEN && process.env.TELEGRAM_CHAT_ID) {
    try {
      const url = `https://api.telegram.org/bot${process.env.TELEGRAM_BOT_TOKEN}/sendMessage`;
      await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chat_id: process.env.TELEGRAM_CHAT_ID,
          text: `🧉 *${title}*\n${message}`,
          parse_mode: 'Markdown',
        }),
      });
    } catch (err) {
      console.error('[Notifier] Telegram error:', err);
    }
  }
}
