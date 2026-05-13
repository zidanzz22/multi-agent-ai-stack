# 🤖 Multi-Agent AI Infrastructure

A production-grade, self-healing multi-agent AI stack built for real-world load. Three autonomous agent instances work together to handle task automation, personal assistance via Telegram, and provider reliability testing — all with automatic failover across LLM providers.

## Architecture Overview

```
User / Telegram
      │
      ▼
┌─────────────────┐
│  Telegram Bot   │  ← Frontend interface
│    Frontend     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Orchestration  │  ← Routes by task type & provider availability
│     Layer       │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌───────┐
│OpenAI │ │Claude │  ← Provider pool (auto-failover)
└───────┘ └───────┘
         │
         ▼
┌─────────────────┐
│  Agent Handler  │  ← Long-context reasoning + tool use
└────────┬────────┘
         │
         ▼
   Streaming Response
```

## Agent Roles

| Agent | Role | Description |
|-------|------|-------------|
| `task_agent` | Task Automation | Handles scheduled and on-demand automation tasks |
| `telegram_agent` | Personal Assistant | Telegram-based conversational AI with context memory |
| `reliability_agent` | Provider Testing | Continuously monitors and benchmarks LLM provider uptime |

## Features

- ✅ **Self-healing pipelines** — auto-retry with exponential backoff on rate limits and auth errors
- ✅ **Provider failover** — seamlessly switches between OpenAI, Anthropic, and others
- ✅ **Real-time streaming** — responses stream back token by token via Telegram
- ✅ **Long-context support** — handles extended reasoning chains and tool use
- ✅ **Silent failure detection** — catches and recovers from silent LLM pipeline breaks
- ✅ **Cost tracking** — monitors token usage and spend per agent per day

## Project Structure

```
multi-agent-infra/
├── agents/
│   ├── task_agent.py          # Task automation agent
│   ├── telegram_agent.py      # Telegram personal assistant
│   └── reliability_agent.py   # Provider reliability tester
├── core/
│   ├── orchestrator.py        # Central dispatch and routing logic
│   ├── provider_router.py     # Provider selection and failover
│   └── self_healing.py        # Retry, backoff, and recovery logic
├── config/
│   └── settings.py            # Centralized config and env loading
├── .env.example               # Environment variable template
├── requirements.txt           # Python dependencies
└── README.md
```

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/multi-agent-ai-infrastructure.git
cd multi-agent-ai-infrastructure
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

```bash
cp .env.example .env
# Edit .env with your actual API keys
```

### 4. Run an agent

```bash
# Start the Telegram bot
python agents/telegram_agent.py

# Start the task automation agent
python agents/task_agent.py

# Run provider reliability tests
python agents/reliability_agent.py
```

## Environment Variables

See `.env.example` for all required variables. Key ones:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key |
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token from @BotFather |
| `PRIMARY_PROVIDER` | Default LLM provider (`openai` or `anthropic`) |
| `FALLBACK_PROVIDERS` | Comma-separated fallback provider list |

## Self-Healing Behavior

The infrastructure handles the following failure modes automatically:

- **Rate limit (429)** → exponential backoff + retry up to 5 times
- **Auth error (401)** → flag provider, route to fallback immediately  
- **Model outage** → detect via reliability agent, remove from pool
- **Timeout** → configurable per-provider timeout with automatic reroute
- **Silent failures** → response validation catches empty/malformed outputs

## Cost Snapshot

Based on production usage (~743M tokens / 30 days):

- Daily average: ~$17/day
- Primary spend: long-context reasoning + tool use chains
- Cost optimization: provider routing prefers cheapest available model per task tier

## License

MIT
