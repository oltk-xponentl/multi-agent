import sys
import os
import pandas as pd
import time
from dotenv import load_dotenv

# Add parent directory to path so we can import 'graph'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph import app_graph

# Load environment variables
load_dotenv()

def run_evaluation():
    print("--- Starting Batch Evaluation ---")
    
    questions_file = os.path.join(os.path.dirname(__file__), "test_questions.txt")
    output_file = os.path.join(os.path.dirname(__file__), "eval_results.csv")
    
    if not os.path.exists(questions_file):
        print(f"Error: {questions_file} not found.")
        return

    with open(questions_file, "r") as f:
        questions = [line.strip() for line in f.readlines() if line.strip()]

    results = []

    for i, question in enumerate(questions):
        clean_q = question
        if question[0].isdigit() and ". " in question:
            clean_q = question.split(". ", 1)[1]
            
        print(f"\n[{i+1}/{len(questions)}] Processing: {clean_q[:50]}...")
        
        start_time = time.time()
        
        # State tracking variables
        captured_draft = ""
        captured_critique = "N/A"
        is_safe = True
        total_tokens = 0
        
        try:
            initial_state = {
                "task": clean_q,
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
            
            # Stream execution
            for output in app_graph.stream(initial_state):
                for node_name, state_update in output.items():
                    print(f"  -> Finished: {node_name}")
                    
                    # Capture Safety
                    if "is_safe" in state_update:
                        is_safe = state_update["is_safe"]
                        
                    # Capture Draft (Persist it even if next node doesn't have it)
                    if "draft" in state_update and state_update["draft"]:
                        captured_draft = state_update["draft"]
                        
                    # Capture Critique
                    if "critique" in state_update:
                        captured_critique = state_update["critique"]
                        
                    # Aggregate Tokens
                    if "metrics" in state_update:
                        for m in state_update["metrics"]:
                            total_tokens += m.get("total_tokens", 0)
            
            end_time = time.time()
            
            results.append({
                "Question": clean_q,
                "Status": "Success" if is_safe else "Blocked",
                "Verifier Output": captured_critique,
                "Latency (s)": round(end_time - start_time, 2),
                "Total Tokens": total_tokens,
                "Draft Length": len(captured_draft),
                "Draft Preview": captured_draft[:100].replace("\n", " ") + "..." if captured_draft else "N/A"
            })

        except Exception as e:
            print(f"  ! Critical Error: {e}")
            results.append({
                "Question": clean_q,
                "Status": "Error",
                "Verifier Output": str(e),
                "Latency (s)": 0,
                "Total Tokens": 0,
                "Draft Length": 0,
                "Draft Preview": "Error"
            })

    # Save to CSV
    if results:
        df = pd.DataFrame(results)
        df.to_csv(output_file, index=False)
        print(f"\nEvaluation complete. Results saved to {output_file}")
        print("-" * 30)
        # Display key columns
        print(df[["Question", "Status", "Draft Length", "Latency (s)"]].to_string())
    else:
        print("No results generated.")

if __name__ == "__main__":
    run_evaluation()