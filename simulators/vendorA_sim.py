# simulators/vendorA_sim.py
import time, json, requests, random, os
BACKEND = os.getenv("BACKEND_URL", "http://localhost:8000")
URL = f"{BACKEND}/normalize"

# Simulated AI event generator
class AINetworkEventGenerator:
    def __init__(self, vendor="VendorA", domain="RAN"):
        self.vendor = vendor
        self.domain = domain
        self.anomaly_models = self._initialize_models()
        self.cells = [f"Cell-{i}" for i in range(1, 4)]
        # Simulated time series state
        self.cell_states = {cell: {
            "rss_baseline": random.uniform(-85, -75),
            "rtt_baseline": random.uniform(40, 80),
            "anomaly_trend": 0,  # 0=normal, +1=degrading, -1=improving
            "anomaly_duration": 0  # how long has anomaly been present
        } for cell in self.cells}
        # Simulated ML anomaly detection thresholds
        self.thresholds = {
            "rss_std_dev": 5.0,  # standard deviation threshold
            "rtt_percent_increase": 50.0,  # percent increase threshold
            "anomaly_confidence": 0.85  # confidence threshold to generate alarm
        }
    
    def _initialize_models(self):
        """Simulate initialization of anomaly detection models"""
        print(f"\033[94m[AI] Initializing {self.domain} anomaly detection models...\033[0m")
        return {
            "rtt_anomaly": "XGBoost",
            "rss_anomaly": "Isolation Forest",
            "call_drop": "LSTM"
        }
    
    def _simulate_cell_behavior(self, cell_id):
        """Simulate realistic cell behavior with trends"""
        state = self.cell_states[cell_id]
        
        # Occasionally change anomaly trend
        if random.random() < 0.1:
            state["anomaly_trend"] = random.choice([-1, 0, 0, 0, 1])  # bias toward normal
        
        # Update anomaly duration based on trend
        if state["anomaly_trend"] != 0:
            state["anomaly_duration"] += state["anomaly_trend"]
            state["anomaly_duration"] = max(0, min(10, state["anomaly_duration"]))
        
        # Generate metrics based on state
        anomaly_factor = state["anomaly_duration"] / 10.0
        
        # Base values with some noise
        rss = state["rss_baseline"] - (anomaly_factor * 15) + random.uniform(-3, 3)
        rtt = state["rtt_baseline"] * (1 + (anomaly_factor * 2)) + random.uniform(-10, 10)
        
        # Return calculated values
        return {
            "rss": rss,
            "rtt": rtt,
            "anomaly_confidence": min(0.95, 0.5 + (anomaly_factor * 0.4))
        }
    
    def generate_event(self):
        """Generate a network event using simulated AI anomaly detection"""
        # Demo mode: Periodically generate critical incidents (every 180 seconds for RAN)
        # Use timestamp to determine if we should force a critical incident
        current_time = time.time()
        force_critical = (int(current_time) % 180) < 5  # 5-second window every 180 seconds
        
        if force_critical:
            # Force a critical incident on a specific cell
            cell = "Cell-1"  # Always use Cell-1 for critical incidents for demo consistency
            # Make all cells have high anomaly duration temporarily
            for c in self.cells:
                self.cell_states[c]["anomaly_duration"] = 10
                self.cell_states[c]["anomaly_trend"] = 1
            
            # Override metrics for the critical incident
            metrics = {
                "rss": -95.0,  # Very poor signal
                "rtt": 250.0,  # Very high latency
                "anomaly_confidence": 0.95  # High confidence
            }
            alarm_type = "RACH_FAIL"
            severity = "critical"  # Special severity level for demo
            
            print(f"\033[91m[DEMO] Generating CRITICAL RAN incident on {cell}\033[0m")
        else:
            # Normal behavior
            # Select a cell with bias toward cells with higher anomaly duration
            weights = [max(1, self.cell_states[c]["anomaly_duration"]) for c in self.cells]
            cell = random.choices(self.cells, weights=weights, k=1)[0]
            
            # Get simulated metrics
            metrics = self._simulate_cell_behavior(cell)
            
            # Determine alarm type based on metrics
            if metrics["rtt"] > 200:
                alarm_type = "HIGH_RTT"
            elif metrics["rss"] < -90:
                alarm_type = "RACH_FAIL"
            elif metrics["anomaly_confidence"] > 0.8:
                alarm_type = "DROP_CALL"
            else:
                alarm_type = random.choice(["RACH_FAIL", "HIGH_RTT", "DROP_CALL"])
            
            # Determine severity based on confidence
            severity = "major" if metrics["anomaly_confidence"] > 0.7 else "minor"
        
        return {
            "vendor": self.vendor,
            "type": "RAN_ALARM",
            "cell": cell,
            "ts": time.time(),
            "desc": alarm_type,
            "severity": severity,
            "metrics": {"rss": metrics["rss"], "rtt": metrics["rtt"]}
        }

# Initialize the AI generator
ai_generator = AINetworkEventGenerator()

def gen_alarm():
    return ai_generator.generate_event()

if __name__ == "__main__":
    print("\033[94m[VendorA Simulator] Starting - RAN Domain\033[0m")
    count = 0
    while True:
        count += 1
        payload = gen_alarm()
        try:
            print(f"\033[94m[VendorA - Event #{count}]\033[0m {payload['type']} on {payload['cell']} | Severity: {payload['severity']} | Metrics: RTT={payload['metrics']['rtt']:.1f}ms, RSS={payload['metrics']['rss']:.1f}dBm")
            response = requests.post(URL, json=payload, timeout=2)
            # Print normalized data if successful
            if response.status_code == 200:
                norm_data = response.json().get('normalized', {})
                print(f"  \033[92m→ Normalized to: Domain={norm_data.get('domain')}, Node={norm_data.get('node_id')}, Type={norm_data.get('alarm_type')}\033[0m")
        except Exception as e:
            print("\033[91mPost error:\033[0m", e)
        time.sleep(1.2)

