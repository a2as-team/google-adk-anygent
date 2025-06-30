# Enhanced Morphing Agent - Google ADK

A sophisticated AI agent built with Google's Agent Development Kit (ADK) that can morph into any specialized agent based on user input. The agent can transform itself into experts, characters, tools, or any other specialized role you desire.

## Features

### 🎭 **Dynamic Morphing**

- Transform into any specialized agent (expert, character, tool, etc.)
- Multiple morphing sessions in a single conversation
- Comprehensive agent persona creation with personality, expertise, and communication style

### 🧠 **Smart State Management**

- Persistent session state across morphing cycles
- Agent history tracking
- Morph count and role tracking
- Automatic state persistence

### 🛠️ **Enhanced Tools**

- **External API Integration**: Simulated API calls for gathering information
- **State Management**: Save and restore agent states
- **Reset Capability**: Return to base state for new morphing
- **Capability Querying**: Check current agent capabilities
- **Graceful Exit**: Personalized goodbye with session summary

### 🔄 **Flexible Interaction**

- Welcome new users with capability explanation
- Confirmation before morphing
- Special commands: `reset`, `morph again`, `exit`, `goodbye`
- Extended conversation loops (up to 20 iterations)

## Quick Start

### Prerequisites

- Python 3.9+
- Google ADK installed: `pip install google-adk`
- Google AI API access (for Gemini models)

### Installation

1. **Clone or download this project**
2. **Install dependencies**:

   ```bash
   pip install google-adk
   ```

3. **Set up environment variables** (create a `.env` file):
   ```bash
   GOOGLE_API_KEY=your_google_api_key_here
   ```

### Running the Agent

#### Option 1: Using ADK CLI

```bash
# Run in terminal mode
adk run anygent

# Run with web UI
adk web anygent

# Run API server
adk api_server anygent
```

#### Option 2: Direct Python execution

```python
from anygent.agent import root_agent
# Use the root_agent in your ADK application
```

## How It Works

### 1. **Welcome Phase**

- New users receive a warm welcome and explanation of capabilities
- Agent explains it can morph into any specialized role

### 2. **Specialization Definition**

- Agent prompts user to describe desired specialization
- User can specify role, expertise, personality, or any combination

### 3. **Confirmation**

- Agent asks for confirmation before morphing
- User can modify or proceed with the transformation

### 4. **Morphing Process**

- Agent searches for relevant information using external APIs
- Creates comprehensive agent persona including:
  - Role and expertise
  - Personality traits
  - Communication style
  - Key capabilities
  - Interaction guidelines

### 5. **Specialized Interaction**

- Agent operates as the specialized persona
- Responds to queries in character
- Maintains role consistency throughout conversation

### 6. **State Management**

- Tracks morphing history
- Counts number of transformations
- Saves state for persistence

## Example Interactions

### Example 1: Becoming a Programming Expert

```
User: "I want you to become a Python programming expert"
Agent: "I'll morph into a Python programming expert for you. Would you like me to proceed?"
User: "yes"
Agent: [Morphs into Python expert with comprehensive knowledge]
User: "How do I implement a decorator pattern in Python?"
Agent: [Responds as Python expert with detailed explanation]
```

### Example 2: Becoming a Creative Character

```
User: "Become a wise old wizard from a fantasy world"
Agent: "I'll transform into a wise old wizard for you. Shall I proceed?"
User: "yes"
Agent: [Morphs into wizard character with mystical personality]
User: "Tell me about the ancient magic"
Agent: [Responds in wizard's mystical, wise tone]
```

### Example 3: Multiple Morphing

```
User: "reset"
Agent: [Returns to base state]
User: "Become a travel agent"
Agent: [Morphs into travel agent]
User: "What's the best time to visit Paris?"
Agent: [Responds as travel agent]
User: "morph again"
Agent: [Returns to base state for new morphing]
```

## Special Commands

- **`reset`** or **`morph again`**: Return to base state for new morphing
- **`exit`** or **`goodbye`**: End session with personalized thank you
- **`capabilities`**: Check current agent capabilities and tools

## Architecture

### Agent Components

1. **WelcomeAgent**: Greets new users and explains capabilities
2. **SpecializationPromptAgent**: Prompts for desired specialization
3. **MorphConfirmationAgent**: Confirms morphing decision
4. **MorphingAgent**: Creates specialized agent persona
5. **SpecializedAgent**: Operates as the morphed agent
6. **ThankYouAgent**: Provides personalized goodbye

### Tools

- **`call_external_api`**: Gathers information for morphing
- **`save_agent_state`**: Persists agent state
- **`reset_agent`**: Returns to base state
- **`exit_with_thanks`**: Graceful session termination
- **`get_agent_capabilities`**: Shows current capabilities

### State Management

The agent maintains several state variables:

- `user_specialization`: Desired agent role
- `morphed_agent_description`: Created agent persona
- `agent_history`: Session history
- `morph_count`: Number of transformations
- `current_role`: Current agent state

## Customization

### Adding New Tools

You can extend the agent by adding new tools to the `specialized_agent`:

```python
def my_custom_tool(tool_context: ToolContext):
    # Your custom tool logic
    return {"result": "custom response"}

# Add to specialized_agent tools list
specialized_agent = LlmAgent(
    # ... other parameters
    tools=[exit_with_thanks, reset_agent, get_agent_capabilities, call_external_api, my_custom_tool],
)
```

### Modifying Agent Behavior

You can customize the agent's behavior by modifying the instructions in each sub-agent:

```python
welcome_agent = LlmAgent(
    # ... other parameters
    instruction="Your custom welcome message and instructions",
)
```

## Troubleshooting

### Common Issues

1. **API Key Issues**: Ensure your Google API key is properly set
2. **Model Access**: Verify you have access to the specified Gemini model
3. **State Persistence**: Check that session state is being maintained properly

### Debug Mode

Enable debug logging by modifying the logging level:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

Feel free to enhance this agent by:

- Adding new tools and capabilities
- Improving the morphing logic
- Enhancing state management
- Adding new agent types or specializations

## License

This project is open source and available under the MIT License.

---

**Built with Google's Agent Development Kit (ADK)** - A flexible and modular framework for developing and deploying AI agents.
