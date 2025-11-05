#!/usr/bin/env python3
"""Streamlit UI for ServiceNow smoke test.

This demonstrates the hibernation retry with exponential backoff using Streamlit widgets.
The pacifier automatically uses Streamlit spinner when available!

Usage:
    streamlit run examples/streamlit_smoke_test.py
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import streamlit as st
except ImportError:
    print("Streamlit not installed. Install with: pip install streamlit")
    sys.exit(1)

from beast_dream_snow_loader.models.servicenow import ServiceNowGatewayCI
from beast_dream_snow_loader.servicenow.api_client import ServiceNowAPIClient
from beast_dream_snow_loader.servicenow.loader import load_gateway_ci

st.set_page_config(page_title="ServiceNow Smoke Test", page_icon="🚀")

st.title("🚀 ServiceNow Smoke Test")
st.markdown("Test ServiceNow connection with automatic hibernation handling")

# Credentials input
with st.expander("🔐 ServiceNow Credentials", expanded=False):
    instance = st.text_input(
        "Instance",
        value=st.session_state.get("instance", ""),
        placeholder="dev12345.service-now.com",
        help="ServiceNow instance URL (without https://)",
    )
    username = st.text_input(
        "Username",
        value=st.session_state.get("username", ""),
        type="default",
        help="ServiceNow username",
    )
    password = st.text_input(
        "Password",
        value=st.session_state.get("password", ""),
        type="password",
        help="ServiceNow password or API key",
    )

    # Store in session state
    if instance:
        st.session_state.instance = instance
    if username:
        st.session_state.username = username
    if password:
        st.session_state.password = password

# Run smoke test button
if st.button("🧪 Run Smoke Test", type="primary"):
    if not instance or not username or not password:
        st.error("Please fill in all credential fields")
        st.stop()

    # Set environment variables for the API client
    import os

    os.environ["SERVICENOW_INSTANCE"] = instance
    os.environ["SERVICENOW_USERNAME"] = username
    os.environ["SERVICENOW_PASSWORD"] = password

    try:
        # Initialize API client (this will show Streamlit spinner if hibernating!)
        with st.spinner("Initializing ServiceNow API client..."):
            client = ServiceNowAPIClient()

        st.success(f"✓ Connected to instance: {client.instance}")

        # Create test gateway CI
        with st.spinner("Creating test gateway CI record..."):
            test_gateway = ServiceNowGatewayCI(
                u_unifi_source_id="smoke_test_gateway_001",
                name="Smoke Test Gateway",
                ip_address="192.168.1.1",
                hostname="smoke-test-gateway.example.com",
                firmware_version="1.0.0",
            )

            try:
                result = load_gateway_ci(client, test_gateway)
            except Exception as e:
                if "Invalid table" in str(e):
                    st.warning(
                        "⚠️ Specific table not available, using base cmdb_ci table..."
                    )
                    # Fallback to base cmdb_ci table
                    test_data = {
                        "sys_class_name": "cmdb_ci",
                        "u_unifi_source_id": "smoke_test_gateway_001",
                        "name": "Smoke Test Gateway",
                        "ip_address": "192.168.1.1",
                        "hostname": "smoke-test-gateway.example.com",
                    }
                    result = client.create_record("cmdb_ci", test_data)
                else:
                    raise

        st.success("✅ Smoke test PASSED!")
        st.json(result)

    except ValueError as e:
        st.error(f"❌ Configuration Error: {e}")
        st.info(
            "Please set environment variables or use the form above:\n\n"
            "- SERVICENOW_INSTANCE\n"
            "- SERVICENOW_USERNAME\n"
            "- SERVICENOW_PASSWORD or SERVICENOW_API_KEY"
        )
    except Exception as e:
        st.error(f"❌ Smoke test FAILED: {e}")
        st.exception(e)
