#!/bin/bash

# Set up environment
cd ~/vision-hack
source venv/bin/activate
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
export no_proxy=localhost,127.0.0.1
export NO_PROXY=localhost,127.0.0.1

# Define variables for terminal colors
GREEN='\033[32m'
YELLOW='\033[33m'
BLUE='\033[34m'
MAGENTA='\033[35m'
CYAN='\033[36m'
RED='\033[31m'
NC='\033[0m' # No Color

# Display header
echo -e "${YELLOW}======================================${NC}"
echo -e "${GREEN}Starting VISION Monitoring System${NC}"
echo -e "${YELLOW}======================================${NC}"
echo ""

# Function to terminate all background processes on exit
cleanup() {
    echo -e "${RED}Stopping all processes...${NC}"
    kill $(jobs -p) 2>/dev/null
    exit
}

# Set trap for clean shutdown
trap cleanup SIGINT SIGTERM

# Terminal 1: Backend
echo -e "${YELLOW}[1/3]${NC} Starting ${BLUE}Backend Server${NC}..."
cd backend && uvicorn app:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo -e "${GREEN}Backend started with PID:${NC} $BACKEND_PID"
sleep 2

# Terminal 2: UI
echo -e "${YELLOW}[2/3]${NC} Starting ${MAGENTA}UI Dashboard${NC}..."
cd ~/vision-hack && streamlit run ui/app.py &
UI_PID=$!
echo -e "${GREEN}UI started with PID:${NC} $UI_PID"
sleep 2

# Terminal 3: Simulators
echo -e "${YELLOW}[3/3]${NC} Starting ${CYAN}Network Simulators${NC}..."
cd ~/vision-hack && ./run_simulators.sh &
SIM_PID=$!
echo -e "${GREEN}Simulators started with PID:${NC} $SIM_PID"

# Print access information
echo ""
echo -e "${YELLOW}======================================${NC}"
echo -e "${GREEN}System is running!${NC}"
echo -e "${BLUE}Backend URL:${NC} http://localhost:8000"
echo -e "${MAGENTA}UI Dashboard:${NC} http://localhost:8501"
echo -e "${YELLOW}======================================${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all components${NC}"

# Wait for any process to exit
wait
