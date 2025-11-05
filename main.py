"""
Interactive CLI Chat for Professor Agent

PERSISTENCE CONFIGURATION:
--------------------------
By default, progress is stored in memory only (lost on restart).

To enable persistent storage across sessions:

Option 1: Environment variables
    export USE_PERSISTENCE=true
    export DB_PATH=checkpoints/progress.db  # optional, this is the default

Option 2: Create a .env file
    USE_PERSISTENCE=true
    DB_PATH=checkpoints/progress.db

Option 3: Inline (for testing)
    USE_PERSISTENCE=true python main.py

With persistence enabled:
- Progress is saved to a SQLite database
- You can resume learning sessions using the same thread_id
- Checkpoints survive application restarts
- Database file created at: checkpoints/progress.db

Without persistence (default):
- Progress stored in memory only
- Faster and simpler for single sessions
- No database files created
"""
import asyncio
import sys
import os
from app.graph import create_graph, LearningState
from app.cli_formatting import (
    print_slow, print_box,
    display_learning_plan, display_lecture, display_quiz_score,
    display_grading_result, display_advance_message, display_repeat_message
)
from app.cli_handlers import handle_quiz, handle_assignment
from dotenv import load_dotenv

load_dotenv()

# Configuration: Set to True to enable persistent storage
USE_PERSISTENCE = os.getenv("USE_PERSISTENCE", "false").lower() == "true"
DB_PATH = os.getenv("DB_PATH", "checkpoints/progress.db")


async def stream_node_output(node_name: str, state: dict):
    """Stream output for each node using formatting utilities"""
    if node_name == "generate_plan":
        plan = state.get("learning_plan")
        if plan:
            display_learning_plan(plan, state.get('topic'))
    
    elif node_name == "lecture":
        lecture = state.get("lecture_content")
        if lecture:
            display_lecture(lecture)
    
    elif node_name == "process_quiz":
        score = state.get("quiz_score", 0)
        display_quiz_score(score)
    
    elif node_name == "grade":
        result = state.get("grading_result")
        if result:
            display_grading_result(result)
    
    elif node_name == "advance":
        msg = state.get("message", "")
        display_advance_message(msg)
    
    elif node_name == "repeat":
        msg = state.get("message", "")
        display_repeat_message(msg)


async def main():
    """Interactive CLI chat"""
    print_box("🎓 PROFESSOR AGENT - Interactive CLI", "=")
    
    # Show persistence mode
    if USE_PERSISTENCE:
        print(f"💾 Persistence: ENABLED (database: {DB_PATH})")
    else:
        print("💾 Persistence: DISABLED (in-memory only)")
    print()
    
    # Get user input
    topic = input("What would you like to learn? ").strip()
    if not topic:
        print("No topic provided. Exiting.")
        return
    
    background = input("Your background (optional, press Enter to skip): ").strip()
    
    # Initialize state
    initial_state: LearningState = {
        "topic": topic,
        "background": background or "No background provided",
        "learning_plan": None,
        "current_lesson_idx": 0,
        "lecture_content": None,
        "quiz_results": None,
        "quiz_score": 0,
        "quiz_answers": None,
        "assignment": None,
        "assignment_submission": "",
        "assignment_score": 0,
        "grading_result": None,
        "weak_points": [],
        "attempt_count": 0,
        "message": "",
        "completed": False,
        "waiting_for_input": False,
        "input_type": None
    }
    
    print_slow(f"\n🚀 Starting your learning journey on: {topic}")
    
    # Create graph with or without persistence
    if USE_PERSISTENCE:
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
        
        # Create checkpoints directory if it doesn't exist
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        async with AsyncSqliteSaver.from_conn_string(DB_PATH) as checkpointer:
            app = create_graph(checkpointer)
            config = {"configurable": {"thread_id": "cli-session"}}
            await run_learning_session(app, config, initial_state)
    else:
        app = create_graph()  # Uses InMemorySaver by default
        config = {"configurable": {"thread_id": "cli-session"}}
        await run_learning_session(app, config, initial_state)


async def run_learning_session(app, config, initial_state):
    
    current_state = initial_state
    is_first_run = True
    
    try:
        while not current_state.get("completed", False):
            # Validate current_state is a dict
            if not isinstance(current_state, dict):
                print(f"Error: current_state is not a dict, it's {type(current_state)}")
                print(f"Value: {current_state}")
                break
            
            # Run graph from current state
            stream_input = current_state if is_first_run else None
            is_first_run = False
            
            async for event in app.astream(stream_input, config):
                # Validate event is a dict
                if not isinstance(event, dict):
                    print(f"Warning: event is not a dict, it's {type(event)}")
                    continue
                
                for node_name, state in event.items():
                    # Skip internal LangGraph nodes
                    if node_name.startswith("__"):
                        continue
                    
                    # Validate state is a dict
                    if not isinstance(state, dict):
                        print(f"Warning: state from node '{node_name}' is not a dict, it's {type(state)}")
                        continue
                    
                    current_state = state
                    await stream_node_output(node_name, state)
                    
                    # Handle interrupts for user input
                    if state.get("waiting_for_input"):
                        if state.get("input_type") == "quiz":
                            answers = await handle_quiz(state)
                            if isinstance(answers, dict):
                                # Update the checkpointed state
                                print(f"\nDEBUG: Setting quiz_answers with {len(answers)} answers")
                                print(f"DEBUG: Answers = {answers}")
                                app.update_state(config, {"quiz_answers": answers, "waiting_for_input": False})
                                current_state["quiz_answers"] = answers
                                current_state["waiting_for_input"] = False
                            else:
                                print(f"Error: quiz answers is not a dict: {type(answers)}")
                            break  # Exit event loop to continue graph
                        
                        elif state.get("input_type") == "assignment":
                            submission = await handle_assignment(state)
                            if isinstance(submission, str):
                                # Update the checkpointed state
                                app.update_state(config, {"assignment_submission": submission, "waiting_for_input": False})
                                current_state["assignment_submission"] = submission
                                current_state["waiting_for_input"] = False
                            else:
                                print(f"Error: assignment submission is not a string: {type(submission)}")
                            break  # Exit event loop to continue graph
            
            # Check completion
            if not isinstance(current_state, dict):
                print("Error: current_state became invalid, exiting")
                break
            
            if current_state.get("completed", False):
                print_box("🎓 Learning Journey Complete!", "=")
                break
    
    except KeyboardInterrupt:
        print("\n\nLearning session interrupted. Progress saved!")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
