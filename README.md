# VISION - Vendor-Independent System for Intelligent Orchestration of Networks

## Project Overview

VISION is a network monitoring and orchestration system that normalizes, correlates, and analyzes network alarms from different vendors to identify cross-domain incidents. The system provides a unified dashboard for network operators and allows intent-based network orchestration.

## Components

This project consists of three main components:

1. **Backend Service**: A FastAPI server that processes events from different network vendors
2. **UI Application**: A Streamlit-based dashboard for visualizing incidents and sending intents
3. **Simulators**: Three vendor-specific simulators that generate synthetic network events

### Backend Service

The backend serves as the core of the system, providing the following functionality:
- Normalizes different vendor alarm formats to a canonical format
- Correlates alarms across vendors to identify incidents
- Provides endpoints for incident retrieval, analytics, and intent translation
- Offers an orchestration simulation endpoint

### UI Dashboard

The UI provides network operators with a unified view of the network:
- Displays correlated incidents with detailed information
- Allows users to input high-level intents that get translated to actions
- Shows analytics and network health status
- Auto-refreshes to display the latest state of the network

### Simulators

Three separate simulators generate events from different network domains:
- **VendorA**: Simulates Radio Access Network (RAN) alarms
- **VendorB**: Simulates Core Network alarms
- **VendorC**: Simulates Transport Network alarms

## Prerequisites

- Python 3.8+
- Virtual environment (venv)

## Installation

1. Clone the repository (if not already done)
2. Set up and activate the virtual environment:
   ```bash
   cd vision-hack
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Quick Start (All Components)

The easiest way to start the entire system is to use the provided script:

```bash
cd vision-hack
./run_all.sh
```

This script will start the backend, UI dashboard, and all three simulators in a single command. Press Ctrl+C to stop all components.

### Running Simulators Only

If you want to run just the simulators (e.g., when backend and UI are already running):

```bash
cd vision-hack
./run_simulators.sh
```

### Running Components Individually

#### 1. Start the Backend

```bash
cd vision-hack
source venv/bin/activate
cd backend
uvicorn app:app --host 0.0.0.0 --port 8000
```

#### 2. Start the UI

```bash
cd vision-hack
source venv/bin/activate
streamlit run ui/app.py
```

The UI will be accessible at http://localhost:8501 by default.

#### 3. Start the Simulators

Run each simulator in a separate terminal window:

```bash
# Terminal 1 - VendorA (RAN)
cd vision-hack
source venv/bin/activate
python simulators/vendorA_sim.py

# Terminal 2 - VendorB (Core)
cd vision-hack
source venv/bin/activate
python simulators/vendorB_sim.py

# Terminal 3 - VendorC (Transport)
cd vision-hack
source venv/bin/activate
python simulators/vendorC_sim.py
```

## Using the Application

1. Open the UI in your browser (typically http://localhost:8501)
2. The simulators will automatically generate random network events
3. The backend will normalize and correlate these events
4. The UI will display incidents when correlations are detected
5. You can enter intents in the "Intent → Action" section (e.g., "create low-latency slice")

## API Endpoints

- `POST /normalize`: Normalize vendor-specific events
- `GET /incidents`: Get list of correlated incidents
- `POST /translate`: Translate high-level intent to concrete action
- `POST /orchestrate`: Simulate executing an action
- `GET /analytics`: Get network analytics data

## AI Features

The VISION system incorporates several AI/ML-based components:

### 1. AI-Based Correlation Engine

The correlation engine uses advanced AI techniques to identify relationships between events:

- **Feature Engineering**: Extracts meaningful features from network events
- **Temporal Proximity Analysis**: Uses time-series analysis to identify related events
- **Confidence Scoring**: ML model calculates confidence levels for each incident
- **Root Cause Analysis**: Uses causal inference to identify probable root causes

### 2. Intent-Based Translation with NLP

The intent translator uses Natural Language Processing to convert high-level intents to actions:

- **Intent Classification**: Classifies user input into known intent categories
- **Named Entity Recognition**: Extracts key parameters from natural language input
- **Confidence Scoring**: Provides confidence levels for each detected intent
- **Parameter Extraction**: Identifies specific values needed for action execution

### 3. AI-Powered Event Generation

Each domain simulator uses domain-specific ML models to generate realistic network events:

- **RAN Domain**: Uses XGBoost and LSTM models for anomaly detection
- **CORE Domain**: Uses LSTM-Autoencoder and Random Forest for attack pattern identification
- **TRANSPORT Domain**: Uses ARIMA for forecasting and GANs for anomaly detection

## Data Flow

### Simulator Data Format

Each vendor simulator generates data in its own proprietary format:

1. **VendorA (RAN)** - Example event:
   ```json
   {
     "vendor": "VendorA",
     "type": "RAN_ALARM",
     "cell": "Cell-1",
     "ts": 1690000000,
     "desc": "HIGH_RTT",
     "severity": "major",
     "metrics": {"rss": -70, "rtt": 120}
   }
   ```

2. **VendorB (Core)** - Example event:
   ```json
   {
     "vendor": "VendorB",
     "alarm": "SESSION_DROP",
     "core_id": "Core-1",
     "time": 1690000001,
     "level": "major",
     "metrics": {"cpu": 90}
   }
   ```

3. **VendorC (Transport)** - Example event:
   ```json
   {
     "vendor": "VendorC",
     "type": "HIGH_LATENCY",
     "link": "Link-1",
     "ts": 1690000002,
     "severity": "major",
     "metrics": {"loss": 5, "latency_ms": 200}
   }
   ```

### Normalized Format

The backend normalizes these diverse formats into a standard structure:

```json
{
  "timestamp": 1690000000,
  "vendor": "VendorA/B/C",
  "domain": "RAN/CORE/TRANSPORT",
  "node_id": "Cell-1/Core-1/Link-1",
  "alarm_type": "HIGH_RTT/SESSION_DROP/HIGH_LATENCY",
  "severity": "major/minor",
  "metrics": {"key": "value"}
}
```

The simulators now show both the raw and normalized data in their console output, making it easy to see the transformation process.

## Customization

You can customize the behavior by setting environment variables:
- `BACKEND_URL`: URL of the backend service (default: http://localhost:8000)
- `PORT`: Port for the backend service (default: 8000)
- `CORRELATION_WINDOW_SECONDS`: Time window for correlation (default: 30)

## Troubleshooting

- If components fail to connect, ensure the backend is running and accessible
- Check for proper activation of the virtual environment
- Verify that all required dependencies are installed
- For simulator connection issues, check that the BACKEND_URL is correctly set
- If you see inconsistent counts between normalized events and incidents, this is because one event can contribute to multiple incidents
