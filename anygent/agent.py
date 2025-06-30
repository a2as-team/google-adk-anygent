import logging
import json
from typing import AsyncGenerator, Dict, Any, Optional
from typing_extensions import override

from google.adk.agents import (
    LlmAgent,
    LoopAgent,
    BaseAgent,
)
from google.adk.agents.invocation_context import InvocationContext
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from google.adk.events import Event

# --- Configure Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Constants ---
APP_NAME = "morphing_agent_app_v1"
USER_ID = "dev_user_01"
SESSION_ID = "morphing_agent_session"
GEMINI_MODEL = "gemini-2.0-flash"

# --- State Keys ---
STATE_USER_SPECIALIZATION = "user_specialization"
STATE_MORPHED_AGENT_DESCRIPTION = "morphed_agent_description"
STATE_USER_QUERY = "user_query"
STATE_AGENT_RESPONSE = "agent_response"
STATE_USER_MORPH_CONFIRMED = "user_morph_confirmed"
STATE_AGENT_HISTORY = "agent_history"
STATE_CURRENT_ROLE = "current_role"
STATE_MORPH_COUNT = "morph_count"
STATE_USER_PREFERENCES = "user_preferences"

# --- Enhanced Tool Definitions ---

def call_external_api(tool_context: ToolContext):
    """
    Enhanced tool for searching or calling external APIs to gather info for morphing.
    """
    query = tool_context.state.get("morphing_search_query", "")
    logger.info(f"[Tool Call] call_external_api with query: {query} | Agent: {tool_context.agent_name} | Invocation: {tool_context.invocation_id}")
    
    # Simulate different types of API responses based on query
    if "weather" in query.lower():
        return {"search_result": f"Weather data for '{query}': Sunny, 72°F, Humidity: 45%"}
    elif "news" in query.lower():
        return {"search_result": f"Latest news for '{query}': Breaking developments in technology and AI"}
    elif "code" in query.lower() or "programming" in query.lower():
        return {"search_result": f"Programming resources for '{query}': Best practices, tutorials, and documentation"}
    else:
        return {"search_result": f"Comprehensive information about '{query}' from various sources"}

def save_agent_state(tool_context: ToolContext):
    """
    Tool to save the current agent state for persistence.
    """
    current_state = {
        "role": tool_context.state.get(STATE_CURRENT_ROLE, ""),
        "specialization": tool_context.state.get(STATE_USER_SPECIALIZATION, ""),
        "morph_count": tool_context.state.get(STATE_MORPH_COUNT, 0),
        "timestamp": str(tool_context.invocation_id)
    }
    
    logger.info(f"[Tool Call] save_agent_state: {current_state}")
    tool_context.state[STATE_AGENT_HISTORY] = tool_context.state.get(STATE_AGENT_HISTORY, []) + [current_state]
    return {"saved": True, "state": current_state}

def reset_agent(tool_context: ToolContext):
    """
    Enhanced tool to reset the agent to its base state for new morphing.
    """
    logger.info(f"[Tool Call] reset_agent triggered by {tool_context.agent_name}")
    
    # Clear morphing-related state but keep history
    tool_context.state[STATE_MORPHED_AGENT_DESCRIPTION] = ""
    tool_context.state[STATE_USER_MORPH_CONFIRMED] = ""
    tool_context.state[STATE_CURRENT_ROLE] = "base_agent"
    tool_context.state["reset_requested"] = True
    tool_context.state["conversation_phase"] = "specialization"
    
    return {"reset": True, "message": "Agent reset to base state"}

def exit_with_thanks(tool_context: ToolContext):
    """
    Enhanced tool to trigger exit with personalized thank you.
    """
    morph_count = tool_context.state.get(STATE_MORPH_COUNT, 0)
    current_role = tool_context.state.get(STATE_CURRENT_ROLE, "agent")
    
    logger.info(f"[Tool Call] exit_with_thanks triggered by {tool_context.agent_name} | Role: {current_role} | Morphs: {morph_count}")
    
    # Save final state before exit
    save_agent_state(tool_context)
    tool_context.state["exit_requested"] = True
    tool_context.state["conversation_phase"] = "exit"
    tool_context.actions.escalate = True
    
    return {
        "exit": True, 
        "morph_count": morph_count,
        "final_role": current_role
    }

def get_agent_capabilities(tool_context: ToolContext):
    """
    Tool to describe current agent capabilities.
    """
    current_role = tool_context.state.get(STATE_CURRENT_ROLE, "base_agent")
    morph_count = tool_context.state.get(STATE_MORPH_COUNT, 0)
    
    capabilities = {
        "current_role": current_role,
        "morph_count": morph_count,
        "can_morph": True,
        "can_reset": True,
        "can_exit": True,
        "available_tools": ["call_external_api", "save_agent_state", "reset_agent", "exit_with_thanks"]
    }
    
    return capabilities

# --- Enhanced LLM Sub-Agents ---

welcome_agent = LlmAgent(
    name="WelcomeAgent",
    model=GEMINI_MODEL,
    include_contents='none',
    instruction=(
        "You are a friendly AI assistant that can morph into any specialized agent the user desires.\n"
        "Welcome the user warmly and briefly explain that you can become any type of agent they want.\n"
        "If the user has already provided their desired specialization, acknowledge it.\n"
        "Output any specialization the user provides as 'user_specialization'."
    ),
    description="Welcomes user and explains morphing capabilities.",
    output_key=STATE_USER_SPECIALIZATION
)

initial_specialization_agent = LlmAgent(
    name="SpecializationPromptAgent",
    model=GEMINI_MODEL,
    include_contents='none',
    instruction=(
        "You are an agent that helps users define what kind of specialized agent they want you to become.\n"
        "If the user has already provided a specialization, use that.\n"
        "Otherwise, ask: \"What kind of specialized agent would you like me to become?\"\n"
        "Extract the user's desired specialization and output it as 'user_specialization'."
    ),
    description="Prompts the user to define the desired specialization for the agent.",
    output_key=STATE_USER_SPECIALIZATION
)

morph_confirmation_agent = LlmAgent(
    name="MorphConfirmationAgent",
    model=GEMINI_MODEL,
    include_contents='none',
    instruction=(
        "You have received the user's desired specialization: \"{user_specialization}\".\n"
        "Ask the user: \"Would you like me to morph into this specialized agent now? (yes/no)\"\n"
        "If the user says 'yes', output 'true' as 'user_morph_confirmed'.\n"
        "If the user says 'no', output 'false' as 'user_morph_confirmed'."
    ),
    description="Asks the user if they want to proceed with morphing.",
    output_key=STATE_USER_MORPH_CONFIRMED
)

morphing_agent = LlmAgent(
    name="MorphingAgent",
    model=GEMINI_MODEL,
    include_contents='none',
    instruction=(
        "You are a morphing agent. Your goal is to transform yourself into the specialized agent the user described:\n"
        "\"{user_specialization}\"\n\n"
        "If you need more information or knowledge to become this agent, describe what you need to search for and call the 'call_external_api' tool with your search query in 'morphing_search_query'.\n\n"
        "If you have enough information, output a comprehensive description of your new specialized agent persona, including:\n"
        "- Role and expertise\n"
        "- Personality traits\n"
        "- Communication style\n"
        "- Key capabilities\n"
        "- How to interact with users\n\n"
        "Output this as 'morphed_agent_description'. Do not output anything else.\n\n"
        "Repeat until you have fully defined your new specialized agent persona."
    ),
    description="Morphs into the specialized agent by searching and iterating as needed.",
    tools=[call_external_api, save_agent_state],
    output_key=STATE_MORPHED_AGENT_DESCRIPTION
)

morphing_loop = LoopAgent(
    name="MorphingLoop",
    sub_agents=[morphing_agent],
    max_iterations=5
)

specialized_agent = LlmAgent(
    name="SpecializedAgent",
    model=GEMINI_MODEL,
    include_contents='none',
    instruction=(
        "You are now acting as the following specialized agent:\n"
        "\"{morphed_agent_description}\"\n\n"
        "IMPORTANT: Stay in character as this specialized agent at all times.\n\n"
        "When the user asks a question or gives a task, respond as the specialized agent would.\n\n"
        "Special commands:\n"
        "- If the user says 'reset' or 'morph again', call the 'reset_agent' tool\n"
        "- If the user says 'exit' or 'goodbye', call the 'exit_with_thanks' tool\n"
        "- If the user asks about your capabilities, call the 'get_agent_capabilities' tool\n\n"
        "IMPORTANT: Only call these tools when the user explicitly requests them.\n"
        "Otherwise, respond naturally as your specialized agent persona.\n\n"
        "Output your response as 'agent_response'."
    ),
    description="Handles user queries as the newly morphed specialized agent.",
    tools=[exit_with_thanks, reset_agent, get_agent_capabilities, call_external_api],
    output_key=STATE_AGENT_RESPONSE
)

specialized_agent_loop = LoopAgent(
    name="SpecializedAgentLoop",
    sub_agents=[specialized_agent],
    max_iterations=20  # Increased for longer conversations
)

thank_you_agent = LlmAgent(
    name="ThankYouAgent",
    model=GEMINI_MODEL,
    include_contents='none',
    instruction=(
        "Generate a personalized thank you message based on the session:\n"
        "- Mention the number of times the agent morphed\n"
        "- Reference the final role the agent was in\n"
        "- Express gratitude for using the morphing agent\n"
        "- Say goodbye warmly\n\n"
        "Output your thank you message."
    ),
    description="Says personalized thank you and exits.",
    output_key=None
)

# --- Enhanced Custom Orchestrator Agent ---

class MorphingOrchestratorAgent(BaseAgent):
    """
    Enhanced custom agent for morphing into user-defined specialized agents with better state management.
    """

    # --- Field Declarations for Pydantic ---
    welcome_agent: LlmAgent
    initial_specialization_agent: LlmAgent
    morph_confirmation_agent: LlmAgent
    morphing_loop: LoopAgent
    specialized_agent_loop: LoopAgent
    thank_agent: LlmAgent

    model_config = {"arbitrary_types_allowed": True}

    def __init__(
        self,
        name: str,
        welcome_agent: LlmAgent,
        initial_specialization_agent: LlmAgent,
        morph_confirmation_agent: LlmAgent,
        morphing_loop: LoopAgent,
        specialized_agent_loop: LoopAgent,
        thank_agent: LlmAgent,
    ):
        sub_agents_list = [
            welcome_agent,
            initial_specialization_agent,
            morph_confirmation_agent,
            morphing_loop,
            specialized_agent_loop,
            thank_agent,
        ]
        super().__init__(
            name=name,
            welcome_agent=welcome_agent,
            initial_specialization_agent=initial_specialization_agent,
            morph_confirmation_agent=morph_confirmation_agent,
            morphing_loop=morphing_loop,
            specialized_agent_loop=specialized_agent_loop,
            thank_agent=thank_agent,
            sub_agents=sub_agents_list,
        )

    @staticmethod
    def user_specialization_not_defined(state):
        """Returns True if the user specialization is not yet defined in state."""
        val = state.get(STATE_USER_SPECIALIZATION)
        return not val or (isinstance(val, str) and val.strip() == "")

    @staticmethod
    def user_morph_not_confirmed(state):
        """Returns True if the user has not confirmed morphing."""
        val = state.get(STATE_USER_MORPH_CONFIRMED)
        if isinstance(val, str):
            return val.strip().lower() != "true"
        return not val

    @staticmethod
    def morphed_agent_not_defined(state):
        """Returns True if the morphed agent description is not yet defined in state."""
        val = state.get(STATE_MORPHED_AGENT_DESCRIPTION)
        return not val or (isinstance(val, str) and val.strip() == "")

    @staticmethod
    def should_welcome_user(state):
        """Returns True if this is the first interaction (no history)."""
        return not state.get(STATE_AGENT_HISTORY)

    @staticmethod
    def should_exit(state):
        """Returns True if the user has requested to exit."""
        return state.get("exit_requested", False)

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        Simplified orchestration of the morphing agent pipeline.
        """
        state = ctx.session.state
        
        # Initialize state if needed
        if STATE_MORPH_COUNT not in state:
            state[STATE_MORPH_COUNT] = 0
        if STATE_CURRENT_ROLE not in state:
            state[STATE_CURRENT_ROLE] = "base_agent"
        if "flow_step" not in state:
            state["flow_step"] = 0

        logger.info(f"[MorphingOrchestratorAgent] Flow step: {state.get('flow_step')}")

        # Check for exit request first
        if self.should_exit(state):
            logger.info("[MorphingOrchestratorAgent] Exit requested, running thank you agent.")
            async for event in self.thank_agent.run_async(ctx):
                yield event
            return

        # Simple step-based flow control
        flow_step = state.get("flow_step", 0)
        
        # Step 0: Welcome (only for new users)
        if flow_step == 0 and self.should_welcome_user(state):
            logger.info("[MorphingOrchestratorAgent] Step 0: Welcome new user.")
            async for event in self.welcome_agent.run_async(ctx):
                yield event
            state["flow_step"] = 1
            state = ctx.session.state

        # Step 1: Get specialization
        if flow_step == 1:
            logger.info("[MorphingOrchestratorAgent] Step 1: Getting specialization.")
            async for event in self.initial_specialization_agent.run_async(ctx):
                yield event
            state = ctx.session.state
            
            # Check if we got a specialization
            if not self.user_specialization_not_defined(state):
                logger.info(f"[MorphingOrchestratorAgent] Got specialization: {state.get(STATE_USER_SPECIALIZATION)}")
                state["flow_step"] = 2
            else:
                logger.info("[MorphingOrchestratorAgent] No specialization received, staying in step 1")

        # Step 2: Confirm morphing
        elif flow_step == 2:
            logger.info("[MorphingOrchestratorAgent] Step 2: Confirming morphing.")
            async for event in self.morph_confirmation_agent.run_async(ctx):
                yield event
            state = ctx.session.state
            
            # Check if user confirmed
            if not self.user_morph_not_confirmed(state):
                logger.info("[MorphingOrchestratorAgent] User confirmed, moving to morphing")
                state["flow_step"] = 3
            else:
                logger.info("[MorphingOrchestratorAgent] User didn't confirm, going back to step 1")
                state["flow_step"] = 1
                state[STATE_USER_SPECIALIZATION] = ""

        # Step 3: Morph into specialized agent
        elif flow_step == 3:
            logger.info("[MorphingOrchestratorAgent] Step 3: Morphing into specialized agent.")
            async for event in self.morphing_loop.run_async(ctx):
                yield event
            state = ctx.session.state
            
            # Check if morphing was successful
            if not self.morphed_agent_not_defined(state):
                logger.info("[MorphingOrchestratorAgent] Morphing successful, moving to interaction")
                state[STATE_MORPH_COUNT] = state.get(STATE_MORPH_COUNT, 0) + 1
                state[STATE_CURRENT_ROLE] = "specialized_agent"
                state["flow_step"] = 4
            else:
                logger.info("[MorphingOrchestratorAgent] Morphing failed, going back to step 2")
                state["flow_step"] = 2
                state[STATE_USER_MORPH_CONFIRMED] = ""

        # Step 4: Specialized agent interaction
        elif flow_step == 4:
            logger.info("[MorphingOrchestratorAgent] Step 4: Specialized agent interaction.")
            async for event in self.specialized_agent_loop.run_async(ctx):
                yield event
            state = ctx.session.state
            
            # Check for reset or exit requests
            if state.get("reset_requested", False):
                logger.info("[MorphingOrchestratorAgent] Reset requested, going back to step 1")
                state["flow_step"] = 1
                state[STATE_USER_SPECIALIZATION] = ""
                state[STATE_USER_MORPH_CONFIRMED] = ""
                state[STATE_MORPHED_AGENT_DESCRIPTION] = ""
                state["reset_requested"] = False
                state[STATE_CURRENT_ROLE] = "base_agent"
            elif state.get("exit_requested", False):
                logger.info("[MorphingOrchestratorAgent] Exit requested, moving to step 5")
                state["flow_step"] = 5

        # Step 5: Exit with thank you
        elif flow_step == 5:
            logger.info("[MorphingOrchestratorAgent] Step 5: Exit with thank you.")
            async for event in self.thank_agent.run_async(ctx):
                yield event

# --- Instantiate the enhanced orchestrator agent ---

root_agent = MorphingOrchestratorAgent(
    name="EnhancedMorphingAgentPipeline",
    welcome_agent=welcome_agent,
    initial_specialization_agent=initial_specialization_agent,
    morph_confirmation_agent=morph_confirmation_agent,
    morphing_loop=morphing_loop,
    specialized_agent_loop=specialized_agent_loop,
    thank_agent=thank_you_agent,
)