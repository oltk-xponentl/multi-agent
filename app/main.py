import streamlit as st
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph import app_graph

st.set_page_config(page_title="Supply Chain Copilot", page_icon="📦", layout="wide")

st.title("📦 Enterprise Supply Chain Copilot")
st.markdown("### Multi-Agent System powered by Gemini 3 Flash & LangGraph")

with st.sidebar:
    st.header("Status")
    if os.getenv("GOOGLE_API_KEY"):
        st.success("System Online")
    else:
        st.error("API Key Missing")
    st.info(f"Model: {os.environ.get('MODEL_NAME', 'gemini-3-flash-preview')}")

user_task = st.text_area("Enter your request:", height=100)

if st.button("🚀 Run Copilot", type="primary"):
    if not user_task:
        st.warning("Please enter a task.")
    else:
        with st.spinner("Agents are working..."):
            try:
                initial_state = {
                    "task": user_task,
                    "plan": [],
                    "research_notes": [],
                    "draft": "",
                    "critique": "",
                    "revision_number": 0,
                    "max_revisions": 2,
                    "logs": []
                }
                
                result = app_graph.invoke(initial_state)
                
                # 1. Trace Logs
                st.subheader("🕵️ Agent Trace Logs")
                if "logs" in result:
                    for log in result["logs"]:
                        agent_name = log['agent']
                        msg = str(log['message'])
                                                
                        # Header
                        with st.expander(f"{agent_name}"):
                            st.markdown(msg)
                
                # 2. Final Output
                st.subheader("📄 Final Deliverable")
                draft = result.get("draft", "No draft generated.")
                if not isinstance(draft, str):
                    draft = str(draft)
                st.markdown(draft)
                
                # 3. Verification
                st.markdown("---")
                critique = result.get('critique', 'Unknown')
                if not isinstance(critique, str):
                    critique = str(critique)
                
                if "APPROVE" in critique:
                    st.success(f"Verification Status: {critique}")
                else:
                    st.warning(f"Verification Status: {critique}")
                
            except Exception as e:
                st.error(f"An error occurred: {e}")