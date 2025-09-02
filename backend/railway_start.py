#!/usr/bin/env python3
import os
import subprocess
import sys

print("=== Railway Startup Debug ===")
print(f"PORT environment variable: {os.environ.get('PORT', 'NOT SET')}")
print(f"All environment variables with PORT: {[(k,v) for k,v in os.environ.items() if 'PORT' in k.upper()]}")
print(f"Python executable: {sys.executable}")
print(f"Working directory: {os.getcwd()}")
print("=============================")

port = os.environ.get('PORT')
if not port:
    print("ERROR: PORT environment variable not set by Railway!")
    print("Using fallback port 8000")
    port = "8000"

print(f"Starting uvicorn on port: {port}")

# Start uvicorn with the correct port
cmd = [
    "uvicorn", 
    "app.main:app", 
    "--host", "0.0.0.0", 
    "--port", str(port)
]

print(f"Executing command: {' '.join(cmd)}")
subprocess.run(cmd)