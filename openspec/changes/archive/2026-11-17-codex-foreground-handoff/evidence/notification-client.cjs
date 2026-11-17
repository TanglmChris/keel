'use strict';
const http = require('node:http');
const crypto = require('node:crypto');
const path = require('node:path');
const os = require('node:os');
const MAX_MESSAGE = 16 * 1024 * 1024;

// The managed daemon speaks WebSocket over a Unix socket, not JSON lines.
function connect(socketPath, timeout = 5000, onNotification = () => {}) {
  return new Promise((resolve, reject) => {
    const key = crypto.randomBytes(16).toString('base64');
    const pending = new Map();
    let socket, opened = false, closed = false, sequence = 0;
    let buffer = Buffer.alloc(0), fragments = [], fragmentSize = 0;
    const request = http.request({socketPath, path: '/', headers: {
      Host: 'localhost', Upgrade: 'websocket', Connection: 'Upgrade',
      'Sec-WebSocket-Key': key, 'Sec-WebSocket-Version': '13',
    }});
    const deadline = setTimeout(() => fail(Error('Codex host connection timeout')), timeout);
    function fail(error) {
      if (closed) return;
      closed = true;
      clearTimeout(deadline);
      for (const entry of pending.values()) {
        clearTimeout(entry.timer);
        entry.reject(error);
      }
      pending.clear();
      if (!opened) reject(error);
      request.destroy();
      if (socket) socket.destroy();
    }
    function send(opcode, body) {
      if (closed) throw Error('Codex host disconnected');
      if (body.length > MAX_MESSAGE) throw Error('Codex request too large');
      const mask = crypto.randomBytes(4);
      const header = Buffer.alloc(body.length < 126 ? 2 : body.length <= 65535 ? 4 : 10);
      header[0] = 128 | opcode;
      if (header.length === 2) header[1] = 128 | body.length;
      else if (header.length === 4) {header[1] = 254; header.writeUInt16BE(body.length, 2);}
      else {header[1] = 255; header.writeBigUInt64BE(BigInt(body.length), 2);}
      const payload = Buffer.from(body);
      for (let i = 0; i < payload.length; i++) payload[i] ^= mask[i % 4];
      socket.write(Buffer.concat([header, mask, payload]));
    }
    function message(body) {
      const value = JSON.parse(body.toString('utf8'));
      if (typeof value.method === 'string') { onNotification(value); return; }
      const entry = pending.get(value.id);
      if (!entry) return; // Notifications are not acknowledgements of pending RPCs.
      pending.delete(value.id);
      clearTimeout(entry.timer);
      if (value.error) entry.reject(Error(value.error.message));
      else entry.resolve(value.result);
    }
    function receive(chunk) {
      buffer = Buffer.concat([buffer, chunk]);
      try {
        while (buffer.length >= 2) {
          const fin = Boolean(buffer[0] & 128), opcode = buffer[0] & 15;
          if ((buffer[0] & 112) || (buffer[1] & 128)) throw Error('Invalid Codex WebSocket frame');
          let length = buffer[1] & 127, offset = 2;
          if (length === 126) {
            if (buffer.length < 4) return;
            length = buffer.readUInt16BE(2); offset = 4;
          } else if (length === 127) {
            if (buffer.length < 10) return;
            const large = buffer.readBigUInt64BE(2);
            if (large > BigInt(MAX_MESSAGE)) throw Error('Codex response too large');
            length = Number(large); offset = 10;
          }
          if (length > MAX_MESSAGE || fragmentSize + length > MAX_MESSAGE) throw Error('Codex response too large');
          if (opcode >= 8 && (!fin || length > 125)) throw Error('Invalid Codex control frame');
          if (buffer.length < offset + length) return;
          const body = buffer.subarray(offset, offset + length);
          buffer = buffer.subarray(offset + length);
          if (opcode === 8) throw Error('Codex host closed connection');
          if (opcode === 9) {send(10, body); continue;}
          if (opcode === 10) continue;
          if (opcode === 1 && !fragments.length) {
            if (fin) message(body);
            else {fragments = [body]; fragmentSize = length;}
          } else if (opcode === 0 && fragments.length) {
            fragments.push(body); fragmentSize += length;
            if (fin) {message(Buffer.concat(fragments)); fragments = []; fragmentSize = 0;}
          } else throw Error('Unsupported Codex WebSocket frame');
        }
      } catch (error) {fail(error);}
    }
    request.on('error', fail);
    request.on('response', response => {response.resume(); fail(Error(`WebSocket upgrade refused: ${response.statusCode}`));});
    request.on('upgrade', (response, peer, head) => {
      socket = peer;
      const expected = crypto.createHash('sha1').update(key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').digest('base64');
      if (response.headers['sec-websocket-accept'] !== expected) return fail(Error('Invalid WebSocket handshake'));
      clearTimeout(deadline);
      socket.on('data', receive);
      socket.on('error', fail);
      socket.on('close', () => fail(Error('Codex host disconnected')));
      opened = true;
      resolve({
        call(method, params, callTimeout = timeout) {
          return new Promise((resolveCall, rejectCall) => {
            if (closed) return rejectCall(Error('Codex host disconnected'));
            const id = ++sequence;
            const timer = setTimeout(() => fail(Error(`Codex ${method} timeout`)), callTimeout);
            pending.set(id, {resolve: resolveCall, reject: rejectCall, timer});
            try {send(1, Buffer.from(JSON.stringify({id, method, params})));}
            catch (error) {fail(error);}
          });
        },
        notify(method, params = {}) {send(1, Buffer.from(JSON.stringify({method, params})));},
        close() {fail(Error('Codex host disconnected'));},
      });
      if (head.length) receive(head);
    });
    request.end();
  });
}

module.exports = {connect};
