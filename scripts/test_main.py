"""
Test script for the integrated professor agent system
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, LearningState


async def test_simple_flow():
    """Test a simple flow through one lesson"""
    print("=" * 70)
    print("🧪 TESTING PROFESSOR AGENT - SIMPLE FLOW")
    print("=" * 70)
    
    # Initialize state for a very simple topic
    initial_state: LearningState = {
        "topic": "Python Variables",
        "background": "Complete beginner, no programming experience",
        "learning_plan": None,
        "current_lesson_idx": 0,
        "lecture_content": None,
        "quiz_results": None,
        "quiz_score": 0,
        "assignment": None,
        "assignment_submission": "x = 5\ny = 10\nz = x + y\nprint(z)",
        "assignment_score": 0,
        "grading_result": None,
        "weak_points": [],
        "attempt_count": 0,
        "message": "",
        "completed": False
    }
    
    config = {"configurable": {"thread_id": "test-session-1"}}
    
    try:
        print("\n▶️  Starting test flow...")
        print("-" * 70)
        
        step_count = 0
        async for event in app.astream(initial_state, config):
            step_count += 1
            node_name = list(event.keys())[0] if event else "unknown"
            print(f"\n[Step {step_count}] Node executed: {node_name}")
            
            # Limit iterations for testing (avoid infinite loops)
            if step_count > 10:
                print("\n⚠️  Stopping after 10 steps for testing")
                break
        
        print("\n" + "=" * 70)
        print("✅ Test flow completed successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


async def test_state_persistence():
    """Test that state is properly maintained across nodes"""
    print("\n" + "=" * 70)
    print("🧪 TESTING STATE PERSISTENCE")
    print("=" * 70)
    
    initial_state: LearningState = {
        "topic": "Basic Math",
        "background": "Elementary student",
        "learning_plan": None,
        "current_lesson_idx": 0,
        "lecture_content": None,
        "quiz_results": None,
        "quiz_score": 0,
        "assignment": None,
        "assignment_submission": "",
        "assignment_score": 0,
        "grading_result": None,
        "weak_points": [],
        "attempt_count": 0,
        "message": "",
        "completed": False
    }
    
    config = {"configurable": {"thread_id": "test-session-2"}}
    
    try:
        # Run first few steps
        final_state = None
        step_count = 0
        
        async for event in app.astream(initial_state, config):
            step_count += 1
            if event:
                final_state = list(event.values())[0]
            
            # Stop after a few steps
            if step_count >= 3:
                break
        
        if final_state:
            print(f"\n✓ State after {step_count} steps:")
            print(f"  - Topic: {final_state.get('topic')}")
            print(f"  - Has learning plan: {final_state.get('learning_plan') is not None}")
            print(f"  - Current lesson: {final_state.get('current_lesson_idx')}")
        
        print("\n" + "=" * 70)
        print("✅ State persistence test completed!")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ State persistence test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n🚀 Starting Professor Agent Integration Tests\n")
    
    # Test 1: Simple flow
    test1_passed = await test_simple_flow()
    
    # Test 2: State persistence
    test2_passed = await test_state_persistence()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    print(f"Simple Flow Test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"State Persistence Test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print("=" * 70)
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
