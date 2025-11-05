"""
Digital Twin Core Logic

The main Digital Twin class that represents the user's AI self.
This is the first-class citizen that owns all interactions.
"""

from typing import Dict, List, Optional
from datetime import datetime
import os
from pathlib import Path

try:
    from openai import OpenAI
except ImportError as e:
    print(f"⚠️ Failed to import OpenAI: {e}")
    OpenAI = None

try:
    # Try absolute imports first (works in app loader context)
    from dt_identity import DTIdentity
    from dt_state import DTState, build_conversation_context, generate_dt_system_prompt
    from execution_node import ExecutionNode
except ImportError:
    # Fall back to relative imports (for package imports)
    from .dt_identity import DTIdentity
    from .dt_state import DTState, build_conversation_context, generate_dt_system_prompt
    from .execution_node import ExecutionNode


class DigitalTwin:
    """
    The Digital Twin - User's AI representation and first-class citizen.
    
    The DT is NOT an assistant. It IS the user in digital form.
    It owns all interactions and has full authority to act on behalf of the user.
    """
    
    def __init__(self, identity: DTIdentity):
        self.identity = identity
        self.state = DTState(identity.user_id)
        
        # Initialize LLM client
        if OpenAI is None:
            raise ImportError("OpenAI package is not available. Please install with: pip install openai")
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.llm_client = OpenAI(api_key=api_key)
        self.model = os.getenv("LLM_MODEL", "gpt-4")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "6000"))
        
        # DT configuration
        self.dt_mode = os.getenv("DT_MODE", "autonomous")  # autonomous, assisted, manual
        
        # Initialize Execution Node
        apps_dir = Path(__file__).parent.parent.parent  # /apps directory
        self.execution_node = ExecutionNode(
            apps_dir=apps_dir,
            user_id=identity.user_id,
            jwt_token=identity.jwt_token,
            base_url=os.getenv("EXECUTION_NODE_URL", "http://localhost:8000")
        )
        self.tools_discovered = False
    
    async def discover_tools(self) -> Dict:
        
        # Get tools summary
        tools_summary = ""
        if self.tools_discovered and len(self.execution_node.tools) > 0:
            caps = self.execution_node.get_capabilities_summary()
            tools_summary = f"""
⚡ YOUR TOOLS:
- Total Apps: {caps['total_apps']}
- Total Tools: {caps['total_tools']}
- Autonomous (use freely): {caps['tools_by_autonomy']['full']}
- Ask first: {caps['tools_by_autonomy']['ask']}
- Restricted: {caps['tools_by_autonomy']['restricted']}

Available Apps:
{chr(10).join(f"  • {app['name']}: {app['tools']} tools" for app in caps['apps'])}
"""
        else:
            tools_summary = "- Tool discovery in progress..."
        
        # Get tools summary - group by app
        apps_dict = {}
        for tool_name, tool in self.execution_node.tools.items():
            app = tool.app_name
            if app not in apps_dict:
                apps_dict[app] = []
            apps_dict[app].append(tool_name)
        
        apps_list = [f"{app} ({len(tools)} tools)" for app, tools in apps_dict.items()]
        tools_summary = f"Available NOW: {', '.join(apps_list)}" if apps_list else "Discovering apps..."
        
        prompt = f"""You are {user_name}'s digital twin.

CURRENT STATE (use this, ignore old data):
{tools_summary}

CRITICAL RULES:
- Only these apps exist: {', '.join(apps_dict.keys()) if apps_dict else 'none yet'}
- If user asks about apps not in the list: say "That app isn't installed"
- Do NOT pretend to fetch data from non-existent apps
- Do NOT say "I'll fetch" unless you actually have the tool
- Be honest: "I don't have that app" instead of making things up"""
        return prompt
    
    async def discover_tools(self) -> Dict:
        """
        Discover all available tools on the execution node.
        This should be called when the DT is initialized.
        """
        discovery_result = await self.execution_node.discover_all()
        self.tools_discovered = True
        
        print(f"🤖 DT discovered {discovery_result['total_tools']} tools from {discovery_result['apps']} apps")
        return discovery_result
    
    async def think(
        self,
        user_input: str,
        context: Optional[Dict] = None,
        history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Main thinking/reasoning method.
        The DT processes input and decides what to do.
        
        Args:
            user_input: The user's message or request
            context: Additional context (conversation_id, intent, etc.)
            history: Conversation history
            
        Returns:
            Dict with thought_process, decision, action, response, etc.
        """
        context = context or {}
        history = history or []
        
        # Add user message to state
        self.state.add_conversation_message("user", user_input, metadata=context)
        
        # Build messages for LLM using enhanced context management
        system_prompt = generate_dt_system_prompt(
            user_id=self.identity.user_id,
            user_name=self.identity.user_profile.get("name", self.identity.username),
            dt_state=self.state,
            available_tools=[tool.to_dict() for tool in self.execution_node.tools.values()]
        )
        
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add conversation context from state
        conversation_context = self.state.get_conversation_history(max_messages=15, max_tokens=5000)
        # Skip the last message (we just added it)
        messages.extend(conversation_context[:-1])
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        # Prepare tools for function calling
        tools = []
        if self.tools_discovered and len(self.execution_node.tools) > 0:
            tools = [tool.to_openai_function() for tool in self.execution_node.tools.values()]
        
        try:
            # Call LLM with tools (DT's "brain")
            llm_params = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
            
            # Add tools if available
            if tools:
                llm_params["tools"] = tools
                llm_params["tool_choice"] = "auto"
            
            response = self.llm_client.chat.completions.create(**llm_params)
            
            # Check if tool calls were made
            message = response.choices[0].message
            
            if message.tool_calls:
                # DT wants to use tools
                tool_results = []
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    import json
                    tool_params = json.loads(tool_call.function.arguments)
                    
                    # Execute tool
                    result = await self.execution_node.execute_as_user(
                        tool_name=tool_name,
                        parameters=tool_params,
                        autonomous=True
                    )
                    tool_results.append({
                        "tool": tool_name,
                        "params": tool_params,
                        "result": result
                    })
                
                # Get final response with tool results
                messages.append(message)
                messages.append({
                    "role": "tool",
                    "tool_call_id": message.tool_calls[0].id,
                    "content": str(tool_results[0]["result"])
                })
                
                final_response = self.llm_client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                
                dt_response = final_response.choices[0].message.content
                
                # Add to state
                self.state.add_conversation_message("assistant", dt_response, metadata={
                    "tools_used": [t["tool"] for t in tool_results]
                })
                
                self.state.save()
                
                return {
                    "thought_process": f"Used tools: {', '.join([t['tool'] for t in tool_results])}",
                    "decision": "execute_tools",
                    "tools_used": tool_results,
                    "response": dt_response,
                    "dt_confidence": 0.9,
                    "model": self.model
                }
            else:
                # No tools used, just respond
                dt_response = message.content
            
            # Add DT response to state
            self.state.add_conversation_message("assistant", dt_response)
            
            # Learn from this interaction
            self.state.learn_from_interaction(
                user_message=user_input,
                dt_response=dt_response,
                tools_used=[],  # Will be updated if tools are called
                autonomous=False
            )
            
            # Save state
            self.state.save()
            
            return {
                "thought_process": "Processed user input and generated response",
                "decision": "respond",
                "action": None,
                "response": dt_response,
                "dt_confidence": 0.9,
                "model": self.model,
                "tokens_used": response.usage.total_tokens
            }
            
        except Exception as e:
            print(f"❌ DT thinking error: {e}")
            return {
                "thought_process": f"Error occurred: {e}",
                "decision": "error",
                "action": None,
                "response": f"I encountered an error while processing that. Error: {str(e)}",
                "dt_confidence": 0.0,
                "error": str(e)
            }
    
    async def act(
        self,
        action: str,
        tool: Optional[str] = None,
        parameters: Optional[Dict] = None
    ) -> Dict:
        """
        Execute an action autonomously.
        Uses the execution node to execute tools.
        
        Args:
            action: Type of action to execute
            tool: Tool name to use
            parameters: Parameters for the action
            
        Returns:
            Dict with success status and result
        """
        if action == "execute_tool" and tool:
            # Execute tool using execution node
            result = await self.execution_node.execute_as_user(
                tool_name=tool,
                parameters=parameters or {},
                autonomous=True
            )
            
            # Update state
            if result.get("success"):
                self.state.increment_action_count(autonomous=True)
                self.state.state["stats"]["tools_used"][tool] = \
                    self.state.state["stats"]["tools_used"].get(tool, 0) + 1
                self.state.save()
            
            return result
        
        # Default action execution
        self.state.increment_action_count(autonomous=True)
        self.state.save()
        
        return {
            "success": True,
            "action": action,
            "tool": tool,
            "parameters": parameters,
            "result": "Action executed",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_capabilities(self) -> Dict:
        """
        List what the DT can currently do.
        Includes discovered tools from execution node.
        """
        tools_list = []
        if self.tools_discovered:
            tools_list = [tool.to_dict() for tool in self.execution_node.tools.values()]
        
        return {
            "dt_version": "1.0.0",
            "user_id": self.identity.user_id,
            "dt_id": self.identity.dt_id,
            "capabilities": {
                "thinking": True,
                "conversation": True,
                "memory": True,
                "learning": True,
                "tools": tools_list,
                "execution_node": {
                    "accessible": True,
                    "resources": ["apps", "filesystem", "network"],
                    "apps_discovered": len(self.execution_node.apps_discovered),
                    "total_tools": len(self.execution_node.tools)
                },
                "autonomous_actions": self.dt_mode == "autonomous"
            },
            "mode": self.dt_mode,
            "model": self.model
        }
    
    def get_state(self) -> Dict:
        """Get current DT state"""
        return {
            "dt_id": self.identity.dt_id,
            "user_id": self.identity.user_id,
            "dt_active": True,
            "current_context": self.state.get_user_context(),
            "memory": {
                "recent_conversations": len(self.state.state["memory"]["conversations"]),
                "learned_preferences": self.state.state["memory"]["learned_preferences"]
            },
            "capabilities": self.get_capabilities()
        }
    
    def __repr__(self) -> str:
        return f"DigitalTwin(user={self.identity.username}, mode={self.dt_mode})"
