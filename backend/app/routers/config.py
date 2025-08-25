from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import subprocess
import sys

router = APIRouter()


class OpenAIConfig(BaseModel):
    openai_api_key: str


@router.post("/openai")
async def configure_openai(config: OpenAIConfig):
    """Configure OpenAI API key"""
    try:
        # Update .env file
        env_path = "/Users/royantony/auroyra life os/.env"
        
        # Read existing .env
        env_lines = []
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                env_lines = f.readlines()
        
        # Update or add OpenAI key
        updated = False
        for i, line in enumerate(env_lines):
            if line.startswith('OPENAI_API_KEY='):
                env_lines[i] = f'OPENAI_API_KEY={config.openai_api_key}\n'
                updated = True
                break
        
        if not updated:
            env_lines.append(f'OPENAI_API_KEY={config.openai_api_key}\n')
        
        # Write back to .env
        with open(env_path, 'w') as f:
            f.writelines(env_lines)
        
        # Update environment variable for current process
        os.environ['OPENAI_API_KEY'] = config.openai_api_key
        
        # Reload OpenAI service if possible
        try:
            from app.services.openai_service import OpenAIService
            # This would ideally reload the singleton instance
        except Exception:
            pass
        
        return {
            "success": True,
            "message": "OpenAI API key configured successfully",
            "api_key_preview": config.openai_api_key[:10] + "..." if config.openai_api_key else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to configure OpenAI: {str(e)}")


@router.get("/status")
async def get_config_status():
    """Get configuration status"""
    return {
        "openai_configured": bool(os.getenv('OPENAI_API_KEY')),
        "google_client_configured": bool(os.getenv('GOOGLE_CLIENT_ID')),
        "database_configured": bool(os.getenv('DATABASE_URL'))
    }