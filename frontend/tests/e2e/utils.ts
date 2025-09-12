import crypto from 'node:crypto';

export function base64url(input: Buffer | string): string {
  const b = Buffer.isBuffer(input) ? input : Buffer.from(input);
  return b.toString('base64').replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
}

export function signHS256(data: string, secret: string): string {
  const mac = crypto.createHmac('sha256', secret).update(data).digest();
  return base64url(mac);
}

export function makeHS256(sub: string, secret: string): string {
  const header = base64url(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const payload = base64url(JSON.stringify({ sub }));
  const signingInput = `${header}.${payload}`;
  const sig = signHS256(signingInput, secret);
  return `${signingInput}.${sig}`;
}

