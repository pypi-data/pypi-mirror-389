# Switchport SDK - Quick Start Guide

Get started with Switchport in 5 minutes!

## Prerequisites

- Python 3.8+
- Switchport account (sign up at switchport.ai)
- API key from your Switchport dashboard

## Installation

```bash
pip install switchport
```

## Step 1: Get Your API Key

1. Log in to Switchport dashboard
2. Go to **Settings** → **API Keys**
3. Copy your API key (starts with `sp_`)

## Step 2: Set Environment Variable

```bash
# Linux/Mac
export SWITCHPORT_API_KEY=sp_your_key_here

# Windows (PowerShell)
$env:SWITCHPORT_API_KEY="sp_your_key_here"

# Or add to .env file
echo "SWITCHPORT_API_KEY=sp_your_key_here" >> .env
```

## Step 3: Your First Prompt

Create a file `test_switchport.py`:

```python
from switchport import Switchport

# Initialize (reads API key from environment)
client = Switchport()

# Execute a prompt
response = client.prompts.execute(
    prompt_key="welcome-message",
    variables={"name": "Alice"}
)

print("Generated text:")
print(response.text)
print(f"\nUsing model: {response.model}")
print(f"Version: {response.version_name}")
```

Run it:
```bash
python test_switchport.py
```

## Step 4: Set Up Your First Prompt (Dashboard)

Before running the SDK, create a prompt in the dashboard:

1. Go to **Prompts** → **New Prompt Config**
2. Name: "Welcome Message"
3. Key: `welcome-message`
4. Click **Create**
5. Add a version:
   - Model: `gpt-4` (or `claude-3-opus`, `gemini-pro`)
   - Prompt: `Write a welcome message for {{name}}.`
   - Click **Save**
6. Click **Publish** on the version

## Step 5: Configure LLM API Keys (Dashboard)

The SDK calls LLMs on your behalf. Configure your LLM API keys:

1. Go to **Settings** → **Organization Settings**
2. Add your LLM API keys:
   - OpenAI API key (for GPT models)
   - Anthropic API key (for Claude models)
   - Gemini API key (for Gemini models)
3. Click **Save**

## Step 6: Record Your First Metric

```python
from switchport import Switchport

client = Switchport()

# Execute prompt
response = client.prompts.execute(
    prompt_key="welcome-message",
    context={"user_id": "user_123"},
    variables={"name": "Alice"}
)

# Simulate user feedback (1-5 stars)
user_rating = 4.5

# Record metric
result = client.metrics.record(
    metric_key="satisfaction",
    value=user_rating,
    context={"user_id": "user_123"}  # Same context for proper aggregation
)

print(f"Metric recorded! Event ID: {result.metric_event_id}")
```

## Step 7: Create Metric Definition (Dashboard)

Before recording metrics, define them:

1. Go to **Metrics** → **New Metric**
2. Key: `satisfaction`
3. Name: "User Satisfaction"
4. Type: `float`
5. Click **Create**

## Step 8: A/B Testing

Create two versions of your prompt:

**Dashboard:**
1. Go to your prompt config
2. Create version "v1" with one style
3. Create version "v2" with another style
4. Create a traffic config:
   - v1: 50%
   - v2: 50%
5. Activate the traffic config

**Code:**
```python
from switchport import Switchport

client = Switchport()

# Test with different users
for user_id in ["user_001", "user_002", "user_003"]:
    response = client.prompts.execute(
        prompt_key="welcome-message",
        context={"user_id": user_id},  # Deterministic routing
        variables={"name": "User"}
    )
    print(f"{user_id} got version: {response.version_name}")

# Same user always gets same version
response1 = client.prompts.execute(
    prompt_key="welcome-message",
    context={"user_id": "user_001"}
)
response2 = client.prompts.execute(
    prompt_key="welcome-message",
    context={"user_id": "user_001"}
)

assert response1.version_id == response2.version_id  # ✓ Same version!
```

## Common Patterns

### Pattern 1: Email Generation
```python
def send_personalized_email(user):
    response = client.prompts.execute(
        prompt_key="welcome-email",
        context={"user_id": user.id, "tier": user.tier},
        variables={"name": user.name}
    )

    send_email(user.email, response.text)

    # Track if they opened it
    if email_was_opened():
        client.metrics.record(
            metric_key="email-open-rate",
            value=True,
            context={"user_id": user.id, "tier": user.tier}
        )
```

### Pattern 2: Chatbot with Feedback
```python
def handle_chat_message(user_id, message):
    response = client.prompts.execute(
        prompt_key="support-bot",
        context={"user_id": user_id},
        variables={"user_message": message}
    )

    # Show response to user
    display_message(response.text)

    # After conversation, collect rating
    rating = get_user_rating()  # 1-5
    client.metrics.record(
        metric_key="chat-satisfaction",
        value=rating,
        context={"user_id": user_id}
    )
```

### Pattern 3: Product Description Testing
```python
def show_product(product_id, user_segment):
    description = client.prompts.execute(
        prompt_key="product-description",
        context={"segment": user_segment},
        variables={"product": get_product_name(product_id)}
    )

    display(description.text)

    # Track if they bought
    if user_purchased():
        client.metrics.record(
            metric_key="conversion",
            value=True,
            context={"segment": user_segment}
        )
```

## Error Handling

```python
from switchport import (
    Switchport,
    PromptNotFoundError,
    AuthenticationError,
    APIError
)

client = Switchport()

try:
    response = client.prompts.execute("my-prompt")
except PromptNotFoundError:
    print("Prompt not found - check your prompt key")
except AuthenticationError:
    print("Invalid API key - check your credentials")
except APIError as e:
    print(f"API error: {e}")
    # Fallback to default behavior
    response = get_fallback_response()
```

## Troubleshooting

### "Invalid API key"
- Check `SWITCHPORT_API_KEY` environment variable is set
- Verify API key in dashboard hasn't been revoked
- Ensure API key starts with `sp_`

### "Prompt config not found"
- Verify prompt key in dashboard matches code
- Check you created the prompt in the correct project

### "No published version found"
- Create at least one version
- Click **Publish** on the version

### "Organization API keys not configured"
- Go to Settings → Organization Settings
- Add OpenAI/Anthropic/Gemini API keys
- Make sure you save the settings

### "Metric definition not found"
- Create metric in dashboard first
- Verify metric key matches

## Next Steps

- See [examples/](examples/) for more complex use cases
- Read full [README.md](README.md) for API reference
- Join our [Discord community](https://discord.gg/switchport)
- Check out the [documentation](https://docs.switchport.ai)

## Need Help?

- 📚 [Full Documentation](https://docs.switchport.ai)
- 💬 [Discord Community](https://discord.gg/switchport)
- ✉️ [support@switchport.ai](mailto:support@switchport.ai)

Happy prompt engineering! 🚀
