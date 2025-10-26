"""
AgenticQuant - Multi-Agent Quantitative Analysis System

Entry point for the application
"""
import uvicorn
from src.config import config

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║              🤖  AgenticQuant  🤖                        ║
    ║                                                           ║
    ║     Autonomous Quantitative Finance Research              ║
    ║     Powered by Multi-Agent AI Systems                     ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    
    Starting server...
    """)
    
    uvicorn.run(
        "src.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=True,
        log_level="info"
    )
