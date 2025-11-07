from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from app.models import (
    LearningPlan, Lecture, Quiz, Assignment, GradingResult,
    ProgressDecision, RepeatMessage, AdvanceMessage, ShortAnswerEvaluation
)
from app.tools import search
from app.prompts import (
    LEARNING_PLAN_SYSTEM_PROMPT, 
    LEARNING_PLAN_PROMPT, 
    LECTURE_SYSTEM_PROMPT, 
    LECTURE_PROMPT,
    QUIZ_SYSTEM_PROMPT,
    QUIZ_PROMPT,
    ASSIGNMENT_SYSTEM_PROMPT,
    ASSIGNMENT_PROMPT,
    GRADING_SYSTEM_PROMPT,
    GRADING_PROMPT,
    PROGRESS_CHECK_SYSTEM_PROMPT,
    PROGRESS_CHECK_PROMPT,
    REPEAT_LESSON_SYSTEM_PROMPT,
    REPEAT_LESSON_PROMPT,
    ADVANCE_LESSON_SYSTEM_PROMPT,
    ADVANCE_LESSON_PROMPT,
    SHORT_ANSWER_EVALUATION_SYSTEM_PROMPT,
    SHORT_ANSWER_EVALUATION_PROMPT
)

curriculum_agent = create_agent(
    "anthropic:claude-haiku-4-5-20251001",
    tools=[search],
    system_prompt=LEARNING_PLAN_SYSTEM_PROMPT,
    response_format=ToolStrategy(LearningPlan)
)

lecture_agent = create_agent(
    "anthropic:claude-haiku-4-5-20251001",
    tools=[search],
    system_prompt=LECTURE_SYSTEM_PROMPT,
    response_format=ToolStrategy(Lecture)
)

quiz_agent = create_agent(
    "anthropic:claude-haiku-4-5-20251001",
    tools=[],
    system_prompt=QUIZ_SYSTEM_PROMPT,
    response_format=ToolStrategy(Quiz)
)

assignment_agent = create_agent(
    "anthropic:claude-haiku-4-5-20251001",
    tools=[],
    system_prompt=ASSIGNMENT_SYSTEM_PROMPT,
    response_format=ToolStrategy(Assignment)
)

grading_agent = create_agent(
    "anthropic:claude-haiku-4-5-20251001",
    tools=[],
    system_prompt=GRADING_SYSTEM_PROMPT,
    response_format=ToolStrategy(GradingResult)
)

progress_check_agent = create_agent(
    "anthropic:claude-haiku-4-5-20251001",
    tools=[],
    system_prompt=PROGRESS_CHECK_SYSTEM_PROMPT,
    response_format=ToolStrategy(ProgressDecision)
)

repeat_message_agent = create_agent(
    "anthropic:claude-haiku-4-5-20251001",
    tools=[],
    system_prompt=REPEAT_LESSON_SYSTEM_PROMPT,
    response_format=ToolStrategy(RepeatMessage)
)

advance_message_agent = create_agent(
    "anthropic:claude-haiku-4-5-20251001",
    tools=[],
    system_prompt=ADVANCE_LESSON_SYSTEM_PROMPT,
    response_format=ToolStrategy(AdvanceMessage)
)

short_answer_evaluator_agent = create_agent(
    "anthropic:claude-haiku-4-5-20251001",
    tools=[],
    system_prompt=SHORT_ANSWER_EVALUATION_SYSTEM_PROMPT,
    response_format=ToolStrategy(ShortAnswerEvaluation)
)

async def create_learning_plan(topic: str, background: str) -> LearningPlan:
    """
    Create a comprehensive learning plan for a given topic
    
    Generates a structured curriculum with 5-8 progressive lessons tailored to the
    student's background. Uses web search to find relevant resources and ensure
    up-to-date, accurate content.
    
    Args:
        topic: The subject or topic to create a learning plan for (e.g., "Python Programming",
               "Machine Learning Fundamentals", "Spanish Grammar")
        background: Description of the student's current knowledge level and experience
                   (e.g., "Complete beginner", "Knows Python basics", 
                   "Has programming experience but new to ML")
    
    Returns:
        LearningPlan: A structured learning plan containing:
            - topic: The topic being taught
            - lessons: List of 5-8 Lesson objects with objectives, concepts, and difficulty
            - total_duration_minutes: Estimated total time for all lessons
            - overall_difficulty: Overall difficulty level (Beginner/Intermediate/Advanced)
    
    Raises:
        Exception: If the agent fails to generate a valid learning plan
    
    Example:
        >>> plan = await create_learning_plan(
        ...     topic="Python Programming",
        ...     background="Complete beginner with no coding experience"
        ... )
        >>> print(f"Generated {len(plan.lessons)} lessons for {plan.topic}")
        Generated 6 lessons for Python Programming
    """
    prompt = LEARNING_PLAN_PROMPT.format(topic=topic, background=background)
    result = await curriculum_agent.ainvoke({
        "messages": [
            {"role": "user", "content": prompt}
        ]
    })
    return result['structured_response']

async def create_lecture(
    lesson_title: str,
    objectives: list[str],
    key_concepts: list[str],
    current_knowledge: str = "",
    weak_points: list[str] | None = None
) -> Lecture:
    """
    Create a lecture for a specific lesson
    
    Args:
        lesson_title: The title of the lesson
        objectives: List of learning objectives for the lesson
        key_concepts: List of key concepts to cover
        current_knowledge: Description of student's current knowledge level
        weak_points: List of weak points from previous lessons to address
        
    Returns:
        Lecture: Structured lecture content with segments
    """
    if weak_points is None:
        weak_points = []
    
    # Format the prompt with all required variables
    prompt = LECTURE_PROMPT.format(
        lesson_title=lesson_title,
        objectives="\n".join(f"- {obj}" for obj in objectives),
        key_concepts=", ".join(key_concepts),
        current_knowledge=current_knowledge or "No prior knowledge assumed",
        weak_points=", ".join(weak_points) if weak_points else "None identified"
    )
    
    # Invoke the lecture agent
    result = await lecture_agent.ainvoke({
        "messages": [
            {"role": "user", "content": prompt}
        ]
    })
    
    return result['structured_response']

async def create_quiz(
    lesson_title: str,
    objectives: list[str],
    key_concepts: list[str],
    lecture_summary: str
) -> Quiz:
    """
    Create a quiz to assess student understanding of a lecture
    
    Generates exactly 5 questions of mixed types (multiple choice, true/false, short answer)
    that test comprehension and application, not just memorization. Questions are aligned
    with learning objectives and assess understanding at different cognitive levels.
    
    Args:
        lesson_title: The title of the lesson being assessed
        objectives: List of learning objectives the quiz should test
        key_concepts: List of key concepts that should be covered in the questions
        lecture_summary: A summary of the lecture content to ensure questions are
                        answerable based on what was taught
    
    Returns:
        Quiz: A structured quiz containing:
            - lesson_title: The lesson being assessed
            - questions: List of exactly 5 Question objects (mixed types)
            - passing_score: Minimum score to pass (default 70%)
    
    Raises:
        Exception: If the agent fails to generate a valid quiz
    
    Example:
        >>> quiz = await create_quiz(
        ...     lesson_title="Python Variables",
        ...     objectives=["Understand variables", "Use data types"],
        ...     key_concepts=["variables", "int", "str", "float"],
        ...     lecture_summary="Covered variable creation and basic data types..."
        ... )
        >>> print(f"Generated {len(quiz.questions)} questions")
        Generated 5 questions
    """
    # Format the prompt with all required variables
    prompt = QUIZ_PROMPT.format(
        lesson_title=lesson_title,
        objectives="\n".join(f"- {obj}" for obj in objectives),
        key_concepts=", ".join(key_concepts),
        lecture_summary=lecture_summary
    )
    
    # Invoke the quiz agent
    result = await quiz_agent.ainvoke({
        "messages": [
            {"role": "user", "content": prompt}
        ]
    })
    
    return result['structured_response']


async def create_assignment(
    lesson_title: str,
    objectives: list[str],
    key_concepts: list[str],
    quiz_performance: str
) -> Assignment:
    """
    Creates a hands-on assignment for a lesson based on objectives and concepts.
    
    This function generates a practical assignment designed to reinforce learning
    objectives through hands-on exercises. It takes into account the student's
    quiz performance to ensure appropriate difficulty and focus areas.
    
    Args:
        lesson_title: The title/topic of the lesson
        objectives: List of learning objectives for the lesson
        key_concepts: List of key concepts that should be practiced
        quiz_performance: Summary of how the student performed on the quiz
        
    Returns:
        Assignment: A structured assignment with title, overview, steps, and criteria
        
    Example:
        >>> assignment = await create_assignment(
        ...     "Python Functions",
        ...     ["Understand function definitions", "Use parameters and return values"],
        ...     ["def keyword", "parameters", "return statement"],
        ...     "Student scored 80%, struggled with return values"
        ... )
        >>> print(assignment.title)
        "Python Functions Practice Assignment"
    """
    prompt = ASSIGNMENT_PROMPT.format(
        lesson_title=lesson_title,
        objectives="\n".join([f"- {obj}" for obj in objectives]),
        key_concepts=", ".join(key_concepts),
        quiz_results=quiz_performance,
        weak_points="None identified"  # Will be populated from actual quiz results in production
    )
    
    result = await assignment_agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})
    return result['structured_response']


async def grade_assignment(
    assignment_title: str,
    assignment_steps: list[str],
    criteria: list[str],
    student_submission: str
) -> GradingResult:
    """
    Grades a student's assignment submission based on defined criteria.
    
    This function evaluates a student's assignment work against the specified
    grading criteria and provides detailed feedback with a score and suggestions
    for improvement.
    
    Args:
        assignment_title: The title of the assignment being graded
        assignment_steps: List of steps that were part of the assignment
        criteria: List of grading criteria to evaluate against
        student_submission: The student's submitted work (code, text, etc.)
        
    Returns:
        GradingResult: Structured feedback with score, strengths, and improvements
        
    Example:
        >>> result = await grade_assignment(
        ...     "Python Functions Practice",
        ...     ["Write a function", "Add parameters", "Return a value"],
        ...     ["Correct syntax", "Proper use of parameters", "Correct output"],
        ...     "def greet(name):\n    return 'Hello ' + name"
        ... )
        >>> print(result.score)
        85
    """
    # Format assignment instructions and steps
    assignment_instructions = f"Assignment: {assignment_title}\n\nSteps:\n" + "\n".join([f"{i+1}. {step}" for i, step in enumerate(assignment_steps)])
    
    prompt = GRADING_PROMPT.format(
        assignment_instructions=assignment_instructions,
        submission=student_submission,
        success_criteria="\n".join([f"- {c}" for c in criteria]),
        objectives="Evaluate against assignment requirements"  # This should be passed from the lesson
    )
    
    result = await grading_agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})
    return result['structured_response']


async def check_progress(
    lesson_title: str,
    quiz_score: int,
    assignment_score: int,
    weak_points: list[str],
    attempt_count: int
) -> ProgressDecision:
    """
    Determines whether a student should repeat a lesson or advance to the next one.
    
    This function analyzes the student's performance on both quiz and assignment,
    considers identified weak points, and tracks the number of attempts to make
    an informed decision about progression.
    
    Args:
        lesson_title: The title of the current lesson
        quiz_score: The student's quiz score (0-100)
        assignment_score: The student's assignment score (0-100)
        weak_points: List of concepts the student struggled with
        attempt_count: Number of times the student has attempted this lesson
        
    Returns:
        ProgressDecision: Decision to repeat or advance with reasoning
        
    Example:
        >>> decision = await check_progress(
        ...     "Python Variables",
        ...     85,
        ...     90,
        ...     ["type conversion"],
        ...     1
        ... )
        >>> print(decision.decision.value)
        "advance"
    """
    prompt = PROGRESS_CHECK_PROMPT.format(
        current_lesson=lesson_title,
        total_lessons="unknown",  # Not available at this level
        quiz_score=quiz_score,
        assignment_score=assignment_score,
        weak_points=", ".join(weak_points) if weak_points else "None identified",
        attempt_count=attempt_count,
        topic="current curriculum"  # Not available at this level
    )
    
    result = await progress_check_agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})
    return result['structured_response']


async def create_repeat_message(
    lesson_title: str,
    weak_points: list[str],
    attempt_count: int
) -> RepeatMessage:
    """
    Generates an encouraging message for students who need to repeat a lesson.
    
    This function creates a supportive, motivational message that explains why
    the student should review the material and provides specific focus areas
    without discouraging them.
    
    Args:
        lesson_title: The title of the lesson being repeated
        weak_points: List of specific concepts to focus on during review
        attempt_count: Number of times the student has attempted this lesson
        
    Returns:
        RepeatMessage: Encouraging message with focus areas and study tips
        
    Example:
        >>> message = await create_repeat_message(
        ...     "Python Functions",
        ...     ["return statements", "parameter passing"],
        ...     2
        ... )
        >>> print(message.message)
        "Let's review Python Functions together..."
    """
    prompt = REPEAT_LESSON_PROMPT.format(
        quiz_score="N/A",  # Not available at this level
        assignment_score="N/A",  # Not available at this level
        attempt_count=attempt_count,
        weak_points=", ".join(weak_points) if weak_points else "general concepts",
        objectives=f"Master the concepts in {lesson_title}"
    )
    
    result = await repeat_message_agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})
    return result['structured_response']


async def create_advance_message(
    completed_lesson: str,
    next_lesson: str,
    key_takeaways: list[str]
) -> AdvanceMessage:
    """
    Generates a congratulatory message for students advancing to the next lesson.
    
    This function creates a motivational message that celebrates the student's
    achievement, summarizes key takeaways from the completed lesson, and builds
    excitement for the upcoming material.
    
    Args:
        completed_lesson: The title of the lesson just completed
        next_lesson: The title of the next lesson
        key_takeaways: List of important concepts mastered in the completed lesson
        
    Returns:
        AdvanceMessage: Congratulatory message with preview of next lesson
        
    Example:
        >>> message = await create_advance_message(
        ...     "Python Variables",
        ...     "Python Data Types",
        ...     ["Variable assignment", "Naming conventions", "Type basics"]
        ... )
        >>> print(message.message)
        "Excellent work on Python Variables!..."
    """
    prompt = ADVANCE_LESSON_PROMPT.format(
        completed_lesson=completed_lesson,
        quiz_score="N/A",  # Not available at this level
        assignment_score="N/A",  # Not available at this level
        next_lesson=next_lesson,
        current_lesson="N/A",  # Not available at this level
        total_lessons="N/A"  # Not available at this level
    )
    
    result = await advance_message_agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})
    return result['structured_response']


async def evaluate_short_answer(question: str, key_points: list[str], student_answer: str) -> bool:
    """
    Evaluate a short answer question using an LLM
    
    Uses an AI agent to determine if a student's short answer demonstrates sufficient
    understanding of the concept. More sophisticated than keyword matching.
    
    Args:
        question: The question that was asked
        key_points: List of key concepts or points that should be addressed
        student_answer: The student's written response
        
    Returns:
        bool: True if answer demonstrates sufficient understanding, False otherwise
        
    Example:
        >>> is_correct = await evaluate_short_answer(
        ...     "What is a variable in programming?",
        ...     ["storage location", "named reference", "holds data"],
        ...     "A variable is like a box that stores information"
        ... )
        >>> print(is_correct)
        True
    """
    key_points_str = ", ".join(key_points)
    prompt = SHORT_ANSWER_EVALUATION_PROMPT.format(
        question=question,
        key_points=key_points_str,
        student_answer=student_answer
    )
    
    result = await short_answer_evaluator_agent.ainvoke({
        "messages": [{"role": "user", "content": prompt}]
    })
    
    evaluation = result['structured_response']
    print(f"[Short Answer Eval] Question: '{question[:50]}...'")
    print(f"[Short Answer Eval] Student: '{student_answer[:50]}...'")
    print(f"[Short Answer Eval] Result: {evaluation.is_correct} - {evaluation.reasoning}")
    
    return evaluation.is_correct