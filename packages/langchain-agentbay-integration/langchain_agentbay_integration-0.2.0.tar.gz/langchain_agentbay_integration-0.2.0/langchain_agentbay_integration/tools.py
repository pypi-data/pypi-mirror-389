from typing import Any, List
import json
import traceback
import time
import os
import asyncio
from pydantic import Field

# Print the langchain version
try:
    import langchain
    print(f"Langchain version: {langchain.__version__}")
    print(f"Langchain file location: {langchain.__file__}")
except ImportError:
    print("Langchain is not installed")

from langchain.tools import tool, ToolRuntime
from dataclasses import dataclass
from agentbay.browser import ActOptions

try:
    import dashscope
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False

# Data classes for session information
@dataclass
class MobileSessionData:
    """Data class for mobile session information."""
    session: Any = None  # AgentBay session object with session_id attribute
    session_id: str = None  # Add session_id field


@dataclass
class CodespaceSessionData:
    """Data class for codespace session information."""
    session: Any = None  # AgentBay session object with session_id attribute
    session_id: str = None  # Add session_id field


@dataclass
class BrowserSessionData:
    """Data class for browser session information."""
    session: Any = None  # AgentBay session object with session_id attribute
    session_id: str = None  # Add session_id field


@dataclass
class ComputerSessionData:
    """Data class for computer session information."""
    session: Any = None  # AgentBay session object with session_id attribute
    session_id: str = None  # Add session_id field


# Helper functions to get sessions from runtime store
"""
Helper function to get mobile session from runtime store
"""
def get_mobile_session(runtime: ToolRuntime[MobileSessionData, None]) -> Any:
    """Get mobile session from runtime store.
    
    Args:
        runtime: ToolRuntime object containing store with session data
        
    Returns:
        Mobile session object
        
    Raises:
        ValueError: If no mobile session found in store
    """
    # Access session from runtime store
    store = runtime.store
    session_entry = store.get(("mobile_session",), "default")
    if not session_entry:
        raise ValueError("No mobile session found in store")
    session_data = session_entry.value
    
    # Get session either directly or via session_id
    if hasattr(session_data, 'session') and session_data.session:
        session = session_data.session
    elif hasattr(session_data, 'session_id') and session_data.session_id:
        # If we have a session_id but no session object, try to re-acquire
        from agentbay import AgentBay
        agent_bay = AgentBay()
        session_result = agent_bay.get(session_data.session_id)
        if session_result.success:
            session = session_result.session
            # Update the session in store
            session_data.session = session
            store.put(("mobile_session",), session_data, "default")
        else:
            raise ValueError(f"Failed to get session with ID {session_data.session_id}: {session_result.error_message}")
    else:
        raise ValueError("No valid session or session_id found in session_data")
        
    return session


"""
Helper function to get codespace session from runtime store
"""
def get_codespace_session(runtime: ToolRuntime[CodespaceSessionData, None]) -> Any:
    """Get codespace session from runtime store.
    
    Args:
        runtime: ToolRuntime object containing store with session data
        
    Returns:
        Codespace session object
        
    Raises:
        ValueError: If no codespace session found in store
    """
    # Access session from runtime store
    store = runtime.store
    session_entry = store.get(("codespace_session",), "default")
    if not session_entry:
        raise ValueError("No codespace session found in store")
    session_data = session_entry.value
    
    # Get session either directly or via session_id
    if hasattr(session_data, 'session') and session_data.session:
        session = session_data.session
    elif hasattr(session_data, 'session_id') and session_data.session_id:
        # If we have a session_id but no session object, try to re-acquire
        from agentbay import AgentBay
        agent_bay = AgentBay()
        session_result = agent_bay.get(session_data.session_id)
        if session_result.success:
            session = session_result.session
            # Update the session in store
            session_data.session = session
            store.put(("codespace_session",), session_data, "default")
        else:
            raise ValueError(f"Failed to get session with ID {session_data.session_id}: {session_result.error_message}")
    else:
        raise ValueError("No valid session or session_id found in session_data")
        
    return session


"""
Helper function to get browser session from runtime store
"""
def get_browser_session(runtime: ToolRuntime[BrowserSessionData, None]) -> Any:
    """Get browser session from runtime store.
    
    Args:
        runtime: ToolRuntime object containing store with session data
        
    Returns:
        Browser session object
        
    Raises:
        ValueError: If no browser session found in store
    """
    # Access session from runtime store
    store = runtime.store
    session_entry = store.get(("browser_session",), "default")
    if not session_entry:
        raise ValueError("No browser session found in store")
    session_data = session_entry.value
    
    # Get session either directly or via session_id
    if hasattr(session_data, 'session') and session_data.session:
        session = session_data.session
    elif hasattr(session_data, 'session_id') and session_data.session_id:
        # If we have a session_id but no session object, try to re-acquire
        from agentbay import AgentBay
        agent_bay = AgentBay()
        session_result = agent_bay.get(session_data.session_id)
        if session_result.success:
            session = session_result.session
            # Update the session in store
            session_data.session = session
            store.put(("browser_session",), session_data, "default")
        else:
            raise ValueError(f"Failed to get session with ID {session_data.session_id}: {session_result.error_message}")
    else:
        raise ValueError("No valid session or session_id found in session_data")
        
    return session


"""
Helper function to get computer session from runtime store
"""
def get_computer_session(runtime: ToolRuntime[ComputerSessionData, None]) -> Any:
    """Get computer session from runtime store.
    
    Args:
        runtime: ToolRuntime object containing store with session data
        
    Returns:
        Computer session object
        
    Raises:
        ValueError: If no computer session found in store
    """
    # Access session from runtime store
    store = runtime.store
    session_entry = store.get(("computer_session",), "default")
    if not session_entry:
        raise ValueError("No computer session found in store")
    session_data = session_entry.value
    
    # Get session either directly or via session_id
    if hasattr(session_data, 'session') and session_data.session:
        session = session_data.session
    elif hasattr(session_data, 'session_id') and session_data.session_id:
        # If we have a session_id but no session object, try to re-acquire
        from agentbay import AgentBay
        agent_bay = AgentBay()
        session_result = agent_bay.get(session_data.session_id)
        if session_result.success:
            session = session_result.session
            # Update the session in store
            session_data.session = session
            store.put(("computer_session",), session_data, "default")
        else:
            raise ValueError(f"Failed to get session with ID {session_data.session_id}: {session_result.error_message}")
    else:
        raise ValueError("No valid session or session_id found in session_data")
        
    return session


# Mobile tools for AgentBay mobile session operations
@tool("mobile_tap")
def mobile_tap(
    x: int = Field(..., description="X coordinate of the tap position"),
    y: int = Field(..., description="Y coordinate of the tap position"),
    runtime: ToolRuntime[MobileSessionData, None] = None
) -> str:
    """Tap on the mobile screen at specific coordinates. Requires a mobile session with image_id='mobile_latest'"""
    # Log input parameters
    print(f"[mobile_tap] Input: x={x}, y={y}")
    
    try:
        # Access session from runtime store
        session = get_mobile_session(runtime)
        
        # Perform actual tap operation using AgentBay session
        result = session.mobile.tap(x=x, y=y)
        
        if result.success:
            response = {
                "success": True,
                "message": f"Successfully tapped at coordinates ({x}, {y})",
                "x": x,
                "y": y
            }
        else:
            response = {
                "success": False,
                "error": f"Failed to tap at coordinates ({x}, {y}): {result.error_message}"
            }
        # Log output result
        print(f"[mobile_tap] Output: {response}")
        return json.dumps(response, ensure_ascii=False)
    except Exception as e:
        result = {
            "success": False,
            "error": f"Error occurred while tapping: {str(e)}"
        }
        # Log exception
        print(f"[mobile_tap] Exception: {result}")
        traceback.print_exc()
        return json.dumps(result, ensure_ascii=False)


@tool("mobile_swipe")
def mobile_swipe(
    start_x: int = Field(..., description="Starting X coordinate"),
    start_y: int = Field(..., description="Starting Y coordinate"),
    end_x: int = Field(..., description="Ending X coordinate"),
    end_y: int = Field(..., description="Ending Y coordinate"),
    duration_ms: int = Field(default=300, description="Duration of the swipe in milliseconds"),
    runtime: ToolRuntime[MobileSessionData, None] = None
) -> str:
    """Swipe on the mobile screen from one point to another. Requires a mobile session with image_id='mobile_latest'"""
    # Log input parameters
    print(f"[mobile_swipe] Input: start_x={start_x}, start_y={start_y}, end_x={end_x}, end_y={end_y}, duration_ms={duration_ms}")
    
    try:
        # Access session from runtime store
        session = get_mobile_session(runtime)
        
        # Ensure duration_ms parameter is an integer value, not FieldInfo
        if duration_ms is None or not isinstance(duration_ms, int):
            duration_ms = 300
        
        # Perform actual swipe operation using AgentBay session
        result = session.mobile.swipe(
            start_x=start_x,
            start_y=start_y,
            end_x=end_x,
            end_y=end_y,
            duration_ms=duration_ms
        )
        
        if result.success:
            response = {
                "success": True,
                "message": f"Successfully swiped from ({start_x}, {start_y}) to ({end_x}, {end_y}) in {duration_ms}ms",
                "start_x": start_x,
                "start_y": start_y,
                "end_x": end_x,
                "end_y": end_y,
                "duration_ms": duration_ms
            }
        else:
            response = {
                "success": False,
                "error": f"Failed to swipe from ({start_x}, {start_y}) to ({end_x}, {end_y}): {result.error_message}"
            }
        # Log output result
        print(f"[mobile_swipe] Output: {response}")
        return json.dumps(response, ensure_ascii=False)
    except Exception as e:
        result = {
            "success": False,
            "error": f"Error occurred while swiping: {str(e)}"
        }
        # Log exception
        print(f"[mobile_swipe] Exception: {result}")
        traceback.print_exc()
        return json.dumps(result, ensure_ascii=False)


@tool("mobile_input_text")
def mobile_input_text(
    text: str = Field(..., description="Text to input"),
    runtime: ToolRuntime[MobileSessionData, None] = None
) -> str:
    """Input text into the active field on mobile. Requires a mobile session with image_id='mobile_latest'"""
    # Log input parameters
    print(f"[mobile_input_text] Input: text='{text}'")
    
    try:
        # Access session from runtime store
        session = get_mobile_session(runtime)
        
        # Perform actual text input operation using AgentBay session
        result = session.mobile.input_text(text)
        
        if result.success:
            response = {
                "success": True,
                "message": f"Successfully input text: {text}",
                "text": text
            }
        else:
            response = {
                "success": False,
                "error": f"Failed to input text '{text}': {result.error_message}"
            }
        # Log output result
        print(f"[mobile_input_text] Output: {response}")
        return json.dumps(response, ensure_ascii=False)
    except Exception as e:
        result = {
            "success": False,
            "error": f"Error occurred while inputting text: {str(e)}"
        }
        # Log exception
        print(f"[mobile_input_text] Exception: {result}")
        traceback.print_exc()
        return json.dumps(result, ensure_ascii=False)


@tool("mobile_send_key")
def mobile_send_key(
    key_code: int = Field(..., description="Key code to send. Common codes: HOME=3, BACK=4, VOLUME_UP=24, VOLUME_DOWN=25, POWER=26, MENU=82"),
    runtime: ToolRuntime[MobileSessionData, None] = None
) -> str:
    """Send a key event to the mobile device. Requires a mobile session with image_id='mobile_latest'. Common codes: HOME=3, BACK=4, VOLUME_UP=24, VOLUME_DOWN=25, POWER=26, MENU=82"""
    # Log input parameters
    print(f"[mobile_send_key] Input: key_code={key_code}")
    
    try:
        # Access session from runtime store
        session = get_mobile_session(runtime)
        
        # Perform actual key event operation using AgentBay session
        result = session.mobile.send_key(key_code)
        
        # This is a placeholder implementation - in real usage, this would interact with the actual session
        key_names = {
            3: "HOME",
            4: "BACK",
            24: "VOLUME_UP",
            25: "VOLUME_DOWN",
            26: "POWER",
            82: "MENU"
        }
        
        key_name = key_names.get(key_code, f"KEY_CODE_{key_code}")
        
        if result.success:
            response = {
                "success": True,
                "message": f"Successfully sent key event: {key_name} (code: {key_code})",
                "key_code": key_code,
                "key_name": key_name
            }
        else:
            response = {
                "success": False,
                "error": f"Failed to send key event {key_name} (code: {key_code}): {result.error_message}"
            }
        # Log output result
        print(f"[mobile_send_key] Output: {response}")
        return json.dumps(response, ensure_ascii=False)
    except Exception as e:
        result = {
            "success": False,
            "error": f"Error occurred while sending key event: {str(e)}"
        }
        # Log exception
        print(f"[mobile_send_key] Exception: {result}")
        traceback.print_exc()
        return json.dumps(result, ensure_ascii=False)


def get_all_ui_elements_body(session, timeout_ms=2000):
    """Direct call to get all UI elements without LangChain."""
    print(f"Calling get_all_ui_elements with timeout_ms={timeout_ms}")
    
    try:
        # Perform actual clickable UI elements retrieval using AgentBay session
        result = session.mobile.get_all_ui_elements(timeout_ms=timeout_ms)
        print( f"get_all_ui_elements get_request_id:{result.get_request_id()} request_id:{result.request_id}")

        if result.success:
            # Convert elements to serializable format
            elements = []
            for element in result.elements:
                # Convert element to dict, handling potential serialization issues
                try:
                    # Try to convert to dict first
                    if hasattr(element, '__dict__'):
                        element_dict = {}
                        for key, value in element.__dict__.items():
                            try:
                                # Try to serialize the value
                                json.dumps(value)
                                element_dict[key] = value
                            except (TypeError, ValueError):
                                # If not serializable, convert to string
                                element_dict[key] = str(value)
                        elements.append(element_dict)
                    else:
                        elements.append(str(element))
                except Exception:
                    elements.append(str(element))
            
            response = {
                "success": True,
                "message": f"Found {len(result.elements)} UI elements",
                "elements": elements,
                "timeout_ms": timeout_ms
            }
        else:
            response = {
                "success": False,
                "error": f"Failed to get UI elements: {result.error_message}"
            }
        return response
    except Exception as e:
        result = {
            "success": False,
            "error": f"Error occurred while getting UI elements: {str(e)}"
        }
        return result
    
@tool("mobile_get_ui_elements")
def mobile_get_ui_elements(
    timeout_ms: int = Field(default=2000, description="Timeout in milliseconds to wait for UI elements"),
    runtime: ToolRuntime[MobileSessionData, None] = None
) -> str:
    """Get all UI elements on the current mobile screen. Requires a mobile session with image_id='mobile_latest'"""
    # Log input parameters
    print(f"[mobile_get_ui_elements] Input: timeout_ms={timeout_ms}")
    
    try:
        # Access session from runtime store
        session = get_mobile_session(runtime)
        
        # Ensure timeout_ms parameter is an integer value, not FieldInfo
        if timeout_ms is None or not isinstance(timeout_ms, int):
            timeout_ms = 2000
            
        all_ui_elements_result = get_all_ui_elements_body(session, timeout_ms)
        # Log output result
        all_ui_elements_result_str = json.dumps(all_ui_elements_result, ensure_ascii=False)
        print(f"[mobile_get_ui_elements] Output: {all_ui_elements_result_str}")
        return all_ui_elements_result_str
    except Exception as e:
        result = {
            "success": False,
            "error": f"Error occurred while getting UI elements: {str(e)}"
        }
        # Log exception
        print(f"[mobile_get_ui_elements] Exception: {result}")
        traceback.print_exc()
        return json.dumps(result, ensure_ascii=False)


@tool("mobile_screenshot")
def mobile_screenshot(
    file_path: str = Field(..., description="File path to save the screenshot"),
    runtime: ToolRuntime[MobileSessionData, None] = None
) -> str:
    """Take a screenshot of the current mobile screen. Requires a mobile session with image_id='mobile_latest'"""
    # Log function call
    print(f"[mobile_screenshot] Called with file_path: {file_path}")
    
    try:
        # Access session from runtime store
        session = get_mobile_session(runtime)
        
        # Perform actual screenshot operation using AgentBay session
        result = session.mobile.screenshot()
        
        if result.success:
            response_data = {
                "success": True,
                "message": "Screenshot captured successfully",
                "screenshot_url": result.data
            }
            
            # Download and save the screenshot
            try:
                import requests
                import os
                
                # Create directory if it doesn't exist
                directory = os.path.dirname(file_path)
                if directory:
                    os.makedirs(directory, exist_ok=True)
                
                # Download the screenshot
                download_response = requests.get(result.data)
                download_response.raise_for_status()
                
                # Save to file
                with open(file_path, 'wb') as f:
                    f.write(download_response.content)
                
                response_data["file_path"] = file_path
                response_data["message"] += f" and saved to {file_path}"
                
            except Exception as download_error:
                response_data["success"] = False
                response_data["error"] = f"Failed to download or save screenshot: {str(download_error)}"
            
            response = response_data
        else:
            response = {
                "success": False,
                "error": f"Failed to capture screenshot: {result.error_message}"
            }
        # Log output result
        print(f"[mobile_screenshot] Output: {response}")
        return json.dumps(response, ensure_ascii=False)
    except Exception as e:
        result = {
            "success": False,
            "error": f"Error occurred while capturing screenshot: {str(e)}"
        }
        # Log exception
        print(f"[mobile_screenshot] Exception: {result}")
        traceback.print_exc()
        return json.dumps(result, ensure_ascii=False)


@tool("mobile_wait")
def mobile_wait(
    milliseconds: int = Field(..., description="Time to wait in milliseconds"),
    runtime: ToolRuntime[MobileSessionData, None] = None
) -> str:
    """Wait for a specified amount of time in milliseconds. Useful for waiting for remote operations to complete."""
    # Log input parameters
    print(f"[mobile_wait] Input: milliseconds={milliseconds}")
    
    try:
        # Convert milliseconds to seconds for time.sleep()
        seconds = milliseconds / 1000.0
        
        # Wait for the specified time
        time.sleep(seconds)
        
        response = {
            "success": True,
            "message": f"Successfully waited for {milliseconds} milliseconds ({seconds} seconds)"
        }
        
        # Log output result
        print(f"[mobile_wait] Output: {response}")
        return json.dumps(response, ensure_ascii=False)
    except Exception as e:
        result = {
            "success": False,
            "error": f"Error occurred while waiting: {str(e)}"
        }
        # Log exception
        print(f"[mobile_wait] Exception: {result}")
        traceback.print_exc()
        return json.dumps(result, ensure_ascii=False)


# Codespace tools
@tool("codespace_write_file")
def codespace_write_file(
    path: str = Field(..., description="Path where to write the file"),
    content: str = Field(..., description="Content to write to the file"),
    mode: str = Field(default="overwrite", description="Write mode ('overwrite' or 'append')"),
    runtime: ToolRuntime[CodespaceSessionData, None] = None
) -> str:
    """Write content to a file in the AgentBay codespace session"""
    # Log input parameters
    print(f"[codespace_write_file] Input: path={path}, mode={mode}")
    
    try:
        # Access session from runtime store
        session = get_codespace_session(runtime)
        
        # Ensure mode parameter is a string value, not FieldInfo
        if mode is None or not isinstance(mode, str):
            mode = "overwrite"
            
        result = session.file_system.write_file(path, content, mode)
        if result.success:
            response = {
                "success": True,
                "message": f"File written successfully to {path} with mode '{mode}'"
            }
        else:
            response = {
                "success": False,
                "error": f"Failed to write file: {result.error_message}"
            }
        # Log output result
        print(f"[codespace_write_file] Output: {response}")
        return json.dumps(response, ensure_ascii=False)
    except Exception as e:
        result = {
            "success": False,
            "error": f"Error occurred while writing file: {str(e)}"
        }
        # Log exception
        print(f"[codespace_write_file] Exception: {result}")
        traceback.print_exc()
        return json.dumps(result, ensure_ascii=False)


@tool("codespace_read_file")
def codespace_read_file(
    path: str = Field(..., description="Path of the file to read"),
    runtime: ToolRuntime[CodespaceSessionData, None] = None
) -> str:
    """Read content from a file in the AgentBay codespace session"""
    # Log input parameters
    print(f"[codespace_read_file] Input: path={path}")
    
    try:
        # Access session from runtime store
        session = get_codespace_session(runtime)
        
        result = session.file_system.read_file(path)
        if result.success:
            response = {
                "success": True,
                "message": "File read successfully",
                "content": result.content
            }
        else:
            response = {
                "success": False,
                "error": f"Failed to read file: {result.error_message}"
            }
        # Log output result
        print(f"[codespace_read_file] Output: {response}")
        return json.dumps(response, ensure_ascii=False)
    except Exception as e:
        result = {
            "success": False,
            "error": f"Error occurred while reading file: {str(e)}"
        }
        # Log exception
        print(f"[codespace_read_file] Exception: {result}")
        traceback.print_exc()
        return json.dumps(result, ensure_ascii=False)


@tool("codespace_run_code")
def codespace_run_code(
    code: str = Field(..., description="The code to execute"),
    language: str = Field(..., description="The programming language of the code. Supported languages are: 'python', 'javascript'"),
    timeout_s: int = Field(default=60, description="The timeout for the code execution in seconds"),
    runtime: ToolRuntime[CodespaceSessionData, None] = None
) -> str:
    """Execute code in the AgentBay codespace session. Supported languages are: python, javascript. Note: Requires session created with code_latest image."""
    # Log input parameters
    print(f"[codespace_run_code] Input: language={language}, timeout_s={timeout_s}")
    
    try:
        # Access session from runtime store
        session = get_codespace_session(runtime)
        
        # Ensure timeout_s parameter is an integer value, not FieldInfo
        if timeout_s is None or not isinstance(timeout_s, int):
            timeout_s = 60
            
        # Use the direct run_code method from AgentBay SDK
        result = session.code.run_code(code, language, timeout_s)
        if result.success:
            response = {
                "success": True,
                "message": "Code executed successfully",
                "result": result.result,
                "request_id": result.request_id
            }
        else:
            response = {
                "success": False,
                "error": f"Code execution failed with error: {result.error_message}"
            }
        # Log output result
        print(f"[codespace_run_code] Output: {response}")
        return json.dumps(response, ensure_ascii=False)
    except Exception as e:
        result = {
            "success": False,
            "error": f"Error occurred while executing code: {str(e)}"
        }
        # Log exception
        print(f"[codespace_run_code] Exception: {result}")
        traceback.print_exc()
        return json.dumps(result, ensure_ascii=False)


@tool("codespace_execute_command")
def codespace_execute_command(
    command: str = Field(..., description="Shell command to execute"),
    timeout_ms: int = Field(default=1000, description="Timeout for command execution in milliseconds"),
    runtime: ToolRuntime[CodespaceSessionData, None] = None
) -> str:
    """Execute a shell command in the AgentBay codespace session"""
    # Log input parameters
    print(f"[codespace_execute_command] Input: command={command}, timeout_ms={timeout_ms}")
    
    try:
        # Access session from runtime store
        session = get_codespace_session(runtime)
        
        # Ensure timeout_ms parameter is an integer value, not FieldInfo
        if timeout_ms is None or not isinstance(timeout_ms, int):
            timeout_ms = 1000
            
        result = session.command.execute_command(command, timeout_ms)
        if result.success:
            response = {
                "success": True,
                "message": "Command executed successfully",
                "output": result.output
            }
        else:
            response = {
                "success": False,
                "error": f"Command failed with error: {result.error_message}"
            }
        # Log output result
        print(f"[codespace_execute_command] Output: {response}")
        return json.dumps(response, ensure_ascii=False)
    except Exception as e:
        result = {
            "success": False,
            "error": f"Error occurred while executing command: {str(e)}"
        }
        # Log exception
        print(f"[codespace_execute_command] Exception: {result}")
        traceback.print_exc()
        return json.dumps(result, ensure_ascii=False)


# Browser tools
@tool("browser_navigate")
def browser_navigate(
    url: str = Field(..., description="URL to navigate to"),
    runtime: ToolRuntime[BrowserSessionData, None] = None
) -> str:
    """Navigate to a URL in the AgentBay browser session"""
    # Log input parameters
    print(f"[browser_navigate] Input: url={url}")
    
    try:
        # Access session from runtime store
        session = get_browser_session(runtime)
        
        # Handle nested event loop issue
        try:
            # Try to import and apply nest_asyncio to handle nested event loops
            import nest_asyncio
            nest_asyncio.apply()
        except ImportError:
            pass
        
        # Navigate to the URL using the AgentBay session browser agent
        now_agent = session.browser.agent
        # Use run_until_complete if there's an event loop, otherwise use asyncio.run
        try:
            loop = asyncio.get_running_loop()
            result = loop.run_until_complete(now_agent.navigate_async(url))
        except RuntimeError:
            # No event loop running, use asyncio.run
            result = asyncio.run(now_agent.navigate_async(url))
            
        response = {
            "success": True,
            "message": f"Successfully navigated to {url}",
            "url": url
        }
        # Log output result
        print(f"[browser_navigate] Output: {response}")
        return json.dumps(response, ensure_ascii=False)
    except Exception as e:
        result = {
            "success": False,
            "error": f"Error occurred while navigating to URL: {str(e)}"
        }
        # Log exception
        print(f"[browser_navigate] Exception: {result}")
        traceback.print_exc()
        return json.dumps(result, ensure_ascii=False)


@tool("browser_act")
def browser_act(
    action: str = Field(..., description="Action to perform on the page"),
    runtime: ToolRuntime[BrowserSessionData, None] = None
) -> str:
    """Perform an action on browser page in the AgentBay browser session"""
    # Log input parameters
    print(f"[browser_act] Input: action={action}")
    
    try:
        # Access session from runtime store
        session = get_browser_session(runtime)
        
        # Handle nested event loop issue
        try:
            # Try to import and apply nest_asyncio to handle nested event loops
            import nest_asyncio
            nest_asyncio.apply()
        except ImportError:
            pass
        
        # Create ActOptions for the action
        act_options = ActOptions(action=action)
        
        # Use run_until_complete if there's an event loop, otherwise use asyncio.run
        try:
            loop = asyncio.get_running_loop()
            result = loop.run_until_complete(session.browser.agent.act_async(act_options))
        except RuntimeError:
            # No event loop running, use asyncio.run
            result = asyncio.run(session.browser.agent.act_async(act_options))
            
        # Return result as JSON string
        result_dict = {
            "success": result.success,
            "message": result.message,
            "action": action
        }
        
        result_json_str = json.dumps(result_dict, ensure_ascii=False)
        # Log output result
        print(f"[browser_act] Output: {result_json_str}")
        return result_json_str
    except Exception as e:
        result = {
            "success": False,
            "error": f"Error occurred while performing browser action: {str(e)}"
        }
        # Log exception
        print(f"[browser_act] Exception: {result}")
        traceback.print_exc()
        return json.dumps(result, ensure_ascii=False)


@tool("browser_screenshot")
def browser_screenshot(
    file_path: str = Field(..., description="File path to save the screenshot"),
    runtime: ToolRuntime[BrowserSessionData, None] = None
) -> str:
    """Take a screenshot of the current browser page in the AgentBay browser session"""
    # Log input parameters
    print(f"[browser_screenshot] Input: file_path={file_path}")
    
    try:
        # Access session from runtime store
        session = get_browser_session(runtime)
        
        # Handle nested event loop issue
        try:
            # Try to import and apply nest_asyncio to handle nested event loops
            import nest_asyncio
            nest_asyncio.apply()
        except ImportError:
            pass
            
        # Capture screenshot using browser agent
        # Use run_until_complete if there's an event loop, otherwise use asyncio.run
        try:
            loop = asyncio.get_running_loop()
            screenshot_result = loop.run_until_complete(session.browser.agent.screenshot_async())
        except RuntimeError:
            # No event loop running, use asyncio.run
            screenshot_result = asyncio.run(session.browser.agent.screenshot_async())
            
        if screenshot_result:
            import base64
            # Decode base64 string to bytes
            screenshot_data = base64.b64decode(screenshot_result.split(',')[1] if ',' in screenshot_result else screenshot_result)
            
            # Save to file
            with open(file_path, "wb") as f:
                f.write(screenshot_data)
            
            # Return result as JSON string
            result_dict = {
                "success": True,
                "message": "Screenshot captured successfully",
                "file_path": file_path
            }
            
            result_json_str = json.dumps(result_dict, ensure_ascii=False)
            # Log output result
            print(f"[browser_screenshot] Output: {result_json_str}")
            return result_json_str
        else:
            result_dict = {
                "success": False,
                "error": "Failed to capture screenshot"
            }
            result_json_str = json.dumps(result_dict, ensure_ascii=False)
            # Log output result
            print(f"[browser_screenshot] Output: {result_json_str}")
            return result_json_str
    except Exception as e:
        result = {
            "success": False,
            "error": f"Error occurred while capturing screenshot: {str(e)}"
        }
        # Log exception
        print(f"[browser_screenshot] Exception: {result}")
        traceback.print_exc()
        return json.dumps(result, ensure_ascii=False)


# Computer tools
@tool("computer_click_mouse")
def computer_click_mouse(
    x: int = Field(..., description="X coordinate for mouse click"),
    y: int = Field(..., description="Y coordinate for mouse click"),
    button: str = Field(default="left", description="Mouse button to click. Options: 'left', 'right', 'middle', 'double_left'"),
    runtime: ToolRuntime[ComputerSessionData, None] = None
) -> str:
    """Click the mouse at specified coordinates with the specified button. Requires a computer session with image_id='windows_latest'"""
    # Log input parameters
    print(f"[computer_click_mouse] Input: x={x}, y={y}, button={button}")
    
    try:
        # Access session from runtime store
        session = get_computer_session(runtime)
        
        # Ensure button parameter is a string value, not FieldInfo
        if button is None or not isinstance(button, str):
            button = "left"
            
        # Map string button to MouseButton enum
        from agentbay.computer import MouseButton
        button_map = {
            "left": MouseButton.LEFT,
            "right": MouseButton.RIGHT,
            "middle": MouseButton.MIDDLE,
            "double_left": MouseButton.DOUBLE_LEFT
        }
        mouse_button = button_map.get(button.lower(), MouseButton.LEFT)
        
        # Perform actual mouse click operation using AgentBay session
        print(f"[computer_click_mouse] Clicking mouse at coordinates ({x}, {y}) with {mouse_button} button")
        result = session.computer.click_mouse(x=x, y=y, button=mouse_button)
        
        if result.success:
            response = {
                "success": True,
                "message": f"Successfully clicked mouse at coordinates ({x}, {y}) with {button} button",
                "x": x,
                "y": y,
                "button": button
            }
        else:
            response = {
                "success": False,
                "error": f"Failed to click mouse at coordinates ({x}, {y}) with {button} button: {result.error_message}"
            }
        # Log output result
        print(f"[computer_click_mouse] Output: {response}")
        return json.dumps(response, ensure_ascii=False)
    except Exception as e:
        result = {
            "success": False,
            "error": f"Error occurred while clicking mouse: {str(e)}"
        }
        # Log exception
        print(f"[computer_click_mouse] Exception: {result}")
        traceback.print_exc()
        return json.dumps(result, ensure_ascii=False)


@tool("computer_move_mouse")
def computer_move_mouse(
    x: int = Field(..., description="Target X coordinate for mouse movement"),
    y: int = Field(..., description="Target Y coordinate for mouse movement"),
    runtime: ToolRuntime[ComputerSessionData, None] = None
) -> str:
    """Move the mouse to specified coordinates. Requires a computer session with image_id='windows_latest'"""
    # Log input parameters
    print(f"[computer_move_mouse] Input: x={x}, y={y}")
    
    try:
        # Access session from runtime store
        session = get_computer_session(runtime)
        
        # Perform actual mouse move operation using AgentBay session
        result = session.computer.move_mouse(x=x, y=y)
        
        if result.success:
            response = {
                "success": True,
                "message": f"Successfully moved mouse to coordinates ({x}, {y})",
                "x": x,
                "y": y
            }
        else:
            response = {
                "success": False,
                "error": f"Failed to move mouse to coordinates ({x}, {y}): {result.error_message}"
            }
        # Log output result
        print(f"[computer_move_mouse] Output: {response}")
        return json.dumps(response, ensure_ascii=False)
    except Exception as e:
        result = {
            "success": False,
            "error": f"Error occurred while moving mouse: {str(e)}"
        }
        # Log exception
        print(f"[computer_move_mouse] Exception: {result}")
        traceback.print_exc()
        return json.dumps(result, ensure_ascii=False)


@tool("computer_drag_mouse")
def computer_drag_mouse(
    from_x: int = Field(..., description="Starting X coordinate for drag operation"),
    from_y: int = Field(..., description="Starting Y coordinate for drag operation"),
    to_x: int = Field(..., description="Ending X coordinate for drag operation"),
    to_y: int = Field(..., description="Ending Y coordinate for drag operation"),
    button: str = Field(default="left", description="Mouse button to use for dragging. Options: 'left', 'right', 'middle'"),
    runtime: ToolRuntime[ComputerSessionData, None] = None
) -> str:
    """Drag the mouse from one point to another. Requires a computer session with image_id='windows_latest'"""
    # Log input parameters
    print(f"[computer_drag_mouse] Input: from_x={from_x}, from_y={from_y}, to_x={to_x}, to_y={to_y}, button={button}")
    
    try:
        # Access session from runtime store
        session = get_computer_session(runtime)
        
        # Ensure button parameter is a string value, not FieldInfo
        if button is None or not isinstance(button, str):
            button = "left"
            
        # Map string button to MouseButton enum
        from agentbay.computer import MouseButton
        button_map = {
            "left": MouseButton.LEFT,
            "right": MouseButton.RIGHT,
            "middle": MouseButton.MIDDLE
        }
        if button is None:
            button = "left"
        mouse_button = button_map.get(button.lower(), MouseButton.LEFT)
        
        # Perform actual mouse drag operation using AgentBay session
        result = session.computer.drag_mouse(from_x=from_x, from_y=from_y, to_x=to_x, to_y=to_y, button=mouse_button)
        
        if result.success:
            response = {
                "success": True,
                "message": f"Successfully dragged mouse from ({from_x}, {from_y}) to ({to_x}, {to_y}) with {button} button",
                "from_x": from_x,
                "from_y": from_y,
                "to_x": to_x,
                "to_y": to_y,
                "button": button
            }
        else:
            response = {
                "success": False,
                "error": f"Failed to drag mouse from ({from_x}, {from_y}) to ({to_x}, {to_y}) with {button} button: {result.error_message}"
            }
        # Log output result
        print(f"[computer_drag_mouse] Output: {response}")
        return json.dumps(response, ensure_ascii=False)
    except Exception as e:
        result = {
            "success": False,
            "error": f"Error occurred while dragging mouse: {str(e)}"
        }
        # Log exception
        print(f"[computer_drag_mouse] Exception: {result}")
        traceback.print_exc()
        return json.dumps(result, ensure_ascii=False)


@tool("computer_scroll")
def computer_scroll(
    x: int = Field(..., description="X coordinate for scroll operation"),
    y: int = Field(..., description="Y coordinate for scroll operation"),
    direction: str = Field(default="up", description="Scroll direction. Options: 'up', 'down', 'left', 'right'"),
    amount: int = Field(default=1, description="Scroll amount"),
    runtime: ToolRuntime[ComputerSessionData, None] = None
) -> str:
    """Scroll the mouse wheel at specified coordinates. Requires a computer session with image_id='windows_latest'"""
    # Log input parameters
    print(f"[computer_scroll] Input: x={x}, y={y}, direction={direction}, amount={amount}")
    
    try:
        # Access session from runtime store
        session = get_computer_session(runtime)
        
        # Ensure direction parameter is a string value, not FieldInfo
        if direction is None or not isinstance(direction, str):
            direction = "up"
            
        # Ensure amount parameter is an integer value, not FieldInfo
        if amount is None or not isinstance(amount, int):
            amount = 1
            
        # Map string direction to ScrollDirection enum
        from agentbay.computer import ScrollDirection
        direction_map = {
            "up": ScrollDirection.UP,
            "down": ScrollDirection.DOWN,
            "left": ScrollDirection.LEFT,
            "right": ScrollDirection.RIGHT
        }
        scroll_direction = direction_map.get(direction.lower(), ScrollDirection.UP)
        
        # Perform actual scroll operation using AgentBay session
        result = session.computer.scroll(x=x, y=y, direction=scroll_direction, amount=amount)
        
        if result.success:
            response = {
                "success": True,
                "message": f"Successfully scrolled at coordinates ({x}, {y}) in {direction} direction by amount {amount}",
                "x": x,
                "y": y,
                "direction": direction,
                "amount": amount
            }
        else:
            response = {
                "success": False,
                "error": f"Failed to scroll at coordinates ({x}, {y}) in {direction} direction by amount {amount}: {result.error_message}"
            }
        # Log output result
        print(f"[computer_scroll] Output: {response}")
        return json.dumps(response, ensure_ascii=False)
    except Exception as e:
        result = {
            "success": False,
            "error": f"Error occurred while scrolling: {str(e)}"
        }
        # Log exception
        print(f"[computer_scroll] Exception: {result}")
        traceback.print_exc()
        return json.dumps(result, ensure_ascii=False)


@tool("computer_get_cursor_position")
def computer_get_cursor_position(
    runtime: ToolRuntime[ComputerSessionData, None] = None
) -> str:
    """Get the current cursor position. Requires a computer session with image_id='windows_latest'"""
    # Log input parameters
    print(f"[computer_get_cursor_position] Input: None")
    
    try:
        # Access session from runtime store
        session = get_computer_session(runtime)
        
        # Perform actual get cursor position operation using AgentBay session
        result = session.computer.get_cursor_position()
        
        if result.success:
            data = json.loads(result.data)
            response = {
                "success": True,
                "message": "Successfully retrieved cursor position",
                "x": data["x"],
                "y": data["y"]
            }
        else:
            response = {
                "success": False,
                "error": f"Failed to get cursor position: {result.error_message}"
            }
        # Log output result
        print(f"[computer_get_cursor_position] Output: {response}")
        return json.dumps(response, ensure_ascii=False)
    except Exception as e:
        result = {
            "success": False,
            "error": f"Error occurred while getting cursor position: {str(e)}"
        }
        # Log exception
        print(f"[computer_get_cursor_position] Exception: {result}")
        traceback.print_exc()
        return json.dumps(result, ensure_ascii=False)


@tool("computer_input_text")
def computer_input_text(
    text: str = Field(..., description="Text to input"),
    runtime: ToolRuntime[ComputerSessionData, None] = None
) -> str:
    """Input text into the active field. Requires a computer session with image_id='windows_latest'"""
    # Log input parameters
    print(f"[computer_input_text] Input: text='{text}'")
    
    try:
        # Access session from runtime store
        session = get_computer_session(runtime)
        
        # Perform actual text input operation using AgentBay session
        result = session.computer.input_text(text)
        
        if result.success:
            response = {
                "success": True,
                "message": f"Successfully input text: {text}",
                "text": text
            }
        else:
            response = {
                "success": False,
                "error": f"Failed to input text '{text}': {result.error_message}"
            }
        # Log output result
        print(f"[computer_input_text] Output: {response}")
        return json.dumps(response, ensure_ascii=False)
    except Exception as e:
        result = {
            "success": False,
            "error": f"Error occurred while inputting text: {str(e)}"
        }
        # Log exception
        print(f"[computer_input_text] Exception: {result}")
        traceback.print_exc()
        return json.dumps(result, ensure_ascii=False)


def computer_press_keys_body(session, keys: List[str], hold: bool):
    result = session.computer.press_keys(keys, hold=hold)
    return result
    
@tool("computer_press_keys")
def computer_press_keys(
    keys: List[str] = Field(..., description="List of keys to press (e.g., ['Ctrl', 'a'])"),
    hold: bool = Field(default=False, description="Whether to hold the keys"),
    runtime: ToolRuntime[ComputerSessionData, None] = None
) -> str:
    """Press the specified keys. Requires a computer session with image_id='windows_latest'"""
    # Log input parameters
    print(f"[computer_press_keys] Input: keys={keys}, hold={hold}")
    
    try:
        # Access session from runtime store
        session = get_computer_session(runtime)
        
        # Ensure hold parameter is a boolean value, not FieldInfo
        if hold is None or not isinstance(hold, bool):
            hold = False
            
        # Perform actual key press operation using AgentBay session
        result = computer_press_keys_body(session, keys, hold)
        if result.success:
            response = {
                "success": True,
                "message": f"Successfully pressed keys {keys}" + (" and held" if hold else ""),
                "keys": keys,
                "hold": hold
            }
        else:
            response = {
                "success": False,
                "error": f"Failed to press keys {keys}: {result.error_message}"
            }
        # Log output result
        print(f"[computer_press_keys] Output: {response}")
        return json.dumps(response, ensure_ascii=False)
    except Exception as e:
        result = {
            "success": False,
            "error": f"Error occurred while pressing keys: {str(e)}"
        }
        # Log exception
        print(f"[computer_press_keys] Exception: {result}")
        traceback.print_exc()
        return json.dumps(result, ensure_ascii=False)


@tool("computer_ocr_elements", description="输出的OCR坐标系格式：UI坐标结构为 [center_x, center_y, width, height, angle]，enter_x、center_y 为文本框中心点坐标，width为宽度，hight为高度，angle为文本框相对于水平方向的旋转角度，取值范围为[-90, 90]。使用坐标生成点击坐标时，请综合center_x, center_y, width, height计算一个新位于中心的点击点。 ")
def computer_ocr_elements(
    image_url: str = Field(..., description="URL of the screenshot image to analyze"),
    runtime: ToolRuntime[ComputerSessionData, None] = None
) -> str:
    """Analyze a screenshot and identify all interactive UI elements with text, returning their coordinates in [center_x, center_y, width, height, angle] format. Requires DashScope API key."""
    # Log input parameters
    print(f"[computer_ocr_elements] Input: image_url={image_url}")
    
    try:
        # Check if dashscope is available
        if not DASHSCOPE_AVAILABLE:
            response = {
                "success": False,
                "error": "DashScope library not available. Please install dashscope package."
            }
            print(f"[computer_ocr_elements] Output: {response}")
            return json.dumps(response, ensure_ascii=False)
        
        # Get API key from environment
        api_key = os.getenv('DASHSCOPE_API_KEY')
        if not api_key:
            response = {
                "success": False,
                "error": "DASHSCOPE_API_KEY environment variable not set"
            }
            print(f"[computer_ocr_elements] Output: {response}")
            return json.dumps(response, ensure_ascii=False)
        
        # Prepare the message for OCR
        messages = [{
            "role": "user",
            "content": [{
                "image": image_url,
                "min_pixels": 28 * 28 * 4,
                "max_pixels": 2560 * 1440,
                "enable_rotate": False},
                {"text": "定位所有的可以单独被点击操作的按钮、标签文字，并且返回旋转矩形([cx, cy, width, height, angle])的坐标结果。"}]
        }]
        
        # Call DashScope OCR API
        response = dashscope.MultiModalConversation.call(
            api_key=api_key,
            model='qwen-vl-ocr-2025-08-28',
            messages=messages,
            ocr_options={"task": "advanced_recognition"}
        )
        
        # Process the response
        if response.get("output") and response["output"].get("choices"):
            result_text = response["output"]["choices"][0]["message"]["content"][0]["text"]
            
            response_data = {
                "success": True,
                "message": "OCR analysis completed successfully",
                "result": result_text
            }
        else:
            response_data = {
                "success": False,
                "error": "Failed to get valid response from OCR service",
                "raw_response": str(response)
            }
            
        # Log output result
        print(f"[computer_ocr_elements] Output: {response_data}")
        return json.dumps(response_data, ensure_ascii=False)
    except Exception as e:
        result = {
            "success": False,
            "error": f"Error occurred while performing OCR: {str(e)}"
        }
        # Log exception
        print(f"[computer_ocr_elements] Exception: {result}")
        traceback.print_exc()
        return json.dumps(result, ensure_ascii=False)


@tool("computer_screenshot")
def computer_screenshot(
    file_path: str = Field(..., description="File path to save the screenshot"),
    runtime: ToolRuntime[ComputerSessionData, None] = None
) -> str:
    """Take a screenshot of the current screen. Requires a computer session with image_id='windows_latest'"""
    # Log input parameters
    print(f"[computer_screenshot] Input: file_path={file_path}")
    
    try:
        # Access session from runtime store
        session = get_computer_session(runtime)
        
        # Perform actual screenshot operation using AgentBay session
        result = session.computer.screenshot()
        
        if result.success:
            response_data = {
                "success": True,
                "message": "Screenshot captured successfully",
                "screenshot_url": result.data
            }
            
            # Download and save the screenshot
            try:
                import requests
                import os
                
                # Create directory if it doesn't exist
                directory = os.path.dirname(file_path)
                if directory:
                    os.makedirs(directory, exist_ok=True)
                
                # Download the screenshot
                download_response = requests.get(result.data)
                download_response.raise_for_status()
                
                # Save to file
                with open(file_path, 'wb') as f:
                    f.write(download_response.content)
                
                response_data["file_path"] = file_path
                response_data["message"] += f" and saved to {file_path}"
                
            except Exception as download_error:
                response_data["success"] = False
                response_data["error"] = f"Failed to download or save screenshot: {str(download_error)}"
            
            response = response_data
        else:
            response = {
                "success": False,
                "error": f"Failed to capture screenshot: {result.error_message}"
            }
        # Log output result
        print(f"[computer_screenshot] Output: {response}")
        return json.dumps(response, ensure_ascii=False)
    except Exception as e:
        result = {
            "success": False,
            "error": f"Error occurred while capturing screenshot: {str(e)}"
        }
        # Log exception
        print(f"[computer_screenshot] Exception: {result}")
        traceback.print_exc()
        return json.dumps(result, ensure_ascii=False)


@tool("computer_vlm_analysis")
def computer_vlm_analysis(
    image_url: str = Field(..., description="URL of the image to analyze"),
    prompt: str = Field(..., description="Custom prompt for the vision language model"),
    runtime: ToolRuntime[ComputerSessionData, None] = None
) -> str:
    """Analyze an image using a vision language model with a custom prompt. Requires DashScope API key."""
    # Log input parameters
    print(f"[computer_vlm_analysis] Input: image_url={image_url}, prompt={prompt}")
    
    try:
        # Check if dashscope is available
        if not DASHSCOPE_AVAILABLE:
            response = {
                "success": False,
                "error": "DashScope library not available. Please install dashscope package."
            }
            print(f"[computer_vlm_analysis] Output: {response}")
            return json.dumps(response, ensure_ascii=False)
        
        # Get API key from environment
        api_key = os.getenv('DASHSCOPE_API_KEY')
        if not api_key:
            response = {
                "success": False,
                "error": "DASHSCOPE_API_KEY environment variable not set"
            }
            print(f"[computer_vlm_analysis] Output: {response}")
            return json.dumps(response, ensure_ascii=False)
        
        # Prepare the message for VLM
        messages = [
            {
                "role": "user",
                "content": [
                    {"image": image_url},
                    {"text": prompt}
                ]
            }
        ]
        
        # Call DashScope VLM API
        response = dashscope.MultiModalConversation.call(
            api_key=api_key,
            model='qwen3-vl-plus',
            messages=messages
        )
        
        # Process the response
        if response.get("output") and response["output"].get("choices"):
            result_text = response["output"]["choices"][0]["message"]["content"][0]["text"]
            
            response_data = {
                "success": True,
                "message": "VLM analysis completed successfully",
                "result": result_text
            }
        else:
            response_data = {
                "success": False,
                "error": "Failed to get valid response from VLM service",
                "raw_response": str(response)
            }
            
        # Log output result
        print(f"[computer_vlm_analysis] Output: {response_data}")
        return json.dumps(response_data, ensure_ascii=False)
    except Exception as e:
        result = {
            "success": False,
            "error": f"Error occurred while performing VLM analysis: {str(e)}"
        }
        # Log exception
        print(f"[computer_vlm_analysis] Exception: {result}")
        traceback.print_exc()
        return json.dumps(result, ensure_ascii=False)


@tool("computer_wait")
def computer_wait(
    milliseconds: int = Field(..., description="Time to wait in milliseconds"),
    runtime: ToolRuntime[ComputerSessionData, None] = None
) -> str:
    """Wait for a specified amount of time in milliseconds. Useful for waiting for remote operations to complete."""
    # Log input parameters
    print(f"[computer_wait] Input: milliseconds={milliseconds}")
    
    try:
        # Convert milliseconds to seconds for time.sleep()
        seconds = milliseconds / 1000.0
        
        # Wait for the specified time
        time.sleep(seconds)
        
        response = {
            "success": True,
            "message": f"Successfully waited for {milliseconds} milliseconds ({seconds} seconds)"
        }
        
        # Log output result
        print(f"[computer_wait] Output: {response}")
        return json.dumps(response, ensure_ascii=False)
    except Exception as e:
        result = {
            "success": False,
            "error": f"Error occurred while waiting: {str(e)}"
        }
        # Log exception
        print(f"[computer_wait] Exception: {result}")
        traceback.print_exc()
        return json.dumps(result, ensure_ascii=False)


@tool("computer_get_screen_size")
def computer_get_screen_size(
    runtime: ToolRuntime[ComputerSessionData, None] = None
) -> str:
    """Get the screen size (width, height) and DPI scaling factor. Requires a computer session with image_id='windows_latest' or 'linux_latest'"""
    # Log input parameters
    print(f"[computer_get_screen_size] Input: None")
    
    try:
        # Access session from runtime store
        session = get_computer_session(runtime)
        
        # Perform actual get screen size operation using AgentBay session
        result = session.computer.get_screen_size()
        
        if result.success:
            data = json.loads(result.data)
            response = {
                "success": True,
                "message": "Successfully retrieved screen size and DPI scaling factor",
                "width": data["width"],
                "height": data["height"],
                "dpiScalingFactor": data["dpiScalingFactor"]
            }
        else:
            response = {
                "success": False,
                "error": f"Failed to get screen size: {result.error_message}"
            }
        # Log output result
        print(f"[computer_get_screen_size] Output: {response}")
        return json.dumps(response, ensure_ascii=False)
    except Exception as e:
        result = {
            "success": False,
            "error": f"Error occurred while getting screen size: {str(e)}"
        }
        # Log exception
        print(f"[computer_get_screen_size] Exception: {result}")
        traceback.print_exc()
        return json.dumps(result, ensure_ascii=False)