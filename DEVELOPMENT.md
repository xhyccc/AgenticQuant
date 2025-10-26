# Development Notes

## Current Status

✅ **Completed:**
- Core MCP protocol implementation
- All tool implementations
- All agent implementations (6 agents)
- ReAct framework for agents
- Workflow orchestration engine
- Web-based UI with FastAPI
- Complete file-based state management
- Strategy refinement loop (3 iterations)
- Documentation (README, QUICKSTART, ARCHITECTURE)

⚠️ **Known Limitations:**

1. **Sandbox Security**: Current implementation uses subprocess execution. For production:
   - Implement Docker containerization
   - Add gVisor for enhanced isolation
   - Set strict resource limits
   - Consider managed solutions (E2B, Vertex AI)

2. **Error Handling**: Basic error handling implemented. Could be enhanced with:
   - Retry logic with exponential backoff
   - Circuit breakers for external APIs
   - Graceful degradation
   - Better error messages for users

3. **Performance**: Sequential execution. Future improvements:
   - Parallel tool execution where possible
   - Caching of LLM responses
   - Streaming responses to UI
   - Background job queue

4. **Testing**: Basic test suite provided. Need:
   - More comprehensive unit tests
   - Integration tests for full workflows
   - Performance benchmarks
   - Security penetration tests

## Development Setup

```bash
# Install dev dependencies
pip install pytest pytest-asyncio black flake8 mypy

# Run tests
pytest test_system.py -v

# Format code
black src/

# Lint
flake8 src/

# Type check
mypy src/
```

## Adding New Features

### New Tool

1. Create `src/tools/my_tool.py`:
```python
from src.tools.base import BaseTool
from src.mcp.protocol import ToolDefinition, ToolParameter

class MyTool(BaseTool):
    def get_definition(self):
        return ToolDefinition(...)
    
    async def execute(self, **kwargs):
        # Implementation
        return result
```

2. Register in `src/tools/__init__.py`:
```python
from src.tools.my_tool import MyTool

# In ToolRegistry._initialize_tools()
self.tools["my_tool"] = MyTool(self.workspace_root)
```

3. Add to agent mappings in `get_tools_for_agent()`

### New Agent

1. Create `src/agents/my_agent.py`:
```python
from src.agents.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def get_system_prompt(self):
        return "Agent instructions..."
    
    def get_available_tools(self):
        return ["tool1", "tool2"]
```

2. Use in workflow:
```python
my_agent = MyAgent(...)
result = await my_agent.execute_task(task)
```

### New LLM Provider

1. Add to `src/llm_client.py`:
```python
elif self.provider == "my_provider":
    # Implementation
```

2. Update config and .env

## Production Deployment

### Docker Deployment

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ src/
COPY main.py .

EXPOSE 8000
CMD ["python", "main.py"]
```

Build and run:
```bash
docker build -t agenticquant .
docker run -p 8000:8000 -v $(pwd)/workspaces:/app/workspaces agenticquant
```

### Kubernetes Deployment

See `k8s/` directory for manifests (to be created).

### Environment Variables for Production

```bash
# Required
OPENAI_API_KEY=...
SECRET_KEY=...  # Generate with: openssl rand -hex 32

# Optional but recommended
DATABASE_URL=postgresql://...  # If using database instead of files
REDIS_URL=redis://...  # For caching and job queue
SENTRY_DSN=...  # For error tracking
LOG_LEVEL=INFO
```

### Monitoring

Recommended tools:
- **Logging**: Structlog, Sentry
- **Metrics**: Prometheus + Grafana
- **Tracing**: Jaeger, OpenTelemetry
- **APM**: DataDog, New Relic

### Security Checklist

- [ ] Use environment variables for secrets
- [ ] Enable HTTPS/TLS
- [ ] Implement authentication (OAuth2, JWT)
- [ ] Add rate limiting
- [ ] Use security headers (CORS, CSP)
- [ ] Regular dependency updates
- [ ] Security scanning (Snyk, Dependabot)
- [ ] Penetration testing
- [ ] Audit logging
- [ ] Data encryption at rest

## Roadmap

**v1.1 (Next):**
- [ ] Database integration (PostgreSQL)
- [ ] User authentication
- [ ] Improved error handling
- [ ] Streaming UI updates
- [ ] Docker sandbox implementation

**v1.2:**
- [ ] Multiple strategy comparison
- [ ] Portfolio optimization
- [ ] Walk-forward analysis
- [ ] Monte Carlo simulations
- [ ] Risk factor analysis

**v2.0:**
- [ ] Live trading integration (paper trading)
- [ ] Real-time market data
- [ ] Alert system
- [ ] Mobile app
- [ ] Collaborative features

## Contributing Guidelines

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Make changes with tests
4. Format: `black src/`
5. Test: `pytest`
6. Commit: `git commit -m "Add my feature"`
7. Push: `git push origin feature/my-feature`
8. Create Pull Request

## Debugging Tips

**Agent not calling tools:**
- Check system prompt includes tool instructions
- Verify tools are registered for that agent type
- Check LLM temperature (lower = more deterministic)
- Review message history for context issues

**Sandbox execution fails:**
- Check Python version compatibility
- Verify working directory permissions
- Review timeout settings
- Check subprocess creation limits

**LLM API errors:**
- Verify API key in .env
- Check rate limits
- Review token limits for model
- Try different model if needed

**UI not updating:**
- Check WebSocket connection
- Review browser console for errors
- Verify session ID matches
- Refresh and retry

## Performance Tips

1. **Use appropriate model sizes:**
   - Planning: GPT-4 (better reasoning)
   - Execution: GPT-3.5 (faster, cheaper)
   - Writing: GPT-4 (better synthesis)

2. **Parallel execution:**
   - Multiple tool calls in single agent turn
   - Batch similar operations
   - Use async/await effectively

3. **Caching:**
   - Cache web search results
   - Cache downloaded financial data
   - Cache LLM responses (with semantic similarity)

4. **Optimize prompts:**
   - Be specific and concise
   - Provide clear examples
   - Use structured output formats
   - Minimize unnecessary context

## Support & Community

- GitHub Issues: Bug reports and feature requests
- Discussions: Questions and ideas
- Wiki: Extended documentation
- Discord: Real-time chat (TBD)

---

**Last Updated:** October 20, 2025
