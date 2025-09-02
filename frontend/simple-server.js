import { createServer } from 'http';
import { readFileSync, existsSync } from 'fs';
import { join, extname } from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const PORT = process.env.PORT || 3000;
const DIST_DIR = join(__dirname, 'dist');

const mimeTypes = {
  '.html': 'text/html',
  '.js': 'application/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon'
};

const server = createServer((req, res) => {
  console.log(`${req.method} ${req.url}`);

  // Health check
  if (req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', timestamp: new Date().toISOString() }));
    return;
  }

  // Check if dist directory exists
  if (!existsSync(DIST_DIR)) {
    console.error(`ERROR: dist directory not found at ${DIST_DIR}`);
    res.writeHead(500);
    res.end('Build directory not found. Did the build complete?');
    return;
  }

  // Default to index.html for SPA routing
  let filePath = join(DIST_DIR, req.url === '/' ? 'index.html' : req.url);
  
  // If file doesn't exist and no extension, serve index.html (SPA routing)
  if (!existsSync(filePath) && !extname(filePath)) {
    filePath = join(DIST_DIR, 'index.html');
  }

  // Check if file exists
  if (!existsSync(filePath)) {
    res.writeHead(404);
    res.end('Not found');
    return;
  }

  // Read and serve file
  try {
    const content = readFileSync(filePath);
    const ext = extname(filePath);
    const contentType = mimeTypes[ext] || 'application/octet-stream';
    
    res.writeHead(200, { 
      'Content-Type': contentType,
      'Access-Control-Allow-Origin': '*'
    });
    res.end(content);
  } catch (error) {
    console.error('Error serving file:', error);
    res.writeHead(500);
    res.end('Internal server error');
  }
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`🚀 Simple server running on http://0.0.0.0:${PORT}`);
  console.log(`📁 Serving files from: ${DIST_DIR}`);
  console.log(`🏠 Environment: ${process.env.NODE_ENV || 'development'}`);
  
  // Check if dist exists and what's in it
  if (existsSync(DIST_DIR)) {
    const files = require('fs').readdirSync(DIST_DIR);
    console.log(`📂 Files in dist: ${files.join(', ')}`);
    
    // Check for index.html specifically
    if (existsSync(join(DIST_DIR, 'index.html'))) {
      console.log('✅ index.html found');
    } else {
      console.log('❌ index.html NOT found');
    }
  } else {
    console.log('❌ dist directory does NOT exist!');
  }
});