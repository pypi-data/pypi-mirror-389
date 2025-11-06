from importlib import metadata

# Existing imports
try:
    from langchain_agentbay_integration.toolkits import (
        MobileIntegrationToolkit,
        CodespaceIntegrationToolkit,
        BrowserIntegrationToolkit,
        ComputerIntegrationToolkit
    )
except ImportError:
    # Handle case where some modules might not be available
    MobileIntegrationToolkit = None
    CodespaceIntegrationToolkit = None
    BrowserIntegrationToolkit = None
    ComputerIntegrationToolkit = None

# Try to import mobile tools
try:
    from langchain_agentbay_integration.tools import (
        mobile_tap,
        mobile_swipe,
        mobile_input_text,
        mobile_send_key,
        mobile_get_ui_elements,
        mobile_screenshot,
        mobile_wait
    )
except ImportError:
    # Handle case where mobile modules might not be available
    mobile_tap = None
    mobile_swipe = None
    mobile_input_text = None
    mobile_send_key = None
    mobile_get_ui_elements = None
    mobile_screenshot = None
    mobile_wait = None

# Try to import codespace tools
try:
    from langchain_agentbay_integration.tools import (
        codespace_write_file,
        codespace_read_file,
        codespace_run_code,
        codespace_execute_command
    )
except ImportError:
    # Handle case where codespace modules might not be available
    codespace_write_file = None
    codespace_read_file = None
    codespace_run_code = None
    codespace_execute_command = None

# Try to import browser tools
try:
    from langchain_agentbay_integration.tools import (
        browser_navigate,
        browser_act,
        browser_screenshot
    )
except ImportError:
    # Handle case where browser modules might not be available
    browser_navigate = None
    browser_act = None
    browser_screenshot = None

# Try to import computer tools
try:
    from langchain_agentbay_integration.tools import (
        computer_click_mouse,
        computer_move_mouse,
        computer_drag_mouse,
        computer_scroll,
        computer_get_cursor_position,
        computer_input_text,
        computer_press_keys,
        computer_screenshot,
        computer_vlm_analysis,
        computer_wait,
        computer_get_screen_size
    )
except ImportError:
    # Handle case where computer modules might not be available
    computer_click_mouse = None
    computer_move_mouse = None
    computer_drag_mouse = None
    computer_scroll = None
    computer_get_cursor_position = None
    computer_input_text = None
    computer_press_keys = None
    computer_screenshot = None
    computer_vlm_analysis = None
    computer_wait = None
    computer_get_screen_size = None

# Try to import self-evolving agent components
try:
    from langchain_agentbay_integration.self_evolving.self_evolving_agent import (
        PlayerAgent,
        CoachAgent
    )
except ImportError:
    # Handle case where self-evolving modules might not be available
    PlayerAgent = None
    CoachAgent = None

# Try to import self-evolving web visualizer
try:
    from langchain_agentbay_integration.self_evolving.self_evolving_web_visualizer import (
        WebVisualizer
    )
except ImportError:
    # Handle case where web visualizer module might not be available
    WebVisualizer = None

try:
    __version__ = metadata.version(__package__)
except metadata.PackageNotFoundError:
    # Case where package metadata is not available.
    __version__ = ""
del metadata  # optional, avoids polluting the results of dir(__package__)

__all__ = [
    # Toolkits
    "MobileIntegrationToolkit",
    "CodespaceIntegrationToolkit",
    "BrowserIntegrationToolkit",
    "ComputerIntegrationToolkit",
    
    # Mobile tools
    "mobile_tap",
    "mobile_swipe",
    "mobile_input_text",
    "mobile_send_key",
    "mobile_get_ui_elements",
    "mobile_screenshot",
    "mobile_wait",
    
    # Codespace tools
    "codespace_write_file",
    "codespace_read_file",
    "codespace_run_code",
    "codespace_execute_command",
    
    # Browser tools
    "browser_navigate",
    "browser_act",
    "browser_screenshot",
    
    # Computer tools
    "computer_click_mouse",
    "computer_move_mouse",
    "computer_drag_mouse",
    "computer_scroll",
    "computer_get_cursor_position",
    "computer_input_text",
    "computer_press_keys",
    "computer_screenshot",
    "computer_vlm_analysis",
    "computer_wait",
    "computer_get_screen_size",
    
    # Self-evolving agent components
    "PlayerAgent",
    "CoachAgent",
    
    # Self-evolving web visualizer
    "WebVisualizer",
    
    "__version__",
]