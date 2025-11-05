# Switchport Python SDK

Official Python SDK for [Switchport](https://switchport.ai) - Prompt management and A/B testing platform.

## Features

- 🚀 **Easy Integration**: Simple, intuitive API
- 🎯 **Prompt Execution**: Call LLMs with managed prompts
- 📊 **A/B Testing**: Deterministic version routing based on context
- 📈 **Metrics Recording**: Track performance and user feedback
- 🔐 **Secure**: API key authentication
- 🎨 **Flexible Context**: Support for dict or string context

## Installation

```bash
pip install switchport
```

Or install from source:

```bash
git clone https://github.com/switchport-ai/switchport-python.git
cd switchport-python
pip install -e .
```

## Quick Start

### 1. Get Your API Key

1. Sign up at [switchport.ai](https://switchport.ai)
2. Create an organization and project
3. Get your API key from Settings (starts with `sp_`)

### 2. Set Environment Variable

```bash
export SWITCHPORT_API_KEY=sp_your_key_here
```

### 3. Use the SDK

```python
from switchport import Switchport

# Initialize client
client = Switchport()  # Reads API key from environment

# Execute a prompt
response = client.prompts.execute(
    prompt_key="welcome-message",
    variables={"customer_name": "Alice"}
)

print(response.text)  # Generated text from LLM
```

For complete examples and documentation, see the [examples](examples/) directory.
