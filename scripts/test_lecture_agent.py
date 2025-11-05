"""
Test script for the lecture agent
Tests the lecture generation functionality
"""
import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agents import create_lecture
from app.models import Lecture, DifficultyLevel


async def test_lecture_agent():
    """Test the lecture agent with sample lessons"""
    
    print("=" * 80)
    print("TESTING LECTURE AGENT")
    print("=" * 80)
    print()
    
    # Test case 1: Beginner Python lesson
    print("Test Case 1: Beginner Python - Variables and Data Types")
    print("-" * 80)
    
    lesson_title1 = "Introduction to Python Variables and Data Types"
    objectives1 = [
        "Understand what variables are and why they're useful",
        "Learn how to create and name variables in Python",
        "Identify and use basic data types (int, float, str, bool)",
        "Perform basic operations with different data types"
    ]
    key_concepts1 = ["variables", "assignment", "data types", "integers", "strings", "floats", "booleans"]
    current_knowledge1 = "Complete beginner who just installed Python"
    weak_points1 = []
    
    print(f"Lesson: {lesson_title1}")
    print(f"Objectives: {len(objectives1)} objectives")
    print(f"Key Concepts: {', '.join(key_concepts1)}")
    print(f"Current Knowledge: {current_knowledge1}")
    print()
    print("Generating lecture...")
    print()
    
    try:
        lecture1 = await create_lecture(
            lesson_title=lesson_title1,
            objectives=objectives1,
            key_concepts=key_concepts1,
            current_knowledge=current_knowledge1,
            weak_points=weak_points1
        )
        
        print(f"✓ Lecture Generated Successfully!")
        print()
        print(f"Lesson Title: {lecture1.lesson_title}")
        print(f"Total Duration: {lecture1.total_duration_minutes} minutes")
        print(f"Number of Segments: {len(lecture1.segments)}")
        print(f"Key Takeaways: {len(lecture1.key_takeaways)}")
        print()
        
        print("INTRODUCTION:")
        print("-" * 80)
        print(lecture1.introduction[:300] + "..." if len(lecture1.introduction) > 300 else lecture1.introduction)
        print()
        
        print("SEGMENTS:")
        print("-" * 80)
        for i, segment in enumerate(lecture1.segments, 1):
            print(f"\nSegment {i}: {segment.title}")
            print(f"  Duration: {segment.duration_minutes} minutes")
            print(f"  Content Preview: {segment.content[:200]}..." if len(segment.content) > 200 else f"  Content: {segment.content}")
            if segment.interaction_points:
                print(f"  Interaction Points: {len(segment.interaction_points)}")
                for point in segment.interaction_points[:2]:  # Show first 2
                    print(f"    - {point}")
        
        print()
        print("CONCLUSION:")
        print("-" * 80)
        print(lecture1.conclusion[:300] + "..." if len(lecture1.conclusion) > 300 else lecture1.conclusion)
        print()
        
        print("KEY TAKEAWAYS:")
        print("-" * 80)
        for i, takeaway in enumerate(lecture1.key_takeaways, 1):
            print(f"  {i}. {takeaway}")
        
        print()
        print("=" * 80)
        print()
        
    except Exception as e:
        print(f"✗ Error generating lecture: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test case 2: Intermediate lesson with weak points
    print("Test Case 2: Intermediate Topic with Weak Points")
    print("-" * 80)
    
    lesson_title2 = "Object-Oriented Programming: Classes and Objects"
    objectives2 = [
        "Define classes and create objects in Python",
        "Understand the concept of attributes and methods",
        "Use the __init__ constructor method",
        "Apply encapsulation principles"
    ]
    key_concepts2 = ["classes", "objects", "attributes", "methods", "__init__", "self", "encapsulation"]
    current_knowledge2 = "Comfortable with functions, variables, and basic Python syntax"
    weak_points2 = ["function parameters", "return values"]
    
    print(f"Lesson: {lesson_title2}")
    print(f"Objectives: {len(objectives2)} objectives")
    print(f"Key Concepts: {', '.join(key_concepts2)}")
    print(f"Weak Points to Address: {', '.join(weak_points2)}")
    print()
    print("Generating lecture...")
    print()
    
    try:
        lecture2 = await create_lecture(
            lesson_title=lesson_title2,
            objectives=objectives2,
            key_concepts=key_concepts2,
            current_knowledge=current_knowledge2,
            weak_points=weak_points2
        )
        
        print(f"✓ Lecture Generated Successfully!")
        print()
        print(f"Lesson Title: {lecture2.lesson_title}")
        print(f"Total Duration: {lecture2.total_duration_minutes} minutes")
        print(f"Number of Segments: {len(lecture2.segments)}")
        print()
        
        print("SEGMENT OVERVIEW:")
        print("-" * 80)
        for i, segment in enumerate(lecture2.segments, 1):
            print(f"  {i}. {segment.title} ({segment.duration_minutes} min)")
            if segment.interaction_points:
                print(f"     → {len(segment.interaction_points)} interaction points")
        
        print()
        print("KEY TAKEAWAYS:")
        print("-" * 80)
        for i, takeaway in enumerate(lecture2.key_takeaways, 1):
            print(f"  {i}. {takeaway}")
        
        print()
        print("=" * 80)
        print("ALL TESTS COMPLETED SUCCESSFULLY! ✓")
        print("=" * 80)
        
    except Exception as e:
        print(f"✗ Error generating lecture: {e}")
        import traceback
        traceback.print_exc()


async def test_lecture_structure():
    """Test that lecture structure meets requirements"""
    
    print()
    print("=" * 80)
    print("TESTING LECTURE STRUCTURE VALIDATION")
    print("=" * 80)
    print()
    
    lesson_title = "Quick Test Lesson"
    objectives = ["Test objective 1", "Test objective 2", "Test objective 3"]
    key_concepts = ["concept1", "concept2"]
    
    try:
        lecture = await create_lecture(
            lesson_title=lesson_title,
            objectives=objectives,
            key_concepts=key_concepts,
            current_knowledge="Test knowledge"
        )
        
        # Validate structure
        checks = []
        
        # Check 1: Duration is within 15-20 minutes
        duration_ok = 15 <= lecture.total_duration_minutes <= 20
        checks.append(("Duration 15-20 minutes", duration_ok, f"{lecture.total_duration_minutes} min"))
        
        # Check 2: Has 2-3 segments
        segments_ok = 2 <= len(lecture.segments) <= 3
        checks.append(("2-3 segments", segments_ok, f"{len(lecture.segments)} segments"))
        
        # Check 3: Has introduction
        intro_ok = len(lecture.introduction) > 50
        checks.append(("Has introduction", intro_ok, f"{len(lecture.introduction)} chars"))
        
        # Check 4: Has conclusion
        conclusion_ok = len(lecture.conclusion) > 50
        checks.append(("Has conclusion", conclusion_ok, f"{len(lecture.conclusion)} chars"))
        
        # Check 5: Has key takeaways
        takeaways_ok = len(lecture.key_takeaways) >= 3
        checks.append(("Has key takeaways", takeaways_ok, f"{len(lecture.key_takeaways)} takeaways"))
        
        # Check 6: Segments have content
        content_ok = all(len(seg.content) > 100 for seg in lecture.segments)
        checks.append(("Segments have content", content_ok, "All segments substantial"))
        
        # Display results
        print("Structure Validation Results:")
        print("-" * 80)
        for check_name, passed, details in checks:
            status = "✓" if passed else "✗"
            print(f"  {status} {check_name}: {details}")
        
        all_passed = all(check[1] for check in checks)
        print()
        if all_passed:
            print("=" * 80)
            print("STRUCTURE VALIDATION PASSED! ✓")
            print("=" * 80)
        else:
            print("=" * 80)
            print("SOME STRUCTURE CHECKS FAILED")
            print("=" * 80)
        
        print()
        
    except Exception as e:
        print(f"✗ Structure validation failed: {e}")
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
    print("🎓 Professor Agent - Lecture Agent Test Suite")
    print()
    
    # Run lecture generation tests
    asyncio.run(test_lecture_agent())
    
    # Run structure validation tests
    asyncio.run(test_lecture_structure())


if __name__ == "__main__":
    main()
