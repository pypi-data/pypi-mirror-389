"""
Execute tool V3 - Step-by-step execution with state-change verification.

This reimplements the event-driven state verification from the original Mahoraga agent
using a polling-based approach suitable for the client-server architecture.

All state-change detection logic is contained in this file.
"""

import time
import uuid
import asyncio
import hashlib
import json
from typing import Dict, Any, Callable, Optional, Tuple
from ..state import get_state
from ..backend_client import get_backend_client
from ..device.state_capture import get_device_state
from ..device.adb_tools import AdbTools
import logging

# Import mahoraga components for tool functions
try:
    from mahoraga.tools import Tools, describe_tools
    from mahoraga.tools.adb import AdbTools as MahoragaAdbTools
    from mahoraga.agent.context.personas import DEFAULT
    from mahoraga.agent.utils.async_utils import async_to_sync
except ImportError as e:
    print(f"Warning: Could not import mahoraga components: {e}")
    Tools = None
    describe_tools = None
    MahoragaAdbTools = None
    DEFAULT = None
    async_to_sync = None


def get_ui_state_hash(ui_state_dict: Dict[str, Any]) -> str:
    """
    Generate a stable hash of the UI state for comparison.

    Uses accessibility tree structure and package name.
    Hash will change when UI updates after an action.
    """
    def normalize_tree(tree):
        """Extract stable elements from UI tree."""
        if isinstance(tree, list):
            normalized = []
            for item in tree:
                if isinstance(item, dict):
                    element = {
                        "className": item.get("className", ""),
                        "text": item.get("text", ""),
                        "resourceId": item.get("resourceId", ""),
                        "bounds": item.get("bounds", ""),
                    }
                    normalized.append(element)

                    children = item.get("children", [])
                    if children:
                        element["children"] = normalize_tree(children)
            return normalized
        return []

    state_repr = {
        "package": ui_state_dict.get("phone_state", {}).get("package", ""),
        "tree": normalize_tree(ui_state_dict.get("a11y_tree", []))
    }

    state_json = json.dumps(state_repr, sort_keys=True)
    return hashlib.sha256(state_json.encode()).hexdigest()


def get_action_timeout(code: str) -> float:
    """
    Determine appropriate timeout based on action type.

    Returns timeout in seconds.
    """
    code_lower = code.lower()

    if "start_app" in code_lower:
        return 10.0  # App launches can be slow
    elif "tap" in code_lower or "click" in code_lower:
        return 5.0   # Screen transitions
    elif "swipe" in code_lower or "scroll" in code_lower:
        return 2.0   # Scroll animations
    elif "drag" in code_lower:
        return 2.0
    elif "input_text" in code_lower:
        return 2.0   # Text input is fast
    elif "press_back" in code_lower or "press_home" in code_lower:
        return 3.0   # Navigation
    elif "press_key" in code_lower:
        return 1.0
    else:
        return 5.0   # Default timeout


def wait_for_state_change(
    get_state_func,
    device_serial: str,
    old_state_hash: str,
    max_wait: float = 10.0,
    poll_interval: float = 0.5,
    min_wait: float = 0.3
) -> Tuple[Dict[str, Any], bytes, bool]:
    """
    Poll device until UI state changes or timeout.

    This is the core polling mechanism that replaces Mahoraga's event-driven approach.

    Returns:
        Tuple of (ui_state_dict, screenshot_bytes, state_changed: bool)
    """
    # Always wait minimum time for action to take effect
    time.sleep(min_wait)

    start_time = time.time()

    while (time.time() - start_time) < max_wait:
        # Capture current state
        ui_state_dict, screenshot_bytes = get_state_func(device_serial)
        current_hash = get_ui_state_hash(ui_state_dict)

        # Check if state changed
        if current_hash != old_state_hash:
            return ui_state_dict, screenshot_bytes, True

        # State hasn't changed - wait and try again
        time.sleep(poll_interval)

    # Timeout - state never changed
    ui_state_dict, screenshot_bytes = get_state_func(device_serial)
    return ui_state_dict, screenshot_bytes, False


def wait_for_action_effect(
    get_state_func,
    device_serial: str,
    old_ui_state: Dict[str, Any],
    executed_code: str,
    min_wait: float = 0.3,
    poll_interval: float = 0.5
) -> Tuple[Dict[str, Any], bytes, bool]:
    """
    Wait for an action to take effect on the device.

    Returns:
        Tuple of (new_ui_state_dict, screenshot_bytes, state_changed: bool)
    """
    # Check if action should change UI
    code_lower = executed_code.lower()
    if "get_state" in code_lower:
        # Action doesn't change UI - no need to wait
        time.sleep(0.1)
        return get_state_func(device_serial)[0], None, False

    # Get hash of old state
    old_hash = get_ui_state_hash(old_ui_state)

    # Determine timeout based on action type
    timeout = get_action_timeout(executed_code)

    # Poll until state changes
    new_ui_state, screenshot, changed = wait_for_state_change(
        get_state_func,
        device_serial,
        old_hash,
        max_wait=timeout,
        poll_interval=poll_interval,
        min_wait=min_wait
    )

    return new_ui_state, screenshot, changed


# ============================================================
# MAIN EXECUTION FUNCTION
# ============================================================

from ..models import SessionDTO, UIStateInfo, ChatHistoryMessage, ConfigInfo, AgentStepDTO

async def execute_v3(
    task: str,
    max_steps: int = 15,
    progress_callback: Optional[Callable[[str], None]] = None
) -> Dict[str, Any]:
    """
    Execute automation task using step-by-step backend communication.
    """
    state = get_state()
    backend = get_backend_client()

    # Check prerequisites
    if not state.is_device_connected():
        return {
            "status": "error",
            "message": "❌ No device connected. Please run 'connect' first.",
            "prerequisite": "connect"
        }

    if not state.is_configured():
        return {
            "status": "error",
            "message": "❌ Configuration incomplete. Please run 'configure' with your Quash API key.",
            "prerequisite": "configure"
        }

    if not state.portal_ready:
        return {
            "status": "error",
            "message": "⚠️ Portal accessibility service not ready. Please ensure it's enabled on the device.",
            "prerequisite": "connect"
        }

    # Get API key and config
    quash_api_key = state.config["api_key"]
    config = {
        "model": state.config["model"],
        "temperature": state.config["temperature"],
        "vision": state.config["vision"],
        "reasoning": state.config["reasoning"],
        "reflection": state.config["reflection"],
        "debug": state.config["debug"]
    }

    # Validate API key
    validation_result = await backend.validate_api_key(quash_api_key)

    if not validation_result.get("valid", False):
        error_msg = validation_result.get("error", "Invalid API key")
        return {
            "status": "error",
            "message": f"❌ API Key validation failed: {error_msg}",
            "prerequisite": "configure"
        }

    # Check credits
    user_info = validation_result.get("user", {})
    organization_credits = validation_result.get("organization_credits", 0)

    if organization_credits <= 0:
        return {
            "status": "error",
            "message": f"❌ Insufficient credits. Current balance: ${organization_credits:.2f}",
            "user": user_info
        }

    # Progress logging helper
    def log_progress(message: str):
        if progress_callback:
            progress_callback(message)

    log_progress(f"✅ API Key validated - Credits: ${organization_credits:.2f}")
    log_progress(f"👤 User: {user_info.get('name', 'Unknown')}")
    log_progress(f"🚀 Starting task: {task}")
    log_progress(f"📱 Device: {state.device_serial}")
    log_progress(f"🧠 Model: {config['model']}")

    log_progress(f"🔢 Max steps: {max_steps}")

    # Initialize Session DTO

    session = SessionDTO(
        session_id=f"session_{uuid.uuid4().hex[:12]}",
        api_key=quash_api_key,
        task=task,
        device_serial=state.device_serial,
        config=ConfigInfo(**config)
    )

    # Initialize local ADB tools for code execution
    adb_tools = AdbTools(serial=state.device_serial, use_tcp=True)

    # Code executor namespace - add tool functions so generated code can call them
    executor_globals = {
        "__builtins__": __builtins__,
        "adb_tools": adb_tools
    }

    # Add tool functions to executor namespace (like start_app, swipe, etc.)
    if describe_tools and DEFAULT and MahoragaAdbTools:
        try:
            # Create a mahoraga AdbTools instance for tool execution
            mahoraga_tools = MahoragaAdbTools(
                serial=state.device_serial,
                use_tcp=True,
                remote_tcp_port=8080
            )

            # Get all tool functions from mahoraga AdbTools instance
            tool_list = describe_tools(mahoraga_tools, exclude_tools=None)

            # Filter by allowed tools from DEFAULT persona
            allowed_tool_names = DEFAULT.allowed_tools if hasattr(DEFAULT, 'allowed_tools') else []
            filtered_tools = {name: func for name, func in tool_list.items() if name in allowed_tool_names}

            # Add each tool function to executor globals with print wrapper
            for tool_name, tool_function in filtered_tools.items():
                # Convert async functions to sync if needed
                if asyncio.iscoroutinefunction(tool_function):
                    if async_to_sync:
                        tool_function = async_to_sync(tool_function)

                # Wrap tool function to print its return value
                def make_printing_wrapper(func):
                    """Wrap a tool function to print its return value."""
                    def wrapper(*args, **kwargs):
                        result = func(*args, **kwargs)
                        # Print the result so stdout captures it
                        if result is not None:
                            print(result)
                        return result
                    return wrapper

                # Add wrapped function to globals so code can call it directly
                executor_globals[tool_name] = make_printing_wrapper(tool_function)

            # Override the 'complete' function to be a no-op
            # The backend already handles completion via the 'completed' flag
            def complete_no_op(success=True, reason=""):
                """No-op wrapper for complete() - completion is handled by backend."""
                print(f"complete() called: success={success}, reason='{reason}'")
                return None

            executor_globals['complete'] = complete_no_op

            log_progress(f"🔧 Loaded {len(filtered_tools)} tool functions: {list(filtered_tools.keys())}")
        except Exception as e:
            log_progress(f"⚠️ Warning: Could not load tool functions: {e}")
            import traceback
            log_progress(f"Traceback: {traceback.format_exc()}")

    executor_locals = {}

    start_time = time.time()

    try:
        # ============================================================
        # STEP-BY-STEP EXECUTION LOOP
        # ============================================================

        while len(session.steps) < max_steps:

            log_progress(f"🧠 Step {len(session.steps) + 1}/{max_steps}: Analyzing...")

            # 1. Capture device state and update session DTO
            try:
                ui_state_dict, screenshot_bytes = get_device_state(state.device_serial)

                session.ui_state = UIStateInfo(**ui_state_dict)
                # Update local tools with new state
                if mahoraga_tools and "a11y_tree" in ui_state_dict and isinstance(ui_state_dict["a11y_tree"], str):
                    try:
                        import json
                        a11y_tree_obj = json.loads(ui_state_dict["a11y_tree"])
                        mahoraga_tools.update_state(a11y_tree_obj)
                    except (json.JSONDecodeError, TypeError):
                        pass # Ignore if not a valid JSON string

                if not config["vision"]:
                    screenshot_bytes = None

                current_package = ui_state_dict.get("phone_state", {}).get("package", "unknown")
                log_progress(f"📱 Current app: {current_package}")

            except Exception as e:
                log_progress(f"⚠️ Warning: Failed to capture device state: {e}")
                session.ui_state = UIStateInfo(
                    a11y_tree="<error>Failed to capture UI</error>",
                    phone_state={"package": "unknown"}
                )
                screenshot_bytes = None

            # 2. Send session DTO to backend for AI decision
            step_result = await backend.execute_step(
                session=session,
                screenshot_bytes=screenshot_bytes
            )

            # Handle backend errors
            if "error" in step_result:
                log_progress(f"💥 Backend error: {step_result['message']}")
                return {
                    "status": "error",
                    "message": step_result["message"],
                    "error": step_result["error"],
                    "steps_taken": len(session.steps),
                    "tokens": None,
                    "cost": None,
                    "duration_seconds": time.time() - start_time
                }

            # Update Session DTO with new step and chat history
            new_step_data = step_result.get("new_step")
            if new_step_data:
                new_step = AgentStepDTO(**new_step_data)
                session.steps.append(new_step)
            assistant_response = step_result.get("assistant_response", "")
            session.chat_history.append(ChatHistoryMessage(role="assistant", content=assistant_response))


            # Get action from backend
            action = step_result.get("action", {})
            action_type = action.get("type")
            code = action.get("code")
            reasoning = action.get("reasoning")


            # Log reasoning
            if reasoning:
                log_progress(f"🤔 Reasoning: {reasoning}")


            # 3. Execute action locally FIRST (if provided)
            # NOTE: Backend should have already removed complete() from the code
            if code and (action_type == "execute_code" or action_type == "complete"):

                log_progress(f"⚡ Executing action...")

                log_progress(f"```python\n{code}\n```") # Log the code

                old_ui_state = session.ui_state.model_dump().copy()

                try:
                    import io
                    import contextlib

                    stdout = io.StringIO()
                    stderr = io.StringIO()

                    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                        exec(code, executor_globals, executor_locals)

                    execution_output = stdout.getvalue()
                    error_output = stderr.getvalue()

                    log_progress(f"⏳ Waiting for UI state to update...")
                    try:
                        new_ui_state_dict, _, state_changed = wait_for_action_effect(
                            get_device_state,
                            state.device_serial,
                            old_ui_state,
                            code,
                            min_wait=0.3,
                            poll_interval=0.5
                        )

                        if state_changed:
                            old_pkg = old_ui_state.get("phone_state", {}).get("package", "")
                            new_pkg = new_ui_state_dict.get("phone_state", {}).get("package", "")

                            if old_pkg != new_pkg:
                                log_progress(f"✅ State changed: App switched ({old_pkg} → {new_pkg})")
                            else:
                                log_progress(f"✅ State changed: UI updated")

                        else:
                            log_progress(f"⚠️ WARNING: State did NOT change after action (timeout)")
                            log_progress(f"   This might mean the action had no effect or took too long")

                    except Exception as e:
                        log_progress(f"⚠️ Error during state change detection: {e}")
                        state_changed = False
                        time.sleep(1.5)

                    feedback_parts = []

                    if execution_output:
                        feedback_parts.append(f"Action output: {execution_output.strip()}")

                    if state_changed:
                        feedback_parts.append("UI state updated successfully")
                    else:
                        feedback_parts.append("WARNING: UI state did not change (action may have failed)")

                    if error_output:
                        feedback_parts.append(f"Warnings: {error_output.strip()}")

                    feedback = " | ".join(feedback_parts) if feedback_parts else "Action executed"

                    log_progress(f"✅ {feedback[:200]}")

                    session.chat_history.append(ChatHistoryMessage(role="user", content=f"Execution Result:\n```\n{feedback}\n```"))

                    # Introduce a small delay to allow UI effects to settle before checking completion
                    time.sleep(1.0) # Added delay

                except Exception as e:
                    error_msg = f"Error during execution: {str(e)}"
                    log_progress(f"💥 Action failed: {error_msg}")

                    session.chat_history.append(ChatHistoryMessage(role="user", content=f"Execution Error:\n```\n{error_msg}\n```"))

            elif not code:
                log_progress("⚠️ No action code provided by backend")
                session.chat_history.append(ChatHistoryMessage(role="user", content="No code was provided. Please provide code to execute."))


            # 4. Check if task is complete AFTER executing action
            if step_result.get("completed", False):
                success = step_result.get("success", False)
                final_message = step_result.get("final_message", "Task completed")

                duration = time.time() - start_time

                if success:
                    log_progress(f"✅ Task completed successfully!")
                else:
                    log_progress(f"❌ Task marked as failed")

                # Finalize session on backend
                finalize_result = await backend.finalize_session(session=session)

                if success:
                    log_progress(f"✅ Task completed successfully in {len(session.steps)} steps")
                    log_progress(f"💰 Usage: {finalize_result.get('total_tokens', {}).get('total')} tokens, ${finalize_result.get('total_cost', 0):.4f}")

                    return {
                        "status": "success",
                        "steps_taken": len(session.steps),
                        "final_message": final_message,
                        "message": f"✅ Success: {final_message}",
                        "tokens": finalize_result.get("total_tokens"),
                        "cost": finalize_result.get("total_cost"),
                        "duration_seconds": duration
                    }
                else:
                    log_progress(f"❌ Task failed: {final_message}")
                    log_progress(f"💰 Usage: {finalize_result.get('total_tokens', {}).get('total')} tokens, ${finalize_result.get('total_cost', 0):.4f}")

                    return {
                        "status": "failed",
                        "steps_taken": len(session.steps),
                        "final_message": final_message,
                        "message": f"❌ Failed: {final_message}",
                        "tokens": finalize_result.get("total_tokens"),
                        "cost": finalize_result.get("total_cost"),
                        "duration_seconds": duration
                    }


        # Max steps reached
        log_progress(f"⚠️ Reached maximum steps ({max_steps})")

        duration = time.time() - start_time

        # Finalize session on backend
        finalize_result = await backend.finalize_session(session=session)

        return {
            "status": "failed",
            "steps_taken": len(session.steps),
            "final_message": f"Reached maximum step limit of {max_steps}",
            "message": "❌ Failed: Maximum steps reached",
            "tokens": finalize_result.get("total_tokens"),
            "cost": finalize_result.get("total_cost"),
            "duration_seconds": duration
        }

    except KeyboardInterrupt:
        log_progress("ℹ️ Task interrupted by user")
        duration = time.time() - start_time

        # Finalize session on backend
        finalize_result = await backend.finalize_session(session=session)

        return {
            "status": "interrupted",
            "message": "ℹ️ Task execution interrupted",
            "steps_taken": len(session.steps),
            "tokens": finalize_result.get("total_tokens"),
            "cost": finalize_result.get("total_cost"),
            "duration_seconds": duration
        }

    except Exception as e:
        error_msg = str(e)
        log_progress(f"💥 Error: {error_msg}")
        duration = time.time() - start_time

        # Finalize session on backend
        finalize_result = await backend.finalize_session(session=session)

        return {
            "status": "error",
            "message": f"💥 Execution error: {error_msg}",
            "error": error_msg,
            "steps_taken": len(session.steps),
            "tokens": finalize_result.get("total_tokens"),
            "cost": finalize_result.get("total_cost"),
            "duration_seconds": duration
        }

    finally:
        # Cleanup TCP forwarding
        if adb_tools:
            adb_tools.teardown_tcp_forward()