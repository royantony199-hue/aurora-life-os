#!/usr/bin/env python3
"""Simple test server to verify Railway networking"""

import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class TestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print(f"Received request: {self.path}")
        
        if self.path == '/health' or self.path == '/':
            response = {
                "status": "ok",
                "message": "Simple test server is working!",
                "port": os.environ.get('PORT', 'not set'),
                "path": self.path
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not found')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    server = HTTPServer(('0.0.0.0', port), TestHandler)
    print(f"🚀 Simple test server starting on 0.0.0.0:{port}")
    print(f"🌍 PORT environment variable: {os.environ.get('PORT', 'NOT SET')}")
    server.serve_forever()