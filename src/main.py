"""
FastAPI Web Application
Web-based UI for the quantitative analysis system
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
from pathlib import Path
import json

from src.workflow_engine import WorkflowEngine
from src.config import config

app = FastAPI(
    title="AgenticQuant - Multi-Agent Quantitative Analysis System",
    description="Autonomous quantitative finance research powered by multi-agent AI",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize workflow engine
workflow_engine = WorkflowEngine()

# Active sessions
active_sessions: Dict[str, Dict[str, Any]] = {}


# Request/Response Models
class AnalysisRequest(BaseModel):
    request: str
    session_id: Optional[str] = None


class AnalysisResponse(BaseModel):
    session_id: str
    status: str
    message: str


class SessionStatus(BaseModel):
    session_id: str
    status: str
    user_request: str
    plan: Optional[Dict[str, Any]] = None
    files: List[str] = []
    created_at: str
    updated_at: str


# API Endpoints

@app.get("/")
async def root():
    """Serve the main web interface"""
    return HTMLResponse(content=get_html_content(), status_code=200)


@app.post("/api/analyze", response_model=AnalysisResponse)
async def start_analysis(request: AnalysisRequest):
    """Start a new quantitative analysis workflow"""
    try:
        # Start workflow in background
        task = asyncio.create_task(
            workflow_engine.execute_workflow(
                user_request=request.request,
                session_id=request.session_id
            )
        )
        
        # Store session
        session_id = request.session_id or f"session_{len(active_sessions)}"
        active_sessions[session_id] = {
            "task": task,
            "status": "started",
            "request": request.request
        }
        
        return AnalysisResponse(
            session_id=session_id,
            status="started",
            message=f"Analysis workflow started for session {session_id}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions", response_model=List[str])
async def list_sessions():
    """List all analysis sessions"""
    sessions = []
    for session_dir in config.WORKSPACE_ROOT.iterdir():
        if session_dir.is_dir():
            sessions.append(session_dir.name)
    return sorted(sessions, reverse=True)


@app.get("/api/sessions/{session_id}", response_model=SessionStatus)
async def get_session_status(session_id: str):
    """Get status of a specific session"""
    workspace_path = config.WORKSPACE_ROOT / session_id
    
    if not workspace_path.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Read plan if exists
    plan = None
    plan_file = workspace_path / "plan.json"
    if plan_file.exists():
        with open(plan_file, 'r') as f:
            plan = json.load(f)
    
    # List files
    files = []
    for file_path in workspace_path.rglob("*"):
        if file_path.is_file():
            files.append(str(file_path.relative_to(workspace_path)))
    
    # Determine status
    status = "in_progress"
    if (workspace_path / "final_report.md").exists():
        status = "completed"
    elif session_id in active_sessions:
        status = active_sessions[session_id].get("status", "in_progress")
    
    return SessionStatus(
        session_id=session_id,
        status=status,
        user_request=active_sessions.get(session_id, {}).get("request", "Unknown"),
        plan=plan,
        files=files,
        created_at=str(workspace_path.stat().st_ctime),
        updated_at=str(workspace_path.stat().st_mtime)
    )


@app.get("/api/sessions/{session_id}/files/{file_path:path}")
async def get_file(session_id: str, file_path: str):
    """Download a file from a session workspace"""
    workspace_path = config.WORKSPACE_ROOT / session_id
    full_path = workspace_path / file_path
    
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Security check: ensure file is within workspace
    if not str(full_path.resolve()).startswith(str(workspace_path.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return FileResponse(full_path)


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket for real-time updates"""
    await websocket.accept()
    
    try:
        while True:
            # Send status updates
            if session_id in active_sessions:
                status = active_sessions[session_id].get("status")
                await websocket.send_json({
                    "type": "status_update",
                    "session_id": session_id,
                    "status": status
                })
            
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass


def get_html_content() -> str:
    """Get HTML content for the web interface"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AgenticQuant - Multi-Agent Quantitative Analysis</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }
        
        .header h1 {
            font-size: 3em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .main-card {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            margin-bottom: 30px;
        }
        
        .input-section {
            margin-bottom: 30px;
        }
        
        .input-section label {
            display: block;
            font-size: 1.1em;
            font-weight: 600;
            margin-bottom: 10px;
            color: #333;
        }
        
        .input-section textarea {
            width: 100%;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 1em;
            font-family: inherit;
            resize: vertical;
            min-height: 120px;
        }
        
        .input-section textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            font-size: 1.1em;
            font-weight: 600;
            border-radius: 10px;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
        
        .button:active {
            transform: translateY(0);
        }
        
        .button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .sessions-list {
            margin-top: 30px;
        }
        
        .session-item {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 15px;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        .session-item:hover {
            background: #e9ecef;
        }
        
        .session-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .session-id {
            font-weight: 600;
            color: #667eea;
        }
        
        .status-badge {
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
        }
        
        .status-completed {
            background: #d4edda;
            color: #155724;
        }
        
        .status-in-progress {
            background: #fff3cd;
            color: #856404;
        }
        
        .status-failed {
            background: #f8d7da;
            color: #721c24;
        }
        
        .session-request {
            color: #666;
            font-size: 0.95em;
        }
        
        .loading {
            text-align: center;
            padding: 20px;
            color: #667eea;
        }
        
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .examples {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
        }
        
        .examples h3 {
            margin-bottom: 15px;
            color: #333;
        }
        
        .example-item {
            padding: 10px;
            margin-bottom: 10px;
            background: white;
            border-radius: 5px;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        .example-item:hover {
            background: #e9ecef;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AgenticQuant</h1>
            <p>Autonomous Quantitative Finance Research with Multi-Agent AI</p>
        </div>
        
        <div class="main-card">
            <div class="input-section">
                <label for="request">What would you like to analyze?</label>
                <textarea 
                    id="request" 
                    placeholder="e.g., Develop a momentum-based trading strategy for AAPL using Bollinger Bands and RSI indicators. Backtest from 2020 to present and compare against SPY benchmark."
                ></textarea>
            </div>
            
            <button class="button" id="analyzeBtn" onclick="startAnalysis()">
                Start Analysis
            </button>
            
            <div class="examples">
                <h3>Example Requests:</h3>
                <div class="example-item" onclick="useExample(this)">
                    Develop a mean reversion strategy for tech stocks (AAPL, MSFT, GOOGL) using Bollinger Bands
                </div>
                <div class="example-item" onclick="useExample(this)">
                    Create a momentum trading strategy for SPY using moving average crossovers and backtest over the last 3 years
                </div>
                <div class="example-item" onclick="useExample(this)">
                    Design a pairs trading strategy for TSLA and F (Ford), analyze correlation and implement statistical arbitrage
                </div>
            </div>
        </div>
        
        <div class="main-card">
            <h2 style="margin-bottom: 20px;">Analysis Sessions</h2>
            <div id="sessionsList">
                <div class="loading">
                    <div class="spinner"></div>
                    <p style="margin-top: 10px;">Loading sessions...</p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        async function startAnalysis() {
            const request = document.getElementById('request').value.trim();
            if (!request) {
                alert('Please enter an analysis request');
                return;
            }
            
            const btn = document.getElementById('analyzeBtn');
            btn.disabled = true;
            btn.textContent = 'Starting...';
            
            try {
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({request})
                });
                
                const data = await response.json();
                alert(`Analysis started! Session ID: ${data.session_id}`);
                loadSessions();
            } catch (error) {
                alert('Error starting analysis: ' + error.message);
            } finally {
                btn.disabled = false;
                btn.textContent = 'Start Analysis';
            }
        }
        
        async function loadSessions() {
            const container = document.getElementById('sessionsList');
            
            try {
                const response = await fetch('/api/sessions');
                const sessions = await response.json();
                
                if (sessions.length === 0) {
                    container.innerHTML = '<p style="text-align:center;color:#999;">No sessions yet. Start your first analysis above!</p>';
                    return;
                }
                
                container.innerHTML = '';
                
                for (const sessionId of sessions) {
                    const statusResponse = await fetch(`/api/sessions/${sessionId}`);
                    const status = await statusResponse.json();
                    
                    const item = document.createElement('div');
                    item.className = 'session-item';
                    item.onclick = () => window.open(`/api/sessions/${sessionId}/files/final_report.md`, '_blank');
                    
                    const statusClass = status.status === 'completed' ? 'status-completed' :
                                       status.status === 'failed' ? 'status-failed' : 'status-in-progress';
                    
                    item.innerHTML = `
                        <div class="session-header">
                            <span class="session-id">${sessionId}</span>
                            <span class="status-badge ${statusClass}">${status.status}</span>
                        </div>
                        <div class="session-request">${status.user_request}</div>
                        <div style="margin-top:10px;font-size:0.85em;color:#999;">
                            ${status.files.length} files | ${status.plan ? status.plan.steps.length + ' steps' : 'No plan'}
                        </div>
                    `;
                    
                    container.appendChild(item);
                }
            } catch (error) {
                container.innerHTML = '<p style="text-align:center;color:#dc3545;">Error loading sessions</p>';
            }
        }
        
        function useExample(element) {
            document.getElementById('request').value = element.textContent.trim();
        }
        
        // Load sessions on page load
        loadSessions();
        
        // Auto-refresh sessions every 5 seconds
        setInterval(loadSessions, 5000);
    </script>
</body>
</html>
    """


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=True
    )
