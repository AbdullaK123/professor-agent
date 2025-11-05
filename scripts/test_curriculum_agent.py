"""
Test script for the curriculum agent
Tests the learning plan generation functionality
"""
import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agents import create_learning_plan
from app.models import LearningPlan


async def test_curriculum_agent():
    """Test the curriculum agent with a sample topic"""
    
    print("=" * 80)
    print("TESTING CURRICULUM AGENT")
    print("=" * 80)
    print()
    
    # Test case 1: Complete beginner
    print("Test Case 1: Complete Beginner Learning Python")
    print("-" * 80)
    
    topic1 = "Python Programming"
    background1 = "Complete beginner with no coding experience"
    
    print(f"Topic: {topic1}")
    print(f"Background: {background1}")
    print()
    print("Generating learning plan...")
    print()
    
    try:
        learning_plan1 = await create_learning_plan(topic1, background1)
        
        print(f"✓ Learning Plan Generated Successfully!")
        print()
        print(f"Topic: {learning_plan1.topic}")
        print(f"Total Duration: {learning_plan1.total_duration_minutes} minutes")
        print(f"Overall Difficulty: {learning_plan1.overall_difficulty.value}")
        print(f"Number of Lessons: {len(learning_plan1.lessons)}")
        print()
        
        print("Lessons:")
        print("-" * 80)
        for lesson in learning_plan1.lessons:
            print(f"\nLesson {lesson.lesson_number}: {lesson.title}")
            print(f"  Difficulty: {lesson.difficulty.value}")
            print(f"  Duration: {lesson.duration_minutes} minutes")
            print(f"  Objectives:")
            for obj in lesson.objectives:
                print(f"    - {obj}")
            print(f"  Key Concepts: {', '.join(lesson.key_concepts)}")
            if lesson.prerequisites:
                print(f"  Prerequisites: {', '.join(lesson.prerequisites)}")
        
        print()
        print("=" * 80)
        print()
        
    except Exception as e:
        print(f"✗ Error generating learning plan: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test case 2: Intermediate learner
    print("Test Case 2: Intermediate Learner - Machine Learning")
    print("-" * 80)
    
    topic2 = "Machine Learning Fundamentals"
    background2 = "Knows Python and basic statistics, no ML experience"
    
    print(f"Topic: {topic2}")
    print(f"Background: {background2}")
    print()
    print("Generating learning plan...")
    print()
    
    try:
        learning_plan2 = await create_learning_plan(topic2, background2)
        
        print(f"✓ Learning Plan Generated Successfully!")
        print()
        print(f"Topic: {learning_plan2.topic}")
        print(f"Total Duration: {learning_plan2.total_duration_minutes} minutes")
        print(f"Overall Difficulty: {learning_plan2.overall_difficulty.value}")
        print(f"Number of Lessons: {len(learning_plan2.lessons)}")
        print()
        
        print("Lesson Titles:")
        for i, lesson in enumerate(learning_plan2.lessons, 1):
            print(f"  {i}. {lesson.title} ({lesson.difficulty.value}, {lesson.duration_minutes} min)")
        
        print()
        print("=" * 80)
        print("ALL TESTS COMPLETED SUCCESSFULLY! ✓")
        print("=" * 80)
        
    except Exception as e:
        print(f"✗ Error generating learning plan: {e}")
        import traceback
        traceback.print_exc()


async def test_model_validation():
    """Test the Pydantic model validation"""
    
    print()
    print("=" * 80)
    print("TESTING MODEL VALIDATION")
    print("=" * 80)
    print()
    
    # Test that the model validates correctly
    from app.models import Lesson, DifficultyLevel
    
    try:
        lesson = Lesson(
            lesson_number=1,
            title="Introduction to Python",
            objectives=["Learn basic syntax", "Understand variables", "Write first program"],
            key_concepts=["variables", "data types", "print function"],
            duration_minutes=45,
            prerequisites=[],
            difficulty=DifficultyLevel.BEGINNER
        )
        print(f"✓ Lesson model validation passed")
        print(f"  Lesson: {lesson.title}")
        print()
        
        learning_plan = LearningPlan(
            topic="Python Basics",
            lessons=[lesson] * 5,  # 5 identical lessons for testing
            total_duration_minutes=225,
            overall_difficulty=DifficultyLevel.BEGINNER
        )
        print(f"✓ LearningPlan model validation passed")
        print(f"  Plan: {learning_plan.topic} with {len(learning_plan.lessons)} lessons")
        print()
        
        print("=" * 80)
        print("MODEL VALIDATION TESTS PASSED! ✓")
        print("=" * 80)
        print()
        
    except Exception as e:
        print(f"✗ Model validation failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main test runner"""
    
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable not set")
        print("Please set it in your .env file or export it:")
        print("  export OPENAI_API_KEY='your-api-key-here'")
        sys.exit(1)
    
    if not os.getenv("TAVILY_API_KEY"):
        print("WARNING: TAVILY_API_KEY not set - search tool may not work")
        print("You can get a key at: https://tavily.com")
        print()
    
    print()
    print("🎓 Professor Agent - Curriculum Agent Test Suite")
    print()
    
    # Run model validation tests first (synchronous)
    asyncio.run(test_model_validation())
    
    # Run agent tests (asynchronous)
    asyncio.run(test_curriculum_agent())


if __name__ == "__main__":
    main()
