"""
LangGraph workflow for the Professor Agent
"""
from langgraph.graph import StateGraph, END
from typing import Literal, Optional
from typing_extensions import TypedDict
from langgraph.checkpoint.memory import InMemorySaver
from app.agents import (
    create_learning_plan,
    create_lecture,
    create_quiz,
    create_assignment as create_assignment_agent,
    grade_assignment as grade_assignment_agent,
    check_progress as check_progress_agent,
    create_repeat_message,
    create_advance_message,
    evaluate_short_answer
)
from app.models import LearningPlan, Lecture, Quiz, Assignment, GradingResult, ProgressDecision
from dotenv import load_dotenv

load_dotenv()


class LearningState(TypedDict):
    topic: str
    background: str
    learning_plan: Optional[LearningPlan]
    current_lesson_idx: int
    lecture_content: Optional[Lecture]
    quiz_results: Optional[Quiz]
    quiz_score: int
    quiz_answers: Optional[dict]  # Store user's quiz answers
    assignment: Optional[Assignment]
    assignment_submission: str
    assignment_score: int
    grading_result: Optional[GradingResult]
    weak_points: list[str]
    attempt_count: int
    message: str
    completed: bool
    waiting_for_input: bool  # Flag to indicate if waiting for user input
    input_type: Optional[str]  # "quiz" or "assignment"


async def generate_learning_plan(state: LearningState) -> LearningState:
    """Generate a comprehensive learning plan for the topic"""
    print(f"\n📚 Generating learning plan for: {state['topic']}")
    
    learning_plan = await create_learning_plan(
        topic=state['topic'],
        background=state.get('background', 'No background provided')
    )
    
    print(f"✓ Created plan with {len(learning_plan.lessons)} lessons")
    
    return {
        **state,
        "learning_plan": learning_plan,
        "current_lesson_idx": 0,
        "attempt_count": 0,
        "weak_points": [],
        "completed": False,
        "waiting_for_input": False
    }


async def check_progress_node(state: LearningState) -> LearningState:
    """Check if we should continue with next lesson or if course is complete"""
    learning_plan = state['learning_plan']
    if not learning_plan:
        raise ValueError("Learning plan not initialized")
        
    current_idx = state['current_lesson_idx']
    
    # Check if we've completed all lessons
    if current_idx >= len(learning_plan.lessons):
        print("\n🎓 Congratulations! You've completed all lessons!")
        return {
            **state,
            "completed": True,
            "message": "Course completed successfully!",
            "waiting_for_input": False
        }
    
    current_lesson = learning_plan.lessons[current_idx]
    print(f"\n📖 Lesson {current_idx + 1}/{len(learning_plan.lessons)}: {current_lesson.title}")
    
    return {**state, "waiting_for_input": False}


async def give_lecture(state: LearningState) -> LearningState:
    """Deliver a lecture for the current lesson"""
    learning_plan = state['learning_plan']
    if not learning_plan:
        raise ValueError("Learning plan not initialized")
        
    current_lesson = learning_plan.lessons[state['current_lesson_idx']]
    
    print(f"\n🎤 Delivering lecture: {current_lesson.title}")
    
    lecture = await create_lecture(
        lesson_title=current_lesson.title,
        objectives=current_lesson.objectives,
        key_concepts=current_lesson.key_concepts,
        current_knowledge=f"Lesson {state['current_lesson_idx'] + 1} of {len(learning_plan.lessons)}",
        weak_points=state['weak_points'] if state['weak_points'] else None
    )
    
    print(f"✓ Lecture created with {len(lecture.segments)} segments")
    
    return {
        **state,
        "lecture_content": lecture,
        "waiting_for_input": False
    }


async def administer_quiz(state: LearningState) -> LearningState:
    """Create and present a quiz based on the lecture"""
    learning_plan = state['learning_plan']
    lecture = state['lecture_content']
    if not learning_plan or not lecture:
        raise ValueError("Learning plan or lecture not initialized")
        
    current_lesson = learning_plan.lessons[state['current_lesson_idx']]
    
    print(f"\n📝 Creating quiz for: {current_lesson.title}")
    
    # Create a lecture summary for the quiz
    lecture_summary = f"{lecture.introduction}\n" + "\n".join([
        f"{seg.title}: {seg.content[:200]}..." for seg in lecture.segments
    ])
    
    quiz = await create_quiz(
        lesson_title=current_lesson.title,
        objectives=current_lesson.objectives,
        key_concepts=current_lesson.key_concepts,
        lecture_summary=lecture_summary
    )
    
    print(f"✓ Quiz created with {len(quiz.questions)} questions")
    
    # Set waiting_for_input to pause for user answers
    return {
        **state,
        "quiz_results": quiz,
        "waiting_for_input": True,
        "input_type": "quiz"
    }


async def process_quiz_answers(state: LearningState) -> LearningState:
    """Process the user's quiz answers and calculate score"""
    quiz = state['quiz_results']
    answers = state.get('quiz_answers', {})
    
    print(f"\n{'='*70}")
    print(f"DEBUG: Processing quiz answers")
    print(f"Quiz exists: {quiz is not None}")
    print(f"Answers dict: {answers}")
    print(f"Answers type: {type(answers)}")
    print(f"Number of answers: {len(answers) if isinstance(answers, dict) else 'Not a dict!'}")
    print(f"{'='*70}\n")
    
    if not quiz or not answers:
        # If no answers provided, assign a low score
        print(f"ERROR: Missing quiz or answers - quiz={quiz is not None}, answers={answers is not None}")
        return {
            **state,
            "quiz_score": 0,
            "waiting_for_input": False
        }
    
    # Calculate score based on correct answers
    correct_count = 0
    total_questions = len(quiz.questions)
    weak_points = []
    
    print(f"Grading quiz with {total_questions} questions...")
    
    for i, question in enumerate(quiz.questions):
        user_answer = answers.get(f"q{i}", "")
        
        # Handle different question types
        is_correct = False
        
        # Get the enum value for comparison
        from app.models import QuestionType
        
        if question.type == QuestionType.MULTIPLE_CHOICE:
            # Multiple choice: compare letters (A, B, C, D)
            correct_answer = str(question.correct_answer).strip().upper()
            user_answer_clean = str(user_answer).strip().upper()
            is_correct = user_answer_clean == correct_answer
            print(f"Q{i+1} [MC]: User='{user_answer_clean}' Correct='{correct_answer}' Match={is_correct}")
        
        elif question.type == QuestionType.TRUE_FALSE:
            # True/False: compare boolean values
            # User input is string "True" or "False", correct_answer is bool
            correct_answer = question.correct_answer
            user_answer_bool = str(user_answer).strip().lower() == "true"
            is_correct = user_answer_bool == correct_answer
            print(f"Q{i+1} [T/F]: User='{user_answer}' -> {user_answer_bool}, Correct={correct_answer} Match={is_correct}")
        
        elif question.type == QuestionType.SHORT_ANSWER:
            # Short answer: use LLM evaluator for sophisticated grading
            is_correct = await evaluate_short_answer(
                question=question.question,
                key_points=question.key_points,
                student_answer=str(user_answer)
            )
            print(f"Q{i+1} [SA]: User='{user_answer[:30]}...' Match={is_correct}")
        
        else:
            print(f"WARNING: Unknown question type: {question.type}")
        
        if is_correct:
            correct_count += 1
        else:
            # Track weak points for wrong answers
            weak_points.append(question.question[:50])  # First 50 chars
    
    score = int((correct_count / total_questions) * 100) if total_questions > 0 else 0
    
    print(f"✓ Quiz scored: {score}% ({correct_count}/{total_questions} correct)")
    
    return {
        **state,
        "quiz_score": score,
        "weak_points": weak_points[:3],  # Keep top 3 weak points
        "waiting_for_input": False
    }


async def create_assignment_node(state: LearningState) -> LearningState:
    """Create an assignment based on the lesson and quiz performance"""
    learning_plan = state['learning_plan']
    if not learning_plan:
        raise ValueError("Learning plan not initialized")
        
    current_lesson = learning_plan.lessons[state['current_lesson_idx']]
    
    print(f"\n📋 Creating assignment for: {current_lesson.title}")
    
    quiz_performance = f"Quiz score: {state['quiz_score']}%"
    if state['weak_points']:
        quiz_performance += f", Weak areas: {', '.join(state['weak_points'])}"
    
    assignment = await create_assignment_agent(
        lesson_title=current_lesson.title,
        objectives=current_lesson.objectives,
        key_concepts=current_lesson.key_concepts,
        quiz_performance=quiz_performance
    )
    
    print(f"✓ Assignment created: {assignment.title}")
    
    # Set waiting_for_input to pause for user submission
    return {
        **state,
        "assignment": assignment,
        "waiting_for_input": True,
        "input_type": "assignment"
    }


async def grade_assignment_node(state: LearningState) -> LearningState:
    """Grade the student's assignment submission"""
    assignment = state['assignment']
    learning_plan = state['learning_plan']
    if not assignment or not learning_plan:
        raise ValueError("Assignment or learning plan not initialized")
        
    current_lesson = learning_plan.lessons[state['current_lesson_idx']]
    
    print(f"\n✏️ Grading assignment: {assignment.title}")
    
    submission = state.get('assignment_submission', "")
    
    if not submission or submission.strip() == "":
        print("⚠️ No submission provided, assigning low score")
        # Create a minimal grading result
        return {
            **state,
            "assignment_score": 0,
            "weak_points": current_lesson.key_concepts,
            "waiting_for_input": False
        }
    
    grading_result = await grade_assignment_agent(
        assignment_title=assignment.title,
        assignment_steps=[step.instruction for step in assignment.steps],
        criteria=assignment.success_criteria,
        student_submission=submission
    )
    
    print(f"✓ Graded: {grading_result.score}% ({grading_result.grade_level})")
    
    return {
        **state,
        "grading_result": grading_result,
        "assignment_score": int(grading_result.score),
        "weak_points": grading_result.weak_points,
        "waiting_for_input": False
    }


async def should_advance(state: LearningState) -> Literal["advance", "repeat", "end"]:
    """Determine if student should advance or repeat the lesson"""
    
    # Check if course is complete
    if state.get('completed', False):
        return "end"
    
    learning_plan = state['learning_plan']
    if not learning_plan:
        raise ValueError("Learning plan not initialized")
        
    current_lesson = learning_plan.lessons[state['current_lesson_idx']]
    
    print(f"\n🤔 Evaluating progress for: {current_lesson.title}")
    
    decision = await check_progress_agent(
        lesson_title=current_lesson.title,
        quiz_score=state['quiz_score'],
        assignment_score=state['assignment_score'],
        weak_points=state['weak_points'],
        attempt_count=state['attempt_count']
    )
    
    print(f"✓ Decision: {decision.decision.value.upper()} (Confidence: {decision.confidence.value})")
    print(f"  Reason: {decision.reasoning[:100]}...")
    
    return decision.decision.value


async def advance_lesson(state: LearningState) -> LearningState:
    """Advance to the next lesson"""
    learning_plan = state['learning_plan']
    if not learning_plan:
        raise ValueError("Learning plan not initialized")
        
    current_idx = state['current_lesson_idx']
    current_lesson = learning_plan.lessons[current_idx]
    
    # Check if there's a next lesson
    next_idx = current_idx + 1
    if next_idx >= len(learning_plan.lessons):
        next_lesson_title = "Course Completion"
    else:
        next_lesson_title = learning_plan.lessons[next_idx].title
    
    print(f"\n🎉 Advancing from: {current_lesson.title}")
    
    advance_msg = await create_advance_message(
        completed_lesson=current_lesson.title,
        next_lesson=next_lesson_title,
        key_takeaways=current_lesson.key_concepts[:3]  # Top 3 concepts
    )
    
    print(f"✓ {advance_msg.message[:100]}...")
    
    return {
        **state,
        "current_lesson_idx": next_idx,
        "attempt_count": 0,
        "weak_points": [],
        "message": advance_msg.message,
        "lecture_content": None,
        "quiz_results": None,
        "quiz_answers": None,
        "assignment": None,
        "assignment_submission": "",
        "grading_result": None,
        "waiting_for_input": False
    }


async def repeat_lesson(state: LearningState) -> LearningState:
    """Repeat the current lesson with focus on weak areas"""
    learning_plan = state['learning_plan']
    if not learning_plan:
        raise ValueError("Learning plan not initialized")
        
    current_lesson = learning_plan.lessons[state['current_lesson_idx']]
    
    print(f"\n🔄 Repeating lesson: {current_lesson.title}")
    
    repeat_msg = await create_repeat_message(
        lesson_title=current_lesson.title,
        weak_points=state['weak_points'],
        attempt_count=state['attempt_count'] + 1
    )
    
    print(f"✓ {repeat_msg.message[:100]}...")
    print(f"  Focus areas: {', '.join(repeat_msg.focus_areas)}")
    
    return {
        **state,
        "attempt_count": state['attempt_count'] + 1,
        "message": repeat_msg.message,
        "lecture_content": None,
        "quiz_results": None,
        "quiz_answers": None,
        "assignment": None,
        "assignment_submission": "",
        "grading_result": None,
        "waiting_for_input": False
    }


def create_graph(checkpointer=None):
    """
    Create and compile the professor agent graph
    
    Args:
        checkpointer: Optional checkpointer for persisting state. 
                     If None, uses InMemorySaver (no persistence)
    """
    if checkpointer is None:
        checkpointer = InMemorySaver()
    
    graph = StateGraph(LearningState)
    
    # Add all nodes
    graph.add_node("generate_plan", generate_learning_plan)
    graph.add_node("check_progress", check_progress_node)
    graph.add_node("lecture", give_lecture)
    graph.add_node("quiz", administer_quiz)
    graph.add_node("process_quiz", process_quiz_answers)
    graph.add_node("assignment", create_assignment_node)
    graph.add_node("grade", grade_assignment_node)
    graph.add_node("advance", advance_lesson)
    graph.add_node("repeat", repeat_lesson)
    
    # Set entry point
    graph.set_entry_point("generate_plan")
    
    # Add edges
    graph.add_edge("generate_plan", "check_progress")
    graph.add_edge("check_progress", "lecture")
    graph.add_edge("lecture", "quiz")
    graph.add_edge("quiz", "process_quiz")  # Process answers before assignment
    graph.add_edge("process_quiz", "assignment")
    graph.add_edge("assignment", "grade")
    
    # Add conditional routing based on progress
    graph.add_conditional_edges(
        "grade",
        should_advance,
        {
            "advance": "advance",
            "repeat": "repeat",
            "end": END
        }
    )
    
    # Loop back for next lesson or repeat
    graph.add_edge("advance", "check_progress")
    graph.add_edge("repeat", "lecture")
    
    # Compile with checkpointer and interrupt before nodes that need input
    app = graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["process_quiz", "grade"]  # Pause before processing quiz and grading
    )
    
    return app
