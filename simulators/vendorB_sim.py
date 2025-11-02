# simulators/vendorB_sim.py
import time, json, requests, random, os
BACKEND = os.getenv("BACKEND_URL", "http://localhost:8000")
URL = f"{BACKEND}/normalize"

# Simulated AI-based anomaly detection for Core Network
class CoreNetworkAnomalyDetector:
    def __init__(self, vendor="VendorB"):
        self.vendor = vendor
        self.model_type = self._initialize_models()
        self.cores = [f"Core-{i}" for i in range(1, 3)]
        
        # Simulated time-series baseline for each core
        self.core_states = {core: {
            "cpu_baseline": random.uniform(30, 50),  # normal CPU usage
            "session_health": random.uniform(0.9, 1.0),  # session health score (1.0 = perfect)
            "auth_success_rate": random.uniform(0.95, 0.99),  # auth success rate 
            "anomaly_score": 0.0,  # current anomaly score from 0-1
            "incident_in_progress": False,  # if there's an ongoing incident
            "incident_type": None,  # current incident type if any
            "incident_duration": 0  # how long the incident has been happening
        } for core in self.cores}
        
        # Synthetic attack patterns (would be learned from data in a real system)
        self.attack_patterns = [
            {"cpu": 0.3, "session": -0.4, "auth": -0.6},  # auth attack pattern 
            {"cpu": 0.7, "session": -0.3, "auth": -0.1},  # cpu spike pattern
            {"cpu": 0.2, "session": -0.8, "auth": -0.3}   # session drop pattern
        ]
    
    def _initialize_models(self):
        """Simulate loading ML models for anomaly detection"""
        print(f"\033[95m[AI] Loading CORE anomaly detection models...\033[0m")
        return {
            "time_series": "Prophet",
            "anomaly_detector": "LSTM-Autoencoder",
            "classification": "Random Forest"
        }
    
    def _update_core_state(self, core_id):
        """Simulate the evolution of core state over time"""
        state = self.core_states[core_id]
        
        # Decide if we should start/continue/end an incident
        if state["incident_in_progress"]:
            # Incident in progress - decide whether to continue or end
            state["incident_duration"] += 1
            
            # 20% chance to end the incident on each iteration if it's been happening a while
            if state["incident_duration"] > 3 and random.random() < 0.2:
                state["incident_in_progress"] = False
                state["incident_type"] = None
                state["anomaly_score"] *= 0.5  # reduce anomaly score
                
                # Start returning to baseline
                state["cpu_baseline"] = max(30, min(50, state["cpu_baseline"] * 0.9))
                state["session_health"] = min(1.0, state["session_health"] * 1.1)
                state["auth_success_rate"] = min(0.99, state["auth_success_rate"] * 1.05)
        else:
            # No incident - small chance to start one
            if random.random() < 0.1:  # 10% chance of new incident
                state["incident_in_progress"] = True
                state["incident_type"] = random.choice(["AUTH_FAIL", "SESSION_DROP", "HIGH_CPU"])
                state["incident_duration"] = 1
                state["anomaly_score"] = random.uniform(0.6, 0.9)  # significant anomaly
                
                # Apply the corresponding attack pattern
                if state["incident_type"] == "AUTH_FAIL":
                    pattern = self.attack_patterns[0]
                elif state["incident_type"] == "HIGH_CPU":
                    pattern = self.attack_patterns[1]
                else:  # SESSION_DROP
                    pattern = self.attack_patterns[2]
                
                # Apply the pattern effects
                state["cpu_baseline"] *= (1 + pattern["cpu"])
                state["session_health"] *= (1 + pattern["session"])
                state["auth_success_rate"] *= (1 + pattern["auth"])
        
        # Add some noise to all metrics
        cpu = state["cpu_baseline"] + random.uniform(-5, 5)
        cpu = max(5, min(100, cpu))  # bound between 5-100%
        
        # Return current metrics with some randomness
        return {
            "cpu": cpu,
            "session_health": state["session_health"] + random.uniform(-0.05, 0.05),
            "auth_rate": state["auth_success_rate"] + random.uniform(-0.02, 0.02),
            "anomaly_score": state["anomaly_score"],
            "incident_type": state["incident_type"]
        }
    
    def generate_event(self):
        """Generate a core network event based on simulated ML anomaly detection"""
        # Demo mode: Periodically generate critical incidents (every 150 seconds for CORE)
        current_time = time.time()
        force_critical = (int(current_time) % 150) < 5  # 5-second window every 150 seconds
        
        if force_critical:
            # Force a critical incident on Core-1 (matching Cell-1 from VendorA)
            core = "Core-1"  # Use Core-1 for critical incidents
            
            # Set critical state for demo
            for c in self.cores:
                self.core_states[c]["incident_in_progress"] = True
                self.core_states[c]["incident_type"] = "SESSION_DROP"
                self.core_states[c]["anomaly_score"] = 0.95
                self.core_states[c]["incident_duration"] = 5
            
            # Critical core metrics
            metrics = {
                "cpu": 98.5,  # Nearly maxed out CPU
                "session_health": 0.1,  # Very poor session health
                "auth_rate": 0.3,  # Authentication failures
                "anomaly_score": 0.95,
                "incident_type": "SESSION_DROP"
            }
            
            alarm_type = "SESSION_DROP"
            level = "critical"  # Special severity for demo
            
            print(f"\033[91m[DEMO] Generating CRITICAL CORE incident on {core}\033[0m")
        else:
            # Normal behavior
            # Favor cores with incidents in progress
            weights = [5 if self.core_states[c]["incident_in_progress"] else 1 for c in self.cores]
            core = random.choices(self.cores, weights=weights, k=1)[0]
            
            # Get current metrics
            metrics = self._update_core_state(core)
            
            # Determine alarm type
            if metrics["incident_type"]:
                alarm_type = metrics["incident_type"]
            else:
                # If no incident but metrics look concerning, maybe generate an alarm
                if metrics["cpu"] > 70:
                    alarm_type = "HIGH_CPU"
                elif metrics["session_health"] < 0.7:
                    alarm_type = "SESSION_DROP"
                elif metrics["auth_rate"] < 0.8:
                    alarm_type = "AUTH_FAIL"
                else:
                    alarm_type = random.choice(["AUTH_FAIL", "SESSION_DROP", "HIGH_CPU"])
            
            # Severity based on anomaly score
            if metrics["anomaly_score"] > 0.7:
                level = "major"
            else:
                level = "minor"
        
        return {
            "vendor": self.vendor,
            "alarm": alarm_type,
            "core_id": core,
            "time": time.time(),
            "level": level,
            "metrics": {"cpu": metrics["cpu"]}
        }

# Initialize AI detector
ai_detector = CoreNetworkAnomalyDetector()

def gen_alarm():
    return ai_detector.generate_event()

if __name__ == "__main__":
    print("\033[95m[VendorB Simulator] Starting - CORE Domain\033[0m")
    count = 0
    while True:
        count += 1
        payload = gen_alarm()
        try:
            print(f"\033[95m[VendorB - Event #{count}]\033[0m {payload['alarm']} on {payload['core_id']} | Level: {payload['level']} | Metrics: CPU={payload['metrics']['cpu']:.1f}%")
            response = requests.post(URL, json=payload, timeout=2)
            # Print normalized data if successful
            if response.status_code == 200:
                norm_data = response.json().get('normalized', {})
                print(f"  \033[92m→ Normalized to: Domain={norm_data.get('domain')}, Node={norm_data.get('node_id')}, Type={norm_data.get('alarm_type')}\033[0m")
        except Exception as e:
            print("\033[91mPost error:\033[0m", e)
        time.sleep(1.8)

