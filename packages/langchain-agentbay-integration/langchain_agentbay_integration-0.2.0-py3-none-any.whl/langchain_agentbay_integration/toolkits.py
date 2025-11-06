from typing import List
from langchain_core.tools import BaseTool

# Try to import required classes for browser initialization
try:
    from agentbay.browser.browser import BrowserOption
    from playwright.sync_api import sync_playwright
    BROWSER_DEPS_AVAILABLE = True
except ImportError:
    BROWSER_DEPS_AVAILABLE = False


class MobileIntegrationToolkit:
    """Toolkit for mobile operations in AgentBay sessions.
    
    This toolkit provides tools for interacting with mobile environments in AgentBay.
    It requires a mobile session created with image_id="mobile_latest".
    
    Example:
        .. code-block:: python
        
            from agentbay import AgentBay
            from agentbay.session_params import CreateSessionParams
            from langchain_agentbay_integration.toolkits import MobileIntegrationToolkit
            from langchain_agentbay_integration.tools import set_global_session
            
            # Create mobile session
            agent_bay = AgentBay()
            session_params = CreateSessionParams(image_id="mobile_latest")
            result = agent_bay.create(session_params)
            session = result.session
            
            # Set global session for tools to use
            set_global_session(session)
            
            # Create toolkit
            toolkit = MobileIntegrationToolkit()
            tools = toolkit.get_tools()
            
            # Use tools
            for tool in tools:
                print(f"Tool: {tool.name} - {tool.description}")
    """
    
    def __init__(self) -> None:
        """Initialize without a mobile session.
        
        Session is now managed globally via AgentBayGlobalMemory.
        """
        pass
        
    def get_tools(self) -> List[BaseTool]:
        """Get the tools in the toolkit."""
        # Import tools here to avoid circular imports
        from langchain_agentbay_integration.tools import (
            mobile_tap,
            mobile_swipe,
            mobile_input_text,
            mobile_send_key,
            mobile_get_ui_elements,
            mobile_screenshot,
            mobile_wait
        )
        
        # Create tools with session context
        tools = [
            mobile_tap,
            mobile_swipe,
            mobile_input_text,
            mobile_send_key,
            mobile_get_ui_elements,
            mobile_screenshot,
            mobile_wait
        ]
        
        # Return tools (they will access session via global memory)
        return tools


class CodespaceIntegrationToolkit:
    """Toolkit for codespace operations in AgentBay sessions.
    
    This toolkit provides tools for interacting with codespace environments in AgentBay.
    It requires a codespace session created with image_id="code_latest".
    
    Example:
        .. code-block:: python
        
            from agentbay import AgentBay
            from agentbay.session_params import CreateSessionParams
            from langchain_agentbay_integration.toolkits import CodespaceIntegrationToolkit
            
            # Create codespace session
            agent_bay = AgentBay()
            session_params = CreateSessionParams(image_id="code_latest")
            result = agent_bay.create(session_params)
            session = result.session
            
            # Create toolkit
            toolkit = CodespaceIntegrationToolkit()
            tools = toolkit.get_tools()
            
            # Use tools
            for tool in tools:
                print(f"Tool: {tool.name} - {tool.description}")
    """
    
    def __init__(self) -> None:
        """Initialize without a codespace session.
        
        Session is managed via runtime store.
        """
        pass
        
    def get_tools(self) -> List[BaseTool]:
        """Get the tools in the toolkit."""
        # Import tools here to avoid circular imports
        from langchain_agentbay_integration.tools import (
            codespace_write_file,
            codespace_read_file,
            codespace_run_code,
            codespace_execute_command
        )
        
        # Create tools with session context
        tools = [
            codespace_write_file,
            codespace_read_file,
            codespace_run_code,
            codespace_execute_command
        ]
        
        # Return tools
        return tools


class BrowserIntegrationToolkit:
    """Toolkit for browser operations in AgentBay sessions.
    
    This toolkit provides tools for interacting with browser environments in AgentBay.
    It requires a browser session created with image_id="browser_latest".
    
    Browser initialization:
        Browser initialization must be done before using browser tools.
        
        .. code-block:: python
        
            from agentbay import AgentBay
            from agentbay.session_params import CreateSessionParams
            from langchain_agentbay_integration.toolkits import BrowserIntegrationToolkit
            
            # Create browser session
            agent_bay = AgentBay()
            session_params = CreateSessionParams(image_id="browser_latest")
            result = agent_bay.create(session_params)
            session = result.session
            
            # Create toolkit and initialize browser
            toolkit = BrowserIntegrationToolkit()
            browser_context = toolkit.initialize_browser(session)
            
            # Use tools
            tools = toolkit.get_tools()
            
            # Cleanup when done
            toolkit.cleanup_browser()
    
    Example:
        .. code-block:: python
        
            from agentbay import AgentBay
            from agentbay.session_params import CreateSessionParams
            from langchain_agentbay_integration.toolkits import BrowserIntegrationToolkit
            
            # Create browser session
            agent_bay = AgentBay()
            session_params = CreateSessionParams(image_id="browser_latest")
            result = agent_bay.create(session_params)
            session = result.session
            
            # Create toolkit
            toolkit = BrowserIntegrationToolkit()
            tools = toolkit.get_tools()
            
            # Use tools
            for tool in tools:
                print(f"Tool: {tool.name} - {tool.description}")
    """
    
    def __init__(self) -> None:
        """Initialize without a browser session.
        
        Session is managed via runtime store.
        """
        self.browser = None
        self.playwright = None
        
    def initialize_browser(self, session):
        """Initialize browser with actual browser connection.
        
        This method must be called before using browser tools.
        
        Args:
            session: AgentBay session object
            
        Returns:
            Browser context object
            
        Example:
            .. code-block:: python
            
                browser_context = toolkit.initialize_browser(session)
                # Then use browser tools
        """
        if not BROWSER_DEPS_AVAILABLE:
            raise ImportError(
                "Browser dependencies not available. Please install agentbay and playwright packages."
            )
            
        # Initialize browser
        init_result = session.browser.initialize(BrowserOption())
        if not init_result:
            raise Exception("Failed to initialize browser")
        
        return init_result

    def cleanup_browser(self):
        """Clean up browser resources.
        
        This method should be called when finished using browser tools.
        """
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        
    def get_tools(self) -> List[BaseTool]:
        """Get the tools in the toolkit."""
        # Import tools here to avoid circular imports
        from langchain_agentbay_integration.tools import (
            browser_navigate,
            browser_act,
            browser_screenshot
        )
        
        # Create tools with session context
        tools = [
            browser_navigate,
            browser_act,
            browser_screenshot
        ]
        
        # Return tools
        return tools


class ComputerIntegrationToolkit:
    """Toolkit for computer UI operations in AgentBay sessions.
    
    This toolkit provides tools for interacting with computer UI environments in AgentBay.
    It requires a computer session created with image_id="windows_latest".
    
    Example:
        .. code-block:: python
        
            from agentbay import AgentBay
            from agentbay.session_params import CreateSessionParams
            from langchain_agentbay_integration.toolkits import ComputerIntegrationToolkit
            
            # Create computer session
            agent_bay = AgentBay()
            session_params = CreateSessionParams(image_id="windows_latest")
            result = agent_bay.create(session_params)
            session = result.session
            
            # Create toolkit
            toolkit = ComputerIntegrationToolkit()
            tools = toolkit.get_tools()
            
            # Use tools
            for tool in tools:
                print(f"Tool: {tool.name} - {tool.description}")
    """
    
    def __init__(self) -> None:
        """Initialize without a computer session.
        
        Session is managed via runtime store.
        """
        pass
        
    def get_tools(self) -> List[BaseTool]:
        """Get the tools in the toolkit."""
        # Import tools here to avoid circular imports
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
        
        # Create tools with session context
        tools = [
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
        ]
        
        # Return tools
        return tools
