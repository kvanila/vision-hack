import os
import time
import json
import requests
import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

# Initialize session state for critical incidents tracking
if "critical_incidents_history" not in st.session_state:
    st.session_state["critical_incidents_history"] = {
        "RAN": 0,
        "CORE": 0,
        "TRANSPORT": 0,
        "last_reset": time.time()
    }

# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------
# Constants
CORRELATION_WINDOW_SECONDS = int(os.getenv("CORRELATION_WINDOW_SECONDS", "30"))

# Get IP address instead of localhost
try:
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
except Exception:
    ip = "127.0.0.1"

BACKEND = os.getenv("BACKEND_URL", f"http://{ip}:8000")

# Configure page with more styling options
st.set_page_config(
    page_title="VISION Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        text-align: center;
    }
    .card {
        background-color: white;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 0.15rem 0.5rem rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-left: 0.3rem solid #4361ee;
        padding: 0.5rem;
        border-radius: 0.3rem;
    }
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    h1, h2, h3 {
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .card {
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        background-color: #f9f9f9;
    }
    .metric-card {
        padding: 0.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        background-color: #ffffff;
        margin-bottom: 0.5rem;
    }
    .vision-logo {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
    }
    .vision-logo-text {
        font-size: 1.8rem;
        font-weight: bold;
        margin-left: 0.5rem;
        color: #0366d6;
        letter-spacing: 1px;
    }
    .globe-icon {
        font-size: 2rem;
        color: #0366d6;
    }
</style>
""", unsafe_allow_html=True)

# Restore main header in the center
st.markdown('<div class="main-header"><h1>🌐 VISION</h1><p style="font-size:1.2em">Vendor-Independent System for Intelligent Orchestration of Networks</p></div>', unsafe_allow_html=True)

# -------------------------------------------------------------------
# INCIDENT SECTION
# -------------------------------------------------------------------
st.subheader("Incidents (Correlated)")

try:
    # Get both correlated and all incidents
    r_correlated = requests.get(f"{BACKEND}/incidents", timeout=2)
    r_all = requests.get(f"{BACKEND}/all-incidents", timeout=2)
    
    correlated_data = r_correlated.json()
    all_data = r_all.json()
    
    correlated_incidents = correlated_data.get("incidents", [])
    all_incidents = all_data.get("incidents", [])
    
    # Extract single-domain incidents by filtering out correlated ones
    correlated_ids = {inc.get("incident_id") for inc in correlated_incidents}
    single_domain_incidents = [inc for inc in all_incidents if inc.get("incident_id") not in correlated_ids]
    
    # Add VISION logo to top of sidebar
    st.sidebar.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 0.5rem; padding-bottom: 0.5rem; border-bottom: 1px solid #e6e6e6;">
        <div style="font-size: 1.5rem; color: #0366d6; margin-right: 0.5rem;">🌐</div>
        <div style="font-size: 1.2rem; font-weight: bold; color: #0366d6; letter-spacing: 1px;">VISION</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize sidebar filters early
    # Filter options
    st.sidebar.markdown("## Filters")
    vendor_filter = st.sidebar.multiselect(
        "Filter by vendor",
        ["VendorA", "VendorB", "VendorC"],
        default=["VendorA", "VendorB", "VendorC"]
    )
    domain_filter = st.sidebar.multiselect(
        "Filter by domain",
        ["RAN", "CORE", "TRANSPORT"],
        default=["RAN", "CORE", "TRANSPORT"]
    )
    
    # Enhanced metrics section with styled cards
    normalized_count = all_data.get("normalized_count", 0)
    correlated_count = all_data.get("correlated_count", 0)
    single_domain_count = all_data.get("single_domain_count", 0)
    total_count = correlated_count + single_domain_count
    
    # Network health summary based on incident count
    if total_count < 5:
        health_status = "Healthy"
        health_color = "green"
    elif total_count < 15:
        health_status = "Warning"
        health_color = "orange"
    else:
        health_status = "Critical"
        health_color = "red"
    
    # Find critical incidents if any
    critical_incidents = [inc for inc in all_incidents if inc.get("is_critical", False)]
    
    # Summary card at the top with critical incident alert if needed
    if critical_incidents:
        st.markdown('<div class="card" style="border: 2px solid red; background-color: #fff0f0;"><h3>⚠️ CRITICAL NETWORK ALERT</h3></div>', unsafe_allow_html=True)
        
        # Display critical incidents in a prominent alert box
        for i, inc in enumerate(critical_incidents):
            st.error(f"**CRITICAL INCIDENT #{i+1}**: {inc.get('probable_root_cause', 'Unknown')} on {inc.get('node_id', 'Unknown')}", icon="🚨")
            
        # Create a horizontal bar chart for critical incidents
        st.markdown("<h4>Critical Incidents by Domain</h4>", unsafe_allow_html=True)
        
        # Reset history once per day for demo purposes
        if time.time() - st.session_state["critical_incidents_history"]["last_reset"] > 86400: # 24 hours
            st.session_state["critical_incidents_history"] = {
                "RAN": 0,
                "CORE": 0,
                "TRANSPORT": 0,
                "last_reset": time.time()
            }
        
        # Manual count adjustment for demo purposes to match simulator frequencies:
        # TRANSPORT: every 60s, CORE: every 150s, RAN: every 180s
        # This gives a ratio of approximately 3:1.2:1 for TRANSPORT:CORE:RAN
        current_time = time.time()
        last_reset = st.session_state["critical_incidents_history"]["last_reset"]
        elapsed_time = current_time - last_reset
        
        # Only update counts for demo if less than 2 minutes has elapsed (initial data)
        if elapsed_time < 120 and sum(v for k, v in st.session_state["critical_incidents_history"].items() 
                                    if k != "last_reset") < 10:
            # Set simulated counts based on frequencies (they'll accumulate over time normally)
            st.session_state["critical_incidents_history"]["TRANSPORT"] = 6  # highest (every 60s)
            st.session_state["critical_incidents_history"]["CORE"] = 3      # medium (every 150s)
            st.session_state["critical_incidents_history"]["RAN"] = 2       # lowest (every 180s)
        
        # Use the accumulated history for the chart
        history = st.session_state["critical_incidents_history"]
        chart_data = {k: v for k, v in history.items() if k != "last_reset"}
        
        # If we have domain counts, display the bar chart
        if any(chart_data.values()):
            # Sort by count
            sorted_domains = sorted(chart_data.items(), key=lambda x: x[1], reverse=True)
            domains = [d[0] for d in sorted_domains]
            counts = [d[1] for d in sorted_domains]
            
            # Create a DataFrame for plotting
            df = pd.DataFrame({
                'Domain': domains,
                'Count': counts
            })
            
            # Use Plotly for a more customizable horizontal bar chart
            import plotly.express as px
            # Ensure counts are integers for display
            df['Count'] = df['Count'].astype(int)
            
            fig = px.bar(df, x='Count', y='Domain', orientation='h',
                         color='Domain', color_discrete_map={'RAN': '#FF5733', 'CORE': '#C70039', 'TRANSPORT': '#900C3F'})
            
            # Configure the chart to use integers only on x-axis
            fig.update_layout(
                height=200,
                margin=dict(l=0, r=0, t=0, b=0),
                xaxis=dict(
                    tickmode='linear',
                    tick0=0,
                    dtick=1,  # Integer ticks only
                    tickformat='d'  # Force integer format
                ),
                xaxis_title="",
                yaxis_title="",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown('<div class="card"><h3>Network Health Status</h3></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown(f"<h2 style='color: {health_color}; text-align: center;'>{health_status}</h2>", unsafe_allow_html=True)
    with col2:
        # Mini progress bars for each domain
        for domain in ["TRANSPORT", "CORE", "RAN"]:
            if domain in domain_filter:
                domain_value = all_data.get("type_counts", {}).get(domain, 0)
                st.progress(min(domain_value / max(total_count, 1), 1.0), text=domain)
            
    # Metrics in styled cards
    st.markdown('<div class="card"><h3>Incident Summary</h3></div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Normalized Events", normalized_count, help="Total number of raw events received")
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Correlated Incidents", correlated_count, help="Multi-domain incidents")
        st.markdown('</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Single-Domain Incidents", single_domain_count, help="Incidents specific to one domain")
        st.markdown('</div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total Incidents", total_count, help="Sum of correlated and single-domain incidents")
        st.markdown('</div>', unsafe_allow_html=True)

    # Enhanced tabs with styled headers
    st.markdown('<div class="card"><h3>Incident Details</h3></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📊 Correlated Incidents", "🔔 Single-Domain Incidents"])
    
    with tab1:
        if correlated_incidents:
            st.write("### Multi-Domain Correlated Incidents")
            
            # Display a summary of correlated incidents in a table
            incident_summary = []
            for inc in correlated_incidents:
                summary = {
                    "ID": inc.get("incident_id", "Unknown"),
                    "Node": inc.get("node_id", "Unknown"),
                    "Root Cause": inc.get("probable_root_cause", "Unknown"),
                    "Confidence": inc.get("confidence", 0),
                    "Domains": ", ".join(set([e.get("domain", "Unknown") for e in inc.get("supporting_events", [])])),
                    "Vendors": ", ".join(set([e.get("vendor", "Unknown") for e in inc.get("supporting_events", [])]))                
                }
                incident_summary.append(summary)
                
            st.dataframe(incident_summary)
            
            # Add expandable details for each incident
            st.write("#### Incident Details")
            for i, inc in enumerate(correlated_incidents):
                with st.expander(f"Incident {i+1}: {inc.get('incident_id')} - {inc.get('probable_root_cause')}"):
                    st.write(f"**Node ID:** {inc.get('node_id')}")
                    st.write(f"**Confidence:** {inc.get('confidence')}")
                    st.write(f"**Explanation:** {inc.get('explanation')}")
                    
                    # Show supporting events in a table
                    if inc.get("supporting_events"):
                        st.write("**Supporting Events:**")
                        events_df = []
                        for event in inc.get("supporting_events", []):
                            event_summary = {
                                "Domain": event.get("domain", "Unknown"),
                                "Vendor": event.get("vendor", "Unknown"),
                                "Node": event.get("node_id", "Unknown"),
                                "Alarm": event.get("alarm_type", "Unknown"),
                                "Severity": event.get("severity", "Unknown")
                            }
                            events_df.append(event_summary)
                        st.dataframe(events_df)
        else:
            st.info("No correlated incidents yet. Waiting for simulators to post data...")
            
    # SINGLE-DOMAIN INCIDENTS TAB
    with tab2:
        if single_domain_incidents:
            st.write("### Single-Domain Incidents")
            
            # Group by vendor and domain for better organization
            by_vendor = {}
            for inc in single_domain_incidents:
                vendor = inc.get("vendor", "Unknown")
                by_vendor.setdefault(vendor, []).append(inc)
            
            # Display incidents by vendor
            for vendor, vendor_incidents in by_vendor.items():
                with st.expander(f"{vendor} - {len(vendor_incidents)} incidents"):
                    # Summary table for this vendor's incidents
                    incident_summary = []
                    for inc in vendor_incidents:
                        summary = {
                            "ID": inc.get("incident_id", "Unknown"),
                            "Domain": inc.get("domain", "Unknown"),
                            "Node": inc.get("node_id", "Unknown"),
                            "Root Cause": inc.get("probable_root_cause", "Unknown"),
                            "Timestamp": time.strftime("%H:%M:%S", time.localtime(inc.get("timestamp", 0)))
                        }
                        incident_summary.append(summary)
                    
                    st.dataframe(incident_summary)
        else:
            st.info("No single-domain incidents yet.")
except Exception as e:
    st.error(f"Backend not available: {e}")
    st.stop()

# -------------------------------------------------------------------
# INTENT → ACTION SECTION
# -------------------------------------------------------------------
st.subheader("Intent → Action")

intent_text = st.text_input("Enter high-level network intent:")
if st.button("Translate Intent"):
    payload = {"text": intent_text}
    try:
        r = requests.post(f"{BACKEND}/translate", json=payload, timeout=5)
        st.json(r.json())
    except Exception as e:
        st.error(f"Intent translation failed: {e}")

if st.button("Simulate Execute Action"):
    # First translate the intent to get the action
    payload = {"text": intent_text}
    try:
        # First get the translated action
        r_translate = requests.post(f"{BACKEND}/translate", json=payload, timeout=5)
        action_data = r_translate.json().get("translated", {})
        
        # Then execute the action via orchestrate
        r_execute = requests.post(f"{BACKEND}/orchestrate", json={"action": action_data}, timeout=5)
        st.success("✅ Simulated orchestration executed successfully.")
        st.json(r_execute.json())
    except Exception as e:
        st.error(f"Action simulation failed: {e}")

# -------------------------------------------------------------------
# VENDOR ANALYTICS (AUTO-REFRESH)
# -------------------------------------------------------------------
st.subheader("📊 Vendor Analytics (Live)")

# Enhanced sidebar with more options
st.sidebar.markdown("## Dashboard Controls")

# Add navigation options in sidebar
page = st.sidebar.radio(
    "Navigation",
    ["Network Overview", "Settings", "Help"],
    index=0
)

st.sidebar.markdown("---")

# Analytics refresh settings
st.sidebar.markdown("## Refresh Settings")
refresh_rate = st.sidebar.slider("Auto-refresh interval (seconds)", 5, 60, 10)

# Visualization options
st.sidebar.markdown("## Visualization Options")
show_percentages = st.sidebar.checkbox("Show percentages in charts", value=True)
show_single_domain = st.sidebar.checkbox("Include single-domain incidents in analytics", value=True)
dark_theme = st.sidebar.checkbox("Dark theme charts", value=False)

# Rest of sidebar options - filters are defined earlier

st.sidebar.markdown("---")
st.sidebar.info("VISION Demo v1.0")
placeholder = st.empty()

def load_analytics():
    try:
        r = requests.get(f"{BACKEND}/analytics", timeout=2)
        if r.status_code != 200:
            st.warning("Analytics endpoint returned non-200 response.")
            return None
        return r.json()
    except Exception as e:
        st.error(f"Analytics not available: {e}")
        return None

# Auto-refreshing section
for _ in range(10000):  # Run effectively "forever" until stopped
    with placeholder.container():
        analytics = load_analytics()
        if analytics:
            # Advanced analytics section with more visualizations
            st.markdown('<div class="card"><h3>Network Analytics</h3></div>', unsafe_allow_html=True)
            
            # First row - key metrics and summary stats
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                st.metric("Total Incidents", analytics.get("total_incidents", 0))
                st.metric("Network Health", analytics.get("network_health", "Unknown"))
                
            with col2:
                # Time-based metrics
                now = time.time()
                recent_cutoff = now - 60  # Last minute
                
                # Count incidents in the last minute
                recent_incidents = sum(1 for inc in correlated_incidents if inc.get("timestamp", 0) > recent_cutoff)
                
                st.metric("Incidents (Last Min)", recent_incidents)
                
                # Calculate rate of incidents per minute
                if normalized_count > 0:
                    event_rate = round(normalized_count / (CORRELATION_WINDOW_SECONDS/60), 1)
                    st.metric("Events/Minute", event_rate)
            
            with col3:
                # Mini time series chart - simulated for demo
                timestamps = list(range(10))
                values = [analytics.get("total_incidents", 5) - i for i in range(10)]
                time_data = {"Time (min ago)": timestamps, "Incidents": values}
                st.markdown("**Incident Trend (Last 10 Minutes)**")
                st.line_chart(time_data)
            
            # Second row - tabs with analytics
            tab1, tab2, tab3 = st.tabs(["📊 Vendor Analytics", "🔌 Domain Analytics", "🔍 Advanced Stats"])
            
            with tab1:
                col1, col2 = st.columns([3, 2])
                with col1:
                    st.markdown("**Incidents by Vendor**")
                    # Filter vendor data based on sidebar selections
                    vendor_data = {k: v for k, v in analytics.get("vendor_counts", {}).items() 
                                  if k in vendor_filter}
                    if vendor_data:
                        # Use custom color for dark theme if enabled
                        chart_color = "#333" if dark_theme else "#0068c9"
                        st.bar_chart(vendor_data, width=400, height=250)
                
                with col2:
                    if show_percentages and vendor_data:
                        st.markdown("**Vendor Distribution**")
                        # Calculate percentages for the distribution
                        total = sum(vendor_data.values())
                        vendor_percentages = {k: v/total*100 for k, v in vendor_data.items()}
                        
                        # Create a more visual representation
                        for vendor, percentage in vendor_percentages.items():
                            st.markdown(f"**{vendor}:** {percentage:.1f}%")
                            st.progress(percentage/100)
            
            with tab2:
                col1, col2 = st.columns([3, 2])
                with col1:
                    st.markdown("**Incidents by Domain**")
                    # Filter domain data based on sidebar selections
                    domain_data = {k: v for k, v in analytics.get("type_counts", {}).items() 
                                  if k in domain_filter}
                    if domain_data:
                        st.bar_chart(domain_data, width=400, height=250)
                
                with col2:
                    if show_percentages and domain_data:
                        st.markdown("**Domain Distribution**")
                        total = sum(domain_data.values())
                        domain_percentages = {k: v/total*100 for k, v in domain_data.items()}
                        
                        # Create a more visual representation
                        for domain, percentage in domain_percentages.items():
                            st.markdown(f"**{domain}:** {percentage:.1f}%")
                            st.progress(percentage/100)
            
            with tab3:
                # Add more advanced analytics
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Incident Severity Distribution**")
                    # Simulate severity data with different terminology to avoid confusion
                    severity_data = {"High": 3, "Medium": 6, "Low": 10}
                    st.bar_chart(severity_data)
                    
                with col2:
                    st.markdown("**Mean Time Between Failures**")
                    # Simulate MTBF data
                    if total_count > 0:
                        mtbf = round(CORRELATION_WINDOW_SECONDS / max(total_count, 1), 1)
                        st.metric("MTBF (seconds)", mtbf)
        else:
            st.info("No analytics data yet. Waiting for incidents...")

    time.sleep(refresh_rate)
