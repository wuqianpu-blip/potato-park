#!/usr/bin/env python3
"""土豆游乐园 - 静态文件 + 上传服务"""
import http.server
import os, sys, json, base64, shutil

PORT = 8000
ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

class UploadHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path.startswith('/upload'):
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)
                data = json.loads(body.decode('utf-8'))

                filename = data.get('filename', 'unnamed')
                subdir = data.get('subdir', '').strip('/')
                filedata = data.get('data', '')

                if not filedata:
                    self._json_reply(400, {'error': 'empty data'})
                    return

                # strip data URL prefix
                if filedata.startswith('data:'):
                    # data:image/jpeg;base64,xxxx
                    header, encoded = filedata.split(',', 1)
                    # extract extension from mime if available
                    if 'image/' in header:
                        ext = header.split('image/')[1].split(';')[0]
                        if ext == 'jpeg': ext = 'jpg'
                        if not filename.endswith('.' + ext):
                            filename = filename.rsplit('.',1)[0] + '.' + ext if '.' in filename else filename + '.' + ext
                    elif 'audio/' in header:
                        ext = header.split('audio/')[1].split(';')[0]
                        if not filename.endswith('.' + ext):
                            filename = filename.rsplit('.',1)[0] + '.' + ext if '.' in filename else filename + '.' + ext
                else:
                    encoded = filedata

                # decode base64
                try:
                    binary = base64.b64decode(encoded)
                except Exception:
                    self._json_reply(400, {'error': 'invalid base64'})
                    return

                # ensure safe filename
                safe = "".join(c for c in filename if c.isalnum() or c in '._-')
                if not safe: safe = 'file.bin'

                save_dir = os.path.join(ROOT, subdir)
                os.makedirs(save_dir, exist_ok=True)
                filepath = os.path.join(save_dir, safe)

                with open(filepath, 'wb') as f:
                    f.write(binary)

                rel_path = os.path.join(subdir, safe)
                self._json_reply(200, {'ok': True, 'path': rel_path, 'size': len(binary)})

            except Exception as e:
                self._json_reply(500, {'error': str(e)})
        else:
            super().do_POST()

    def _json_reply(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        super().do_GET()

if __name__ == '__main__':
    print(f'🥔 Potato Amusement Park server @ http://0.0.0.0:{PORT}')
    httpd = http.server.HTTPServer(('0.0.0.0', PORT), UploadHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()
