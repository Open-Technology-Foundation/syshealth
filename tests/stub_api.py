#!/usr/bin/env python3
"""Stand-in for the Claude Messages API, for tests/syshealth.bats.

Usage: stub_api.py STATE_DIR

Listens on 127.0.0.1 on a free port, written to STATE_DIR/port. Each POST
is answered according to STATE_DIR/mode (ok, truncated or refusal; ok when
absent), and the request is recorded in STATE_DIR/request: the path, the
headers that matter, whether x-api-key equalled $STUB_KEY (never the key
itself) and the body.
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

STATE = Path(sys.argv[1])
TEXT = '# stubhost: system health\n**Status:** Healthy, stub answer.\n'


def answer(mode: str, model: str) -> dict:
  """The response body for MODE: a thinking block first, as real models send."""
  content = [{'type': 'thinking', 'thinking': 'considering', 'signature': 'sig'}]
  stop = {'ok': 'end_turn', 'truncated': 'max_tokens', 'refusal': 'refusal'}.get(mode, 'end_turn')
  if mode != 'refusal':
    content.append({'type': 'text', 'text': TEXT})
  body = {
    'id': 'msg_stub', 'type': 'message', 'role': 'assistant', 'model': model,
    'content': content, 'stop_reason': stop,
    'usage': {'input_tokens': 1234, 'output_tokens': 56},
  }
  if mode == 'refusal':
    body['stop_details'] = {'type': 'refusal', 'category': 'cyber'}
  return body


class Handler(BaseHTTPRequestHandler):
  def do_POST(self) -> None:
    length = int(self.headers.get('content-length', 0))
    raw = self.rfile.read(length)
    try:
      request = json.loads(raw)
    except ValueError:
      request = None
    record = {
      'path': self.path,
      'anthropic-version': self.headers.get('anthropic-version'),
      'anthropic-beta': self.headers.get('anthropic-beta'),
      'key_ok': self.headers.get('x-api-key') == os.environ.get('STUB_KEY'),
      'body': request,
    }
    (STATE / 'request').write_text(json.dumps(record))
    mode_file = STATE / 'mode'
    mode = mode_file.read_text().strip() if mode_file.exists() else 'ok'
    model = request.get('model', '?') if isinstance(request, dict) else '?'
    reply = json.dumps(answer(mode, model)).encode()
    self.send_response(200)
    self.send_header('content-type', 'application/json')
    self.send_header('content-length', str(len(reply)))
    self.end_headers()
    self.wfile.write(reply)

  def log_message(self, *args) -> None:
    pass


def main() -> None:
  server = HTTPServer(('127.0.0.1', 0), Handler)
  (STATE / 'port').write_text(str(server.server_address[1]))
  server.serve_forever()


if __name__ == '__main__':
  main()
