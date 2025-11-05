from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import typer
from rich.align import Align
from rich.columns import Columns
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from .cli_components.app import app
from .cli_components.constants import PROMPT
from .cli_components import state as cli_state
from .cli_components.state import console, in_selection_hub, set_selection_hub_active
from .cli_components.env import (
    bootstrap_env,
    env_status_label,
    global_env_status_label,
    edit_env_file,
    edit_global_env_file,
    load_env_files,
    load_global_env,
    tail_bytes,
    extract_error_block,
    tty_log_path,
    current_tty_id,
    count_env_keys_in_file,
    global_env_path,
)
from .cli_components.instructions import edit_langcode_md
from .cli_components.mcp import edit_mcp_json, mcp_status_label, mcp_target_path
from .cli_components.display import (
    print_session_header,
    panel_agent_output,
    panel_router_choice,
    show_loader,
    pause_if_in_launcher,
    normalize_chat_history_for_anthropic,
    session_banner,
    print_langcode_ascii,
)
from .cli_components.agents import (
    agent_cache_get,
    agent_cache_put,
    resolve_provider,
    build_react_agent_with_optional_llm,
    build_deep_agent_with_optional_llm,
)
from .cli_components.runtime import (
    InputPatch,
    TodoLive,
    RichDeepLogs,
    maybe_coerce_img_command,
    extract_last_content,
    thread_id_for,
)
from .cli_components.todos import render_todos_panel, diff_todos, short, _coerce_sequential_todos
from .cli_components.launcher import (
    launcher_loop,
    default_state,
    help_content,
    list_ollama_models,
    provider_model_choices,
)
from .config_core import get_model, get_model_info, get_model_by_name
from .workflows.feature_impl import FEATURE_INSTR
from .workflows.bug_fix import BUGFIX_INSTR
from .workflows.auto import AUTO_DEEP_INSTR



def _unwrap_exc(e: BaseException) -> BaseException:

    """Drill down through ExceptionGroup/TaskGroup, __cause__, and __context__ to the root error."""

    seen = set()

    while True:

        # Python 3.11 ExceptionGroup (incl. TaskGroup)

        inner = getattr(e, "exceptions", None)

        if inner:

            e = inner[0]

            continue

        if getattr(e, "__cause__", None) and e.__cause__ not in seen:

            seen.add(e)

            e = e.__cause__

            continue

        if getattr(e, "__context__", None) and e.__context__ not in seen:

            seen.add(e)

            e = e.__context__

            continue

        return e



def _friendly_agent_error(e: BaseException) -> str:

    root = _unwrap_exc(e)

    name = root.__class__.__name__

    msg = (str(root) or "").strip() or "(no details)"

    return (

        "Sorry, a tool run failed. Please try again :)\n\n"

        f"| {name}: {msg}\n\n"

    )



def _todos_to_text_summary(todos: List[dict]) -> str:

    seq = _coerce_sequential_todos(todos)

    icon = {"pending": "○", "in_progress": "◔", "completed": "✓"}

    lines: List[str] = []

    for idx, item in enumerate(seq, 1):

        status = (item.get("status") or "pending").lower().replace("-", "_")

        mark = icon.get(status, "-")

        content = (item.get("content") or "").strip() or "(empty)"

        lines.append(f"{idx}. {mark} {content} [{status.replace('_', ' ')}]")

    header = "Agent steps:"

    return header + ("\n" + "\n".join(lines) if lines else "\n(no steps recorded)")



_AGENT_EXECUTOR = ThreadPoolExecutor(max_workers=2)


def _dispatch_from_state(chosen: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """Dispatch the chosen launcher state and report navigation plus status text."""
    if chosen.get("llm") == "ollama" and not list_ollama_models():
        return {"nav": "select", "info": "Cannot start: no Ollama models installed."}

    try:
        cmd = chosen["command"]
        if cmd == "chat":
            nav = chat(
                llm=chosen["llm"],
                project_dir=chosen["project_dir"],
                mode=chosen["engine"],
                auto=bool(chosen["autopilot"] and chosen["engine"] == "deep"),
                router=chosen["router"],
                priority=chosen["priority"],
                verbose=False,
            )
            return {"nav": nav, "info": None}

        if cmd == "feature":
            req = console.input("[bold]Feature request[/bold] (e.g. Add a dark mode toggle): ").strip()
            if not req:
                return {"nav": "select", "info": "Feature request aborted (empty input)."}
            feature(
                request=req,
                llm=chosen["llm"],
                project_dir=chosen["project_dir"],
                test_cmd=chosen["test_cmd"],
                apply=chosen["apply"],
                router=chosen["router"],
                priority=chosen["priority"],
                verbose=False,
            )
            return {"nav": "select", "info": "Feature workflow completed."}

        if cmd == "fix":
            req = console.input("[bold]Bug summary[/bold] (e.g. Fix crash on image upload) [Enter to skip]: ").strip() or None
            log_path = console.input("[bold]Path to error log[/bold] [Enter to skip]: ").strip()
            log = Path(log_path) if log_path else None
            fix(
                request=req,
                log=log if log and log.exists() else None,
                llm=chosen["llm"],
                project_dir=chosen["project_dir"],
                test_cmd=chosen["test_cmd"],
                apply=chosen["apply"],
                router=chosen["router"],
                priority=chosen["priority"],
                verbose=False,
            )
            return {"nav": "select", "info": "Fix workflow completed."}

        req = console.input("[bold]Analysis question[/bold] (e.g. What are the main components?): ").strip()
        if not req:
            return {"nav": "select", "info": "Analysis aborted (empty question)."}
        analyze(
            request=req,
            llm=chosen["llm"],
            project_dir=chosen["project_dir"],
            router=chosen["router"],
            priority=chosen["priority"],
            verbose=False,
        )
        return {"nav": "select", "info": "Analysis results provided."}

    except RuntimeError as exc:
        return {"nav": "select", "info": str(exc)}
    except Exception as exc:
        return {"nav": "select", "info": _friendly_agent_error(exc)}

def selection_hub(initial_state: Optional[Dict[str, Any]] = None) -> None:
    """Persistent launcher loop so users can switch modes without restarting the CLI."""
    state = dict(initial_state or default_state())

    try:
        bootstrap_env(state["project_dir"], interactive_prompt_if_missing=True)
    except Exception:
        pass

    set_selection_hub_active(True)
    try:
        while True:
            chosen = launcher_loop(state)
            if not chosen:
                return
            state.update(chosen)
            result = _dispatch_from_state(chosen)
            nav = result.get("nav") if result else None
            info = result.get("info") if result else None
            if info:
                state["_status"] = info
            elif "_status" in state:
                state.pop("_status", None)
            if nav == "quit":
                console.print("\n[bold]Goodbye![/bold]")
                return
            if nav == "select":
                continue
    finally:
        set_selection_hub_active(False)



@app.command(help="Run a command inside a PTY and capture output to a session log (used by ix --from-tty).")

def wrap( 

    cmd: List[str] = typer.Argument(..., help="Command to run (e.g., pytest -q)"), 

    project_dir: Path = typer.Option(Path.cwd(), "--project-dir", exists=True, file_okay=False), 

    tty_id: Optional[str] = typer.Option(None, "--tty-id", help="Override session id (default: auto per TTY)"), 

): 

    log_path = tty_log_path(tty_id) 

    log_path.parent.mkdir(parents=True, exist_ok=True) 

    console.print(Panel.fit(Text(f"Logging to: {log_path}", style="dim"), title="TTY Capture", border_style="cyan")) 

    os.chdir(project_dir) 

    if platform.system().lower().startswith("win"): 

        with open(log_path, "a", encoding="utf-8", errors="ignore") as f: 

            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) 

            assert proc.stdout is not None 

            for line in proc.stdout: 

                sys.stdout.write(line) 

                f.write(line) 

            rc = proc.wait() 

            raise typer.Exit(rc) 

    else: 

        import pty, os as _os 

        with open(log_path, "a", encoding="utf-8", errors="ignore") as f: 

            old_env = dict(_os.environ) 

            _os.environ["LANGCODE_TTY_LOG"] = str(log_path) 

            _os.environ["LANGCODE_TTY_ID"] = tty_id or current_tty_id() 

            def _tee(master_fd): 

                data = _os.read(master_fd, 1024) 

                if data: 

                    try: 

                        f.write(data.decode("utf-8", "ignore")) 

                        f.flush() 

                    except Exception: 

                        pass 

                return data 

            try: 

                status = pty.spawn(cmd, master_read=_tee) 

            finally: 

                _os.environ.clear(); _os.environ.update(old_env) 

            raise typer.Exit(status >> 8) 



@app.command(help="Open a logged subshell. Anything you run here is captured for ix --from-tty.")

def shell( 

    project_dir: Path = typer.Option(Path.cwd(), "--project-dir", exists=True, file_okay=False), 

    tty_id: Optional[str] = typer.Option(None, "--tty-id", help="Override session id (default: auto per TTY)"), 

): 

    sh = os.environ.get("SHELL") if platform.system().lower() != "windows" else os.environ.get("COMSPEC", "cmd.exe") 

    if not sh: 

        sh = "/bin/bash" if platform.system().lower() != "windows" else "cmd.exe" 

    return wrap([sh], project_dir=project_dir, tty_id=tty_id)



@app.command(help="Run environment checks for providers, tools, and MCP.")

def doctor(

    project_dir: Path = typer.Option(Path.cwd(), "--project-dir", exists=True, file_okay=False)

):

    bootstrap_env(project_dir, interactive_prompt_if_missing=False)



    def yes(x): return Text("? " + x, style="green")

    def no(x):  return Text("? " + x, style="red")

    rows = []



    rows.append(yes(f"Python {sys.version.split()[0]} on {platform.platform()}"))



    for tool in ["git", "npx", "node", "ollama"]:

        rows.append(yes(f"{tool} found") if shutil.which(tool) else no(f"{tool} missing"))



    provider_keys = {

        "OPENAI_API_KEY": "OpenAI",

        "ANTHROPIC_API_KEY": "Anthropic",

        "GOOGLE_API_KEY": "Gemini",

        "GEMINI_API_KEY": "Gemini (alt)",

        "GROQ_API_KEY": "Groq",

        "TOGETHER_API_KEY": "Together",

        "FIREWORKS_API_KEY": "Fireworks",

        "PERPLEXITY_API_KEY": "Perplexity",

        "DEEPSEEK_API_KEY": "DeepSeek",

        "TAVILY_API_KEY": "Tavily (web search)"

    }

    provider_panel = Table.grid(padding=(0,2))

    provider_panel.add_column("Provider")

    provider_panel.add_column("Status")

    for env, label in provider_keys.items():

        ok = env in os.environ and bool(os.environ.get(env, "").strip())

        provider_panel.add_row(label, ("[green]OK[/green]" if ok else "[red]missing[/red]") + f"  [dim]{env}[/dim]")



    # MCP config

    mcp_path = mcp_target_path(project_dir)

    mcp_status = "exists" if mcp_path.exists() else "missing"

    mcp_card = Panel(Text(f"{mcp_status}: {os.path.relpath(mcp_path, project_dir)}"), title="MCP", border_style=("green" if mcp_path.exists() else "red"))



    ollama = shutil.which("ollama")

    if ollama:

        models = list_ollama_models()

        oll_text = ", ".join(models[:6]) + (" ..." if len(models) > 6 else "") if models else "(none installed)"

        oll_card = Panel(Text(oll_text), title="Ollama models", border_style=("green" if models else "yellow"))

    else:

        oll_card = Panel(Text("ollama not found"), title="Ollama", border_style="red")



    gpath = global_env_path()

    gexists = gpath.exists()

    gkeys = count_env_keys_in_file(gpath) if gexists else 0

    gmsg = f"{'exists' if gexists else 'missing'}: {gpath}\nkeys: {gkeys}"

    global_card = Panel(Text(gmsg), title="Global .env", border_style=("green" if gexists else "red"))



    console.print(Panel(Align.left(Text.assemble(*[r + Text("\n") for r in rows])), title="System", border_style="cyan"))

    console.print(Panel(provider_panel, title="Providers", border_style="cyan"))

    console.print(Columns([mcp_card, oll_card, global_card]))

    console.print(Panel(Text("Tip: run 'langcode instr' to set project rules; edit environment via the launcher."), border_style="blue"))



def _quick_route_free_text(free_text: str, project_dir: Path) -> Optional[str]: 

    """Route free-text to analyze/fix/chat based on simple intent heuristics.""" 

    t = free_text.lower().strip() 

    # Heuristics (intentionally simple; you can swap for an LLM classifier later) 

    if any(k in t for k in ["fix", "error", "traceback", "stack", "crash", "red tests", "failing", "broken"]): 

        # Try to pull recent error from TTY capture (see wrap/shell below) 

        return fix( 

            request=free_text, 

            log=None, 

            project_dir=project_dir, 

            from_tty=True,  # new flag added below 

            router=False, 

            verbose=False, 

        ) 

    if any(k in t for k in ["what's going on", "whats going on", "overview", "summary", "explain the codebase", "architecture"]): 

        analyze( 

            request=free_text, 

            project_dir=project_dir, 

            router=False, 

            verbose=False, 

        ) 

        return None 



    return chat( 

        message=[free_text], 

        project_dir=project_dir, 

        mode="react", 

        router=False, 

        verbose=False, 

        inline = True

    ) 



@app.callback(invoke_without_command=True)

def _root(

    ctx: typer.Context,

    project_dir: Path = typer.Option(Path.cwd(), "--project-dir", exists=True, file_okay=False),

):

    if ctx.invoked_subcommand is not None:

        return

    extras = [a for a in ctx.args if not a.startswith("-")]

    if extras:

        return chat(

            message=extras,

            project_dir=project_dir,

            mode="react",

            router=False,

            verbose=False,

            inline=True,  

        )

    selection_hub()

    raise typer.Exit()



@app.command(help="Open an interactive chat with the agent. Modes: react | deep (default: react). Use --auto in deep mode for full autopilot (plan+act with no questions).")

def chat(

    message: Optional[List[str]] = typer.Argument(None, help="Optional initial message to send (quotes not required)."),

    llm: Optional[str] = typer.Option(None, "--llm", help="anthropic | gemini | openai | ollama"),

    project_dir: Path = typer.Option(Path.cwd(), "--project-dir", exists=True, file_okay=False),

    mode: str = typer.Option("react", "--mode", help="react | deep"),

    auto: bool = typer.Option(False, "--auto", help="Autonomy mode: plan+act with no questions (deep mode only)."),

    router: bool = typer.Option(False, "--router", help="Auto-route to the most efficient LLM per query."),

    priority: str = typer.Option("balanced", "--priority", help="Router priority: balanced | cost | speed | quality"),

    verbose: bool = typer.Option(False, "--verbose", help="Show model selection panels (and deep logs)."),

    inline: bool = typer.Option(False, "--inline", help="Inline single-turn output (no banners/clear)."),

) -> Optional[str]:

    """

    Returns:

      - "quit": user explicitly exited chat; caller should terminate program

      - "select": user requested to return to launcher

      - None: normal return (caller may continue)

    """

    from rich.live import Live
    from langchain_core.messages import HumanMessage, AIMessage



    bootstrap_env(project_dir, interactive_prompt_if_missing=True)



    priority = (priority or "balanced").lower()

    if priority not in {"balanced", "cost", "speed", "quality"}:

        priority = "balanced"



    provider = resolve_provider(llm, router)

    mode = (mode or "react").lower()

    if mode not in {"react", "deep"}:

        mode = "react"



    input_queue: List[str] = []

    if isinstance(message, list):

        first_msg = " ".join(message).strip()

        if first_msg:

            input_queue.append(first_msg)



    if inline and input_queue:

        first = input_queue.pop(0)

        coerced = maybe_coerce_img_command(first)

        use_loader = not (mode == "react" and verbose)

        cm = show_loader() if use_loader else nullcontext()

        with cm:

            model_info = None

            chosen_llm = None

            if router:

                model_info = get_model_info(provider, coerced, priority)

                chosen_llm = get_model(provider, coerced, priority)

                model_key = model_info.get("langchain_model_name") if model_info else "default"

            else:

                env_override = os.getenv("LANGCODE_MODEL_OVERRIDE")

                chosen_llm = get_model_by_name(provider, env_override) if env_override else get_model(provider)

                model_key = env_override or "default"



            cache_key = (

                "deep" if mode == "deep" else "react",

                provider,

                model_key,

                str(project_dir.resolve()),

                bool(auto) if mode == "deep" else False,

            )

            agent = agent_cache_get(cache_key)

            if agent is None:

                if mode == "deep":

                    seed = AUTO_DEEP_INSTR if auto else None

                    agent = build_deep_agent_with_optional_llm(

                        provider=provider, project_dir=project_dir, llm=chosen_llm, instruction_seed=seed, apply=auto

                    )

                else:

                    agent = build_react_agent_with_optional_llm(

                        provider=provider, project_dir=project_dir, llm=chosen_llm

                    )

                agent_cache_put(cache_key, agent)

            try:

                if mode == "deep":

                    res = agent.invoke(

                        {"messages": [{"role": "user", "content": coerced}]},

                        config={

                            "recursion_limit": 30 if priority in {"speed", "cost"} else 45,

                            "configurable": {"thread_id": thread_id_for(project_dir, "chat-inline")},

                        },

                    )

                    output = (

                        extract_last_content(res.get("messages", [])).strip()

                        if isinstance(res, dict) and "messages" in res

                        else str(res)

                    )

                else:

                    payload = {"input": coerced, "chat_history": []}

                    if provider == "anthropic":

                        payload["chat_history"] = normalize_chat_history_for_anthropic([])

                    if verbose:

                        res = agent.invoke(payload, config={"callbacks": [RichDeepLogs(console)]})

                    else:

                        res = agent.invoke(payload)



                    output = res.get("output", "") if isinstance(res, dict) else str(res)

                    if provider == "anthropic":

                        output = _to_text(output)

                output = (output or "").strip() or "No response generated."

            except Exception as e:

                output = _friendly_agent_error(e)

        console.print(output)

        return None



    session_title = "LangChain Code Agent | Deep Chat" if mode == "deep" else "LangChain Code Agent | Chat"

    if mode == "deep" and auto:

        session_title += " (Auto)"

    print_session_header(

        session_title,

        provider,

        project_dir,

        interactive=True,

        router_enabled=router,

        deep_mode=(mode == "deep"),

        command_name="chat",

    )



    history: list = []

    msgs: list = []

    last_todos: list = []

    last_files: dict = {}

    user_turns = 0

    ai_turns = 0

    deep_thread_id = thread_id_for(project_dir, "chat")

    db_path = project_dir / ".langcode" / "memory.sqlite"



    static_agent = None
    static_agent_future = None
    if not router:
        def _build_static_agent() -> Any:
            env_override = os.getenv("LANGCODE_MODEL_OVERRIDE")
            chosen_llm = get_model_by_name(provider, env_override) if env_override else get_model(provider)
            if mode == "deep":
                seed = AUTO_DEEP_INSTR if auto else None
                return build_deep_agent_with_optional_llm(
                    provider=provider,
                    project_dir=project_dir,
                    llm=chosen_llm,
                    instruction_seed=seed,
                    apply=auto,
                )
            return build_react_agent_with_optional_llm(
                provider=provider,
                project_dir=project_dir,
                llm=chosen_llm,
            )

        static_agent_future = _AGENT_EXECUTOR.submit(_build_static_agent)



    prio_limits = {"speed": 30, "cost": 35, "balanced": 45, "quality": 60}



    import re as _re, ast as _ast, json as _json

    from langchain_core.callbacks import BaseCallbackHandler



    class TodoLiveMinimal(BaseCallbackHandler):

        """Updates the single TODO table in-place; no extra logs."""

        def __init__(self, live: Live):

            self.live = live

            self.todos: list[dict] = []

            self.seen = False



        def _extract_todos(self, payload) -> Optional[list]:

            if isinstance(payload, dict):

                if isinstance(payload.get("todos"), list):

                    return payload["todos"]

                upd = payload.get("update")

                if isinstance(upd, dict) and isinstance(upd.get("todos"), list):

                    return upd["todos"]



            upd = getattr(payload, "update", None)

            if isinstance(upd, dict) and isinstance(upd.get("todos"), list):

                return upd["todos"]



            s = str(payload)

            m = _re.search(r"Command\([^)]*update=(\{.*\})\)?$", s, _re.S) or _re.search(r"update=(\{.*\})", s, _re.S)

            if m:

                try:

                    data = _ast.literal_eval(m.group(1))

                    if isinstance(data, dict) and isinstance(data.get("todos"), list):

                        return data["todos"]

                except Exception:

                    pass

            jm = _re.search(r"(\{.*\"todos\"\s*:\s*\[.*\].*\})", s, _re.S)

            if jm:

                try:

                    data = _json.loads(jm.group(1))

                    if isinstance(data.get("todos"), list):

                        return data["todos"]

                except Exception:

                    pass

            return None



        def _render(self, todos: list[dict]):

            todos = _coerce_sequential_todos(todos)

            self.todos = todos

            self.seen = True

            self.live.update(render_todos_panel(todos))



        def on_tool_end(self, output, **kwargs):

            t = self._extract_todos(output)

            if t is not None:

                self._render(t)



        def on_chain_end(self, outputs, **kwargs):

            t = self._extract_todos(outputs)

            if t is not None:

                self._render(t)



    try:

        while True:

            if input_queue:

                user = input_queue.pop(0)

            else:

                user = console.input(PROMPT).strip()



            if not user:

                continue



            low = user.lower()

            if low in {"cls", "clear", "/clear"}:

                print_session_header(

                    session_title, provider, project_dir,

                    interactive=True, router_enabled=router,

                    deep_mode=(mode == "deep"), command_name="chat"

                )

                history.clear()

                msgs.clear()

                last_todos = []

                last_files = {}

                continue



            if low in {"select", "/select", "/menu", ":menu"}:

                console.print("[cyan]Returning to launcher...[/cyan]")

                if in_selection_hub():
                    return "select"
                selection_hub({

                    "command": "chat",

                    "engine": mode,

                    "router": router,

                    "priority": priority,

                    "autopilot": bool(auto),

                    "apply": False,

                    "llm": llm,

                    "project_dir": project_dir,

                    "test_cmd": None,

                })

                return "quit"



            if low in {"exit", "quit", ":q", "/exit", "/quit"}:

                return "quit"



            if low in {"help", "/help", ":help"}:

                print_session_header(

                    session_title, provider, project_dir, interactive=True,

                    router_enabled=router, deep_mode=(mode == "deep"),

                    command_name="chat"

                )

                console.print(help_content())

                continue



            if low in {"/memory", "/stats"}:

                if mode != "deep":

                    console.print(Panel.fit(Text("Memory & stats are available in deep mode only.", style="yellow"),

                                            border_style="yellow"))

                    continue

                from rich.table import Table as _Table

                if low == "/memory":

                    t = _Table.grid(padding=(0, 2))

                    t.add_row(Text("Thread", style="bold"), Text(deep_thread_id))

                    t.add_row(Text("DB", style="bold"), Text(str(db_path)))

                    t.add_row(

                        Text("Todos", style="bold"),

                        Text(", ".join(f"[{i+1}] {it.get('content','')}: {it.get('status','pending')}"

                                       for i, it in enumerate(last_todos)) or "(none)")

                    )

                    t.add_row(Text("Files", style="bold"), Text(", ".join(sorted(last_files.keys())) or "(none)"))

                    console.print(Panel(t, title="/memory", border_style="cyan", box=box.ROUNDED))

                else:

                    t = _Table.grid(padding=(0, 2))

                    t.add_row(Text("User turns", style="bold"), Text(str(user_turns)))

                    t.add_row(Text("Agent turns", style="bold"), Text(str(ai_turns)))

                    t.add_row(Text("Messages (current buffer)", style="bold"), Text(str(len(msgs))))

                    t.add_row(Text("Routing", style="bold"),

                              Text(("on | priority=" + priority) if router else "off"))

                    t.add_row(Text("Checkpointer", style="bold"), Text(str(db_path)))

                    t.add_row(Text("Thread", style="bold"), Text(deep_thread_id))

                    console.print(Panel(t, title="/stats", border_style="cyan", box=box.ROUNDED))

                continue



            coerced = maybe_coerce_img_command(user)

            user_turns += 1



            pending_router_panel: Optional[Panel] = None

            pending_output_panel: Optional[Panel] = None

            react_history_update: Optional[Tuple[HumanMessage, AIMessage]] = None



            agent = static_agent

            model_info = None

            chosen_llm = None



            loader_cm = show_loader() if (router and not verbose) else nullcontext()

            with loader_cm:

                if router:

                    provider = resolve_provider(llm, router=True)

                    model_info = get_model_info(provider, coerced, priority)

                    chosen_llm = get_model(provider, coerced, priority)



                    model_key = model_info.get("langchain_model_name") if model_info else "default"

                    cache_key = (

                        "deep" if mode == "deep" else "react",

                        provider,

                        model_key,

                        str(project_dir.resolve()),

                        bool(auto) if mode == "deep" else False,

                    )

                    cached = agent_cache_get(cache_key)

                    if cached is not None:

                        agent = cached

                    else:

                        if verbose and model_info:

                            pending_router_panel = panel_router_choice(model_info)

                        if mode == "deep":

                            seed = AUTO_DEEP_INSTR if auto else None

                            agent = build_deep_agent_with_optional_llm(

                                provider=provider,

                                project_dir=project_dir,

                                llm=chosen_llm,

                                instruction_seed=seed,

                                apply=auto,

                            )

                        else:

                            agent = build_react_agent_with_optional_llm(

                                provider=provider,

                                project_dir=project_dir,

                                llm=chosen_llm,

                            )

                        agent_cache_put(cache_key, agent)

                else:

                    if agent is None:

                        if static_agent_future is not None:

                            future_done = static_agent_future.done()

                            build_cm = nullcontext() if (verbose or future_done) else show_loader()

                            try:

                                with build_cm:

                                    agent = static_agent_future.result()

                            except Exception:

                                agent = None

                            static_agent_future = None

                        if agent is None:

                            build_cm = nullcontext() if verbose else show_loader()

                            with build_cm:

                                env_override = os.getenv("LANGCODE_MODEL_OVERRIDE")

                                chosen_llm = get_model_by_name(provider, env_override) if env_override else get_model(provider)

                                if mode == "deep":

                                    seed = AUTO_DEEP_INSTR if auto else None

                                    agent = build_deep_agent_with_optional_llm(

                                        provider=provider,

                                        project_dir=project_dir,

                                        llm=chosen_llm,

                                        instruction_seed=seed,

                                        apply=auto,

                                    )

                                else:

                                    agent = build_react_agent_with_optional_llm(

                                        provider=provider,

                                        project_dir=project_dir,

                                        llm=chosen_llm,

                                    )

                        static_agent = agent

            if pending_router_panel:

                console.print(pending_router_panel)



            def _current_model_label() -> Optional[str]:

                if router:

                    if model_info and model_info.get("langchain_model_name"):

                        return model_info["langchain_model_name"]

                    return None

                env_override = os.getenv("LANGCODE_MODEL_OVERRIDE")

                if env_override:

                    return env_override

                try:

                    return get_model_info(provider).get("langchain_model_name")

                except Exception:

                    return None



            _model_label = _current_model_label()





            if mode == "react":

                try:

                    payload = {"input": coerced, "chat_history": history}

                    if provider == "anthropic":

                        payload["chat_history"] = normalize_chat_history_for_anthropic(payload["chat_history"])



                    if verbose:

                        res = agent.invoke(payload, config={"callbacks": [RichDeepLogs(console)]})

                    else:

                        loader = show_loader() if router else nullcontext()

                        with loader:

                            res = agent.invoke(payload)



                    output = res.get("output", "") if isinstance(res, dict) else str(res)

                    if provider == "anthropic":

                        output = _to_text(output)

                    if not output.strip():

                        steps = res.get("intermediate_steps") if isinstance(res, dict) else None

                        if steps:

                            previews = []

                            for pair in steps[-3:]:

                                try:

                                    previews.append(str(pair))

                                except Exception:

                                    continue

                            output = "Model returned empty output. Recent steps:\n" + "\n".join(previews)

                        else:

                            output = "No response generated. Try rephrasing your request."

                except Exception as e:

                    output = _friendly_agent_error(e)



                pending_output_panel = panel_agent_output(output, model_label=_model_label)

                react_history_update = (HumanMessage(content=coerced), AIMessage(content=output))

                ai_turns += 1

            else:

                msgs.append({"role": "user", "content": coerced})

                if auto:

                    msgs.append({

                        "role": "system",

                        "content": (

                            "AUTOPILOT: Start now. Discover files (glob/list_dir/grep), read targets (read_file), "

                            "perform edits (edit_by_diff/write_file), and run at least one run_cmd (git/tests) "

                            "capturing stdout/stderr + exit code. Then produce one 'FINAL:' report and STOP. No questions."

                        )

                    })



                deep_config: Dict[str, Any] = {

                    "recursion_limit": prio_limits.get(priority, 100),

                    "configurable": {"thread_id": deep_thread_id},

                }



                placeholder = Panel(

                    Text("Planning tasks...", style="dim"),

                    title="TODOs",

                    border_style="blue",

                    box=box.ROUNDED,

                    padding=(1, 1),

                    expand=True

                )



                output: str = ""



                with Live(placeholder, refresh_per_second=8, transient=False) as live:
                    cli_state.current_live = live
                    todo_cb = TodoLiveMinimal(live)
                    deep_config["callbacks"] = [todo_cb]
                    res = {}
                    try:
                        res = agent.invoke({"messages": msgs}, config=deep_config)

                        if isinstance(res, dict) and "messages" in res:

                            msgs = res["messages"]

                            last_files = res.get("files") or last_files

                            last_content = extract_last_content(msgs).strip()

                        else:

                            last_content = ""

                            res = res if isinstance(res, dict) else {}



                    except Exception as e:

                        last_content = ""

                        output = (f"Agent hit recursion limit. Last response: {extract_last_content(msgs)}"

                                  if "recursion" in str(e).lower()

                                  else f"Agent error: {e}")

                        res = {}

                    if not output:

                        if not last_content:

                            # one safety retry to force a response

                            msgs.append({

                                "role": "system",

                                "content": "You must provide a response. Use your tools to complete the request and give a clear answer."

                            })

                            try:

                                res2 = agent.invoke({"messages": msgs}, config=deep_config)

                                if isinstance(res2, dict) and "messages" in res2:

                                    msgs = res2["messages"]

                                last_content = extract_last_content(msgs).strip()

                            except Exception as e:

                                last_content = f"Agent failed after retry: {e}"

                        output = last_content or "No response generated."



                    final_todos = res.get("todos") if isinstance(res, dict) else None

                    if not isinstance(final_todos, list) or not final_todos:

                        final_todos = getattr(todo_cb, "todos", [])



                    if final_todos:

                        normalized_todos = _coerce_sequential_todos(final_todos)

                        # Animate progression so each step visibly completes
                        animated_final = [{**todo, "status": todo.get("status", "pending")} for todo in normalized_todos]
                        any_completed = any(todo.get("status") == "completed" for todo in animated_final)
                        if not any_completed:
                            for idx in range(len(animated_final)):
                                step_view: List[dict] = []
                                for j, todo in enumerate(animated_final):
                                    status = todo.get("status", "pending")
                                    if j < idx:
                                        status = "completed"
                                    elif j == idx:
                                        status = "in_progress" if status != "completed" else status
                                    step_view.append({**todo, "status": status})
                                live.update(render_todos_panel(step_view))
                                time.sleep(0.15)

                        completed_view = [
                            {**todo, "status": "completed"} for todo in normalized_todos
                        ]

                        live.update(render_todos_panel(completed_view))

                        last_todos = completed_view

                        if not output.strip():

                            output = _todos_to_text_summary(completed_view)

                    else:

                        live.update(Panel(
                            Text("No tasks were emitted by the agent.", style="dim"),
                            title="TODOs",
                            border_style="blue",
                            box=box.ROUNDED,
                            padding=(1, 1),
                            expand=True
                        ))

                cli_state.current_live = None

                pending_output_panel = panel_agent_output(output, model_label=_model_label)
                ai_turns += 1



            if pending_output_panel:

                console.print(pending_output_panel)



            if react_history_update:

                human_msg, ai_msg = react_history_update

                history.append(human_msg)

                history.append(ai_msg)

                if len(history) > 20:

                    history[:] = history[-20:]

    except (KeyboardInterrupt, EOFError):

        return "quit"



@app.command(help="Implement a feature end-to-end (plan ? search ? edit ? verify). Supports --apply and optional --test-cmd (e.g., 'pytest -q').")

def feature(

    request: str = typer.Argument(..., help='e.g. "Add a dark mode toggle in settings"'),

    llm: Optional[str] = typer.Option(None, "--llm", help="anthropic | gemini | openai | ollama"),

    project_dir: Path = typer.Option(Path.cwd(), "--project-dir", exists=True, file_okay=False),

    test_cmd: Optional[str] = typer.Option(None, "--test-cmd", help='e.g. "pytest -q" or "npm test"'),

    apply: bool = typer.Option(False, "--apply", help="Apply writes and run commands without interactive confirm."),

    router: bool = typer.Option(False, "--router", help="Auto-route to the most efficient LLM for this request."),

    priority: str = typer.Option("balanced", "--priority", help="balanced | cost | speed | quality"),

    verbose: bool = typer.Option(False, "--verbose", help="Show model selection panel."),

):

    bootstrap_env(project_dir, interactive_prompt_if_missing=True)



    priority = (priority or "balanced").lower()

    if priority not in {"balanced", "cost", "speed", "quality"}:

        priority = "balanced"



    provider = resolve_provider(llm, router)

    model_info = None

    chosen_llm = None



    if router:

        model_info = get_model_info(provider, request, priority)

        chosen_llm = get_model(provider, request, priority)



    print_session_header(

        "LangChain Code Agent | Feature",

        provider,

        project_dir,

        interactive=False,

        apply=apply,

        test_cmd=test_cmd,

        model_info=(model_info if (router and verbose) else None),

        router_enabled=router,

        

    )

    if router and verbose and model_info:

        console.print(panel_router_choice(model_info))



    model_key = (model_info or {}).get("langchain_model_name", "default")

    cache_key = ("react", provider, model_key, str(project_dir.resolve()), False)

    cached = agent_cache_get(cache_key)

    if not router and provider in {"openai", "ollama"}:

        chosen_llm = get_model(provider)

    if cached is None:

        agent = build_react_agent_with_optional_llm(

            provider=provider,

            project_dir=project_dir,

            llm=chosen_llm,

            apply=apply,

            test_cmd=test_cmd,

            instruction_seed=FEATURE_INSTR,

        )

        agent_cache_put(cache_key, agent)

    else:

        agent = cached



    with show_loader():

        res = agent.invoke({"input": request, "chat_history": []})

        output = res.get("output", "") if isinstance(res, dict) else str(res)

    console.print(panel_agent_output(output, title="Feature Result"))

    pause_if_in_launcher()



@app.command(help="Diagnose & fix a bug (trace ? pinpoint ? patch ? test). Accepts --log, --test-cmd, and supports --apply.")

def fix(

    request: Optional[str] = typer.Argument(None, help='e.g. "Fix crash on image upload"'),

    log: Optional[Path] = typer.Option(None, "--log", exists=True, help="Path to error log or stack trace."),

    llm: Optional[str] = typer.Option(None, "--llm", help="anthropic | gemini | openai | ollama"),

    project_dir: Path = typer.Option(Path.cwd(), "--project-dir", exists=True, file_okay=False),

    test_cmd: Optional[str] = typer.Option(None, "--test-cmd", help='e.g. "pytest -q"'),

    apply: bool = typer.Option(False, "--apply", help="Apply writes and run commands without interactive confirm."),

    router: bool = typer.Option(False, "--router", help="Auto-route to the most efficient LLM for this request."),

    priority: str = typer.Option("balanced", "--priority", help="balanced | cost | speed | quality"),

    verbose: bool = typer.Option(False, "--verbose", help="Show model selection panel."),

    from_tty: bool = typer.Option(False, "--from-tty", help="Use most recent output from the current logged terminal session (run your command via `langcode wrap ...` or `langcode shell`)."),

    tty_id: Optional[str] = typer.Option(None, "--tty-id", help="Which session to read; defaults to current TTY."),

 ):

    bootstrap_env(project_dir, interactive_prompt_if_missing=True)



    priority = (priority or "balanced").lower()

    if priority not in {"balanced", "cost", "speed", "quality"}:

        priority = "balanced"



    provider = resolve_provider(llm, router)



    bug_input = (request or "").strip() 

    if log: 

        bug_input += "\n\n--- ERROR LOG ---\n" + Path(log).read_text(encoding="utf-8", errors="ignore") 

    elif from_tty: 

        tlog = os.environ.get("LANGCODE_TTY_LOG") or str(tty_log_path(tty_id)) 

        p = Path(tlog) 

        if p.exists(): 

            recent = tail_bytes(p) 

            block = extract_error_block(recent).strip() 

            if block: 

                bug_input += "\n\n--- ERROR LOG (from TTY) ---\n" + block 

                console.print(Panel.fit(Text(f"Using error from session log: {p}", style="dim"), border_style="cyan")) 

        else: 

            console.print(Panel.fit(Text("No TTY session log found. Run your failing command via `langcode wrap <cmd>` or `langcode shell`.", style="yellow"), border_style="yellow"))

    bug_input = bug_input.strip() or "Fix the bug using the provided log."



    model_info = None

    chosen_llm = None

    if router:

        model_info = get_model_info(provider, bug_input, priority)

        chosen_llm = get_model(provider, bug_input, priority)



    print_session_header(

        "LangChain Code Agent | Fix",

        provider,

        project_dir,

        interactive=False,

        apply=apply,

        test_cmd=test_cmd,

        model_info=(model_info if (router and verbose) else None),

        router_enabled=router,

    )

    if router and verbose and model_info:

        console.print(panel_router_choice(model_info))



    model_key = (model_info or {}).get("langchain_model_name", "default")

    cache_key = ("react", provider, model_key, str(project_dir.resolve()), False)

    cached = agent_cache_get(cache_key)

    if not router and provider in {"openai", "ollama"}:

        chosen_llm = get_model(provider)

    if cached is None:

        agent = build_react_agent_with_optional_llm(

            provider=provider,

            project_dir=project_dir,

            llm=chosen_llm,

            apply=apply,

            test_cmd=test_cmd,

            instruction_seed=BUGFIX_INSTR,

        )

        agent_cache_put(cache_key, agent)

    else:

        agent = cached



    with show_loader():

        res = agent.invoke({"input": bug_input, "chat_history": []})

        output = res.get("output", "") if isinstance(res, dict) else str(res)

    console.print(panel_agent_output(output, title="Fix Result"))

    pause_if_in_launcher()



@app.command(help="Analyze any codebase and generate insights (deep agent).")

def analyze(

    request: str = typer.Argument(..., help='e.g. "What are the main components of this project?"'),

    llm: Optional[str] = typer.Option(None, "--llm", help="anthropic | gemini | openai | ollama"),

    project_dir: Path = typer.Option(Path.cwd(), "--project-dir", exists=True, file_okay=False),

    router: bool = typer.Option(False, "--router", help="Auto-route to the most efficient LLM for this request."),

    priority: str = typer.Option("balanced", "--priority", help="balanced | cost | speed | quality"),

    verbose: bool = typer.Option(False, "--verbose", help="Show model selection panel."),

):

    bootstrap_env(project_dir, interactive_prompt_if_missing=True)



    priority = (priority or "balanced").lower()

    if priority not in {"balanced", "cost", "speed", "quality"}:

        priority = "balanced"



    provider = resolve_provider(llm, router)



    model_info = None

    chosen_llm = None

    if router:

        model_info = get_model_info(provider, request, priority)

        chosen_llm = get_model(provider, request, priority)



    print_session_header(

        "LangChain Code Agent | Analyze",

        provider,

        project_dir,

        interactive=False,

        apply=False,

        model_info=(model_info if (router and verbose) else None),

        router_enabled=router,

    )

    if router and verbose and model_info:

        console.print(panel_router_choice(model_info))



    model_key = (model_info or {}).get("langchain_model_name", "default")

    cache_key = ("deep", provider, model_key, str(project_dir.resolve()), False)

    cached = agent_cache_get(cache_key)

    if not router and provider in {"openai", "ollama"}:

        chosen_llm = get_model(provider)

    if cached is None:

        agent = build_deep_agent_with_optional_llm(

            provider=provider,

            project_dir=project_dir,

            llm=chosen_llm,

            apply=False,

        )

        agent_cache_put(cache_key, agent)

    else:

        agent = cached



    with show_loader():

        output = ""

        try:

            res = agent.invoke(

                {"messages": [{"role": "user", "content": request}]},

                config={

                    "recursion_limit": 45,

                    "configurable": {"thread_id": thread_id_for(project_dir, "analyze")},

                },

            )

            output = (

                extract_last_content(res.get("messages", [])).strip()

                if isinstance(res, dict) and "messages" in res

                else str(res)

            )

        except Exception as e:

            output = f"Analyze error: {e}"

    console.print(panel_agent_output(output or "No response generated.", title="Analysis Result"))

    pause_if_in_launcher()



@app.command(help="Edit environment. Use --global to edit your global env (~/.config/langcode/.env or ).")

def env(

    global_: bool = typer.Option(False, "--global", "-g", help="Edit the global env file."),

    project_dir: Path = typer.Option(Path.cwd(), "--project-dir", exists=True, file_okay=False)

):

    if global_:

        print_session_header("LangCode | Global Environment", provider=None, project_dir=project_dir, interactive=False)

        edit_global_env_file()

        load_global_env(override_existing=True)

        console.print(Panel.fit(Text("Global environment loaded.", style="green"), border_style="green"))

    else:

        print_session_header("LangCode | Project Environment", provider=None, project_dir=project_dir, interactive=False)

        edit_env_file(project_dir)

        load_env_files(project_dir, override_existing=False)

        console.print(Panel.fit(Text("Project environment loaded.", style="green"), border_style="green"))



@app.command(name="instr", help="Open or create project-specific instructions (.langcode/langcode.md) in your editor.")

def edit_instructions(

    project_dir: Path = typer.Option(Path.cwd(), "--project-dir", exists=True, file_okay=False)

):

    print_session_header(

        "LangChain Code Agent | Custom Instructions",

        provider=None,

        project_dir=project_dir,

        interactive=False

    )

    edit_langcode_md(project_dir)



def main() -> None:

    app()


if __name__ == "__main__":
    main()

