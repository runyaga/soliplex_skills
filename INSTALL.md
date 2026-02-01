# soliplex

> LLM-executable installation instructions for Soliplex - an AI-powered RAG system with multi-room architecture.

**AI Agent**: Follow these instructions to install Soliplex from scratch using `uv`. Execute each step in order, verify success before proceeding, and adapt commands to the user's environment.

---

## OBJECTIVE

Install a fully functional Soliplex backend server with:
- Python 3.12+ virtual environment managed by `uv`
- All Python dependencies installed
- RAG database initialized and indexed with documentation
- Backend server running and responding to API requests

---

## DONE WHEN

- [ ] `uv run soliplex-cli --help` displays available commands
- [ ] `uv run soliplex-cli check-config example/minimal.yaml` reports no critical errors
- [ ] `uv run soliplex-cli list-rooms example/minimal.yaml` shows available rooms
- [ ] Backend server starts without errors on port 8000
- [ ] `curl http://localhost:8000/health` returns successful response
- [ ] RAG database exists at `db/rag/rag.lancedb/`

---

## TODO

- [ ] Verify prerequisites (Python 3.12+, uv, git, Ollama or OpenAI key)
- [ ] Clone soliplex repository
- [ ] Install dependencies with uv
- [ ] Configure environment variables
- [ ] Initialize RAG database
- [ ] Index documentation into RAG
- [ ] Validate configuration
- [ ] Start backend server
- [ ] Verify installation

---

## Step 1: Verify Prerequisites

Check that required tools are installed.

### Python 3.12+

```bash
python3 --version
```

Expected: `Python 3.12.x` or higher. If not installed:

**macOS:**
```bash
brew install python@3.13
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install python3.13 python3.13-venv
```

### uv (Python package manager)

```bash
uv --version
```

Expected: `uv 0.x.x`. If not installed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or with Homebrew:
```bash
brew install uv
```

### Git

```bash
git --version
```

### Ollama (Recommended for local LLM)

```bash
ollama --version
```

If not installed:
```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh
```

Start Ollama and pull required models:
```bash
ollama serve &
ollama pull qwen2.5:latest
ollama pull qwen3-embedding:4b
```

**Alternative**: If using OpenAI instead of Ollama, you need an API key from https://platform.openai.com/api-keys

---

## Step 2: Clone Repository

```bash
git clone https://github.com/soliplex/soliplex.git
cd soliplex
```

Verify clone succeeded:
```bash
ls -la pyproject.toml
```

---

## Step 3: Install Dependencies with uv

Create virtual environment and install all dependencies:

```bash
uv sync
```

This creates `.venv/` and installs all dependencies from `pyproject.toml`.

Verify installation:
```bash
uv run soliplex-cli --help
```

Expected output shows available commands: `serve`, `check-config`, `list-rooms`, etc.

### Install Additional Dependencies

Install haiku-rag for RAG indexing:
```bash
uv pip install haiku-rag
```

Install TUI dependencies (optional):
```bash
uv sync --group tui
```

---

## Step 4: Configure Environment

### Option A: Using Ollama (Recommended)

Create `.env` file:
```bash
cat > .env << 'EOF'
OLLAMA_BASE_URL=http://localhost:11434
EOF
```

### Option B: Using OpenAI

Create `.env` file with your API key:
```bash
cat > .env << 'EOF'
OPENAI_API_KEY=sk-proj-your-key-here
EOF
```

**Important**: Replace `sk-proj-your-key-here` with your actual OpenAI API key.

### Load Environment Variables

```bash
source .env
```

Verify:
```bash
echo $OLLAMA_BASE_URL  # Should show http://localhost:11434
# OR
echo $OPENAI_API_KEY   # Should show your key (if using OpenAI)
```

---

## Step 5: Initialize RAG Database

Create database directory:
```bash
mkdir -p db/rag
```

Initialize the LanceDB database:
```bash
uv run haiku-rag --config example/haiku.rag.yaml init --db db/rag/rag.lancedb
```

Expected output: Database initialization confirmation.

---

## Step 6: Index Documentation

Index Soliplex documentation into the RAG database:

```bash
uv run haiku-rag --config example/haiku.rag.yaml add-src --db db/rag/rag.lancedb docs/
```

Expected output: `17 documents added successfully.` (or similar count)

Verify database was created:
```bash
ls -la db/rag/rag.lancedb/
```

Should show database files.

---

## Step 7: Validate Configuration

Check configuration for errors:

```bash
uv run soliplex-cli check-config example/minimal.yaml
```

This reports:
- Missing secrets
- Missing environment variables
- Configuration errors

**Fix any reported issues before proceeding.**

List available rooms:
```bash
uv run soliplex-cli list-rooms example/minimal.yaml
```

Expected rooms:
- `ask_soliplex` - RAG-powered documentation assistant
- `haiku` - General purpose chat
- `joker` - Entertainment room

---

## Step 8: Start Backend Server

Start the server in development mode (no authentication):

```bash
uv run soliplex-cli serve example/minimal.yaml --no-auth-mode
```

Expected output:
```
INFO:     Started server process [xxxxx]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

**Keep this terminal running.** Open a new terminal for verification.

---

## Step 9: Verify Installation

In a **new terminal**, run these verification commands:

### Health Check

```bash
curl http://localhost:8000/health
```

Expected: JSON response with status information.

### List Rooms API

```bash
curl http://localhost:8000/api/v1/rooms
```

Expected: JSON array of available rooms.

### OpenAPI Documentation

Open in browser: http://localhost:8000/docs

Should display interactive API documentation.

---

## Quick Reference Commands

After installation, use these commands:

```bash
# Start server (from soliplex directory)
cd /path/to/soliplex
source .env
uv run soliplex-cli serve example/minimal.yaml --no-auth-mode

# Start TUI client (in separate terminal)
uv run soliplex-tui

# Check configuration
uv run soliplex-cli check-config example/minimal.yaml

# List rooms
uv run soliplex-cli list-rooms example/minimal.yaml

# Add more documents to RAG
uv run haiku-rag --config example/haiku.rag.yaml add-src --db db/rag/rag.lancedb /path/to/docs/
```

---

## Configuration Profiles

| Profile | LLM | Use Case |
|---------|-----|----------|
| `example/minimal.yaml` | Ollama | Local development |
| `example/minimal-openai.yaml` | OpenAI | OpenAI users |
| `example/installation.yaml` | Ollama | Full features + MCP |

---

## Troubleshooting

### "Ollama connection refused"

Ensure Ollama is running:
```bash
ollama serve
```

Check URL in `.env`:
```bash
curl $OLLAMA_BASE_URL/api/tags
```

### "Module not found"

Reinstall dependencies:
```bash
uv sync --reinstall
```

### "RAG database not found"

Re-initialize:
```bash
mkdir -p db/rag
uv run haiku-rag --config example/haiku.rag.yaml init --db db/rag/rag.lancedb
```

### "Port 8000 already in use"

Use different port:
```bash
uv run soliplex-cli serve example/minimal.yaml --no-auth-mode --port 8001
```

### Check Python version issues

```bash
uv python list
uv python install 3.13
```

---

## EXECUTE NOW

Complete the TODO checklist above. After each step, verify success before proceeding. The installation is complete when all DONE WHEN criteria are satisfied.

If you encounter errors:
1. Check the Troubleshooting section
2. Verify prerequisites are correctly installed
3. Ensure environment variables are loaded (`source .env`)
4. Check Ollama is running if using local LLM

---

## Next Steps After Installation

1. **Try the TUI**: `uv run soliplex-tui`
2. **Explore rooms**: Chat with `ask_soliplex` for RAG-powered answers
3. **Add your documents**: Index your own docs into the RAG database
4. **Configure authentication**: Set up OIDC for production use
5. **Install soliplex_skills**: Add skill-based capabilities to your rooms
