#!/bin/bash
# ─────────────────────────────────────────────────────────────────────
# 🇪🇬 Telecom Egypt Intelligent Assistant — Start Script
# ─────────────────────────────────────────────────────────────────────
# Double-click this file to launch the chatbot.
# On macOS: right-click → Open With → Terminal
# ─────────────────────────────────────────────────────────────────────

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Navigate to project directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                  ║${NC}"
echo -e "${CYAN}║   🇪🇬  ${BOLD}Telecom Egypt Intelligent Assistant${NC}${CYAN}       ║${NC}"
echo -e "${CYAN}║       WE-CHB — RAG-Powered Chatbot               ║${NC}"
echo -e "${CYAN}║                                                  ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# ─── Step 1: Check Ollama ────────────────────────────────────────────────────
echo -e "${BOLD}[1/5]${NC} Checking Ollama..."

if ! command -v ollama &> /dev/null; then
    echo -e "${RED}✗ Ollama is not installed.${NC}"
    echo "  Install from: https://ollama.ai"
    echo "  Press any key to exit..."
    read -n 1
    exit 1
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Ollama is not running. Starting it...${NC}"
    ollama serve &> /dev/null &
    sleep 3
    if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${RED}✗ Could not start Ollama. Please start it manually: ollama serve${NC}"
        echo "  Press any key to exit..."
        read -n 1
        exit 1
    fi
fi
echo -e "${GREEN}✓ Ollama is running${NC}"

# ─── Step 2: Check required models ──────────────────────────────────────────
echo -e "${BOLD}[2/5]${NC} Checking AI models..."

if ! ollama list | grep -q "qwen3:1.7b"; then
    echo -e "${YELLOW}⚠ Pulling qwen3:1.7b (this may take a few minutes)...${NC}"
    ollama pull qwen3:1.7b
fi
echo -e "${GREEN}✓ qwen3:1.7b ready${NC}"

if ! ollama list | grep -q "nomic-embed-text"; then
    echo -e "${YELLOW}⚠ Pulling nomic-embed-text...${NC}"
    ollama pull nomic-embed-text
fi
echo -e "${GREEN}✓ nomic-embed-text ready${NC}"

# ─── Step 3: Activate virtual environment ────────────────────────────────────
echo -e "${BOLD}[3/5]${NC} Setting up Python environment..."

if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚠ Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

source .venv/bin/activate

# Check if dependencies are installed
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo -e "${YELLOW}⚠ Installing dependencies (first run only)...${NC}"
    pip install -r requirements.txt --quiet
fi
echo -e "${GREEN}✓ Python environment ready${NC}"

# ─── Step 4: Check knowledge base ───────────────────────────────────────────
echo -e "${BOLD}[4/5]${NC} Checking knowledge base..."

if [ ! -f "data/raw/te_eg_pages.json" ]; then
    echo -e "${YELLOW}⚠ Knowledge base not found. Scraping te.eg (this takes ~2 minutes)...${NC}"
    SCRAPE_MAX_PAGES=50 python3 -m src.ingestion.scraper
fi
echo -e "${GREEN}✓ Website data available${NC}"

if [ ! -d "data/vectorstore" ] || [ -z "$(ls -A data/vectorstore 2>/dev/null)" ]; then
    echo -e "${YELLOW}⚠ Vector store not built. Indexing (this takes ~30 seconds)...${NC}"
    python3 -m src.ingestion.indexer
fi
echo -e "${GREEN}✓ Vector store ready${NC}"

# ─── Step 5: Launch the app ─────────────────────────────────────────────────
echo ""
echo -e "${BOLD}[5/5]${NC} ${GREEN}Launching Telecom Egypt Assistant...${NC}"
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  🌐 App URL:  ${BOLD}http://localhost:8501${NC}"
echo -e "  📖 Press ${BOLD}Ctrl+C${NC} to stop the server"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Open browser after a short delay
(sleep 2 && open "http://localhost:8501" 2>/dev/null || xdg-open "http://localhost:8501" 2>/dev/null) &

# Launch Streamlit
streamlit run app.py --server.port 8501 --server.headless true
