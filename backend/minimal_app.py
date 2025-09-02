#!/usr/bin/env python3
"""Minimal FastAPI app for Railway debugging"""

from fastapi import FastAPI
import os

app = FastAPI(title="Minimal Test App")

@app.get("/")
async def root():
    return {
        "message": "Minimal FastAPI app is working!",
        "port": os.environ.get("PORT", "unknown"),
        "status": "success"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)