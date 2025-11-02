#!/bin/bash

# Set up environment
echo "Setting up environment..."
cd ~/vision-hack
source venv/bin/activate
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
export no_proxy=localhost,127.0.0.1
export NO_PROXY=localhost,127.0.0.1

# Define variables for terminal colors
BLUE='\033[34m'
MAGENTA='\033[35m'
CYAN='\033[36m'
GREEN='\033[32m'
YELLOW='\033[33m'
RED='\033[31m'
NC='\033[0m' # No Color

# Display header
echo -e "${YELLOW}======================================${NC}"
echo -e "${GREEN}Starting VISION Network Simulators${NC}"
echo -e "${YELLOW}======================================${NC}"
echo ""
echo -e "${BLUE}RAN Simulator (VendorA)${NC}: Cell events"
echo -e "${MAGENTA}CORE Simulator (VendorB)${NC}: Core events"
echo -e "${CYAN}TRANSPORT Simulator (VendorC)${NC}: Link events"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all simulators${NC}"
echo -e "${YELLOW}======================================${NC}"
echo ""

# Function to terminate all background processes on exit
cleanup() {
    echo -e "${RED}Stopping all simulators...${NC}"
    kill $(jobs -p) 2>/dev/null
    exit
}

# Set trap for clean shutdown
trap cleanup SIGINT SIGTERM

# Start simulators in background
python simulators/vendorA_sim.py &
python simulators/vendorB_sim.py &
python simulators/vendorC_sim.py &

# Wait for any process to exit
wait
