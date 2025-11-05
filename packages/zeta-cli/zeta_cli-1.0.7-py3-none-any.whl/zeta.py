#!/usr/bin/env python3
"""
ZETA - The most accessible AI terminal agent for learning and building.
A friendly AI terminal agent for non-technical users.
"""

import os
import json
import subprocess
import re
import uuid
import requests
import webbrowser
import http.server
import socketserver
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
from rich.table import Table
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

# Initialize Rich console
console = Console()

# Constants
# Use home directory for log file to avoid permission issues
LOG_FILE = Path.home() / ".zeta_log.md"
CONFIG_FILE = Path.home() / ".zeta_config.json"

# LLM Provider Configuration (supports cloud APIs like Gemini, Claude, OpenAI)
# Set via environment variables or config file:
# - ZETA_PROVIDER: "openai", "anthropic", "google", "ollama" (default)
# - OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY for respective providers
# - ZETA_MODEL: model name (default varies by provider)
LLM_PROVIDER = os.getenv("ZETA_PROVIDER", "ollama").lower()


def load_config():
    """Load configuration from file if it exists."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Set environment variables from config
                for key, value in config.items():
                    if value and key not in os.environ:  # Don't override existing env vars
                        os.environ[key] = str(value)
                return config
        except Exception:
            pass
    return {}


def save_config(config: Dict[str, Any]):
    """Save configuration to file, including API keys."""
    try:
        # Save provider, model, and API keys (needed for persistence)
        full_config = {
            "ZETA_PROVIDER": config.get("ZETA_PROVIDER"),
            "ZETA_MODEL": config.get("ZETA_MODEL"),
            # Save API keys from environment (they're set before calling save_config)
            "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY", ""),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
            "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", "")
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(full_config, f, indent=2)
    except Exception:
        pass


def is_configured() -> bool:
    """Check if ZETA is properly configured."""
    # Always try loading config first
    load_config()
    
    provider = os.getenv("ZETA_PROVIDER", "").lower()
    
    if not provider:
        return False
    
    if provider == "ollama":
        # For Ollama, just check if it's available
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    # For cloud providers, check if API key is set
    if provider == "google":
        return bool(os.getenv("GOOGLE_API_KEY"))
    elif provider == "openai":
        return bool(os.getenv("OPENAI_API_KEY"))
    elif provider == "anthropic":
        return bool(os.getenv("ANTHROPIC_API_KEY"))
    
    return False


class AgentState(TypedDict):
    """State for the LangGraph agent."""
    messages: List[Any]


class ZetaTools:
    """Collection of tools available to ZETA."""
    
    # Track confirmed files in current session to avoid repeated prompts
    _confirmed_files = set()
    
    @staticmethod
    @tool
    def read_file(file_path: str) -> str:
        """Read the contents of a file. Returns file content as string."""
        try:
            path = Path(file_path)
            if not path.exists():
                return f"Error: File '{file_path}' does not exist."
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    @staticmethod
    def write_file(file_path: str, content: str, confirm: bool = True) -> str:
        """Write content to a file. Creates parent directories if needed."""
        try:
            # Expand environment variables (e.g., %userprofile% -> actual path)
            expanded_path = os.path.expandvars(file_path)
            # Expand user home directory (~ -> actual home)
            expanded_path = os.path.expanduser(expanded_path)
            
            # If path is relative, make it relative to current working directory
            if not os.path.isabs(expanded_path):
                path = Path(expanded_path).resolve()
            else:
                # For absolute paths, resolve them
                path = Path(expanded_path).resolve()
            
            # If writing to a system/protected directory fails, fallback to current directory
            # Check if parent directory is writable
            try:
                test_file = path.parent / ".zeta_write_test"
                test_file.touch()
                test_file.unlink()
            except (PermissionError, OSError):
                # Can't write to this location, use current directory instead
                console.print(f"[yellow]⚠ Cannot write to '{path.parent}'. Using current directory instead.[/yellow]")
                path = Path.cwd() / path.name
            
            existing = path.exists()
            
            if confirm:
                # If we already confirmed this file in this session, skip confirmation
                if file_path not in ZetaTools._confirmed_files:
                    action = "modify" if existing else "create"
                    if not Confirm.ask(f"\n[bold yellow]Would you like me to {action} '{file_path}'?[/bold yellow]"):
                        return f"User declined to {action} '{file_path}'"
                    # Mark as confirmed
                    ZetaTools._confirmed_files.add(file_path)
                # If already confirmed, proceed silently (within same session)
            
            # Check content before writing
            if not content:
                return f"Error: Cannot write empty file to '{path}'. Content parameter is missing or empty. The LLM may not have included the code in the TOOL_CALL."
            
            content_str = str(content).strip()
            if len(content_str) == 0:
                return f"Error: Cannot write empty file to '{path}'. Content parameter is empty. Please ensure the LLM includes the full code in the TOOL_CALL."
            
            # Create parent directories if they don't exist
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the file
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Verify file was written
            if path.exists() and path.stat().st_size > 0:
                return f"Successfully wrote {len(content)} characters to '{path}'"
            else:
                return f"Warning: File '{path}' was created but appears to be empty. Expected {len(content)} characters but file size is {path.stat().st_size if path.exists() else 0} bytes."
        except PermissionError as e:
            return f"Permission denied: Cannot write to '{file_path}'. Try running from a different directory or check file permissions. Error: {str(e)}"
        except OSError as e:
            return f"OS Error writing file '{file_path}': {str(e)}. Make sure the path is valid and you have write permissions."
        except Exception as e:
            return f"Error writing file '{file_path}': {str(e)}. Full error: {type(e).__name__}"
    
    @staticmethod
    def reset_confirmed_files():
        """Reset confirmed files tracker (call at start of new task)."""
        ZetaTools._confirmed_files.clear()
    
    @staticmethod
    @tool
    def run_command(command: str) -> str:
        """Run a shell command and return its output."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return result.stdout if result.stdout else "Command executed successfully."
            else:
                return f"Error: {result.stderr or 'Command failed'}"
        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 30 seconds."
        except Exception as e:
            return f"Error running command: {str(e)}"
    
    @staticmethod
    @tool
    def list_files(directory: str = ".") -> str:
        """List files and directories in a given path."""
        try:
            path = Path(directory)
            if not path.exists():
                return f"Error: Directory '{directory}' does not exist."
            items = []
            for item in sorted(path.iterdir()):
                if item.is_dir():
                    items.append(f"[DIR] {item.name}/")
                else:
                    items.append(f"[FILE] {item.name}")
            return "\n".join(items) if items else "Directory is empty."
        except Exception as e:
            return f"Error listing directory: {str(e)}"


class ZetaLogger:
    """Handles logging to zeta_log.md."""
    
    @staticmethod
    def init_log():
        """Initialize log file if it doesn't exist."""
        global LOG_FILE
        log_path = Path(LOG_FILE)
        try:
            if not log_path.exists():
                # Ensure parent directory exists
                log_path.parent.mkdir(parents=True, exist_ok=True)
                with open(log_path, 'w', encoding='utf-8') as f:
                    f.write("# ZETA Learning Log\n\n")
                    f.write("Welcome to ZETA! This log tracks your coding journey.\n\n")
                    f.write("---\n\n")
        except (PermissionError, IOError) as e:
            # If can't write to home directory, try current directory
            try:
                alt_log = Path("zeta_log.md")
                if not alt_log.exists():
                    with open(alt_log, 'w', encoding='utf-8') as f:
                        f.write("# ZETA Learning Log\n\n")
                        f.write("Welcome to ZETA! This log tracks your coding journey.\n\n")
                        f.write("---\n\n")
                # Update LOG_FILE to use alternative
                LOG_FILE = alt_log
            except:
                # If both fail, logging is disabled - continue without it
                pass
    
    @staticmethod
    def log(action: str, explanation: str, lesson: Optional[str] = None):
        """Log an action and explanation."""
        try:
            ZetaLogger.init_log()
            log_path = Path(LOG_FILE)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(f"## {timestamp}\n\n")
                f.write(f"**Action:** {action}\n\n")
                f.write(f"**Explanation:** {explanation}\n\n")
                if lesson:
                    f.write(f"**Lesson:** {lesson}\n\n")
                f.write("---\n\n")
        except (PermissionError, IOError):
            # If logging fails, just continue - don't break the app
            pass
    
    @staticmethod
    def show_log():
        """Display the log file."""
        global LOG_FILE
        log_path = Path(LOG_FILE)
        # Try home directory first, then current directory
        if not log_path.exists():
            alt_log = Path("zeta_log.md")
            if alt_log.exists():
                log_path = alt_log
            else:
                console.print("[yellow]No log entries yet. Start using ZETA to see your learning journey![/yellow]")
                return
        
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
            console.print(Markdown(content))
        except (PermissionError, IOError) as e:
            console.print(f"[yellow]Could not read log file: {e}[/yellow]")


class ZetaAgent:
    """Main agent that handles conversations and actions."""
    
    def __init__(self, teach_mode: bool = False, critic_mode: bool = False):
        self.teach_mode = teach_mode
        self.critic_mode = critic_mode
        self.llm = self._create_llm()
        self.tools = [
            ZetaTools.read_file,
            ZetaTools.write_file,
            ZetaTools.run_command,
            ZetaTools.list_files
        ]
        self.intent = None  # Will store detected intent
        self.setup_agent()
    
    def _create_llm(self):
        """Create LLM instance based on configured provider."""
        # Load config from file first
        load_config()
        
        # Read provider at runtime, not import time
        provider = os.getenv("ZETA_PROVIDER", "ollama").lower()
        model_name = os.getenv("ZETA_MODEL", "")
        
        if provider == "openai":
            try:
                from langchain_openai import ChatOpenAI
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    console.print("[red]Error: OPENAI_API_KEY not set. Set it with:[/red]")
                    console.print("[yellow]  $env:OPENAI_API_KEY='your-key-here'[/yellow]")
                    raise ValueError("OPENAI_API_KEY not found")
                return ChatOpenAI(
                    model=model_name or "gpt-4o-mini",
                    temperature=0.7,
                    api_key=api_key
                )
            except ImportError:
                console.print("[red]Error: langchain-openai not installed.[/red]")
                console.print("[yellow]Install with: pip install langchain-openai[/yellow]")
                raise
        
        elif provider == "anthropic":
            try:
                from langchain_anthropic import ChatAnthropic
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    console.print("[red]Error: ANTHROPIC_API_KEY not set.[/red]")
                    console.print("[yellow]  $env:ANTHROPIC_API_KEY='your-key-here'[/yellow]")
                    raise ValueError("ANTHROPIC_API_KEY not found")
                return ChatAnthropic(
                    model=model_name or "claude-3-5-sonnet-20241022",
                    temperature=0.7,
                    api_key=api_key
                )
            except ImportError:
                console.print("[red]Error: langchain-anthropic not installed.[/red]")
                console.print("[yellow]Install with: pip install langchain-anthropic[/yellow]")
                raise
        
        elif provider == "google":
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                api_key = os.getenv("GOOGLE_API_KEY")
                if not api_key:
                    console.print("[red]Error: GOOGLE_API_KEY not set.[/red]")
                    console.print("[yellow]Run: zeta setup[/yellow]")
                    raise ValueError("GOOGLE_API_KEY not found")
                
                # Use correct Google Gemini model names for Google AI Studio API
                # Valid models WITHOUT -latest suffix: gemini-1.5-flash, gemini-1.5-pro
                models_to_try = []
                if model_name:
                    # Remove -latest suffix if present (not valid in API)
                    clean_name = model_name.replace("-latest", "")
                    models_to_try.append(clean_name)
                
                # Add valid model names in order of preference (NO -latest suffix)
                valid_models = [
                    "gemini-1.5-flash",  # Fastest, free tier - NO -latest suffix
                    "gemini-1.5-pro",    # More capable - NO -latest suffix
                    "gemini-pro"         # Legacy fallback
                ]
                
                # Add valid models if not already in list
                for valid_model in valid_models:
                    if valid_model not in models_to_try:
                        models_to_try.append(valid_model)
                
                # Try each model - create instance
                for model in models_to_try:
                    try:
                        llm = ChatGoogleGenerativeAI(
                            model=model,
                            temperature=0.7,
                            google_api_key=api_key
                        )
                        # Return first successful instance creation
                        return llm
                    except Exception:
                        # Continue to next model if this one fails
                        continue
                
                # Final fallback - use gemini-1.5-flash (NO -latest suffix)
                return ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    temperature=0.7,
                    google_api_key=api_key
                )
            except ImportError:
                console.print("[red]Error: langchain-google-genai not installed.[/red]")
                console.print("[yellow]Run: pip install langchain-google-genai[/yellow]")
                raise
        
        else:  # Default: Ollama (local)
            try:
                from langchain_ollama import OllamaLLM
                model = model_name or os.getenv("ZETA_MODEL", "llama3.2:latest")
                return OllamaLLM(
                    model=model,
                    temperature=0.7,
                    timeout=120.0,
                    base_url="http://localhost:11434"
                )
            except ImportError:
                console.print("[red]Error: langchain-ollama not installed.[/red]")
                console.print("[yellow]Install with: pip install langchain-ollama[/yellow]")
                raise
    
    def setup_agent(self):
        """Set up the LangGraph agent."""
        def agent_node(state: AgentState):
            messages = state["messages"]
            
            # Build system prompt
            system_prompt = self._build_system_prompt()
            
            # Add system message
            full_messages = [SystemMessage(content=system_prompt)] + messages
            
            # Get response from LLM
            response = self.llm.invoke(full_messages)
            
            return {"messages": [AIMessage(content=response.content if hasattr(response, 'content') else str(response))]}
        
        # Create graph
        workflow = StateGraph(AgentState)
        workflow.add_node("agent", agent_node)
        workflow.set_entry_point("agent")
        workflow.add_edge("agent", END)
        
        self.graph = workflow.compile()
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt based on mode and detected intent."""
        base_prompt = """You are ZETA, the most accessible AI terminal agent for learning and building. A friendly AI terminal agent designed for non-technical users.

Your personality:
- Patient, encouraging, and educational
- Never use jargon without explaining it
- Always explain what you're doing in plain English
- Ask clarifying questions when tasks are vague
- End responses with questions to encourage learning

Available tools (call them using TOOL_CALL format):
- read_file(file_path="path/to/file"): Read a file
- write_file(file_path="path/to/file", content="file content"): Write/create a file
- run_command(command="shell command"): Execute shell commands
- list_files(directory="path/to/dir"): List directory contents

When you need to use a tool, format it exactly like this:
TOOL_CALL: tool_name(param1="value1", param2="value2")

For multiline content (like file content), use triple quotes:
TOOL_CALL: write_file(file_path="app.py", content=\"\"\"multiline
content
here\"\"\")

CRITICAL: When creating files, you MUST include the COMPLETE code/content inside the triple quotes. Do NOT use placeholders or say "here's the code" - actually include the full code in the TOOL_CALL.

Important rules:
1. ALWAYS ACT - use tools to create files, run commands, etc. Do NOT ask questions unless the task is completely unclear.
2. If the user wants something created, CREATE IT IMMEDIATELY using tools. Do not ask "what should I create?" - just create it.
3. After every action, explain what was done in simple terms
4. If in teaching mode, provide detailed explanations with definitions
5. Use friendly, encouraging language like "Great choice!", "Nice!", "Let's do this!"
6. If you need to create or modify files, use the write_file tool. The system will ask for confirmation automatically.
7. CRITICAL: When user asks to create something, CREATE IT. Do not ask more questions - just create files and execute commands.
"""
        
        # Add intent-specific guidance
        if self.intent:
            intent_guidance = {
                'landing_page': """
CONTEXT: User wants a landing page (marketing/product showcase page).
- Create HTML file with modern, responsive design
- Include CSS for styling (can be inline or separate file)
- Add JavaScript for interactivity if needed
- Focus on visual appeal, clear messaging, call-to-action buttons
- Include sections: hero, features, testimonials, contact
""",
                'web_app': """
CONTEXT: User wants a web application (interactive app).
- Create HTML file with form inputs and interactive elements
- Include JavaScript for functionality
- Add CSS for styling
- Focus on user interaction: forms, buttons, dynamic content
- Consider adding backend (Python/Node.js) if needed for data persistence
""",
                'automation_script': """
CONTEXT: User wants an automation script.
- Create Python script (.py file)
- Include necessary imports (requests, selenium, etc.)
- Add error handling and logging
- Make it executable and well-documented
- Focus on reliability and reusability
""",
                'data_project': """
CONTEXT: User wants a data analysis project.
- Create Python script (.py file) with pandas/numpy
- Include data loading, processing, and visualization
- Add Jupyter notebook if appropriate
- Include CSV/Excel reading capabilities
- Focus on clear analysis and visualizations
"""
            }
            
            if self.intent in intent_guidance:
                base_prompt += f"\n{intent_guidance[self.intent]}"
        
        # Add teaching mode guidance
        if self.teach_mode:
            base_prompt += """
TEACHING MODE ENABLED:
- Provide detailed explanations for every concept
- Define technical terms (e.g., "HTML is the skeleton of a webpage")
- Break down complex ideas into simple steps
- Use analogies when helpful
"""
        
        # Add critic mode guidance
        if self.critic_mode:
            base_prompt += """
CRITIC MODE ENABLED:
- Review all code for bugs, style, and security
- Provide a score from 1-10
- Suggest fixes if score is below 8
- Explain each issue clearly
"""
        
        return base_prompt
    
    def ask_clarifying_question(self, vague_task: str) -> Optional[str]:
        """Detect vague tasks and ask clarifying questions."""
        prompt = f"""The user said: "{vague_task}"

This task is vague. Generate 3-5 numbered options to clarify what they want.
Format: Return ONLY a JSON object with this structure:
{{
    "question": "What kind of [thing] would you like?",
    "options": [
        "Option 1 description",
        "Option 2 description",
        "Option 3 description"
    ]
}}

Return ONLY the JSON, no other text."""
        
        try:
            response = self.llm.invoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Try to extract JSON
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)
                return data
        except Exception as e:
            console.print(f"[red]Error generating clarifying question: {e}[/red]")
        
        return None
    
    def explain_action(self, action: str, result: str, teach_mode: bool = False) -> str:
        """Generate an explanation for an action."""
        prompt = f"""The following action was performed:
Action: {action}
Result: {result}

Generate a friendly, plain English explanation of what happened.
{"Include detailed explanations and definitions if this is teaching mode." if teach_mode else "Keep it concise but informative."}
Use encouraging language. End with a question to encourage learning."""
        
        try:
            response = self.llm.invoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception:
            return f"Completed: {action}. {result}"
    
    def critic_review(self, code: str, file_path: str) -> Dict[str, Any]:
        """Review code using critic mode."""
        # Determine language from file extension
        ext = Path(file_path).suffix
        lang_map = {'.py': 'python', '.js': 'javascript', '.html': 'html', 
                   '.css': 'css', '.ts': 'typescript', '.jsx': 'javascript', '.tsx': 'typescript'}
        lang = lang_map.get(ext, 'code')
        
        prompt = f"""Review this {lang} code from '{file_path}':

```{lang}
{code}
```

Provide a JSON response with:
{{
    "score": <1-10>,
    "issues": ["issue1", "issue2"],
    "suggestions": ["suggestion1", "suggestion2"],
    "explanation": "Overall assessment"
}}

Return ONLY the JSON."""
        
        try:
            response = self.llm.invoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            console.print(f"[yellow]Critic review failed: {e}[/yellow]")
        
        return {"score": 5, "issues": [], "suggestions": [], "explanation": "Could not complete review."}
    
    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Execute a tool and return the result."""
        if tool_name == "read_file":
            # read_file is decorated with @tool, access underlying function via func attribute
            return ZetaTools.read_file.func(args.get("file_path", ""))
        elif tool_name == "write_file":
            return ZetaTools.write_file(
                args.get("file_path", ""),
                args.get("content", ""),
                confirm=True
            )
        elif tool_name == "run_command":
            # run_command is decorated with @tool
            return ZetaTools.run_command.func(args.get("command", ""))
        elif tool_name == "list_files":
            # list_files is decorated with @tool
            return ZetaTools.list_files.func(args.get("directory", "."))
        else:
            return f"Unknown tool: {tool_name}"
    
    def parse_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """Parse tool calls from LLM response."""
        tool_calls = []
        
        # Look for patterns like: TOOL_CALL: tool_name(...)
        # Handle multiline content with triple quotes
        # Better pattern that handles nested parentheses and multiline content
        pattern = r'TOOL_CALL:\s*(\w+)\s*\((.*?)\)(?=\s*(?:TOOL_CALL:|$))'
        matches = list(re.finditer(pattern, response, re.DOTALL))
        
        for match in matches:
            tool_name = match.group(1)
            args_str = match.group(2).strip()
            
            # Parse arguments
            args = {}
            
            # Handle triple-quoted strings (multiline content)
            # Try to find content= with triple quotes (either """ or ''')
            # Improved patterns that handle various formats
            triple_quote_patterns = [
                # content=("""...""") - with parentheses
                (r'content=\("""(.*?)"""\)', 1),
                # content=('''...''') - with parentheses  
                (r"content=\('''(.*?)'''\)", 1),
                # content="""...""" - without parentheses
                (r'content="""(.*?)"""', 1),
                # content='''...''' - without parentheses
                (r"content='''(.*?)'''", 1),
                # content= """...""" - with space
                (r'content=\s*"""(.*?)"""', 1),
                # content= '''...''' - with space
                (r"content=\s*'''(.*?)'''", 1),
            ]
            
            content_found = False
            for pattern, group_num in triple_quote_patterns:
                content_match = re.search(pattern, args_str, re.DOTALL)
                if content_match:
                    try:
                        content = content_match.group(group_num)
                        if content and len(content.strip()) > 0:
                            args['content'] = content.strip()
                            # Remove the matched content from args_str
                            args_str = re.sub(pattern, '', args_str, flags=re.DOTALL)
                            content_found = True
                            break
                    except (IndexError, AttributeError):
                        continue
            
            # If no triple quotes found, try to extract content after content= until end of args
            if not content_found and 'content=' in args_str:
                # Try to find content= and extract everything after it (might be single-line)
                content_simple = re.search(r'content=["\'](.*?)["\']', args_str, re.DOTALL)
                if content_simple:
                    args['content'] = content_simple.group(1).strip()
            
            # Parse simple quoted arguments
            arg_pattern = r'(\w+)=["\']([^"\']*)["\']'
            for arg_match in re.finditer(arg_pattern, args_str):
                key = arg_match.group(1)
                value = arg_match.group(2)
                if key not in args:  # Don't overwrite multiline content
                    args[key] = value
            
            # Handle unquoted arguments (for directory="." type cases)
            simple_pattern = r'(\w+)=([^,)]+)'
            for arg_match in re.finditer(simple_pattern, args_str):
                key = arg_match.group(1).strip()
                value = arg_match.group(2).strip().strip('"\'')
                if key not in args:
                    args[key] = value
            
            if args:
                tool_calls.append({"tool": tool_name, "args": args})
        
        return tool_calls
    
    def process_task(self, task: str, max_iterations: int = 5) -> str:
        """Process a task using the agent with tool execution."""
        try:
            messages = [HumanMessage(content=task)]
            system_prompt = self._build_system_prompt()
            
            for iteration in range(max_iterations):
                # Get response from LLM
                full_messages = [SystemMessage(content=system_prompt)] + messages
                response = self.llm.invoke(full_messages)
                response_text = response.content if hasattr(response, 'content') else str(response)
                
                # Check for tool calls
                tool_calls = self.parse_tool_calls(response_text)
                
                if not tool_calls:
                    # No tool calls - check if LLM is asking about conflicts
                    # If so, tell it to just create/overwrite automatically
                    if "?" in response_text.lower() and ("file" in response_text.lower() or "conflict" in response_text.lower() or "overwrite" in response_text.lower() or "existing" in response_text.lower()):
                        # LLM is asking about file conflicts - force it to create
                        messages.append(AIMessage(content=response_text))
                        messages.append(HumanMessage(content="Just create the file. If it exists, overwrite it automatically. The system handles confirmation. Use write_file tool now. Do not ask questions - just create."))
                        continue  # Continue to force tool execution
                    
                    # No tool calls and no conflicts - return response
                    return response_text
                
                # Execute tools
                tool_results = []
                for tool_call in tool_calls:
                    tool_name = tool_call["tool"]
                    args = tool_call["args"]
                    
                    # Show what's being executed (truncate long content)
                    args_display = {}
                    for k, v in args.items():
                        if k == 'content' and len(str(v)) > 50:
                            args_display[k] = str(v)[:50] + "..."
                        else:
                            args_display[k] = v
                    console.print(f"[dim]Executing: {tool_name}({', '.join(f'{k}={v[:30]}...' if len(str(v)) > 30 else f'{k}={v}' for k, v in args_display.items())})[/dim]")
                    
                    # Check if write_file is being called with empty content
                    if tool_name == "write_file":
                        content_value = args.get("content", "")
                        if not content_value or len(str(content_value).strip()) == 0:
                            console.print("[red]⚠ Error: write_file called with empty content![/red]")
                            console.print("[yellow]The LLM may not have included the code in the TOOL_CALL.[/yellow]")
                            console.print(f"[dim]Debug: args keys = {list(args.keys())}, content type = {type(content_value)}[/dim]")
                            # Show a sample of what was parsed
                            if 'file_path' in args:
                                console.print(f"[dim]File path: {args['file_path']}[/dim]")
                            result = "Error: Cannot write empty file. The content parameter is missing or empty. The LLM needs to include the FULL code/content in the TOOL_CALL using triple quotes."
                        else:
                            # Log that we have content (for debugging)
                            console.print(f"[dim]Content length: {len(str(content_value))} characters[/dim]")
                            result = self.execute_tool(tool_name, args)
                    else:
                        result = self.execute_tool(tool_name, args)
                    
                    tool_results.append(f"{tool_name} result: {result}")
                    
                    # If write_file failed, show a more helpful message
                    if tool_name == "write_file" and ("Error" in result or "empty" in result.lower()):
                        console.print(f"[yellow]⚠ {result}[/yellow]")
                        # Suggest retry with explicit instruction
                        if "empty" in result.lower() or "missing" in result.lower():
                            console.print("[cyan]Hint: Retrying with explicit content requirement...[/cyan]")
                            messages.append(AIMessage(content=response_text))
                            messages.append(HumanMessage(content="""The write_file tool was called but the content parameter was empty or missing. 

CRITICAL: You MUST include the COMPLETE code/content inside the TOOL_CALL. Do NOT use placeholders.

Example format:
TOOL_CALL: write_file(file_path="todo.py", content=\"\"\"
# Complete Python code here
def main():
    print("Hello")
\"\"\")

Now create the file with the FULL code included in the content parameter."""))
                            continue
                
                # Add tool results to conversation
                messages.append(AIMessage(content=response_text))
                messages.append(HumanMessage(content="Tool results:\n" + "\n".join(tool_results)))
            
            # If we've done max iterations, return last response
            return response_text if 'response_text' in locals() else "I'm not sure how to help with that. Could you be more specific?"
            
        except Exception as e:
            error_msg = str(e)
            # Provide helpful error messages
            if "404" in error_msg or "not found" in error_msg.lower():
                return f"I encountered an error: The model might not be available. Try running `zeta setup` to configure a different model, or check your API key."
            elif "429" in error_msg or "quota" in error_msg.lower():
                return f"I encountered an error: API quota exceeded. Try running `zeta setup` to switch to a different provider (like Google Gemini with free tier)."
            elif "10061" in error_msg or "connection refused" in error_msg.lower():
                return f"I encountered an error: Cannot connect to Ollama server. Please start Ollama or run `zeta setup` to use a cloud API instead."
            else:
                return f"I encountered an error: {error_msg}. Try running `zeta setup` to reconfigure, or rephrasing your request."


def ask_clarifying_questions(intent: str, task: str) -> Dict[str, Any]:
    """
    Ask interactive clarifying questions based on detected intent.
    Returns a dictionary with user responses.
    """
    responses = {}
    
    if intent == 'landing_page':
        console.print("\n[bold cyan]Let's customize your landing page![/bold cyan]\n")
        
        # Question 1: Product name
        product_name = Prompt.ask("[bold]What's your product name?[/bold]", default="My Product")
        responses['product_name'] = product_name
        
        # Question 2: Main goal
        console.print("\n[bold]What's the main goal of the page?[/bold]")
        goal_options = ["info", "signup", "waitlist"]
        console.print("  1. Info - showcase product features")
        console.print("  2. Signup - collect user registrations")
        console.print("  3. Waitlist - build anticipation")
        goal_choice = Prompt.ask("\n[bold]Choose (1-3)[/bold]", default="1")
        try:
            goal_idx = int(goal_choice) - 1
            if 0 <= goal_idx < len(goal_options):
                responses['goal'] = goal_options[goal_idx]
            else:
                responses['goal'] = goal_options[0]
        except ValueError:
            responses['goal'] = goal_options[0]
        
        # Question 3: Style
        console.print("\n[bold]Choose style:[/bold]")
        style_options = ["modern gradient", "minimal", "dark theme"]
        console.print("  1. Modern gradient - colorful, eye-catching")
        console.print("  2. Minimal - clean, simple, professional")
        console.print("  3. Dark theme - sleek, modern, dark colors")
        style_choice = Prompt.ask("\n[bold]Choose (1-3)[/bold]", default="1")
        try:
            style_idx = int(style_choice) - 1
            if 0 <= style_idx < len(style_options):
                responses['style'] = style_options[style_idx]
            else:
                responses['style'] = style_options[0]
        except ValueError:
            responses['style'] = style_options[0]
    
    elif intent == 'web_app':
        console.print("\n[bold cyan]Let's build your web app![/bold cyan]\n")
        
        # Question 1: App type
        console.print("[bold]What type of app?[/bold]")
        app_types = ["to-do", "notes", "tracker"]
        console.print("  1. To-do - task management")
        console.print("  2. Notes - note-taking app")
        console.print("  3. Tracker - track habits/goals")
        app_choice = Prompt.ask("\n[bold]Choose (1-3)[/bold]", default="1")
        try:
            app_idx = int(app_choice) - 1
            if 0 <= app_idx < len(app_types):
                responses['app_type'] = app_types[app_idx]
            else:
                responses['app_type'] = app_types[0]
        except ValueError:
            responses['app_type'] = app_types[0]
        
        # Question 2: Auth mode
        auth_mode = Prompt.ask("\n[bold]Do you want login or offline mode?[/bold]", default="offline")
        if auth_mode.lower() not in ['login', 'offline']:
            auth_mode = 'offline'
        responses['auth_mode'] = auth_mode.lower()
    
    elif intent == 'automation_script':
        console.print("\n[bold cyan]Let's set up your automation script![/bold cyan]\n")
        script_type = Prompt.ask("[bold]What should this script do?[/bold]", default="File processing")
        responses['script_type'] = script_type
    
    elif intent == 'data_script':
        console.print("\n[bold cyan]Let's create your data analysis project![/bold cyan]\n")
        data_source = Prompt.ask("[bold]What's your data source? (CSV file, API, database)[/bold]", default="CSV file")
        responses['data_source'] = data_source
    
    return responses


def extract_project_name(task: str) -> str:
    """
    Extract a project name from the task description.
    Falls back to a generic name if none can be extracted.
    """
    task_lower = task.lower()
    
    # Try to find project name after common verbs
    patterns = [
        r'(?:create|make|build|generate)\s+(?:a\s+)?(?:landing\s+page|website|page|app|application|script|project|tool)\s+(?:for|called|named)?\s+["\']?([^"\']+)["\']?',
        r'(?:create|make|build)\s+["\']?([^"\']+)["\']?\s+(?:landing\s+page|website|app|application|script)',
        r'for\s+["\']?([^"\']+)["\']?',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, task_lower)
        if match:
            name = match.group(1).strip()
            if name and len(name) > 2:
                # Clean up the name
                name = re.sub(r'\s+', '_', name)
                name = re.sub(r'[^\w\-_]', '', name)
                return name[:50]  # Limit length
    
    # Fallback: generate name from intent
    return None


def start_preview_server(project_path: Path, port: int = 8080):
    """
    Start a lightweight HTTP server to preview the project.
    Returns (server_thread, httpd) if successful, (None, None) otherwise.
    """
    try:
        # Create a custom handler that serves from the project directory
        class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(project_path), **kwargs)
            
            def log_message(self, format, *args):
                # Suppress server logs for cleaner output
                pass
        
        # Try to start the server
        httpd = socketserver.TCPServer(("", port), CustomHTTPRequestHandler)
        
        # Start server in a daemon thread so it doesn't block
        def run_server():
            httpd.serve_forever()
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Give server a moment to start
        import time
        time.sleep(0.5)
        
        return server_thread, httpd
    except OSError as e:
        if "Address already in use" in str(e) or "Only one usage" in str(e) or "10048" in str(e):
            console.print(f"[yellow]Warning: Port {port} is already in use. Try a different port.[/yellow]")
        else:
            console.print(f"[yellow]Warning: Could not start server: {e}[/yellow]")
        return None, None
    except Exception as e:
        console.print(f"[yellow]Warning: Error starting preview server: {e}[/yellow]")
        return None, None


def open_browser(url: str) -> bool:
    """
    Open the default browser to the given URL.
    Works on Windows, macOS, and Linux.
    Returns True if successful, False otherwise.
    """
    try:
        webbrowser.open(url)
        return True
    except Exception as e:
        console.print(f"[yellow]Warning: Could not open browser: {e}[/yellow]")
        console.print(f"[dim]Please manually open: {url}[/dim]")
        return False


def generate_file_explanations(intent: str, created_files: List[Dict[str, str]]) -> str:
    """
    Generate simple explanations for created files based on intent.
    Returns a formatted explanation string.
    """
    explanations = []
    
    if intent == 'landing_page':
        file_explanations = {
            'index.html': 'main structure - defines the page layout, text, and sections',
            'style.css': 'layout and colors - controls how everything looks (fonts, colors, spacing)',
            'script.js': 'button logic and animations - makes buttons work and adds smooth scrolling'
        }
    elif intent == 'web_app':
        file_explanations = {
            'app.py': 'backend server - handles requests and responses (like a waiter taking orders)',
            'templates/index.html': 'frontend interface - what users see and interact with',
            'requirements.txt': 'dependencies list - tells Python which packages to install'
        }
    elif intent == 'automation_script':
        file_explanations = {
            'automation.py': 'main script - contains the automation logic and instructions'
        }
    elif intent == 'data_script':
        file_explanations = {
            'analyze_data.py': 'analysis script - loads data, creates charts, and finds patterns',
            'requirements.txt': 'dependencies list - tells Python which packages to install'
        }
    else:
        # Generic fallback
        file_explanations = {}
    
    # Build explanations for each created file
    for file_info in created_files:
        file_name = file_info['file']
        # Get just the filename without path
        base_name = Path(file_name).name
        
        if base_name in file_explanations:
            explanations.append(f"• [cyan]{base_name}[/cyan] - {file_explanations[base_name]}")
        else:
            # Generic explanation for unknown files
            ext = Path(file_name).suffix.lower()
            if ext == '.html':
                explanations.append(f"• [cyan]{base_name}[/cyan] - HTML page structure")
            elif ext == '.css':
                explanations.append(f"• [cyan]{base_name}[/cyan] - styling and design")
            elif ext == '.js':
                explanations.append(f"• [cyan]{base_name}[/cyan] - interactive functionality")
            elif ext == '.py':
                explanations.append(f"• [cyan]{base_name}[/cyan] - Python script")
            elif ext == '.txt':
                explanations.append(f"• [cyan]{base_name}[/cyan] - text configuration file")
            else:
                explanations.append(f"• [cyan]{base_name}[/cyan] - project file")
    
    if explanations:
        summary = "[bold]Here's what I created:[/bold]\n\n" + "\n".join(explanations)
        summary += "\n\n[dim]You can edit these files in any text editor.[/dim]"
        return summary
    
    return "[bold]Files created successfully![/bold]"


def preview_project(project_path: Path, intent: str) -> bool:
    """
    Start a preview server and open browser for landing_page or web_app projects.
    Returns True if preview started successfully, False otherwise.
    """
    if intent not in ['landing_page', 'web_app']:
        return False
    
    port = 8080
    url = f"http://localhost:{port}"
    
    # Check if project directory exists
    if not project_path.exists():
        console.print(f"[yellow]Warning: Project directory not found: {project_path}[/yellow]")
        return False
    
    # Check if index.html exists (for landing_page) or app.py exists (for web_app)
    if intent == 'landing_page' and not (project_path / 'index.html').exists():
        console.print("[yellow]Warning: index.html not found in project directory.[/yellow]")
        return False
    
    if intent == 'web_app' and not (project_path / 'app.py').exists():
        console.print("[yellow]Warning: app.py not found. Flask app needs to be running separately.[/yellow]")
        console.print("[dim]For Flask apps, run: cd {project_path} && python app.py[/dim]")
        return False
    
    # Start server
    server_thread, httpd = start_preview_server(project_path, port)
    
    if server_thread is None or httpd is None:
        return False
    
    # Open browser
    if open_browser(url):
        console.print(f"\n[green]Local preview started at {url}[/green]")
        console.print(f"[dim]Server running in background. Press Ctrl+C to stop.[/dim]")
        console.print(f"[dim]Preview directory: {project_path}[/dim]\n")
        return True
    else:
        # Server started but browser failed - user can still access manually
        console.print(f"\n[yellow]⚠ Server started at {url}, but could not open browser automatically.[/yellow]")
        console.print(f"[dim]Please manually open: {url}[/dim]\n")
        return True


def generate_project_files(intent: str, project_name: str, project_path: Path, user_responses: Dict[str, Any] = None) -> List[Dict[str, str]]:
    """
    Generate project files based on detected intent.
    Returns a list of dictionaries with 'file' and 'path' keys.
    """
    created_files = []
    
    if intent == 'landing_page':
        # Get user responses or use defaults
        product_name = user_responses.get('product_name', 'My Product') if user_responses else 'My Product'
        goal = user_responses.get('goal', 'info') if user_responses else 'info'
        style = user_responses.get('style', 'modern gradient') if user_responses else 'modern gradient'
        
        # Determine CTA button text based on goal
        cta_text = {
            'info': 'Learn More',
            'signup': 'Sign Up Now',
            'waitlist': 'Join Waitlist'
        }.get(goal, 'Get Started')
        
        # Landing page: HTML, CSS, JS
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{product_name} - Landing Page</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>
        <nav>
            <div class="logo">{product_name}</div>
            <ul class="nav-links">
                <li><a href="#home">Home</a></li>
                <li><a href="#features">Features</a></li>
                <li><a href="#about">About</a></li>
                <li><a href="#contact">Contact</a></li>
            </ul>
        </nav>
    </header>
    
    <section id="hero" class="hero">
        <div class="hero-content">
            <h1>Welcome to {product_name}</h1>
            <p>Your compelling headline goes here</p>
            <button class="cta-button">{cta_text}</button>
        </div>
    </section>
    
    <section id="features" class="features">
        <h2>Features</h2>
        <div class="feature-grid">
            <div class="feature-card">
                <h3>Feature 1</h3>
                <p>Description of feature 1</p>
            </div>
            <div class="feature-card">
                <h3>Feature 2</h3>
                <p>Description of feature 2</p>
            </div>
            <div class="feature-card">
                <h3>Feature 3</h3>
                <p>Description of feature 3</p>
            </div>
        </div>
    </section>
    
    <footer>
        <p>&copy; 2025 {product_name}. All rights reserved.</p>
    </footer>
    
    <script src="script.js"></script>
</body>
</html>"""
        
        # Generate CSS based on style choice
        if style == 'modern gradient':
            hero_bg = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
            cta_color = '#667eea'
        elif style == 'minimal':
            hero_bg = '#f8f9fa'
            cta_color = '#333'
        else:  # dark theme
            hero_bg = 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)'
            cta_color = '#fff'
        
        hero_text_color = 'white' if style != 'minimal' else '#333'
        body_bg = '#fff' if style != 'dark theme' else '#0f0f1e'
        body_color = '#333' if style != 'dark theme' else '#fff'
        header_bg = '#fff' if style != 'dark theme' else '#1a1a2e'
        footer_bg = '#333' if style != 'dark theme' else '#0a0a0a'
        
        css_content = f"""* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    line-height: 1.6;
    color: {body_color};
    background: {body_bg};
}}

header {{
    background: {header_bg};
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    position: sticky;
    top: 0;
    z-index: 100;
}}

nav {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 1rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.logo {{
    font-size: 1.5rem;
    font-weight: bold;
    color: #007bff;
}}

.nav-links {{
    display: flex;
    list-style: none;
    gap: 2rem;
}}

.nav-links a {{
    text-decoration: none;
    color: {body_color};
    transition: color 0.3s;
}}

.nav-links a:hover {{
    color: #007bff;
}}

.hero {{
    background: {hero_bg};
    color: {hero_text_color};
    padding: 100px 2rem;
    text-align: center;
}}

.hero-content h1 {{
    font-size: 3rem;
    margin-bottom: 1rem;
}}

.hero-content p {{
    font-size: 1.25rem;
    margin-bottom: 2rem;
}}

.cta-button {{
    background: {cta_color if style == 'minimal' else '#fff'};
    color: {cta_color if style != 'minimal' else '#fff'};
    border: none;
    padding: 12px 30px;
    font-size: 1.1rem;
    border-radius: 5px;
    cursor: pointer;
    transition: transform 0.3s;
}}

.cta-button:hover {{
    transform: scale(1.05);
}}

.features {{
    max-width: 1200px;
    margin: 80px auto;
    padding: 0 2rem;
}}

.features h2 {{
    text-align: center;
    font-size: 2.5rem;
    margin-bottom: 3rem;
}}

.feature-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
}}

.feature-card {{
    background: {'#f8f9fa' if style != 'dark theme' else '#1a1a2e'};
    padding: 2rem;
    border-radius: 8px;
    text-align: center;
    transition: transform 0.3s;
}}

.feature-card:hover {{
    transform: translateY(-5px);
}}

.feature-card h3 {{
    margin-bottom: 1rem;
    color: #007bff;
}}

footer {{
    background: {footer_bg};
    color: white;
    text-align: center;
    padding: 2rem;
    margin-top: 80px;
}}

@media (max-width: 768px) {{
    .nav-links {{
        flex-direction: column;
        gap: 1rem;
    }}
    
    .hero-content h1 {{
        font-size: 2rem;
    }}
    
    .feature-grid {{
        grid-template-columns: 1fr;
    }}
}}"""
        
        js_content = """// Landing page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // CTA button click handler
    const ctaButton = document.querySelector('.cta-button');
    if (ctaButton) {
        ctaButton.addEventListener('click', function() {
            alert('Get started clicked! Add your signup/login logic here.');
        });
    }
});"""
        
        files = [
            ('index.html', html_content),
            ('style.css', css_content),
            ('script.js', js_content)
        ]
        
    elif intent == 'web_app':
        # Get user responses
        app_type = user_responses.get('app_type', 'to-do') if user_responses else 'to-do'
        auth_mode = user_responses.get('auth_mode', 'offline') if user_responses else 'offline'
        
        # Web app: Flask app (Python)
        if app_type == 'to-do':
            app_description = 'To-Do List App'
            app_title = 'My To-Do List'
        elif app_type == 'notes':
            app_description = 'Notes App'
            app_title = 'My Notes'
        else:  # tracker
            app_description = 'Tracker App'
            app_title = 'My Tracker'
        
        auth_import = 'from flask_login import LoginManager, login_required, current_user\n' if auth_mode == 'login' else ''
        auth_decorator = '@login_required\n    ' if auth_mode == 'login' else ''
        auth_setup = '''
# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    # Load user from database
    return None  # Implement your user loading logic
''' if auth_mode == 'login' else ''
        
        app_py = f"""from flask import Flask, render_template, request, jsonify
import os
{auth_import}
app = Flask(__name__)
{auth_setup}
@app.route('/')
{auth_decorator}def index():
    return render_template('index.html', app_title='{app_title}')

@app.route('/api/data', methods=['GET'])
{auth_decorator}def get_data():
    # API endpoint for {app_description}
    return jsonify({{'message': 'Hello from Flask API', 'status': 'success', 'app_type': '{app_type}'}})

@app.route('/api/data', methods=['POST'])
{auth_decorator}def post_data():
    # POST endpoint for {app_description}
    data = request.get_json()
    return jsonify({{'received': data, 'status': 'success'}})

if __name__ == '__main__':
    app.run(debug=True, port=5000)"""
        
        templates_index = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web App</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            padding: 2rem;
            background: #f5f5f5;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            margin-bottom: 2rem;
            color: #333;
        }
        .form-group {
            margin-bottom: 1.5rem;
        }
        label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: bold;
        }
        input, textarea {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 1rem;
        }
        button {
            background: #007bff;
            color: white;
            border: none;
            padding: 0.75rem 2rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 1rem;
        }
        button:hover {
            background: #0056b3;
        }
        #output {
            margin-top: 2rem;
            padding: 1rem;
            background: #f8f9fa;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Web Application</h1>
        <form id="appForm">
            <div class="form-group">
                <label for="name">Name:</label>
                <input type="text" id="name" name="name" required>
            </div>
            <div class="form-group">
                <label for="message">Message:</label>
                <textarea id="message" name="message" rows="4" required></textarea>
            </div>
            <button type="submit">Submit</button>
        </form>
        <div id="output"></div>
    </div>
    
    <script>
        document.getElementById('appForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const formData = {
                name: document.getElementById('name').value,
                message: document.getElementById('message').value
            };
            
            try {
                const response = await fetch('/api/data', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData)
                });
                const data = await response.json();
                document.getElementById('output').innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
            } catch (error) {
                document.getElementById('output').innerHTML = '<p style="color: red;">Error: ' + error.message + '</p>';
            }
        });
    </script>
</body>
</html>"""
        
        requirements_txt = """Flask==3.0.0
Werkzeug==3.0.1"""
        
        files = [
            ('app.py', app_py),
            ('templates/index.html', templates_index),
            ('requirements.txt', requirements_txt)
        ]
        
    elif intent == 'automation_script':
        # Automation script: Python file
        script_content = """#!/usr/bin/env python3
\"\"\"
Automation Script
Description: Add your automation task description here
\"\"\"

import os
import sys
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    \"\"\"Main function to execute automation tasks.\"\"\"
    logger.info("Starting automation script...")
    
    try:
        # TODO: Add your automation logic here
        # Example: Process files, send emails, fetch data, etc.
        
        logger.info("Automation completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Error occurred: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)"""
        
        files = [
            ('automation.py', script_content)
        ]
        
    elif intent == 'data_script':
        # Data script: Python script for data analysis
        data_script = """#!/usr/bin/env python3
\"\"\"
Data Analysis Project
Description: Load and analyze CSV data
\"\"\"

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set style for plots
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)


def load_data(file_path: str) -> pd.DataFrame:
    \"\"\"Load data from CSV file.\"\"\"
    try:
        df = pd.read_csv(file_path)
        print(f"✓ Loaded {len(df)} rows and {len(df.columns)} columns")
        return df
    except FileNotFoundError:
        print(f"✗ Error: File '{file_path}' not found")
        return None
    except Exception as e:
        print(f"✗ Error loading data: {e}")
        return None


def explore_data(df: pd.DataFrame):
    \"\"\"Explore the dataset with basic statistics.\"\"\"
    print("\\n" + "="*50)
    print("DATASET OVERVIEW")
    print("="*50)
    print(f"Shape: {df.shape}")
    print(f"\\nColumn names: {list(df.columns)}")
    print(f"\\nData types:\\n{df.dtypes}")
    print(f"\\nMissing values:\\n{df.isnull().sum()}")
    print(f"\\nBasic statistics:\\n{df.describe()}")


def visualize_data(df: pd.DataFrame, output_dir: str = "output"):
    \"\"\"Create visualizations of the data.\"\"\"
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Example: Create histogram for numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        for col in numeric_cols[:3]:  # Limit to first 3 numeric columns
            plt.figure()
            df[col].hist(bins=30)
            plt.title(f'Distribution of {col}')
            plt.xlabel(col)
            plt.ylabel('Frequency')
            plt.savefig(output_path / f'{col}_histogram.png')
            plt.close()
            print(f"✓ Saved histogram: {output_path / f'{col}_histogram.png'}")


def main():
    \"\"\"Main function.\"\"\"
    # TODO: Update this path to your CSV file
    data_file = "data.csv"
    
    # Load data
    df = load_data(data_file)
    if df is None:
        print("\\nPlease update the 'data_file' variable with your CSV file path.")
        return
    
    # Explore data
    explore_data(df)
    
    # Create visualizations
    print("\\n" + "="*50)
    print("CREATING VISUALIZATIONS")
    print("="*50)
    visualize_data(df)
    
    # TODO: Add your analysis here
    # Example analyses:
    # - Correlation analysis
    # - Group by operations
    # - Filtering and aggregations
    # - Feature engineering
    
    print("\\n✓ Analysis complete!")


if __name__ == "__main__":
    main()"""
        
        requirements_txt = """pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
seaborn>=0.12.0"""
        
        files = [
            ('analyze_data.py', data_script),
            ('requirements.txt', requirements_txt)
        ]
        
    else:
        # Unknown intent - create a basic README
        readme_content = f"""# {project_name.replace('_', ' ').title()}

Project generated by ZETA CLI.

## Description
Add your project description here.

## Getting Started
1. Install dependencies (if any)
2. Run the project
3. Follow the instructions in the code

## Files
This project contains the following files:
- (Files will be listed here)
"""
        files = [
            ('README.md', readme_content)
        ]
    
    # Create the files
    for file_path, content in files:
        full_path = project_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Ensure content is not empty
            if not content or len(str(content).strip()) == 0:
                console.print(f"[yellow]⚠ Warning: {file_path} has empty content, using fallback template...[/yellow]")
                # Generate minimal fallback based on file type
                if file_path.endswith('.html'):
                    content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project</title>
</head>
<body>
    <h1>Welcome</h1>
    <p>Your project is ready. Edit this file to customize.</p>
</body>
</html>"""
                elif file_path.endswith('.css'):
                    content = """body { font-family: Arial, sans-serif; margin: 20px; }"""
                elif file_path.endswith('.js'):
                    content = """// JavaScript file\nconsole.log('Hello from ZETA!');"""
                elif file_path.endswith('.py'):
                    content = """#!/usr/bin/env python3\n# Python script\ndef main():\n    print('Hello from ZETA!')\n\nif __name__ == '__main__':\n    main()"""
            
            full_path.write_text(content, encoding='utf-8')
            created_files.append({
                'file': file_path,
                'path': str(full_path)
            })
        except Exception as e:
            console.print(f"[red]Error creating {file_path}: {e}[/red]")
            # Try fallback
            try:
                fallback_content = "<!DOCTYPE html><html><body><h1>Error</h1><p>Could not generate file.</p></body></html>" if file_path.endswith('.html') else "# Error: Could not generate file"
                full_path.write_text(fallback_content, encoding='utf-8')
                created_files.append({
                    'file': file_path,
                    'path': str(full_path)
                })
            except:
                pass
    
    return created_files


def detect_intent(task: str) -> str:
    """
    Detect user intent from natural language prompt.
    
    Returns one of: 'web_app', 'landing_page', 'automation_script', 'data_script', 'other'
    """
    task_lower = task.lower()
    
    # Simple keyword detection as specified
    if any(keyword in task_lower for keyword in ['landing', 'landing page', 'website', 'web page', 'homepage', 'marketing page']):
        return 'landing_page'
    elif any(keyword in task_lower for keyword in ['to-do', 'todo', 'task', 'task list', 'app', 'application', 'web app']):
        return 'web_app'
    elif any(keyword in task_lower for keyword in ['automate', 'automation', 'email', 'script', 'bot']):
        return 'automation_script'
    elif any(keyword in task_lower for keyword in ['data', 'csv', 'dataset', 'analysis', 'analyze']):
        return 'data_script'
    else:
        return 'other'


def detect_vague_task(task: str) -> bool:
    """Detect if a task is too vague."""
    vague_keywords = ["make", "create", "build", "make a", "create a", "build a"]
    task_lower = task.lower()
    
    # Check if task is very short or contains vague keywords without specifics
    if len(task.split()) < 4:
        return True
    
    for keyword in vague_keywords:
        if keyword in task_lower:
            # Check if there's more detail after the keyword
            parts = task_lower.split(keyword, 1)
            if len(parts) > 1 and len(parts[1].strip().split()) < 3:
                return True
    
    return False


def show_welcome():
    """Display welcome message like Kimi CLI."""
    # Load config first
    load_config()
    
    # Get current directory
    current_dir = str(Path.cwd())
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    # Get model/provider info - read at runtime
    provider = os.getenv("ZETA_PROVIDER", "ollama").lower()
    model_name = os.getenv("ZETA_MODEL", "")
    
    if provider == "ollama":
        model_status = f"[yellow]Ollama (local)[/yellow]"
        if model_name:
            model_status += f" - {model_name}"
        model_status += f"\n[dim]Send `zeta setup` to configure cloud APIs for faster responses[/dim]"
    elif provider == "openai":
        model_status = f"[green]OpenAI[/green] - {model_name or 'gpt-4o-mini'}"
    elif provider == "anthropic":
        model_status = f"[green]Anthropic Claude[/green] - {model_name or 'claude-3-5-sonnet-20241022'}"
    elif provider == "google":
        model_status = f"[green]Google Gemini[/green] - {model_name or 'gemini-1.5-flash'}"
    else:
        model_status = f"[yellow]not set[/yellow], send `zeta setup` to configure"
    
    # Welcome panel with tagline next to welcome message
    welcome_text = f"""[bold cyan]Welcome to ZETA CLI![/bold cyan] [dim]— The most accessible AI terminal agent for learning and building.[/dim]

Send `zeta --help` for help information.

[dim]Directory:[/dim] `{current_dir}`
[dim]Session:[/dim] `{session_id}`
[dim]Model:[/dim] {model_status}"""
    
    # Create panel
    console.print(Panel(
        welcome_text,
        border_style="cyan",
        padding=(1, 2),
        title="[bold cyan]ZETA[/bold cyan]"
    ))


@click.group()
@click.version_option(version="1.0.7")
def cli():
    """ZETA - The most accessible AI terminal agent for learning and building.
    
    A friendly AI terminal agent for non-technical users.
    
    Supports multiple LLM providers:
    - OpenAI (set OPENAI_API_KEY and ZETA_PROVIDER=openai)
    - Anthropic/Claude (set ANTHROPIC_API_KEY and ZETA_PROVIDER=anthropic)
    - Google/Gemini (set GOOGLE_API_KEY and ZETA_PROVIDER=google)
    - Ollama/Local (default, requires Ollama running)
    """
    pass


@cli.command()
@click.argument('task', required=False)
@click.option('--teach', is_flag=True, help='Enable teaching mode with detailed explanations')
@click.option('--critic', is_flag=True, help='Enable critic mode for code review')
def run(task: Optional[str], teach: bool, critic: bool):
    """Run ZETA with a task. If no task provided, starts interactive mode."""
    # Load configuration from file
    load_config()
    
    # Check if configured (like Kimi CLI's /setup prompt)
    if not is_configured():
        console.print("\n[yellow]⚠ ZETA is not configured yet![/yellow]")
        console.print("[cyan]Let's set it up quickly...[/cyan]\n")
        
        if Confirm.ask("[bold]Would you like to run setup now?[/bold]", default=True):
            # Call setup function directly
            _run_setup()
            # Reload config after setup
            load_config()
        else:
            console.print("\n[yellow]You can run 'zeta setup' later to configure ZETA.[/yellow]")
            console.print("[yellow]For now, ZETA will try to use Ollama (local).[/yellow]\n")
    
    show_welcome()
    
    if not task:
        task = Prompt.ask("\n[bold]What would you like to do?[/bold]")
    
    try:
        agent = ZetaAgent(teach_mode=teach, critic_mode=critic)
    except Exception as e:
        error_msg = str(e)
        if "not configured" in error_msg.lower() or "not set" in error_msg.lower():
            console.print("\n[red]Configuration Error[/red]")
            console.print("[yellow]Please run 'zeta setup' to configure ZETA.[/yellow]\n")
            return
        else:
            raise
    
    # Check if task is vague
    if detect_vague_task(task):
        console.print("\n[yellow]Hmm...[/yellow] [bold]I need a bit more information![/bold]\n")
        
        clarification = agent.ask_clarifying_question(task)
        if clarification:
            console.print(f"[bold]{clarification['question']}[/bold]\n")
            for i, option in enumerate(clarification['options'], 1):
                console.print(f"  [cyan]{i}.[/cyan] {option}")
            
            choice = Prompt.ask("\n[bold]Choose an option[/bold]", default="1")
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(clarification['options']):
                    task = clarification['options'][idx]
                    console.print(f"\n[green]Great choice![/green] Let's create: {task.lower()}.\n")
                else:
                    console.print("[yellow]Invalid choice. Using default option.[/yellow]")
            except ValueError:
                console.print("[yellow]Invalid input. Continuing with original task.[/yellow]")
    
    # Reset confirmed files for this new task (fresh start)
    ZetaTools.reset_confirmed_files()
    
    # Detect user intent
    detected_intent = detect_intent(task)
    agent.intent = detected_intent
    
    # Extract project name and set up project directory
    project_name = extract_project_name(task) or "zeta_project"
    project_base = Path("ZETA_projects")
    project_path = project_base / project_name
    
    agent.project_name = project_name
    agent.project_path = project_path
    
    # Auto-generate project files based on intent (if not unknown or other)
    preview_started = False
    files_auto_generated = False
    created_files = []
    user_responses = {}
    
    if detected_intent not in ['unknown', 'other']:
        console.print(f"\n[cyan]Detected intent: {detected_intent.replace('_', ' ')}[/cyan]\n")
        
        # Ask clarifying questions BEFORE generating files
        try:
            user_responses = ask_clarifying_questions(detected_intent, task)
            console.print(f"\n[green]✓ Got it! Generating your project...[/green]\n")
        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled by user.[/yellow]\n")
            return
        except Exception as e:
            console.print(f"[yellow]Warning: Error asking questions: {e}[/yellow]")
            console.print("[dim]Continuing with defaults...[/dim]\n")
        
        console.print(f"[cyan]Creating project: {project_name}[/cyan]\n")
        
        try:
            created_files = generate_project_files(detected_intent, project_name, project_path, user_responses)
            
            if created_files:
                files_auto_generated = True
                # Print structured summary
                console.print(Panel.fit(
                    f"[bold green]Project created successfully![/bold green]\n\n"
                    f"[bold]Project:[/bold] {project_name}\n"
                    f"[bold]Location:[/bold] {project_path}\n\n"
                    f"[bold]Created Files:[/bold]\n" +
                    "\n".join([f"  • {f['file']}" for f in created_files]),
                    title="[bold cyan]ZETA Project Generator[/bold cyan]",
                    border_style="green"
                ))
                
                console.print(f"\n[dim]Files saved to: {project_path}[/dim]\n")
                
                # Show educational summary
                file_explanations = generate_file_explanations(detected_intent, created_files)
                console.print(Panel(
                    file_explanations,
                    title="[bold yellow]What Each File Does[/bold yellow]",
                    border_style="yellow",
                    padding=(1, 2)
                ))
                console.print()  # Add spacing
                
                # Offer browser preview for landing_page and web_app
                if detected_intent in ['landing_page', 'web_app']:
                    if Confirm.ask("\n[bold cyan]Would you like to view it live in your browser?[/bold cyan]", default=True):
                        preview_started = preview_project(project_path, detected_intent)
                
                # Completion response
                response = f"""Perfect! I've created your {detected_intent.replace('_', ' ')} project based on your preferences!

**Project Location:** `{project_path}`

**Files Created:**
{chr(10).join([f"- {f['file']}" for f in created_files])}

Your project is ready! You can now:
- Open and edit the files in any text editor
- Customize the content to match your needs
- View it in your browser (if you chose the preview option)

I can explain how each file works. Would you like me to?"""
            else:
                # Files weren't generated, proceed with LLM
                files_auto_generated = False
        except Exception as e:
            console.print(f"[yellow]Warning: Could not auto-generate files: {e}[/yellow]")
            console.print("[dim]ZETA will proceed with normal task processing...[/dim]\n")
            files_auto_generated = False
    
    # Only process with LLM if files weren't auto-generated
    if not files_auto_generated:
        # Process the task
        console.print("\n[dim]Processing your request...[/dim]\n")
        
        # For creation tasks, add context about project directory
        if detected_intent != 'unknown' and ("create" in task.lower() or "make" in task.lower() or "build" in task.lower()):
            task = f"{task} IMPORTANT: Create files in the '{project_path}' directory. Use the write_file tool with COMPLETE code/content inside triple quotes. Do NOT use empty content - include the FULL code."
        elif "create" in task.lower() or "make" in task.lower() or "build" in task.lower():
            task = f"{task}. IMPORTANT: Use tools to create files or execute commands immediately. Include COMPLETE code/content in write_file calls using triple quotes. Do NOT ask questions - just create it."
        
        response = agent.process_task(task)
        
        # Check if response is just questions (not actual creation)
        question_keywords = ["what", "how", "would you", "could you", "which", "do you want", "should i"]
        has_questions = any(keyword in response.lower() for keyword in question_keywords) and "?" in response
        
        if has_questions and not any(keyword in response.lower() for keyword in ["created", "wrote", "executed", "made", "file", "tool"]):
            # LLM is asking questions instead of acting - force it to create
            console.print("[yellow]Creating that for you now...[/yellow]\n")
            task_with_action = f"Create {task.lower()} RIGHT NOW. Use write_file or run_command tools immediately. Do NOT ask any questions - just create files and execute commands."
            response = agent.process_task(task_with_action)
        
        # Display response
        console.print(Panel(Markdown(response), title="ZETA", border_style="cyan"))
    else:
        # Files were auto-generated, display the completion message
        console.print(Panel(Markdown(response), title="ZETA", border_style="cyan"))
        # Mark as successful creation for learning prompt
        response = response  # Keep response for learning prompt logic
    
    # If critic mode is enabled, review any created code files
    if critic:
        code_extensions = ['.py', '.js', '.html', '.css', '.ts', '.jsx', '.tsx']
        code_files = []
        for ext in code_extensions:
            code_files.extend(Path(".").glob(f"*{ext}"))
        
        if code_files:
            console.print("\n[bold yellow]🔍 Critic Mode: Reviewing code...[/bold yellow]\n")
            for code_file in code_files:
                try:
                    code = code_file.read_text(encoding='utf-8')
                    review = agent.critic_review(code, str(code_file))
                    
                    score = review.get("score", 5)
                    color = "green" if score >= 8 else "yellow" if score >= 6 else "red"
                    
                    console.print(f"\n[bold]{code_file.name}[/bold] - Score: [{color}]{score}/10[/{color}]")
                    console.print(f"[dim]{review.get('explanation', 'No explanation')}[/dim]")
                    
                    if score < 8:
                        issues = review.get("issues", [])
                        suggestions = review.get("suggestions", [])
                        if issues:
                            console.print("\n[bold red]Issues:[/bold red]")
                            for issue in issues:
                                console.print(f"  • {issue}")
                        if suggestions:
                            console.print("\n[bold green]Suggestions:[/bold green]")
                            for suggestion in suggestions:
                                console.print(f"  • {suggestion}")
                except Exception as e:
                    console.print(f"[yellow]Could not review {code_file}: {e}[/yellow]")
    
    # Check if task was actually completed successfully
    # Only ask "Would you like to learn?" if task was completed without errors
    response_lower = response.lower()
    
    # Check for error/problem indicators - don't ask "learn?" if ZETA is having problems
    error_indicators = ["trouble", "problem", "error", "failed", "can't", "cannot", "unable", "still having", "looks like", "having trouble"]
    has_errors = any(indicator in response_lower for indicator in error_indicators)
    
    # Check if response indicates successful creation
    creation_keywords = ["created", "wrote", "successfully", "completed", "done", "finished", "ready"]
    has_creation = any(keyword in response_lower for keyword in creation_keywords)
    
    # Check if files were actually created (look for file mentions and verify they exist)
    import re
    file_mentions = re.findall(r'[\w\-_]+\.(?:py|js|html|css|txt|json|md|ts|jsx|tsx)', response, re.IGNORECASE)
    files_exist = False
    if file_mentions:
        # Check if any mentioned files actually exist
        for file_name in file_mentions[:5]:  # Check first 5 files mentioned
            if Path(file_name).exists():
                files_exist = True
                break
    
    # Only ask about learning if task was completed successfully AND no errors/problems mentioned
    # Also check if files were auto-generated successfully
    if files_auto_generated or ((has_creation or files_exist) and not has_errors):
        # Log the interaction
        explanation = agent.explain_action("Task execution", response, teach_mode=teach)
        ZetaLogger.log(f"User task: {task}", explanation)
        
        # Ask if user wants to learn more (only after successful completion)
        console.print()  # Add spacing
        if Confirm.ask("[bold]Would you like to learn how this works?[/bold]", default=False):
            lesson_prompt = f"Explain how '{task}' works in simple terms suitable for beginners."
            lesson = agent.process_task(lesson_prompt)
            console.print(Panel(Markdown(lesson), title="Lesson", border_style="green"))
            ZetaLogger.log("Learning session", lesson, lesson=lesson)
    else:
        # Task might not be complete - just log without asking about learning
        explanation = agent.explain_action("Task execution", response, teach_mode=teach)
        ZetaLogger.log(f"User task: {task}", explanation)


def _run_setup():
    """Internal setup function (called by both CLI command and auto-setup)."""
    # Load existing config first
    load_config()
    
    console.print("\n[bold cyan]ZETA Setup Wizard[/bold cyan]\n")
    console.print("Let's configure ZETA to work with your preferred AI provider.\n")
    
    # Choose provider
    console.print("[bold]Choose your AI provider:[/bold]")
    console.print("  1. Google Gemini (FREE tier available) [cyan]Recommended[/cyan]")
    console.print("  2. OpenAI (GPT-4, GPT-3.5)")
    console.print("  3. Anthropic Claude")
    console.print("  4. Ollama (Local, requires Ollama installed)")
    
    choice = Prompt.ask("\n[bold]Enter choice (1-4)[/bold]", default="1")
    
    if choice == "1":
        # Google Gemini setup
        console.print("\n[bold]Setting up Google Gemini...[/bold]")
        console.print("Get your FREE API key: https://makersuite.google.com/app/apikey\n")
        
        api_key = Prompt.ask("[bold]Enter your Google API key[/bold]")
        if api_key:
            # Set environment variables
            os.environ["ZETA_PROVIDER"] = "google"
            os.environ["GOOGLE_API_KEY"] = api_key
            os.environ["ZETA_MODEL"] = "gemini-1.5-flash"  # Use valid model name (NO -latest suffix)
            
            config = {
                "ZETA_PROVIDER": "google",
                "ZETA_MODEL": "gemini-1.5-flash"
            }
            save_config(config)
            
            console.print("\n[green]✓ Configuration saved![/green]")
            
            # Check if package is installed
            try:
                import langchain_google_genai
                console.print("[green]✓ Google Gemini support is installed![/green]")
            except ImportError:
                console.print("\n[yellow]⚠ Installing Google Gemini support...[/yellow]")
                import subprocess
                result = subprocess.run(["pip", "install", "langchain-google-genai"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    console.print("[green]✓ Installation complete![/green]")
                else:
                    console.print("[yellow]⚠ Installation had issues. You may need to install manually:[/yellow]")
                    console.print("[yellow]  pip install langchain-google-genai[/yellow]")
    
    elif choice == "2":
        # OpenAI setup
        console.print("\n[bold]Setting up OpenAI...[/bold]")
        console.print("Get your API key: https://platform.openai.com/api-keys\n")
        
        api_key = Prompt.ask("[bold]Enter your OpenAI API key[/bold]")
        if api_key:
            os.environ["ZETA_PROVIDER"] = "openai"
            os.environ["OPENAI_API_KEY"] = api_key
            os.environ["ZETA_MODEL"] = "gpt-4o-mini"
            
            config = {
                "ZETA_PROVIDER": "openai",
                "ZETA_MODEL": "gpt-4o-mini"
            }
            save_config(config)
            
            console.print("\n[green]✓ Configuration saved![/green]")
            
            try:
                import langchain_openai
                console.print("[green]✓ OpenAI support is installed![/green]")
            except ImportError:
                console.print("\n[yellow]⚠ Installing OpenAI support...[/yellow]")
                import subprocess
                result = subprocess.run(["pip", "install", "langchain-openai"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    console.print("[green]✓ Installation complete![/green]")
                else:
                    console.print("[yellow]⚠ Installation had issues. You may need to install manually:[/yellow]")
                    console.print("[yellow]  pip install langchain-openai[/yellow]")
    
    elif choice == "3":
        # Anthropic setup
        console.print("\n[bold]Setting up Anthropic Claude...[/bold]")
        console.print("Get your API key: https://console.anthropic.com/\n")
        
        api_key = Prompt.ask("[bold]Enter your Anthropic API key[/bold]")
        if api_key:
            os.environ["ZETA_PROVIDER"] = "anthropic"
            os.environ["ANTHROPIC_API_KEY"] = api_key
            os.environ["ZETA_MODEL"] = "claude-3-haiku-20240307"
            
            config = {
                "ZETA_PROVIDER": "anthropic",
                "ZETA_MODEL": "claude-3-haiku-20240307"
            }
            save_config(config)
            
            console.print("\n[green]✓ Configuration saved![/green]")
            
            try:
                import langchain_anthropic
                console.print("[green]✓ Anthropic support is installed![/green]")
            except ImportError:
                console.print("\n[yellow]⚠ Installing Anthropic support...[/yellow]")
                import subprocess
                result = subprocess.run(["pip", "install", "langchain-anthropic"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    console.print("[green]✓ Installation complete![/green]")
                else:
                    console.print("[yellow]⚠ Installation had issues. You may need to install manually:[/yellow]")
                    console.print("[yellow]  pip install langchain-anthropic[/yellow]")
    
    elif choice == "4":
        # Ollama setup
        console.print("\n[bold]Setting up Ollama (Local)...[/bold]")
        console.print("Make sure Ollama is installed and running.\n")
        
        model = Prompt.ask("[bold]Enter model name[/bold]", default="llama3.2:latest")
        os.environ["ZETA_PROVIDER"] = "ollama"
        os.environ["ZETA_MODEL"] = model
        
        config = {
            "ZETA_PROVIDER": "ollama",
            "ZETA_MODEL": model
        }
        save_config(config)
        
        console.print("\n[green]✓ Configuration saved![/green]")
        console.print("\n[yellow]Note:[/yellow] Make sure Ollama is running before using ZETA!")
        console.print("[yellow]To start Ollama:[/yellow] Just run 'ollama' or start it from Start Menu")
    
    console.print("\n[bold green]✓ Setup complete! Try: zeta run \"say hello\"[/bold green]\n")


@cli.command()
def setup():
    """Interactive setup wizard to configure ZETA with any provider."""
    _run_setup()


@cli.command()
def teach():
    """Start an interactive teaching session."""
    console.print(Panel.fit(
        "[bold green]Teaching Mode[/bold green]\n"
        "[dim]Learn coding concepts in detail[/dim]",
        border_style="green"
    ))
    
    agent = ZetaAgent(teach_mode=True)
    
    console.print("\n[bold]What would you like to learn about?[/bold]")
    console.print("[dim]Type 'exit' to end the session[/dim]\n")
    
    while True:
        topic = Prompt.ask("[bold cyan]You[/bold cyan]")
        if topic.lower() in ['exit', 'quit', 'q']:
            console.print("\n[green]Great learning session! Keep coding! 🚀[/green]")
            break
        
        response = agent.process_task(f"Explain '{topic}' in detail with definitions and examples for beginners.")
        console.print(Panel(Markdown(response), title="📖 Lesson", border_style="green"))
        
        ZetaLogger.log(f"Teaching: {topic}", response, lesson=response)


@cli.command()
def log():
    """View your ZETA learning log."""
    console.print(Panel.fit(
        "[bold yellow]📝 Learning Log[/bold yellow]",
        border_style="yellow"
    ))
    console.print()
    ZetaLogger.show_log()


if __name__ == "__main__":
    cli()

