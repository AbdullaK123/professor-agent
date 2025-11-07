"""
LangGraph workflow for the Professor Agent
"""
from langgraph.graph import StateGraph, END, add_messages
from typing import Literal, Optional, Annotated
from typing_extensions import TypedDict
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import BaseMessage
from app.agents import (
    create_learning_plan,
    create_lecture,
    create_quiz,
    extract_topic_and_background,
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


class LearningState(TypedDict, total=False):
    # Required by agent-chat-ui
    messages: Annotated[list[BaseMessage], add_messages]
    
    # Existing fields - all optional to allow incremental building
    query: str
    topic: str
    background: str
    learning_plan: Optional[LearningPlan]
    current_lesson_idx: int
    lecture_content: Optional[Lecture]
    quiz_results: Optional[Quiz]
    quiz_score: int
    quiz_answers: Optional[dict[str, str]]  # Store user's quiz answers as dict (q0-q4)
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


# Helper function to create AI messages
from langchain_core.messages import AIMessage

def create_ai_message(content: str) -> AIMessage:
    """Helper to create AI messages for the chat UI"""
    return AIMessage(content=content)


async def extract_topic_and_background_node(state: LearningState) -> LearningState:
    """Extract the topic the user wants to learn along with their background"""
    # Get query from the last user message
    query = state.get("query", "")
    if not query and state.get("messages"):
        # Extract from last message if query not provided
        messages = state.get("messages", [])
        if messages:
            last_message = messages[-1]
            content = last_message.content if hasattr(last_message, 'content') else str(last_message)
            # Handle content being a list or dict
            if isinstance(content, list):
                query = " ".join(str(item) for item in content)
            elif isinstance(content, dict):
                query = str(content)
            else:
                query = str(content)
    
    if not query:
        # If still no query, return error state
        return {
            **state,
            "query": "",
            "topic": "failed to detect",
            "background": "failed to detect",
            "waiting_for_input": False
        }
    
    inputs = await extract_topic_and_background(query)
    return {
        **state,
        "query": query,
        "topic": inputs.topic,
        "background": inputs.background,
        "waiting_for_input": False  # Clear the flag after extraction
    }

async def check_extraction_result(state: LearningState) -> LearningState:
    """Checks if the result of the extraction was successful"""
    # Check if extraction failed
    topic = state.get("topic", "").strip()
    background = state.get("background", "").strip()
    
    failed_values = ["failed to detect", "failed"]
    topic_failed = not topic or any(fail in topic.lower() for fail in failed_values)
    background_failed = not background or any(fail in background.lower() for fail in failed_values)
    
    # If extraction failed, set waiting_for_input flag
    if topic_failed or background_failed:
        return {
            **state,
            "waiting_for_input": True,
            "input_type": "extraction_retry"
        }
    
    return state


async def request_new_query(state: LearningState) -> LearningState:
    """Request a new query from the user when extraction fails"""
    error_msg = "I couldn't understand your request. Please provide more details about what you'd like to learn and your background."
    return {
        **state,
        "messages": [create_ai_message(error_msg)],
        "waiting_for_input": True,
        "input_type": "new_query",
        "message": error_msg
    }


async def generate_learning_plan(state: LearningState) -> LearningState:
    """Generate a comprehensive learning plan for the topic"""
    print(f"\n📚 Generating learning plan for: {state['topic']}")
    
    learning_plan = await create_learning_plan(
        topic=state['topic'],
        background=state.get('background', 'No background provided')
    )
    
    print(f"✓ Created plan with {len(learning_plan.lessons)} lessons")
    
    # Format learning plan for chat UI
    plan_text = f"# 📚 Learning Plan: {learning_plan.topic}\n\n"
    plan_text += f"**Total Duration:** {learning_plan.total_duration_minutes} minutes\n"
    plan_text += f"**Difficulty Level:** {learning_plan.overall_difficulty.value}\n\n"
    plan_text += "## Lessons\n\n"
    
    for lesson in learning_plan.lessons:
        plan_text += f"### Lesson {lesson.lesson_number}: {lesson.title}\n"
        plan_text += f"**Duration:** {lesson.duration_minutes} min | **Difficulty:** {lesson.difficulty.value}\n\n"
        plan_text += "**Objectives:**\n"
        for obj in lesson.objectives:
            plan_text += f"- {obj}\n"
        plan_text += "\n"
    
    plan_text += "\nLet's begin with the first lesson! 🚀"
    
    return {
        **state,
        "messages": [create_ai_message(plan_text)],
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
        completion_msg = "# 🎓 Congratulations!\n\nYou've completed all lessons! You've demonstrated excellent progress and mastery of the material. Well done! 🎉"
        print("\n🎓 Congratulations! You've completed all lessons!")
        return {
            **state,
            "messages": [create_ai_message(completion_msg)],
            "completed": True,
            "message": "Course completed successfully!",
            "waiting_for_input": False
        }
    
    current_lesson = learning_plan.lessons[current_idx]
    lesson_intro = f"## 📖 Lesson {current_idx + 1}/{len(learning_plan.lessons)}: {current_lesson.title}\n\n"
    lesson_intro += f"**Duration:** {current_lesson.duration_minutes} minutes\n"
    lesson_intro += f"**Difficulty:** {current_lesson.difficulty.value}\n\n"
    lesson_intro += "**Learning Objectives:**\n"
    for obj in current_lesson.objectives:
        lesson_intro += f"- {obj}\n"
    lesson_intro += "\nLet's get started! 📚"
    
    print(f"\n📖 Lesson {current_idx + 1}/{len(learning_plan.lessons)}: {current_lesson.title}")
    
    return {
        **state,
        "messages": [create_ai_message(lesson_intro)],
        "waiting_for_input": False
    }


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
    
    # Format lecture content for chat UI
    lecture_text = f"# {lecture.lesson_title}\n\n"
    lecture_text += f"## Introduction\n\n{lecture.introduction}\n\n"
    
    for segment in lecture.segments:
        lecture_text += f"{segment.content}\n\n"
        if segment.interaction_points:
            lecture_text += "**Think About This:**\n"
            for point in segment.interaction_points:
                lecture_text += f"- {point}\n"
            lecture_text += "\n"
    
    lecture_text += f"## Conclusion\n\n{lecture.conclusion}\n\n"
    lecture_text += "**Key Takeaways:**\n"
    for takeaway in lecture.key_takeaways:
        lecture_text += f"- {takeaway}\n"
    
    return {
        **state,
        "messages": [create_ai_message(lecture_text)],
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
    
    # Format quiz for chat UI
    quiz_text = f"## Quiz Time! 📝\n\n"
    for i, q in enumerate(quiz.questions, 1):
        quiz_text += f"**Question {i}:** {q.question}\n\n"
        # Check question type using the type field
        from app.models import QuestionType
        if q.type == QuestionType.MULTIPLE_CHOICE and hasattr(q, 'options'):
            for i, opt in enumerate(q.options):
                quiz_text += f"- {i+1}. {opt}\n"
        quiz_text += "\n"
    
    # Set waiting_for_input to pause for user answers
    return {
        **state,
        "messages": [create_ai_message(quiz_text)],
        "quiz_results": quiz,
        "waiting_for_input": True,
        "input_type": "quiz"
    }


async def process_quiz_answers(state: LearningState) -> LearningState:
    """Process the user's quiz answers and calculate score"""
    quiz = state['quiz_results']
    
    # Try to parse answers from the last user message
    answers: dict[str, str] = {}
    quiz_answers_from_state = state.get('quiz_answers')
    if quiz_answers_from_state:
        answers = quiz_answers_from_state
    
    messages = state.get("messages", [])
    
    if not answers and messages and quiz:
        # Find the last human message
        human_messages = [m for m in messages if hasattr(m, 'type') and m.type == 'human']
        if human_messages:
            msg_content = human_messages[-1].content
            # Handle content that could be string or list
            raw_message = msg_content if isinstance(msg_content, str) else str(msg_content)
            
            # Format quiz questions for parser context
            quiz_questions_str = "\n".join([
                f"{i+1}. {q.question}" for i, q in enumerate(quiz.questions)
            ])
            
            print(f"\n{'='*70}")
            print(f"DEBUG: Parsing quiz answers from message")
            print(f"Raw message: {raw_message[:200]}...")
            print(f"{'='*70}\n")
            
            # Parse the answers from natural language
            from app.agents import parse_quiz_answers
            try:
                answers = await parse_quiz_answers(raw_message, quiz_questions_str)
                print(f"Parsed answers: {answers}")
            except Exception as e:
                print(f"Error parsing quiz answers: {e}")
                answers = {}
    
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
        error_msg = "⚠️ No quiz answers received. Please try again."
        return {
            **state,
            "messages": [create_ai_message(error_msg)],
            "quiz_score": 0,
            "waiting_for_input": False
        }
    
    # Calculate score based on correct answers
    correct_count = 0
    total_questions = len(quiz.questions)
    weak_points = []
    results_text = "## 📊 Quiz Results\n\n"
    
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
            correct_answer_bool = question.correct_answer
            user_answer_bool = str(user_answer).strip().lower() == "true"
            is_correct = user_answer_bool == correct_answer_bool
            print(f"Q{i+1} [T/F]: User='{user_answer}' -> {user_answer_bool}, Correct={correct_answer_bool} Match={is_correct}")
        
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
        
        # Add to results display
        status = "✅" if is_correct else "❌"
        results_text += f"{status} **Question {i+1}:** {question.question}\n"
        results_text += f"   Your answer: {user_answer}\n\n"
        
        if is_correct:
            correct_count += 1
        else:
            # Track weak points for wrong answers
            weak_points.append(question.question[:50])  # First 50 chars
    
    score = int((correct_count / total_questions) * 100) if total_questions > 0 else 0
    
    print(f"✓ Quiz scored: {score}% ({correct_count}/{total_questions} correct)")
    
    # Add score summary
    results_text += f"\n### Final Score: {score}%\n"
    results_text += f"You got {correct_count} out of {total_questions} questions correct.\n\n"
    
    if score >= 80:
        results_text += "🎉 Excellent work! You have a strong understanding of the material.\n"
    elif score >= 60:
        results_text += "👍 Good job! You're making progress.\n"
    else:
        results_text += "💪 Keep practicing! Let's review some concepts.\n"
    
    return {
        **state,
        "messages": [create_ai_message(results_text)],
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
    
    # Format assignment for chat UI
    assignment_text = f"# 📋 {assignment.title}\n\n"
    assignment_text += f"## 📖 Background\n{assignment.background}\n\n"
    assignment_text += f"## 🎯 Objective\n{assignment.objective}\n\n"
    assignment_text += f"## 📝 Instructions\n\n"
    
    for i, step in enumerate(assignment.steps, 1):
        assignment_text += f"{i}. {step.instruction}\n"
        if step.expected_outcome:
            assignment_text += f"   *Expected outcome: {step.expected_outcome}*\n"
        if step.hints:
            assignment_text += f"   💡 *Hint: {step.hints[0]}*\n"
        assignment_text += "\n"
    
    assignment_text += f"## ✅ Success Criteria\n\n"
    for criterion in assignment.success_criteria:
        assignment_text += f"- {criterion}\n"
    
    assignment_text += "\n📤 Please submit your completed assignment when ready!"
    
    # Set waiting_for_input to pause for user submission
    return {
        **state,
        "messages": [create_ai_message(assignment_text)],
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
    
    # Try to parse submission from the last user message
    submission = state.get('assignment_submission', "") or ""
    messages = state.get("messages", [])
    
    if not submission and messages:
        # Find the last human message
        human_messages = [m for m in messages if hasattr(m, 'type') and m.type == 'human']
        if human_messages:
            msg_content = human_messages[-1].content
            # Handle content that could be string or list
            raw_message = msg_content if isinstance(msg_content, str) else str(msg_content)
            
            # Format assignment description for parser context
            assignment_desc = f"{assignment.title}\n{assignment.objective}\n\nSteps:\n"
            assignment_desc += "\n".join([f"{s.step_number}. {s.instruction}" for s in assignment.steps])
            
            print(f"\n{'='*70}")
            print(f"DEBUG: Parsing assignment submission from message")
            print(f"Raw message: {raw_message[:200]}...")
            print(f"{'='*70}\n")
            
            # Parse the submission from natural language
            from app.agents import parse_assignment_submission
            try:
                submission = await parse_assignment_submission(raw_message, assignment_desc)
                print(f"Parsed submission length: {len(submission)} chars")
            except Exception as e:
                print(f"Error parsing assignment submission: {e}")
                submission = ""
    
    if not submission or submission.strip() == "":
        print("⚠️ No submission provided, assigning low score")
        no_submission_msg = "⚠️ No submission received. Please submit your assignment to continue."
        # Create a minimal grading result
        return {
            **state,
            "messages": [create_ai_message(no_submission_msg)],
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
    
    # Format grading result for chat UI
    grading_text = f"# ✏️ Assignment Grading Results\n\n"
    grading_text += f"## 📊 Score: {grading_result.score}%\n"
    grading_text += f"**Grade Level:** {grading_result.grade_level}\n\n"
    
    if grading_result.strengths:
        grading_text += f"## ✅ Strengths\n\n"
        for strength in grading_result.strengths:
            grading_text += f"- {strength}\n"
        grading_text += "\n"
    
    if grading_result.weak_points:
        grading_text += f"## 📝 Areas for Improvement\n\n"
        for weakness in grading_result.weak_points:
            grading_text += f"- {weakness}\n"
        grading_text += "\n"
    
    grading_text += f"## 💬 Detailed Feedback\n\n{grading_result.detailed_feedback}\n\n"
    
    if grading_result.recommendations:
        grading_text += f"## 💡 Recommendations\n\n"
        for recommendation in grading_result.recommendations:
            grading_text += f"- {recommendation}\n"
    
    return {
        **state,
        "messages": [create_ai_message(grading_text)],
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
        assignment_score=state.get('assignment_score',0),
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
    
    # Format advancement message for chat UI
    advance_text = f"# 🎉 Lesson Complete!\n\n"
    advance_text += f"Congratulations on completing **{current_lesson.title}**!\n\n"
    advance_text += f"## 🔑 Key Takeaways\n\n"
    for takeaway in current_lesson.key_concepts[:3]:
        advance_text += f"- {takeaway}\n"
    advance_text += f"\n{advance_msg.message}\n\n"
    
    if next_idx < len(learning_plan.lessons):
        advance_text += f"**Next up:** {next_lesson_title} 🚀"
    else:
        advance_text += "You're ready for the final steps! 🎓"
    
    return {
        **state,
        "messages": [create_ai_message(advance_text)],
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
    
    # Format repeat message for chat UI
    repeat_text = f"# 🔄 Let's Review: {current_lesson.title}\n\n"
    repeat_text += f"{repeat_msg.message}\n\n"
    repeat_text += f"## 🎯 Focus Areas\n\n"
    for area in repeat_msg.focus_areas:
        repeat_text += f"- {area}\n"
    repeat_text += "\nLet's try this again with these areas in mind! 💪"
    
    return {
        **state,
        "messages": [create_ai_message(repeat_text)],
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


def route_after_extraction(state: LearningState) -> Literal["generate_plan", "request_new_query"]:
    """Route based on whether extraction was successful"""
    # Check if topic and background are properly extracted
    topic = state.get("topic", "").strip()
    background = state.get("background", "").strip()
    
    # Check if extraction failed (as specified in the prompt)
    failed_values = ["failed to detect", "failed"]
    
    topic_failed = not topic or any(fail in topic.lower() for fail in failed_values)
    background_failed = not background or any(fail in background.lower() for fail in failed_values)
    
    # If extraction successful (both topic and background are valid), proceed
    if not topic_failed and not background_failed:
        return "generate_plan"
    
    # Otherwise, request new query from user
    return "request_new_query"


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
    graph.add_node("extract", extract_topic_and_background_node)
    graph.add_node("check_extraction", check_extraction_result)
    graph.add_node("request_new_query", request_new_query)
    graph.add_node("generate_plan", generate_learning_plan)
    graph.add_node("check_progress", check_progress_node)
    graph.add_node("lecture", give_lecture)
    graph.add_node("quiz", administer_quiz)
    graph.add_node("process_quiz", process_quiz_answers)
    graph.add_node("assignment", create_assignment_node)
    graph.add_node("grade", grade_assignment_node)
    graph.add_node("advance", advance_lesson)
    graph.add_node("repeat", repeat_lesson)
    
    # Set entry point to extraction
    graph.set_entry_point("extract")
    
    # Check extraction and route accordingly
    graph.add_edge("extract", "check_extraction")
    graph.add_conditional_edges(
        "check_extraction",
        route_after_extraction,
        {
            "generate_plan": "generate_plan",
            "request_new_query": "request_new_query"
        }
    )
    
    # Loop back from request_new_query to extract after getting new input
    graph.add_edge("request_new_query", "extract")
    
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
        interrupt_before=["request_new_query"],
        interrupt_after=["quiz", "assignment"],
        debug=True  # Pause before requesting new query, processing quiz and grading
    )
    
    return app
