# backend/app.py
import time
import threading
from collections import defaultdict
from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn
import requests
import os

app = FastAPI()

# In-memory storage (simple for demo)
normalized_events: List[Dict[str, Any]] = []
incidents: List[Dict[str, Any]] = [] # Correlated incidents (multi-domain)
single_domain_incidents: List[Dict[str, Any]] = [] # Non-correlated incidents (single-domain)

# Config
CORRELATION_WINDOW_SECONDS = int(os.getenv("CORRELATION_WINDOW_SECONDS", "30"))
CONFIDENCE_BASE = 0.7

def map_to_canonical(payload: Dict[str, Any]) -> Dict[str, Any]:
    v = payload.get("vendor", "unknown")
    # Very small sample mappings - expand as needed
    if v == "VendorA":
        return {
            "timestamp": payload.get("ts", time.time()),
            "vendor": v,
            "domain": "RAN",
            "node_id": payload.get("cell") or payload.get("node"),
            "alarm_type": payload.get("desc"),
            "severity": payload.get("severity", "major"),
            "metrics": payload.get("metrics", {})
        }
    if v == "VendorB":
        return {
            "timestamp": payload.get("time", time.time()),
            "vendor": v,
            "domain": "CORE",
            "node_id": payload.get("core_id"),
            "alarm_type": payload.get("alarm"),
            "severity": payload.get("level", "minor"),
            "metrics": payload.get("metrics", {})
        }
    if v == "VendorC":
        return {
            "timestamp": payload.get("ts", time.time()),
            "vendor": v,
            "domain": "TRANSPORT",
            "node_id": payload.get("link") or payload.get("node"),
            "alarm_type": payload.get("type"),
            "severity": payload.get("severity", "minor"),
            "metrics": payload.get("metrics", {})
        }
    # Default fallback
    return {
        "timestamp": payload.get("ts", time.time()),
        "vendor": v,
        "domain": payload.get("domain", "UNKNOWN"),
        "node_id": payload.get("node_id", "unknown"),
        "alarm_type": payload.get("alarm_type", "unknown"),
        "severity": payload.get("severity", "minor"),
        "metrics": payload.get("metrics", {})
    }

@app.post("/normalize")
async def normalize(req: Request):
    payload = await req.json()
    norm = map_to_canonical(payload)
    # add to normalized storage
    normalized_events.append(norm)
    # forward to correlator endpoint (internal function)
    _process_for_correlation(norm)
    return {"status": "ok", "normalized": norm}

def _process_for_correlation(event: Dict[str, Any]):
    global incidents, single_domain_incidents
    
    # Simulated AI-based correlation engine
    # In a production system, this would use a trained ML model to:
    # 1. Calculate correlation probabilities between events
    # 2. Use historical patterns to identify anomalies
    # 3. Apply transformer-based sequence modeling for temporal patterns
    
    # Append and run the correlation algorithms
    now = time.time()
    # Clean old events beyond window (part of the time-series preprocessing)
    cutoff = now - CORRELATION_WINDOW_SECONDS
    
    # Clean up normalized events
    while normalized_events and normalized_events[0]["timestamp"] < cutoff:
        normalized_events.pop(0)
    
    # Clean up old incidents (both correlated and single-domain)
    old_incident_cutoff = now - (CORRELATION_WINDOW_SECONDS * 2)  # Keep incidents a bit longer
    incidents = [inc for inc in incidents if inc.get("timestamp", 0) > old_incident_cutoff]
    single_domain_incidents = [inc for inc in single_domain_incidents if inc.get("timestamp", 0) > old_incident_cutoff]
    
    # Limit number of incidents to avoid memory issues
    if len(incidents) > 50:
        incidents.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        incidents = incidents[:50]  # Keep only the 50 most recent
    
    if len(single_domain_incidents) > 100:
        single_domain_incidents.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        single_domain_incidents = single_domain_incidents[:100]  # Keep only the 100 most recent
    # Try to detect incidents based on the following rules:
    # 1. Group events by node_id first (like Cell-1, Link-2, etc.)
    # 2. If events from multiple domains affect the same node_id, create a node-specific incident
    # 3. If we see patterns across domains even with different node_ids, create cross-domain incidents
    
    # First, group by node_id
    node_grouped = {}
    for e in normalized_events:
        node_id = e.get("node_id", "unknown")
        if node_id != "unknown":
            node_grouped.setdefault(node_id, []).append(e)
    
    # Then, group by domain to ensure we get cross-domain incidents
    domains_grouped = {}
    for e in normalized_events:
        domain = e.get("domain", "UNKNOWN")
        domains_grouped.setdefault(domain, []).append(e)
    
    # Process both correlated and non-correlated incidents
    
    # 1. Create correlated incidents for node-specific issues (multi-domain)
    grouped = {}
    for node_id, events in node_grouped.items():
        # Get distinct domains for this node
        domains = set([e.get("domain", "UNKNOWN") for e in events])
        
        if len(domains) >= 2:
            # Multi-domain incident
            key = f"node-{node_id}"
            grouped[key] = []
            # Get the most recent event from each domain for this node
            for domain in domains:
                domain_events = [e for e in events if e.get("domain", "UNKNOWN") == domain]
                if domain_events:
                    # Sort by timestamp and take the most recent
                    most_recent = max(domain_events, key=lambda x: x.get("timestamp", 0))
                    grouped[key].append(most_recent)
        else:
            # Single-domain incident
            for e in events:
                process_single_domain_incident(e)
    
    # Also create a general cross-domain incident if multiple domains have issues
    if len(domains_grouped.keys()) >= 2:
        # Use a timestamp-based key to allow multiple cross-domain incidents over time
        timestamp = int(time.time())
        key = f"cross-domain-{timestamp % 100}"  # Use modulo to limit the number of such incidents
        grouped[key] = []
        for domain_events in domains_grouped.values():
            # Take the most recent event from each domain
            if domain_events:
                most_recent = max(domain_events, key=lambda x: x.get("timestamp", 0))
                grouped[key].append(most_recent)

    new_incidents = []
    for key, events in grouped.items():
        # require at least 2 events and at least 2 distinct vendors/domains
        vendors = set([ev.get("vendor") for ev in events])
        domains = set([ev.get("domain") for ev in events])
        if len(events) >= 2 and len(domains) >= 2:
            # Simulated AI root cause analysis
            # In production, this would use a causal inference model to determine
            # the most likely root cause based on event sequences and topology knowledge
            
            # Calculate confidence score using our "AI model"
            # Features that would go into a real ML model:
            domain_weights = {"RAN": 0.7, "TRANSPORT": 0.8, "CORE": 0.9}
            severity_factor = sum(1.2 if e.get("severity") == "major" else 0.8 for e in events) / len(events)
            temporal_proximity = 1.0 - (max(e.get("timestamp", 0) for e in events) - 
                                   min(e.get("timestamp", 0) for e in events)) / CORRELATION_WINDOW_SECONDS
            
            # Root cause determination using domain knowledge
            if "TRANSPORT" in domains and ("RAN" in domains or "CORE" in domains):
                probable_rc = "Cross-domain congestion in transport layer"
            elif "RAN" in domains and "CORE" in domains:
                probable_rc = "End-to-end connectivity issue"
            else:
                probable_rc = "Domain-specific degradation"
                
            # Check for any critical events
            has_critical = any(e.get("severity", "").lower() == "critical" for e in events)
            
            # "AI-generated" confidence score - boosted for critical events
            confidence = min(0.99, CONFIDENCE_BASE + 
                         0.1 * len(events) + 
                         0.05 * len(domains) +
                         0.1 * severity_factor +
                         0.1 * temporal_proximity +
                         (0.3 if has_critical else 0))  # Major boost for critical events
            
            # Special handling for critical incidents
            if has_critical:
                probable_rc = "CRITICAL: " + probable_rc
                explanation = f"CRITICAL ALERT: {len(events)} correlated events across domains {list(domains)}"
            else:
                explanation = f"{len(events)} correlated events across domains {list(domains)}"
                
            incident = {
                "incident_id": f"INC-{key}-{int(time.time())}",
                "node_id": key,
                "probable_root_cause": probable_rc,
                "supporting_events": events.copy(),
                "confidence": round(min(confidence, 0.99), 2),
                "explanation": explanation,
                "timestamp": time.time(),
                "is_critical": has_critical  # Flag for critical incidents
            }
            # To avoid duplicates, remove older ones for same node_id
            # (simple approach: replace any existing with same node_id)
            # remove previous incidents with same node_id
            incidents = [inc for inc in incidents if inc.get("node_id") != key]
            incidents.append(incident)
            new_incidents.append(incident)
    # store incidents back to memory
    # done above
    return new_incidents

@app.get("/incidents")
async def get_incidents():
    # Return incidents sorted by timestamp desc
    sorted_inc = sorted(incidents, key=lambda x: x["timestamp"], reverse=True)
    
    # Count unique events in the incidents
    event_ids = set()
    for inc in sorted_inc:
        for evt in inc.get("supporting_events", []):
            if "timestamp" in evt and "vendor" in evt and "node_id" in evt:
                event_id = f"{evt['vendor']}-{evt['node_id']}-{evt['timestamp']}"
                event_ids.add(event_id)
    
    # Make sure normalized_count is at least equal to incident count
    event_count = max(len(normalized_events), len(event_ids), len(incidents))
    
    return {
        "incidents": sorted_inc, 
        "normalized_count": event_count,
        "incident_count": len(incidents)
    }

@app.get("/all-incidents")
async def get_all_incidents():
    # Return both correlated and single-domain incidents
    all_inc = incidents + single_domain_incidents
    sorted_all = sorted(all_inc, key=lambda x: x["timestamp"], reverse=True)
    
    # Count the actual normalized events used to create incidents (for accurate counting)
    event_ids = set()
    for inc in all_inc:
        for evt in inc.get("supporting_events", []):
            # Use a combination of fields to uniquely identify events
            if "timestamp" in evt and "vendor" in evt and "node_id" in evt:
                event_id = f"{evt['vendor']}-{evt['node_id']}-{evt['timestamp']}"
                event_ids.add(event_id)
    
    # Make sure normalized_count is never less than the count of incidents
    event_count = max(len(normalized_events), len(event_ids), len(incidents) + len(single_domain_incidents))
    
    return {
        "incidents": sorted_all, 
        "normalized_count": event_count,  # Use the calculated count
        "correlated_count": len(incidents), 
        "single_domain_count": len(single_domain_incidents),
        "total_incident_count": len(incidents) + len(single_domain_incidents)
    }

class IntentRequest(BaseModel):
    text: str

@app.post("/translate")
async def translate_intent(req: IntentRequest):
    text = req.text.lower()
    
    # Simulated AI-based NLP intent recognition
    # In production, this would use:
    # 1. A fine-tuned LLM for intent classification
    # 2. Named entity recognition for parameters
    # 3. Context-aware parameter extraction
    
    # Simulate NLP intent classification confidence scores
    intent_scores = {
        "create_slice": 0.0,
        "reroute_traffic": 0.0,
        "scale_service": 0.0,
        "unknown": 0.1  # base probability for unknown intent
    }
    
    # Simulated semantic matching (in production: embedding similarity or transformer attention)
    if "latency" in text:
        intent_scores["create_slice"] += 0.4
        if "low" in text:
            intent_scores["create_slice"] += 0.4
        if "slice" in text:
            intent_scores["create_slice"] += 0.2
    
    if "reroute" in text or "divert" in text:
        intent_scores["reroute_traffic"] += 0.5
        if "traffic" in text:
            intent_scores["reroute_traffic"] += 0.3
        if "avoid" in text or "around" in text:
            intent_scores["reroute_traffic"] += 0.2
    
    if "scale" in text or "increase" in text or "more" in text:
        intent_scores["scale_service"] += 0.3
        if "capacity" in text or "resources" in text:
            intent_scores["scale_service"] += 0.2
        if "up" in text:
            intent_scores["scale_service"] += 0.3
    
    # Get highest scoring intent
    intent = max(intent_scores.items(), key=lambda x: x[1])
    intent_name, confidence = intent
    
    # Parameter extraction (simulating NER)
    extracted_params = {}
    explanation = ""
    
    if intent_name == "create_slice":
        # Simulate parameter extraction
        slice_type = "default"
        priority = "medium"
        latency_target = 50
        
        if "gaming" in text or "real-time" in text or "realtime" in text:
            slice_type = "ultra_low_latency"
            latency_target = 5
        elif "low" in text and "latency" in text:
            slice_type = "low_latency"
            latency_target = 10
        elif "high" in text and "bandwidth" in text:
            slice_type = "high_bandwidth"
        
        if "high" in text and "priority" in text:
            priority = "high"
        elif "critical" in text or "emergency" in text:
            priority = "critical"
        
        action = {
            "action": "create_slice",
            "slice_type": slice_type,
            "params": {
                "priority": priority,
                "latency_target_ms": latency_target
            },
            "simulation": True
        }
        explanation = f"AI interpreted intent as 'create_slice' ({confidence:.2f} confidence)" + \
                     f": Creating {slice_type} slice with {priority} priority and {latency_target}ms target"
    
    elif intent_name == "reroute_traffic":
        # Extract node to avoid using simulated NER
        node = "Node-1"  # default
        for word in text.split():
            if word.startswith("node") or word.startswith("cell") or word.startswith("link"):
                node = word
                break
        
        action = {
            "action": "reroute_traffic",
            "params": {"avoid_node": node},
            "simulation": True
        }
        explanation = f"AI interpreted intent as 'reroute_traffic' ({confidence:.2f} confidence)" + \
                     f": Rerouting traffic to avoid {node}"
    
    elif intent_name == "scale_service":
        # Extract parameters
        scale_direction = "up" if any(w in text for w in ["up", "increase", "more"]) else "down"
        amount = 50  # default percentage
        
        # Look for percentage or numeric values
        for i, word in enumerate(text.split()):
            if word.endswith("%") and i > 0:
                try:
                    amount = int(text.split()[i-1])
                except:
                    pass
        
        action = {
            "action": "scale_service",
            "params": {"scale": scale_direction, "amount": amount},
            "simulation": True
        }
        explanation = f"AI interpreted intent as 'scale_service' ({confidence:.2f} confidence)" + \
                     f": Scaling {scale_direction} resources by {amount}%"
    
    else:  # Unknown intent
        action = {"action": "unknown", "raw_text": text}
        explanation = "AI could not determine a clear intent. Please provide more details."
    
    return {"translated": action, "explanation": explanation, "intent_scores": intent_scores}

class OrchestrateRequest(BaseModel):
    action: Dict[str, Any]

@app.post("/orchestrate")
async def orchestrate(req: OrchestrateRequest):
    # Simulate execution and return simulated result
    action = req.action
    result = {
        "status": "simulated",
        "action": action,
        "result_details": f"Simulated execution at {time.time()}"
    }
    # Log as a normalized event for demo purposes (simulate effect)
    normalized_events.append({
        "timestamp": time.time(),
        "vendor": "VISION",
        "domain": "ORCHESTRATOR",
        "node_id": action.get("params", {}).get("target", "orchestrator"),
        "alarm_type": f"ORCH_{action.get('action')}",
        "severity": "info",
        "metrics": {}
    })
    return result

@app.get("/analytics")
def get_analytics():
    """
    Simple analytics endpoint:
    - Counts incidents per vendor
    - Counts incidents per type
    - Provides a quick health summary
    """
    # If correlation data isn't initialized, just return empty analytics
    global incidents
    if not incidents:
        return {
            "vendor_counts": {},
            "type_counts": {},
            "total_incidents": 0,
            "network_health": "Unknown"
        }

    vendor_counts = {}
    type_counts = {}

    # Process both correlated and single-domain incidents for analytics
    all_incidents = incidents + single_domain_incidents
    
    # Loop through all incidents (both correlated and single-domain)
    for inc in all_incidents:
        # Get vendors and domains from supporting events
        inc_vendors = set()
        inc_domains = set()
        
        for event in inc.get("supporting_events", []):
            vendor = event.get("vendor", "Unknown")
            domain = event.get("domain", "Unknown")
            inc_vendors.add(vendor)
            inc_domains.add(domain)
        
        # Count each vendor and domain once per incident
        for vendor in inc_vendors:
            vendor_counts[vendor] = vendor_counts.get(vendor, 0) + 1
        for domain in inc_domains:
            type_counts[domain] = type_counts.get(domain, 0) + 1
    
    # Count total incidents
    total_incidents = len(all_incidents)
    health = "Healthy" if total_incidents < 5 else "Warning" if total_incidents < 15 else "Critical"

    return {
        "vendor_counts": dict(vendor_counts),
        "type_counts": dict(type_counts),
        "total_incidents": total_incidents,
        "network_health": health
    }

def process_single_domain_incident(event: Dict[str, Any]):
    """Process a single domain event and create non-correlated incidents"""
    global single_domain_incidents
    
    # Extract key information
    vendor = event.get("vendor", "Unknown")
    domain = event.get("domain", "Unknown")
    node_id = event.get("node_id", "unknown")
    alarm_type = event.get("alarm_type", "unknown")
    timestamp = event.get("timestamp", time.time())
    
    # Create a unique ID for the incident
    incident_id = f"INC-{vendor}-{node_id}-{int(timestamp)}"
    
    # Check if we already have a recent incident for this vendor+node
    recent_cutoff = timestamp - 60  # Don't create duplicates within 60 seconds
    for inc in single_domain_incidents:
        if (inc.get("vendor") == vendor and 
            inc.get("node_id") == node_id and 
            inc.get("timestamp", 0) > recent_cutoff):
            # Update existing incident
            inc["supporting_events"] = [event]  # Replace with latest event
            inc["timestamp"] = timestamp
            inc["explanation"] = f"Updated {domain} issue on {node_id}"
            return
    
    # Check if this is a critical severity event
    is_critical = event.get("severity", "").lower() == "critical"
    
    # Adjust confidence and message based on severity
    confidence = 0.85 if is_critical else 0.6
    
    # Create root cause and explanation with critical prefix if needed
    root_cause = f"{domain} issue: {alarm_type}"
    explanation = f"Single {domain} issue on {node_id}"
    
    if is_critical:
        root_cause = f"CRITICAL: {root_cause}"
        explanation = f"CRITICAL ALERT: {explanation}"
    
    # Create a new single-domain incident
    incident = {
        "incident_id": incident_id,
        "vendor": vendor,
        "domain": domain,
        "node_id": node_id,
        "is_correlated": False,  # Flag to identify single-domain incidents
        "probable_root_cause": root_cause,
        "supporting_events": [event],
        "confidence": confidence,
        "explanation": explanation,
        "timestamp": timestamp,
        "is_critical": is_critical  # Flag for critical incidents
    }
    
    # Add to single-domain incidents list
    single_domain_incidents.append(incident)
    
    # Note: We don't need to limit single_domain_incidents here as it's done in _process_for_correlation

if __name__ == "__main__":
    uvicorn.run("backend.app:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)

