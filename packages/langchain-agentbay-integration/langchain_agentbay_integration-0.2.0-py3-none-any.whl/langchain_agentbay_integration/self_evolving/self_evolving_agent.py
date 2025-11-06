import os
import json
import uuid
import shutil
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from collections import namedtuple

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.store.memory import InMemoryStore

from agentbay import AgentBay
from agentbay.session_params import CreateSessionParams

# Fix the import path for MobileIntegrationToolkit
from ..toolkits import MobileIntegrationToolkit
from ..tools import MobileSessionData


def json_serializer(obj):
    """Custom JSON serializer for objects that are not natively serializable."""
    if isinstance(obj, (HumanMessage, AIMessage, SystemMessage, ToolMessage)):
        result = {
            "type": obj.__class__.__name__,
            "content": obj.content if hasattr(obj, 'content') else str(obj)
        }
        # Include additional attributes if they exist
        if hasattr(obj, 'additional_kwargs'):
            result["additional_kwargs"] = obj.additional_kwargs
        if hasattr(obj, 'name'):
            result["name"] = obj.name
        if hasattr(obj, 'tool_calls'):
            result["tool_calls"] = obj.tool_calls
        if hasattr(obj, 'tool_call_id'):
            result["tool_call_id"] = obj.tool_call_id
        return result
    elif hasattr(obj, '__dict__'):
        # For other custom objects, try to serialize their __dict__
        return obj.__dict__
    else:
        # For everything else, convert to string
        return str(obj)


def extract_ui_elements_info(execution_result: Dict[str, Any]) -> str:
    """
    Extract UI elements information from execution result.
    
    Args:
        execution_result: The execution result from Player Agent
        
    Returns:
        Formatted string with UI elements information
    """
    ui_elements_info = "No UI elements information found"
    if 'full_result' in execution_result and execution_result['full_result']:
        full_result = execution_result['full_result']
        # Look for mobile_get_ui_elements tool calls in the messages
        if 'messages' in full_result:
            ui_elements_list = []
            for message in full_result['messages']:
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    for tool_call in message.tool_calls:
                        if tool_call.get('name') == 'mobile_get_ui_elements':
                            ui_elements_list.append(tool_call)
                # Also check for tool messages that might contain UI elements
                elif hasattr(message, 'name') and message.name == 'mobile_get_ui_elements':
                    ui_elements_list.append({
                        'name': message.name,
                        'content': getattr(message, 'content', 'No content available')
                    })
        
            if ui_elements_list:
                ui_elements_info = f"Found {len(ui_elements_list)} UI elements retrieval operations:\n"
                for i, elem in enumerate(ui_elements_list):
                    ui_elements_info += f"{i+1}. Tool: {elem.get('name', 'Unknown')}\n"
                    if 'content' in elem:
                        ui_elements_info += f"   Content: {elem['content'][:500]}...\n"  # Limit length
                    if 'args' in elem:
                        ui_elements_info += f"   Args: {elem['args']}\n"
    
    return ui_elements_info


def extract_tool_execution_sequence(execution_result: Dict[str, Any]) -> str:
    """
    Extract simplified tool execution sequence from execution result.
    
    Args:
        execution_result: The execution result from Player Agent
        
    Returns:
        Formatted string with tool execution sequence
    """
    tool_sequence = "No simplified tool execution sequence available"
    if 'full_result' in execution_result and execution_result['full_result']:
        full_result = execution_result['full_result']
        if 'messages' in full_result:
            tool_calls = []
            for message in full_result['messages']:
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    for tool_call in message.tool_calls:
                        tool_calls.append({
                            'name': tool_call.get('name', 'Unknown'),
                            'args': tool_call.get('args', {})
                        })
            
            if tool_calls:
                tool_sequence = "Executed tool sequence:\n"
                for i, call in enumerate(tool_calls):
                    tool_sequence += f"{i+1}. {call['name']}"
                    if call['args']:
                        tool_sequence += f" with args {call['args']}"
                    tool_sequence += "\n"
    
    return tool_sequence


def generate_result_from_execution(execution_result: Dict[str, Any], plan: str) -> str:
    """
    Generate a result in the specified format based on execution result and plan.
    
    Args:
        execution_result: The execution result from Player Agent
        plan: The original plan
        
    Returns:
        Formatted result string
    """
    # Initialize LLM
    llm = ChatOpenAI(
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model=os.getenv("DASHSCOPE_MODEL", "qwen3-max")
    )
    
    # Extract UI elements information from execution result
    ui_elements_info = extract_ui_elements_info(execution_result)
    
    prompt = f"""
Based on the plan and execution result, generate a result in the following format:

Result
#<actual step 1 content from the plan>
##是否成功 ：OK|Failed
##是否成功的UI元素证明
#<actual step 2 content from the plan>
##是否成功 ：OK|Failed
##是否成功的UI元素证明

For example, if the plan has a step "#打开浏览器应用。通过点击桌面上的浏览器图标启动浏览器应用", 
the result should be:
#打开浏览器应用。通过点击桌面上的浏览器图标启动浏览器应用
##打开浏览器应用。通过点击桌面上的浏览器图标启动浏览器应用是否成功 ：OK|Failed
##打开浏览器应用。通过点击桌面上的浏览器图标启动浏览器应用是否成功的UI元素证明

按照上面 the format,按照计划执行步骤成功的越多，最后的打分越高。

Plan:
{plan}

Execution Result:
{execution_result.get('final_output', 'No output available')}

UI Elements Information:
{ui_elements_info}

Tool Execution Sequence:
{extract_tool_execution_sequence(execution_result)}

Please generate the result in the specified format, replacing the placeholder step names with actual step content from the plan.
"""
    
    response = llm.invoke(prompt)
    return response.content if hasattr(response, 'content') else str(response)


class PlayerAgent:
    """Player Agent responsible for executing tool sequences provided by Coach Agent."""
    
    def __init__(self, agent_bay: AgentBay, session_id: str = None, snapshots_dir: str = None):
        self.id = str(uuid.uuid4())
        self.agent_bay = agent_bay
        self.session_id = session_id
        self.session = None
        self.store = InMemoryStore()
        self.snapshots_dir = snapshots_dir
        
        # Initialize session if session_id provided
        if self.session_id:
            session_result = self.agent_bay.get(self.session_id)
            if session_result.success:
                self.session = session_result.session
                session_data = MobileSessionData(session=self.session, session_id=self.session.session_id)
                self.store.put(("mobile_session",), "default", session_data)
            else:
                raise Exception(f"Failed to get session with ID {self.session_id}: {session_result.error_message}")
        else:
            # Create a new session
            session_params = CreateSessionParams(image_id="mobile_latest")
            result = self.agent_bay.create(session_params)
            if result.success:
                self.session = result.session
                self.session_id = self.session.session_id
                session_data = MobileSessionData(session=self.session, session_id=self.session_id)
                self.store.put(("mobile_session",), "default", session_data)
            else:
                raise Exception(f"Failed to create session: {result.error_message}")
    
    def execute_task(self, task_description: str) -> Dict[str, Any]:
        """
        Execute a task based on natural language description of tool sequences.
        
        Args:
            task_description: Natural language description of tool sequences
            
        Returns:
            Dictionary containing execution results and process information
        """
        # Create the toolkit and tools
        toolkit = MobileIntegrationToolkit()
        tools = toolkit.get_tools()
        
        # Initialize LLM
        llm = ChatOpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model=os.getenv("DASHSCOPE_MODEL", "qwen3-max")
        )
        
        # Load mobile tools documentation
        current_dir = os.path.dirname(os.path.abspath(__file__))
        tools_doc_path = os.path.join(current_dir, "mobile_tools_documentation.md")
        with open(tools_doc_path, "r", encoding="utf-8") as f:
            tools_documentation = f.read()
        
        # Prepare system prompt with snapshots directory information
        system_prompt = f"""You are a helpful assistant that executes precise mobile automation tasks based on natural language descriptions.
            
Available tools documentation:
{tools_documentation}

Follow the given task description precisely. Each step in the description should be executed in order.
Be specific with coordinates when tapping or swiping.
For key events, use these common codes:
- HOME: 3
- BACK: 4
- VOLUME_UP: 24
- VOLUME_DOWN: 25
- POWER: 26
- MENU: 82

When generating tool calls, make sure to provide all required parameters as specified in the documentation.
Each step should correspond to exactly one tool call with appropriate parameters.
"""
        
        # Add snapshots directory information if available
        if self.snapshots_dir:
            system_prompt += f"\nDefault snapshots directory for saving files (screenshots, etc.): {self.snapshots_dir}\n"
            system_prompt += "When using tools that save files (like mobile_screenshot), save them in this directory.\n"
        
        # Create agent using the new LangChain v1.0 method
        agent = create_agent(
            llm,
            tools=tools,
            store=self.store,
            system_prompt=system_prompt
        )
        
        # Execute the agent with the task description
        try:
            result = agent.invoke(
                {"messages": [{"role": "user", "content": task_description}]},
                {"recursion_limit": 200}
            )
            
            # Extract the final output
            final_message = result["messages"][-1] if "messages" in result and len(result["messages"]) > 0 else result
            
            execution_result = {
                "player_id": self.id,
                "success": True,
                "task_description": task_description,
                "final_output": final_message.content if hasattr(final_message, 'content') else str(final_message),
                "full_result": result
            }
        except Exception as e:
            execution_result = {
                "player_id": self.id,
                "success": False,
                "task_description": task_description,
                "error": str(e),
                "full_result": None
            }
        
        return execution_result
    
    def cleanup(self):
        """Clean up the AgentBay session."""
        if self.session and self.agent_bay:
            try:
                self.agent_bay.delete(self.session)
            except:
                pass  # Ignore cleanup errors


class CoachAgent:
    """Coach Agent responsible for training and evolving Player Agents."""
    
    def __init__(self, base_directory: str = "./self_evolving_agent_training", prior_knowledge_path: str = None):
        self.base_directory = Path(base_directory)
        self.base_directory.mkdir(exist_ok=True)
        self.agent_bay = AgentBay()
        self.current_epoch = 0
        self.best_score = 0.0
        self.best_plan = None
        self.best_player_id = None
        self.best_epoch = 0
        self.max_epochs = 10  # Default max epochs
        self.prior_knowledge_path = prior_knowledge_path or str(self.base_directory / "prior_knowledge")
        self.prior_knowledge = []
        self.prior_knowledge_tasks = []  # Store initial tasks separately for similarity matching
        
        # Load prior knowledge if path is provided
        self._load_prior_knowledge()
    
    def _load_prior_knowledge(self):
        """Load prior knowledge from files in the prior knowledge directory."""
        prior_knowledge_dir = Path(self.prior_knowledge_path)
        if not prior_knowledge_dir.exists():
            print(f"Warning: Prior knowledge directory {prior_knowledge_dir} does not exist")
            return
        
        # Iterate through all .json files in the directory
        for file_path in prior_knowledge_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    # Load JSON data
                    knowledge_data = json.load(f)
                    
                    # Extract initial task and best plan
                    initial_task = knowledge_data.get("initial_task")
                    best_plan = knowledge_data.get("best_plan")
                    
                    # Add initial task and best plan to prior knowledge as separate items
                    if initial_task and initial_task not in self.prior_knowledge:
                        self.prior_knowledge.append(initial_task)
                        self.prior_knowledge_tasks.append({
                            "task": initial_task,
                            "file_path": str(file_path)
                        })
                    if best_plan and best_plan not in self.prior_knowledge:
                        self.prior_knowledge.append(best_plan)
            except Exception as e:
                print(f"Warning: Failed to load prior knowledge from {file_path}: {e}")
        
        print(f"Loaded {len(self.prior_knowledge)} prior knowledge items")

    def _compute_text_similarity(self, text1: str, text2: str) -> float:
        """
        Compute a simple text similarity score between two texts using character n-grams.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0 and 1
        """
        def get_ngrams(text, n=2):
            """Generate character n-grams for a text."""
            # Remove spaces and convert to lowercase for better matching
            text = text.replace(" ", "").lower()
            return [text[i:i+n] for i in range(len(text)-n+1)]
        
        # Get n-grams for both texts
        ngrams1 = set(get_ngrams(text1, 2))
        ngrams2 = set(get_ngrams(text2, 2))
        
        # Handle edge case where one or both texts are too short
        if not ngrams1 and not ngrams2:
            return 1.0  # Both empty
        if not ngrams1 or not ngrams2:
            return 0.0  # One empty, one not
        
        # Calculate Jaccard similarity
        intersection = len(ngrams1.intersection(ngrams2))
        union = len(ngrams1.union(ngrams2))
        
        return intersection / union if union > 0 else 0.0

    def _get_most_similar_prior_knowledge(self, task: str, threshold: float = 0.1) -> Optional[Dict[str, str]]:
        """
        Find the most similar prior knowledge task to the given task.
        
        Args:
            task: Current task description
            threshold: Minimum similarity threshold (default: 0.1)
            
        Returns:
            Dictionary containing the most similar prior knowledge task and plan if similarity is above threshold, 
            otherwise None
        """
        if not self.prior_knowledge_tasks:
            return None
        
        best_similarity = 0.0
        best_task = None
        best_plan = None
        
        # Load all prior knowledge data to access both tasks and plans
        prior_knowledge_dir = Path(self.prior_knowledge_path)
        if not prior_knowledge_dir.exists():
            return None
            
        # Iterate through all .json files in the directory
        for file_path in prior_knowledge_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    knowledge_data = json.load(f)
                    initial_task = knowledge_data.get("initial_task")
                    best_plan_data = knowledge_data.get("best_plan")
                    
                    if initial_task:
                        similarity = self._compute_text_similarity(task, initial_task)
                        if similarity > best_similarity:
                            best_similarity = similarity
                            best_task = initial_task
                            best_plan = best_plan_data
            except Exception as e:
                print(f"Warning: Failed to load prior knowledge from {file_path}: {e}")
        
        # Only return the task and plan if similarity is above threshold
        if best_similarity >= threshold:
            print(f"Found similar prior knowledge with similarity {best_similarity:.2f}")
            return {
                "task": best_task,
                "plan": best_plan
            }
        else:
            print(f"No sufficiently similar prior knowledge found (best similarity: {best_similarity:.2f})")
            return None

    def _generate_initial_plan(self, task: str) -> str:
        """
        Generate an initial plan based on the high-level task.
        
        Args:
            task: High-level task description
            
        Returns:
            Natural language description of tool sequences
        """
        # Initialize LLM
        llm = ChatOpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model=os.getenv("DASHSCOPE_MODEL", "qwen3-max")
        )
        
        # Load mobile tools documentation
        current_dir = os.path.dirname(os.path.abspath(__file__))
        tools_doc_path = os.path.join(current_dir, "mobile_tools_documentation.md")
        with open(tools_doc_path, "r", encoding="utf-8") as f:
            tools_documentation = f.read()
        
        # Find the most similar prior knowledge task
        relevant_prior_knowledge = self._get_most_similar_prior_knowledge(task)
        
        # Prepare prior knowledge section if available
        prior_knowledge_section = ""
        if relevant_prior_knowledge:
            prior_knowledge_section = f"\nPrior Knowledge (most similar previous task):\nTask: {relevant_prior_knowledge['task']}\nPlan: {relevant_prior_knowledge['plan']}"
            print(f"prior_knowledge_section:{prior_knowledge_section}")

        prompt = f"""
You are a mobile automation expert. Given a high-level task, break it down into a sequence of mobile operations.
The available tools are documented below:

{tools_documentation}{prior_knowledge_section}

Task: {task}

Provide a plan in the following format:

Plan
#执行步骤1。自然语言的描述
##固定调用工具：获取UI元素，截图
##执行工具1.1 及必要参数
##执行工具1.2 及必要参数
##执行工具1.3 及必要参数
#执行步骤2。自然语言的描述
##固定调用工具：获取UI元素，截图
##执行工具2.1 及必要参数
##执行工具2.2 及必要参数
#结尾步骤
##固定调用工具：获取UI元素，截图


Example format:
Plan
#打开浏览器应用。通过点击桌面上的浏览器图标启动浏览器应用
##固定调用工具：获取UI元素，截图
##mobile_get_ui_elements(timeout_ms=3000)
##mobile_screenshot(filename="/path/to/screenshot.png")
##mobile_tap(x=150, y=320)
##mobile_get_ui_elements(timeout_ms=3000)
#搜索天气信息。在浏览器中输入"杭州天气"并搜索
##固定调用工具：获取UI元素，截图
##mobile_get_ui_elements(timeout_ms=3000)
##mobile_screenshot(filename="/path/to/screenshot.png")
##mobile_input_text(text="杭州天气")
##mobile_get_ui_elements(timeout_ms=3000)
##mobile_tap(x=300, y=400)
##mobile_get_ui_elements(timeout_ms=3000)
##mobile_wait(milliseconds=2000)
##mobile_get_ui_elements(timeout_ms=3000)
##mobile_screenshot(filename="/path/to/screenshot.png")
#结尾步骤
##固定调用工具：获取UI元素，截图
##mobile_get_ui_elements(timeout_ms=3000)
##mobile_screenshot(filename="/path/to/final_screenshot.png")

Important guidelines:
1. Start with "Plan" on its own line
2. Each major step should begin with # followed by a natural language description
3. Each step must start with the fixed perception tools: mobile_get_ui_elements and mobile_screenshot
4. Each tool call should begin with ## followed by the tool name and parameters
5. After each specific tool call (except mobile_get_ui_elements and mobile_screenshot), add a mobile_get_ui_elements call to get the latest UI state
6. Include concrete coordinates for tap and swipe operations
7. Use specific key codes for send_key operations
8. Include appropriate timeouts and wait times
9. Always specify file paths for screenshot operations
10. Make sure all required parameters are provided according to the documentation
11. End with a final perception step "#结尾步骤" that includes mobile_get_ui_elements and mobile_screenshot
"""
        
        response = llm.invoke(prompt)
        return response.content if hasattr(response, 'content') else str(response)
    
    def initialize_training(self, initial_task: str, max_epochs: int = 10):
        """
        Initialize the training process with an initial task.
        
        Args:
            initial_task: High-level task description
            max_epochs: Maximum number of training epochs
        """
        self.max_epochs = max_epochs
        
        # Create epoch_0 directory
        epoch_dir = self.base_directory / "epoch_0"
        epoch_dir.mkdir(exist_ok=True)
        
        # Create snapshots directory for this epoch
        snapshots_dir = epoch_dir / "snapshots"
        snapshots_dir.mkdir(exist_ok=True)
        
        # Generate initial plan
        initial_plan = self._generate_initial_plan(initial_task)
        
        # Save training plan
        training_plan = {
            "epoch": 0,
            "initial_task": initial_task,
            "plan": initial_plan,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(epoch_dir / "training_plan.json", "w", encoding='utf-8') as f:
            json.dump(training_plan, f, indent=2, ensure_ascii=False, default=json_serializer)
        
        return initial_plan
    
    def train(self, initial_task: str, max_epochs: int = 10) -> Dict[str, Any]:
        """
        Train the self-evolving agent system.
        
        Args:
            initial_task: High-level task description
            max_epochs: Maximum number of training epochs
            
        Returns:
            Final training results
        """
        # Initialize training
        current_plan = self.initialize_training(initial_task, max_epochs)
        
        # Training loop
        for epoch in range(max_epochs):
            print(f"======= STARTING EPOCH {epoch} =======")  # 显示epoch开始
            
            # Print the current plan at the beginning of each iteration
            print(f"Current Plan for Epoch {epoch}:")
            print(current_plan)
            print("=" * 50)
            
            self.current_epoch = epoch
            epoch_dir = self.base_directory / f"epoch_{epoch}"
            
            # Create snapshots directory for this epoch
            snapshots_dir = epoch_dir / "snapshots"
            snapshots_dir.mkdir(exist_ok=True)
            
            # Create player agent for this epoch with snapshots directory
            player_agent = PlayerAgent(self.agent_bay, snapshots_dir=str(snapshots_dir))
            
            try:
                # Execute task with current plan
                execution_result = player_agent.execute_task(current_plan)
                
                # Save execution result
                with open(epoch_dir / "execution_result.json", "w", encoding='utf-8') as f:
                    json.dump(execution_result, f, indent=2, ensure_ascii=False, default=json_serializer)
                
                # Generate result in the specified format
                result_format = generate_result_from_execution(execution_result, current_plan)
                
                # Save the formatted result
                with open(epoch_dir / "result_format.txt", "w", encoding='utf-8') as f:
                    f.write(result_format)
                
                # Print the result analysis
                print(f"Result Analysis for Epoch {epoch}:")
                print(result_format)
                print("=" * 50)
                
                # Evaluate the result
                score, feedback = self._evaluate_result(execution_result, initial_task)
                
                # Save training result
                training_result = {
                    "epoch": epoch,
                    "initial_task": initial_task,
                    "plan": current_plan,
                    "execution_result": execution_result,
                    "result_format": result_format,
                    "score": score,
                    "feedback": feedback,
                    "player_id": player_agent.id,
                    "timestamp": datetime.now().isoformat()
                }
                
                with open(epoch_dir / "training_result.txt", "w", encoding='utf-8') as f:
                    f.write(json.dumps(training_result, indent=2, ensure_ascii=False, default=json_serializer))
                
                # Update best result if needed
                if score > self.best_score:
                    self.best_score = score
                    self.best_plan = current_plan
                    self.best_player_id = player_agent.id
                    self.best_epoch = epoch
                
                # Check if task is completed
                task_completed = self._is_task_completed(execution_result, initial_task, feedback)
                
                # Check if training should continue
                should_continue = self._should_continue_training(score, epoch, feedback, task_completed)
                
                print(f"======= FINISHED EPOCH {epoch} (Score: {score}, Completed: {task_completed}) =======")  # 显示epoch结束
                
                if not should_continue or epoch == max_epochs - 1:
                    # Training finished
                    break
                
                # Evolve the plan for next iteration
                current_plan = self._evolve_plan(current_plan, execution_result, feedback)
                
                # Create next epoch directory and save the new plan
                next_epoch_dir = self.base_directory / f"epoch_{epoch + 1}"
                next_epoch_dir.mkdir(exist_ok=True)
                
                # Create snapshots directory for next epoch
                next_snapshots_dir = next_epoch_dir / "snapshots"
                next_snapshots_dir.mkdir(exist_ok=True)
                
                next_training_plan = {
                    "epoch": epoch + 1,
                    "initial_task": initial_task,
                    "plan": current_plan,
                    "previous_score": score,
                    "feedback": feedback,
                    "timestamp": datetime.now().isoformat()
                }
                
                with open(next_epoch_dir / "training_plan.json", "w", encoding='utf-8') as f:
                    json.dump(next_training_plan, f, indent=2, ensure_ascii=False, default=json_serializer)
                    
            finally:
                # Clean up player agent
                player_agent.cleanup()
        
        # Save final training result
        final_result = {
            "total_epochs": self.current_epoch + 1,
            "best_epoch": self.best_epoch,
            "best_score": self.best_score,
            "best_plan": self.best_plan,
            "best_player_id": self.best_player_id,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(self.base_directory / "final_training_result.txt", "w", encoding='utf-8') as f:
            f.write(json.dumps(final_result, indent=2, ensure_ascii=False, default=json_serializer))
        
        # Extract and save prior knowledge
        # Extract prior knowledge from the best result
        best_epoch_dir = self.base_directory / f"epoch_{self.best_epoch}"
        best_training_result_path = best_epoch_dir / "training_result.txt"
        
        if best_training_result_path.exists():
            try:
                with open(best_training_result_path, "r", encoding='utf-8') as f:
                    best_training_result = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to save prior knowledge: {e}")
                
        save_prior_knowledge(self.prior_knowledge_path, initial_task, self.best_plan)
        return final_result
    
    def _evaluate_result(self, execution_result: Dict[str, Any], initial_task: str) -> tuple:
        """
        Evaluate the execution result and provide a score and feedback.
        
        Args:
            execution_result: Result from Player Agent execution
            initial_task: Original high-level task
            
        Returns:
            Tuple of (score, feedback)
        """
        # Initialize LLM for evaluation
        llm = ChatOpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model=os.getenv("DASHSCOPE_MODEL", "qwen3-max")
        )
        
        prompt = f"""
You are evaluating the performance of a mobile automation agent. 

Original Task: {initial_task}
Execution Result: {execution_result.get('final_output', 'No output available')}

Please provide:
1. A score between 0 and 1, where:
   - 0 = completely failed
   - 1 = perfectly executed
2. Feedback on what went well and what could be improved

Calculate the score based on:
- How many steps in the plan were successfully executed
- Whether the final goal was achieved
- Quality of the UI element evidence provided

Format your response as JSON:
{{
  "score": 0.0-1.0,
  "feedback": "Detailed feedback"
}}
"""
        
        try:
            response = llm.invoke(prompt)
            evaluation = json.loads(response.content if hasattr(response, 'content') else str(response))
            return evaluation["score"], evaluation["feedback"]
        except Exception as e:
            # Fallback evaluation
            return 0.1, f"Evaluation failed: {str(e)}. Assuming poor performance."
    
    def _is_task_completed(self, execution_result: Dict[str, Any], initial_task: str, feedback: str) -> bool:
        """
        Determine whether the task has been successfully completed based on execution results and feedback.
        
        Args:
            execution_result: Result from Player Agent execution
            initial_task: Original high-level task
            feedback: Evaluation feedback
            
        Returns:
            Boolean indicating whether the task has been completed
        """
        # Initialize LLM for task completion determination
        llm = ChatOpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model=os.getenv("DASHSCOPE_MODEL", "qwen3-max")
        )
        
        # Check for objective evidence of completion, such as file existence
        final_output = execution_result.get('final_output', 'No output available')
        
        # Look for UI elements information in the execution result
        ui_elements_info = extract_ui_elements_info(execution_result)
        
        # Look for file paths in the output that should exist if the task was completed
        import re
        file_paths = re.findall(r'[./\w]*\.(?:png|jpg|jpeg|gif|bmp|svg|webp|txt|csv|json)', final_output)
        
        # Check if mentioned files actually exist
        files_exist = []
        for file_path in file_paths:
            if os.path.exists(file_path):
                files_exist.append(file_path)
        
        file_verification_info = ""
        if file_paths:
            file_verification_info = f"\nReferenced files: {file_paths}\nActually existing files: {files_exist}\nFile verification: {'PASS' if len(files_exist) == len(file_paths) else 'FAIL'}"
        
        prompt = f"""
You are determining whether a mobile automation task has been successfully completed.

Initial Task: {initial_task}
Execution Result: {final_output}
UI Elements Information: {ui_elements_info}
Feedback: {feedback}
File Verification: {file_verification_info}

Based on the execution result, UI elements information, and feedback, determine if the initial task has been successfully completed.
A task should only be considered completed if there is explicit evidence that the desired outcome was achieved,
not just that the steps were executed. Pay attention to objective verification like:
1. Do the UI elements show concrete evidence of task completion? 
   For example, if looking for stock prices, are there UI elements showing stock price information?
   If searching for information, are there UI elements displaying the search results?
2. If specific information was requested, is it clearly present in the output?

Answer with a JSON object:
{{
  "completed": true/false,
  "reasoning": "Explanation of why the task is considered completed or not, taking into account objective evidence like UI elements information"
}}
"""
        
        try:
            response = llm.invoke(prompt)
            result = json.loads(response.content if hasattr(response, 'content') else str(response))
            return result["completed"]
        except Exception as e:
            # If we can't determine, assume task is not completed
            return False

    def _should_continue_training(self, score: float, epoch: int, feedback: str, task_completed: bool = False) -> bool:
        """
        Determine whether training should continue.
        
        Args:
            score: Current evaluation score
            epoch: Current epoch number
            feedback: Evaluation feedback
            task_completed: Boolean indicating whether the task has been successfully completed
            
        Returns:
            Boolean indicating whether to continue training
        """
        # Continue if task is not completed and we haven't reached max epochs
        return not task_completed and epoch < self.max_epochs - 1
    
    def _evolve_plan(self, current_plan: str, execution_result: Dict[str, Any], feedback: str) -> str:
        """
        Evolve the plan based on execution results and feedback.
        
        Args:
            current_plan: Current plan
            execution_result: Execution results
            feedback: Evaluation feedback
            
        Returns:
            Evolved plan
        """
        # Initialize LLM for plan evolution
        llm = ChatOpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model=os.getenv("DASHSCOPE_MODEL", "qwen3-max")
        )
        
        # Extract UI elements information from current execution result
        current_ui_elements_info = extract_ui_elements_info(execution_result)
        
        # Get information about the best performing epoch so far
        best_epoch_info = "No previous best epoch information available"
        if self.best_plan and self.best_score > 0:
            best_epoch_info = f"""
Best performing plan (Score: {self.best_score}):
{self.best_plan}
"""
        
        # Get simplified tool execution sequence
        tool_sequence = extract_tool_execution_sequence(execution_result)
        
        # Load mobile tools documentation
        current_dir = os.path.dirname(os.path.abspath(__file__))
        tools_doc_path = os.path.join(current_dir, "mobile_tools_documentation.md")
        with open(tools_doc_path, "r", encoding="utf-8") as f:
            tools_documentation = f.read()
        
        # Find the most similar prior knowledge task
        # We don't have access to the original task here, so we'll use all prior knowledge
        prior_knowledge_section = ""
        if self.prior_knowledge:
            prior_knowledge_section = "\nPrior Knowledge (useful information from previous tasks):\n" + "\n".join(f"- {pk}" for pk in self.prior_knowledge)
        
        prompt = f"""
You are improving a mobile automation plan based on execution results and feedback.

Current Plan:
{current_plan}

Execution Result:
{execution_result.get('final_output', 'No output available')}

Current UI Elements Information:
{current_ui_elements_info}

Tool Execution Sequence:
{tool_sequence}

Feedback:
{feedback}

Best Performing Epoch Information:
{best_epoch_info}

Available tools documentation:
{tools_documentation}{prior_knowledge_section}

Please improve the plan to better achieve the intended task using the following format:

Plan
#执行步骤1。自然语言的描述
##固定调用工具：获取UI元素，截图
##执行工具1.1 及必要参数
##执行工具1.2 及必要参数
##执行工具1.3 及必要参数
#执行步骤2。自然语言的描述
##固定调用工具：获取UI元素，截图
##执行工具2.1 及必要参数
##执行工具2.2 及必要参数
#结尾步骤
##固定调用工具：获取UI元素，截图

Example format:
Plan
#打开浏览器应用。通过点击桌面上的浏览器图标启动浏览器应用
##固定调用工具：获取UI元素，截图
##mobile_get_ui_elements(timeout_ms=3000)
##mobile_screenshot(filename="/path/to/screenshot.png")
##mobile_tap(x=150, y=320)
##mobile_get_ui_elements(timeout_ms=3000)
#搜索天气信息。在浏览器中输入"杭州天气"并搜索
##固定调用工具：获取UI元素，截图
##mobile_get_ui_elements(timeout_ms=3000)
##mobile_screenshot(filename="/path/to/screenshot.png")
##mobile_input_text(text="杭州天气")
##mobile_get_ui_elements(timeout_ms=3000)
##mobile_tap(x=300, y=400)
##mobile_get_ui_elements(timeout_ms=3000)
##mobile_wait(milliseconds=2000)
##mobile_get_ui_elements(timeout_ms=3000)
##mobile_screenshot(filename="/path/to/screenshot.png")
#结尾步骤
##固定调用工具：获取UI元素，截图
##mobile_get_ui_elements(timeout_ms=3000)
##mobile_screenshot(filename="/path/to/final_screenshot.png")

Important guidelines:
1. Start with "Plan" on its own line
2. Each major step should begin with # followed by a natural language description
3. Each step must start with the fixed perception tools: mobile_get_ui_elements and mobile_screenshot
4. Each tool call should begin with ## followed by the tool name and parameters
5. Focus on the actual UI elements and tool execution results rather than just the descriptive output
6. Learn from the best performing epoch if it provides valuable insights
7. Avoid unnecessary repetition and 冗余 steps that don't contribute to task completion
8. Prune steps that have been identified as unhelpful or redundant in previous iterations
9. Do not simply expand the plan - focus on making it more efficient and effective
10. If the current plan is already working well, you may choose to keep it with minor adjustments
11. Include concrete coordinates for tap and swipe operations
12. Use specific key codes for send_key operations
13. Include appropriate timeouts and wait times
14. Always specify file paths for screenshot operations
15. Make sure all required parameters are provided according to the documentation
16. After each specific tool call (except mobile_get_ui_elements and mobile_screenshot), add a mobile_get_ui_elements call to get the latest UI state
17. End with a final perception step "#结尾步骤" that includes mobile_get_ui_elements and mobile_screenshot

Provide the improved plan in the specified format.
"""
        
        response = llm.invoke(prompt)
        return response.content if hasattr(response, 'content') else str(response)


def extract_prior_knowledge_from_training(training_result: Dict[str, Any], plan: str, initial_task: str = None) -> List[str]:
    """
    Extract prior knowledge from training results that can be reused in future tasks.
    
    Args:
        training_result: The training result from Coach Agent
        plan: The final plan
        initial_task: The initial task description
        
    Returns:
        Empty list (knowledge extraction is no longer performed)
    """
    # Knowledge extraction is no longer performed as per requirements
    return []


def save_prior_knowledge(prior_knowledge_path: str, initial_task: str = None, best_plan: str = None):
    """
    Save initial task and best plan to a file in the prior_knowledge directory.
    
    Args:
        prior_knowledge_path: Path to the prior knowledge directory
        initial_task: The initial task description
        best_plan: The best plan that achieved the highest score
    """
    # Create prior_knowledge directory
    prior_knowledge_dir = Path(prior_knowledge_path)
    prior_knowledge_dir.mkdir(exist_ok=True)
    
    # Generate filename with timestamp and random string
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    import random
    import string
    random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    filename = f"pk-{timestamp}-{random_string}.json"  # Changed to .json extension
    
    file_path = prior_knowledge_dir / filename
    
    try:
        # Create a dictionary with task and plan
        knowledge_data = {
            "initial_task": initial_task,
            "best_plan": best_plan
        }
        
        # Save as JSON
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(knowledge_data, f, indent=2, ensure_ascii=False)
        print(f"Saved initial task and best plan to {file_path}")
    except Exception as e:
        print(f"Warning: Failed to save prior knowledge to {file_path}: {e}")
