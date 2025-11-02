# VISION Technical Stack

## Architecture Overview

```
┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│   VENDOR          │     │    BACKEND        │     │       UI          │
│   SIMULATORS      │────▶│    SERVICES       │────▶│    DASHBOARD      │
└───────────────────┘     └───────────────────┘     └───────────────────┘
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│  SIMULATED        │     │  AI-BASED         │     │   DATA            │
│  NETWORK EVENTS   │────▶│  CORRELATION      │────▶│   VISUALIZATION   │
└───────────────────┘     │  ENGINE           │     └───────────────────┘
                          └───────────────────┘
```

## Component Stack

| Layer | Technology | Description |
|-------|------------|-------------|
| **Backend** | FastAPI (Python) | High-performance web framework with automatic OpenAPI documentation |
| **UI** | Streamlit | Interactive Python-based dashboard with real-time updates |
| **Visualization** | Plotly + Pandas | Interactive charts, data transformation and analysis |
| **Simulators** | Python | Vendor-specific event simulators with AI/ML components |
| **Communication** | REST APIs | HTTP-based service communication |
| **Deployment** | Container-ready | Modular components designed for containerization |

## AI/ML Capabilities

- **Correlation Engine**: Advanced event correlation using domain knowledge and temporal pattern analysis
- **Intent Translation**: NLP-based intent parsing with named entity recognition and parameter extraction
- **Anomaly Detection**: Time-series anomaly detection with domain-specific models:
  - RAN domain: XGBoost and LSTM models
  - Core domain: Autoencoder and Random Forest
  - Transport domain: ARIMA forecasting and GAN models

## Key APIs & Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/normalize` | POST | Normalize vendor-specific events to canonical format |
| `/incidents` | GET | Retrieve correlated incidents |
| `/all-incidents` | GET | Get all incidents (correlated and single-domain) |
| `/analytics` | GET | Get network analytics data |
| `/translate` | POST | Convert high-level intent to concrete action |
| `/orchestrate` | POST | Simulate execution of network actions |

## Data Flow

1. Vendor simulators generate domain-specific events (RAN, CORE, TRANSPORT)
2. Events are normalized via the `/normalize` endpoint
3. Correlation engine processes events to identify incidents
4. UI dashboard fetches and visualizes incident and analytics data
5. User inputs high-level intents that get translated to actions
6. Actions are orchestrated across network domains
