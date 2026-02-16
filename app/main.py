import streamlit as st
import pandas as pd
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph import app_graph

st.set_page_config(page_title="Supply Chain Copilot", page_icon="box", layout="wide")

st.title("Enterprise Supply Chain Copilot")
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
                    "logs": [],
                    "metrics": [],
                    "is_safe": True
                }
                
                result = app_graph.invoke(initial_state)
                
                # Check Security
                if not result.get("is_safe", True):
                    st.error("SECURITY ALERT: The request was blocked by the Prompt Injection Defense system.")
                    with st.expander("🛡️ Defense Logic"):
                        if "logs" in result:
                            for log in result["logs"]:
                                st.write(log['message'])
                    if "metrics" in result:
                        st.caption("Defense Metrics:")
                        st.dataframe(pd.DataFrame(result["metrics"]))

                else:
                    # 1. Trace Logs
                    st.subheader("🕵️ Agent Trace Logs")
                    if "logs" in result:
                        for log in result["logs"]:
                            agent_name = log['agent']
                            msg = str(log['message'])
                            icon = "🤖"
                            if "Defense" in agent_name: icon = "🛡️"
                            elif "Planner" in agent_name: icon = "🧠"
                            elif "Researcher" in agent_name: icon = "🔍"
                            elif "Writer" in agent_name: icon = "✍️"
                            elif "Verifier" in agent_name: icon = "⚖️"
                            
                            with st.expander(f"{icon} {agent_name}"):
                                st.markdown(msg)

                                    
                    # 2. Final Output
                    st.subheader("Final Deliverable")
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
                        
                    # 4. Observability Table
                    st.markdown("---")
                    st.subheader("📊 Observability Metrics")
                    
                    if "metrics" in result and result["metrics"]:
                        df = pd.DataFrame(result["metrics"])
                        
                        if "latency" in df.columns:
                            df["latency"] = df["latency"].apply(lambda x: f"{x:.2f}s")
                        
                        cols = ["agent", "status", "latency", "total_tokens", "input_tokens", "output_tokens"]
                        existing_cols = [c for c in cols if c in df.columns]
                        df = df[existing_cols]
                        
                        st.dataframe(df, width="stretch")
                        
                        if "input_tokens" in df.columns and "output_tokens" in df.columns:
                            total_input = df["input_tokens"].sum()
                            total_output = df["output_tokens"].sum()
                            est_cost = ((total_input / 1_000_000) * 0.50) + ((total_output / 1_000_000) * 3.00)
                            st.caption(f"Total Session Cost (Est): ${est_cost:.5f} | Total Tokens: {total_input + total_output}")

            except Exception as e:
                st.error(f"An error occurred: {e}")