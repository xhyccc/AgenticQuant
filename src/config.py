"""
System Configuration
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Config:
    """System configuration"""
    
    # LLM Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    
    # SiliconFlow Configuration
    SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY", "")
    SILICONFLOW_API_ENDPOINT = os.getenv("SILICONFLOW_API_ENDPOINT", "https://api.siliconflow.cn/v1/chat/completions")
    SILICONFLOW_MODEL = os.getenv("SILICONFLOW_MODEL", "deepseek-ai/DeepSeek-V3.1-Terminus")
    
    DEFAULT_LLM_PROVIDER = os.getenv("DEFAULT_LLM_PROVIDER", "siliconflow")
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "deepseek-ai/DeepSeek-V3.1-Terminus")
    CODE_LLM_PROVIDER = os.getenv("CODE_LLM_PROVIDER", DEFAULT_LLM_PROVIDER)
    CODE_LLM_MODEL = os.getenv("CODE_LLM_MODEL", DEFAULT_MODEL)
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096"))
    LLM_CODE_MAX_TOKENS = int(os.getenv("LLM_CODE_MAX_TOKENS", "2048"))
    
    # Server Configuration
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    
    # Workspace Configuration
    BASE_DIR = Path(__file__).parent.parent
    WORKSPACE_ROOT = Path(os.getenv("WORKSPACE_ROOT", BASE_DIR / "workspaces"))
    WORKSPACE_ROOT.mkdir(exist_ok=True)
    
    # Sandbox Configuration
    SANDBOX_TIMEOUT = int(os.getenv("SANDBOX_TIMEOUT", 300))
    SANDBOX_MAX_MEMORY_MB = int(os.getenv("SANDBOX_MAX_MEMORY_MB", 2048))
    SANDBOX_MAX_CPU_PERCENT = int(os.getenv("SANDBOX_MAX_CPU_PERCENT", 80))
    SANDBOX_PYTHON_EXECUTABLE = os.getenv("SANDBOX_PYTHON_EXECUTABLE", sys.executable)
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production")
    
    # Strategy Refinement
    MAX_REFINEMENT_ITERATIONS = 3
    
    # Agent Prompts Directory
    PROMPTS_DIR = BASE_DIR / "src" / "prompts"
    PROMPTS_DIR.mkdir(exist_ok=True)
    
    def get_api_key(self, provider: str) -> str:
        """Get API key for specified provider"""
        if provider == "openai":
            return self.OPENAI_API_KEY
        elif provider == "anthropic":
            return self.ANTHROPIC_API_KEY
        elif provider == "siliconflow":
            return self.SILICONFLOW_API_KEY
        else:
            raise ValueError(f"Unknown provider: {provider}")


config = Config()
