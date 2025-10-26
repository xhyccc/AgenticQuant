"""
Command-line interface for AgenticQuant.
Allows direct task creation and debugging without the web interface.
"""
import asyncio
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import Config
from src.workflow_engine import WorkflowEngine
from src.llm_client import LLMClient
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class AgenticQuantCLI:
    """Command-line interface for AgenticQuant system."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.config = Config()
        self.engine = WorkflowEngine()
        self.workspaces_dir = Path(__file__).parent / "workspaces"
        self.workspaces_dir.mkdir(exist_ok=True)
        
    def print_banner(self):
        """Print the CLI banner."""
        banner = f"""
{Colors.OKBLUE}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              🤖 AgenticQuant CLI - Debug Mode 🤖              ║
║                                                               ║
║         Multi-Agent Quantitative Analysis System              ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
{Colors.ENDC}

{Colors.OKCYAN}Configuration:{Colors.ENDC}
  • Provider: {Colors.OKGREEN}{self.config.DEFAULT_LLM_PROVIDER}{Colors.ENDC}
  • Model: {Colors.OKGREEN}{self.config.DEFAULT_MODEL}{Colors.ENDC}
  • Workspaces: {Colors.OKGREEN}{self.workspaces_dir}{Colors.ENDC}

{Colors.WARNING}Commands:{Colors.ENDC}
  • Type your analytical request (e.g., "Develop a momentum strategy for AAPL")
  • Type {Colors.BOLD}'help'{Colors.ENDC} for more commands
  • Type {Colors.BOLD}'quit'{Colors.ENDC} or {Colors.BOLD}'exit'{Colors.ENDC} to exit
  • Press {Colors.BOLD}Ctrl+C{Colors.ENDC} to interrupt

{Colors.HEADER}═══════════════════════════════════════════════════════════════{Colors.ENDC}
"""
        print(banner)
    
    def print_help(self):
        """Print help message."""
        help_text = f"""
{Colors.OKBLUE}{Colors.BOLD}Available Commands:{Colors.ENDC}

{Colors.OKCYAN}Analysis Commands:{Colors.ENDC}
  • Just type your request naturally (e.g., "Analyze TSLA with RSI strategy")
  • The system will create a workspace and run the full workflow

{Colors.OKCYAN}System Commands:{Colors.ENDC}
  • {Colors.BOLD}help{Colors.ENDC}           - Show this help message
  • {Colors.BOLD}list{Colors.ENDC}           - List all previous workspaces
  • {Colors.BOLD}status{Colors.ENDC}         - Show current system status
  • {Colors.BOLD}config{Colors.ENDC}         - Show current configuration
  • {Colors.BOLD}clear{Colors.ENDC}          - Clear the screen
  • {Colors.BOLD}quit{Colors.ENDC} / {Colors.BOLD}exit{Colors.ENDC}  - Exit the CLI

{Colors.OKCYAN}Example Requests:{Colors.ENDC}
  1. "Develop a momentum strategy for AAPL using 20-day and 50-day moving averages"
  2. "Create a mean reversion strategy for SPY with Bollinger Bands"
  3. "Analyze TSLA using RSI and MACD indicators for swing trading"
  4. "Build a pairs trading strategy between GOOGL and MSFT"
  5. "Develop a volatility-based strategy for QQQ using ATR"

{Colors.WARNING}Note:{Colors.ENDC} Each analysis creates a new workspace with:
  • Plan JSON
  • Downloaded market data (CSV files)
  • Strategy code (Python)
  • Backtest results
  • Final report (Markdown)
"""
        print(help_text)
    
    def list_workspaces(self):
        """List all previous workspaces."""
        workspaces = sorted(self.workspaces_dir.glob("*"), reverse=True)
        
        if not workspaces:
            print(f"{Colors.WARNING}No workspaces found.{Colors.ENDC}\n")
            return
        
        print(f"\n{Colors.OKBLUE}{Colors.BOLD}Previous Workspaces:{Colors.ENDC}\n")
        
        for i, ws in enumerate(workspaces[:10], 1):  # Show last 10
            # Parse workspace name
            name_parts = ws.name.split("_", 3)
            if len(name_parts) >= 4:
                date = name_parts[0]
                time = name_parts[1]
                task = name_parts[3].replace("_", " ")[:50]
            else:
                date, time, task = "N/A", "N/A", ws.name[:50]
            
            # Check for final report
            report_path = ws / "final_report.md"
            status = f"{Colors.OKGREEN}✓ Complete{Colors.ENDC}" if report_path.exists() else f"{Colors.WARNING}⚠ Incomplete{Colors.ENDC}"
            
            print(f"  {i}. {Colors.OKCYAN}{date} {time}{Colors.ENDC}")
            print(f"     Task: {task}")
            print(f"     Status: {status}")
            print(f"     Path: {Colors.BOLD}{ws}{Colors.ENDC}\n")
    
    def show_status(self):
        """Show system status."""
        print(f"\n{Colors.OKBLUE}{Colors.BOLD}System Status:{Colors.ENDC}\n")
        print(f"  • LLM Provider: {Colors.OKGREEN}{self.config.DEFAULT_LLM_PROVIDER}{Colors.ENDC}")
        print(f"  • Model: {Colors.OKGREEN}{self.config.DEFAULT_MODEL}{Colors.ENDC}")
        print(f"  • Workspaces Directory: {Colors.OKGREEN}{self.workspaces_dir}{Colors.ENDC}")
        
        # Count workspaces
        workspaces = list(self.workspaces_dir.glob("*"))
        completed = sum(1 for ws in workspaces if (ws / "final_report.md").exists())
        
        print(f"  • Total Workspaces: {Colors.OKGREEN}{len(workspaces)}{Colors.ENDC}")
        print(f"  • Completed: {Colors.OKGREEN}{completed}{Colors.ENDC}")
        print(f"  • Incomplete: {Colors.WARNING}{len(workspaces) - completed}{Colors.ENDC}\n")
    
    def show_config(self):
        """Show current configuration."""
        print(f"\n{Colors.OKBLUE}{Colors.BOLD}Configuration:{Colors.ENDC}\n")
        
        # LLM Config
        print(f"{Colors.OKCYAN}LLM Configuration:{Colors.ENDC}")
        print(f"  • Provider: {Colors.OKGREEN}{self.config.DEFAULT_LLM_PROVIDER}{Colors.ENDC}")
        print(f"  • Model: {Colors.OKGREEN}{self.config.DEFAULT_MODEL}{Colors.ENDC}")
        
        # Show which API keys are configured
        providers = []
        if self.config.OPENAI_API_KEY:
            providers.append(f"OpenAI ({Colors.OKGREEN}✓{Colors.ENDC})")
        if self.config.ANTHROPIC_API_KEY:
            providers.append(f"Anthropic ({Colors.OKGREEN}✓{Colors.ENDC})")
        if self.config.SILICONFLOW_API_KEY:
            providers.append(f"SiliconFlow ({Colors.OKGREEN}✓{Colors.ENDC})")
        
        print(f"  • Available Providers: {', '.join(providers)}")
        
        # Directories
        print(f"\n{Colors.OKCYAN}Directories:{Colors.ENDC}")
        print(f"  • Project Root: {Colors.OKGREEN}{Path(__file__).parent}{Colors.ENDC}")
        print(f"  • Workspaces: {Colors.OKGREEN}{self.workspaces_dir}{Colors.ENDC}")
        print(f"  • Logs: {Colors.OKGREEN}{Path(__file__).parent / 'logs'}{Colors.ENDC}\n")
    
    async def run_analysis(self, request: str):
        """Run an analysis task."""
        print(f"\n{Colors.OKBLUE}{Colors.BOLD}Starting Analysis...{Colors.ENDC}\n")
        print(f"{Colors.OKCYAN}Request:{Colors.ENDC} {request}\n")
        
        # Create session ID
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        safe_name = "".join(c if c.isalnum() else "_" for c in request[:50])
        session_id = f"{timestamp}_{safe_name}"
        
        # The workspace will be created by the engine
        workspace_path = self.workspaces_dir / session_id
        
        print(f"{Colors.OKGREEN}✓{Colors.ENDC} Session: {Colors.BOLD}{session_id}{Colors.ENDC}")
        print(f"{Colors.OKGREEN}✓{Colors.ENDC} Workspace: {Colors.BOLD}{workspace_path}{Colors.ENDC}\n")
        
        try:
            # Run workflow
            result = await self.engine.execute_workflow(
                user_request=request,
                session_id=session_id
            )
            
            # Display results
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}{'═' * 60}{Colors.ENDC}")
            print(f"{Colors.OKGREEN}{Colors.BOLD}Analysis Complete!{Colors.ENDC}")
            print(f"{Colors.OKGREEN}{Colors.BOLD}{'═' * 60}{Colors.ENDC}\n")
            
            print(f"{Colors.OKCYAN}Results:{Colors.ENDC}")
            print(f"  • Session ID: {Colors.BOLD}{result.session_id}{Colors.ENDC}")
            print(f"  • Workspace: {Colors.BOLD}{result.workspace_path}{Colors.ENDC}")
            print(f"  • Status: {Colors.BOLD}{result.status}{Colors.ENDC}")
            
            # List generated files
            ws_path = Path(result.workspace_path)
            if ws_path.exists():
                files = list(ws_path.glob("*"))
                print(f"\n{Colors.OKCYAN}Generated Files ({len(files)}):{Colors.ENDC}")
                for f in sorted(files):
                    if f.is_file():
                        size = f.stat().st_size
                        size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB"
                        print(f"  • {Colors.BOLD}{f.name}{Colors.ENDC} ({size_str})")
                
                # Show final report path
                report_path = ws_path / "final_report.md"
                if report_path.exists():
                    print(f"\n{Colors.OKGREEN}✓{Colors.ENDC} Final report: {Colors.BOLD}{report_path}{Colors.ENDC}")
                    print(f"\n{Colors.WARNING}Tip:{Colors.ENDC} Open the report with: {Colors.BOLD}open {report_path}{Colors.ENDC}")
            
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}{'═' * 60}{Colors.ENDC}\n")
            
            return True
            
        except KeyboardInterrupt:
            print(f"\n\n{Colors.WARNING}⚠ Analysis interrupted by user{Colors.ENDC}\n")
            return False
        except Exception as e:
            print(f"\n\n{Colors.FAIL}✗ Error during analysis:{Colors.ENDC}")
            print(f"{Colors.FAIL}{str(e)}{Colors.ENDC}\n")
            logger.exception("Analysis error")
            return False
    
    async def interactive_loop(self):
        """Run the interactive CLI loop."""
        self.print_banner()
        
        while True:
            try:
                # Prompt
                user_input = input(f"{Colors.BOLD}{Colors.OKGREEN}AgenticQuant>{Colors.ENDC} ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                command = user_input.lower()
                
                if command in ['quit', 'exit', 'q']:
                    print(f"\n{Colors.OKCYAN}Goodbye! 👋{Colors.ENDC}\n")
                    break
                
                elif command == 'help':
                    self.print_help()
                
                elif command == 'list':
                    self.list_workspaces()
                
                elif command == 'status':
                    self.show_status()
                
                elif command == 'config':
                    self.show_config()
                
                elif command == 'clear':
                    os.system('clear' if os.name != 'nt' else 'cls')
                    self.print_banner()
                
                else:
                    # Treat as analysis request
                    await self.run_analysis(user_input)
            
            except KeyboardInterrupt:
                print(f"\n\n{Colors.WARNING}Use 'quit' or 'exit' to close the CLI{Colors.ENDC}\n")
                continue
            except EOFError:
                print(f"\n{Colors.OKCYAN}Goodbye! 👋{Colors.ENDC}\n")
                break
            except Exception as e:
                print(f"\n{Colors.FAIL}Error: {str(e)}{Colors.ENDC}\n")
                logger.exception("CLI error")


async def main():
    """Main entry point."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='AgenticQuant CLI - Multi-Agent Quantitative Analysis System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (default)
  python cli.py
  
  # One-shot mode with prompt
  python cli.py "Develop a momentum strategy for AAPL"
  
  # One-shot mode with explicit argument
  python cli.py --prompt "Analyze TSLA using RSI indicators"
  
  # Change provider and model
  python cli.py --provider openai --model gpt-4-turbo-preview "Create a pairs trading strategy"
  
  # Debug mode with verbose logging
  python cli.py --debug "Build a mean reversion strategy for SPY"
        """
    )
    
    parser.add_argument(
        'prompt',
        nargs='?',
        help='Analysis prompt/request. If provided, runs in one-shot mode. If omitted, starts interactive mode.'
    )
    
    parser.add_argument(
        '--prompt', '-p',
        dest='prompt_arg',
        help='Alternative way to specify the prompt (useful if prompt starts with -)'
    )
    
    parser.add_argument(
        '--provider',
        choices=['openai', 'anthropic', 'siliconflow'],
        help='LLM provider to use (overrides .env setting)'
    )
    
    parser.add_argument(
        '--model', '-m',
        help='Model name to use (overrides .env setting)'
    )
    
    parser.add_argument(
        '--workspace', '-w',
        help='Custom workspace directory path'
    )
    
    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List all previous workspaces and exit'
    )
    
    parser.add_argument(
        '--status', '-s',
        action='store_true',
        help='Show system status and exit'
    )
    
    args = parser.parse_args()
    
    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Initialize CLI
    cli = AgenticQuantCLI()
    
    # Override provider if specified
    if args.provider:
        os.environ['DEFAULT_LLM_PROVIDER'] = args.provider
        logger.info(f"Using provider: {args.provider}")
    
    # Override model if specified
    if args.model:
        os.environ['DEFAULT_MODEL'] = args.model
        logger.info(f"Using model: {args.model}")
    
    # Handle --list flag
    if args.list:
        cli.list_workspaces()
        return
    
    # Handle --status flag
    if args.status:
        cli.show_status()
        return
    
    # Determine prompt (positional argument takes precedence)
    prompt = args.prompt or args.prompt_arg
    
    if prompt:
        # One-shot mode: run analysis and exit
        print(f"{Colors.OKBLUE}{Colors.BOLD}AgenticQuant CLI - One-Shot Mode{Colors.ENDC}\n")
        success = await cli.run_analysis(prompt)
        sys.exit(0 if success else 1)
    else:
        # Interactive mode
        await cli.interactive_loop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nExiting...\n")
        sys.exit(0)
