# simulators/vendorC_sim.py
import time, json, requests, random, os
BACKEND = os.getenv("BACKEND_URL", "http://localhost:8000")
URL = f"{BACKEND}/normalize"

# Simulated AI-based transport network monitoring
class TransportNetworkMonitor:
    def __init__(self, vendor="VendorC"):
        self.vendor = vendor
        self.models = self._initialize_models()
        self.links = [f"Link-{i}" for i in range(1, 4)]
        
        # Network topology simulation - which links are connected to what
        self.topology = {
            "Link-1": {"connects": ["RAN", "CORE"], "capacity_gbps": 10},
            "Link-2": {"connects": ["RAN", "TRANSPORT"], "capacity_gbps": 5},
            "Link-3": {"connects": ["TRANSPORT", "CORE"], "capacity_gbps": 15}
        }
        
        # Time series state for each link
        self.link_states = {link: {
            "baseline_latency": random.uniform(10, 50),
            "baseline_loss": random.uniform(0.1, 0.5),
            "traffic_level": random.uniform(0.2, 0.5),  # percentage of capacity
            "anomaly_state": "normal",  # normal, degrading, critical
            "anomaly_duration": 0,
            # Simulated seasonal patterns - would be learned from data
            "daily_pattern": [0.6, 0.4, 0.3, 0.3, 0.4, 0.6, 0.8, 1.0, 1.0, 0.9, 0.9, 0.8,
                            0.9, 1.0, 1.0, 0.9, 0.8, 0.7, 0.8, 0.9, 0.8, 0.7, 0.6, 0.5]
        } for link in self.links}
    
    def _initialize_models(self):
        """Simulate loading AI models for network performance prediction"""
        print(f"\033[96m[AI] Initializing Transport Network ML models...\033[0m")
        return {
            "forecasting": "ARIMA",
            "anomaly": "GAN", 
            "root_cause": "Graph Neural Network",
            "optimization": "Reinforcement Learning"
        }
    
    def _get_time_of_day_factor(self):
        """Simulates the time-of-day effect on network traffic"""
        hour = int(time.strftime("%H"))
        return self.link_states[self.links[0]]["daily_pattern"][hour]
    
    def _update_link_state(self, link_id):
        """Update the state of a link using simulated time series forecasting"""
        state = self.link_states[link_id]
        time_factor = self._get_time_of_day_factor()
        
        # Random state transitions with some memory
        if state["anomaly_state"] == "normal":
            if random.random() < 0.05:  # 5% chance to start degrading
                state["anomaly_state"] = "degrading"
                state["anomaly_duration"] = 1
        elif state["anomaly_state"] == "degrading":
            state["anomaly_duration"] += 1
            if state["anomaly_duration"] > 5 and random.random() < 0.2:
                state["anomaly_state"] = "critical"
            elif random.random() < 0.1:
                state["anomaly_state"] = "normal"
                state["anomaly_duration"] = 0
        elif state["anomaly_state"] == "critical":
            state["anomaly_duration"] += 1
            if random.random() < 0.15:  # 15% chance to start recovery
                state["anomaly_state"] = "degrading"
        
        # Adjust traffic level based on time factor and some randomness
        state["traffic_level"] = min(0.95, state["traffic_level"] * 0.8 + 0.2 * time_factor + random.uniform(-0.05, 0.05))
        
        # Calculate metrics based on state
        anomaly_factor = 1.0
        if state["anomaly_state"] == "degrading":
            anomaly_factor = 1.5
        elif state["anomaly_state"] == "critical":
            anomaly_factor = 3.0
        
        # Congestion effects
        congestion_effect = pow(state["traffic_level"], 2) * anomaly_factor
        
        # Calculate current metrics
        latency = state["baseline_latency"] * (1 + congestion_effect) + random.uniform(-5, 5)
        loss = state["baseline_loss"] * congestion_effect + random.uniform(0, 0.5)
        
        return {
            "latency_ms": max(1, latency),
            "loss": max(0, min(100, loss)),
            "state": state["anomaly_state"],
            "traffic_level": state["traffic_level"]
        }
    
    def generate_event(self):
        """Generate a transport network event based on AI forecasting"""
        # Demo mode: Periodically generate critical incidents (every 60 seconds for TRANSPORT)
        current_time = time.time()
        force_critical = (int(current_time) % 60) < 5  # 5-second window every 60 seconds
        
        if force_critical:
            # Force a critical incident on Link-1 (connects RAN to CORE) to complete the cross-domain incident
            link = "Link-1"  # Always use Link-1 for critical incidents
            
            # Set all links to critical state temporarily
            for l in self.links:
                self.link_states[l]["anomaly_state"] = "critical"
                self.link_states[l]["anomaly_duration"] = 10
                self.link_states[l]["traffic_level"] = 0.95  # Very high traffic
            
            # Override metrics for critical incident
            metrics = {
                "latency_ms": 350.0,  # Very high latency
                "loss": 25.0,  # Severe packet loss
                "state": "critical",
                "traffic_level": 0.95
            }
            
            alarm_type = "PACKET_LOSS"
            severity = "critical"  # Special severity level for demo
            
            print(f"\033[91m[DEMO] Generating CRITICAL TRANSPORT incident on {link}\033[0m")
        else:
            # Normal behavior
            # More likely to select links in worse states
            weights = {
                "normal": 1,
                "degrading": 3,
                "critical": 6
            }
            link_weights = [weights[self.link_states[link]["anomaly_state"]] for link in self.links]
            link = random.choices(self.links, weights=link_weights, k=1)[0]
            
            # Get current metrics
            metrics = self._update_link_state(link)
            
            # Determine alarm type based on metrics and state
            if metrics["loss"] > 5:
                alarm_type = "PACKET_LOSS"
            elif metrics["latency_ms"] > 100:
                alarm_type = "HIGH_LATENCY"
            elif metrics["state"] == "critical" or random.random() < 0.2:
                alarm_type = "LINK_FLAP"
            else:
                alarm_type = random.choice(["LINK_FLAP", "HIGH_LATENCY", "PACKET_LOSS"])
            
            # Severity based on state
            severity = "major" if metrics["state"] == "critical" else "minor"
        
        return {
            "vendor": self.vendor,
            "type": alarm_type,
            "link": link,
            "ts": time.time(),
            "severity": severity,
            "metrics": {"loss": metrics["loss"], "latency_ms": metrics["latency_ms"]}
        }

# Initialize the transport network monitor
ai_monitor = TransportNetworkMonitor()

def gen_alarm():
    return ai_monitor.generate_event()

if __name__ == "__main__":
    print("\033[96m[VendorC Simulator] Starting - TRANSPORT Domain\033[0m")
    count = 0
    while True:
        count += 1
        payload = gen_alarm()
        try:
            print(f"\033[96m[VendorC - Event #{count}]\033[0m {payload['type']} on {payload['link']} | Severity: {payload['severity']} | Metrics: Loss={payload['metrics']['loss']:.1f}%, Latency={payload['metrics']['latency_ms']:.1f}ms")
            response = requests.post(URL, json=payload, timeout=2)
            # Print normalized data if successful
            if response.status_code == 200:
                norm_data = response.json().get('normalized', {})
                print(f"  \033[92m→ Normalized to: Domain={norm_data.get('domain')}, Node={norm_data.get('node_id')}, Type={norm_data.get('alarm_type')}\033[0m")
        except Exception as e:
            print("\033[91mPost error:\033[0m", e)
        time.sleep(2.1)

