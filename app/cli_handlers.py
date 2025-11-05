"""
CLI Input Handlers for Professor Agent

This module contains all interactive input handling functions for the CLI,
including quiz and assignment submission interfaces.
"""
import textwrap
from app.models import QuestionType
from app.cli_formatting import print_box, print_slow


async def handle_quiz(state):
    """
    Handle quiz interaction with robust error handling.
    
    Displays quiz questions with proper formatting and collects user answers.
    Supports multiple choice, true/false, and short answer questions.
    
    Args:
        state: LearningState dictionary containing quiz_results
        
    Returns:
        dict: Dictionary mapping question IDs (q0, q1, etc.) to user answers
        
    Example:
        >>> answers = await handle_quiz(state)
        >>> print(answers)
        {'q0': 'A', 'q1': 'True', 'q2': 'Python is a programming language'}
    """
    # Validate state is a dict
    if not isinstance(state, dict):
        print(f"Error: Invalid state type: {type(state)}")
        return {}
    
    quiz = state.get("quiz_results")
    if not quiz:
        return {}
    
    print_box(f"📝 QUIZ TIME! (Pass: {quiz.passing_score}%)", "=")
    answers = {}
    correct_answers = {}  # Track correct answers for debug
    
    for i, question in enumerate(quiz.questions):
        print(f"\n{'─' * 70}")
        print(f"Question {i+1}:")
        print()
        
        # Wrap question text
        question_wrapped = textwrap.fill(question.question, width=68, initial_indent="  ", subsequent_indent="  ")
        print(question_wrapped)
        print()
        
        try:
            if question.type == QuestionType.MULTIPLE_CHOICE:
                # Print options with proper formatting
                for idx, option in enumerate(question.options):
                    option_wrapped = textwrap.fill(option, width=64, initial_indent=f"  {chr(65+idx)}. ", subsequent_indent="     ")
                    print(option_wrapped)
                print()
                
                # Store correct answer for debug
                correct_answers[f"q{i}"] = question.correct_answer
                
                max_attempts = 3
                for attempt in range(max_attempts):
                    try:
                        answer = input("Your answer (A/B/C/D): ").strip().upper()
                        if answer in ['A', 'B', 'C', 'D']:
                            answers[f"q{i}"] = answer
                            break
                        print(f"Invalid input. Please enter A, B, C, or D. ({max_attempts - attempt - 1} attempts left)")
                    except (EOFError, KeyboardInterrupt):
                        print("\nSkipping question...")
                        answers[f"q{i}"] = "A"  # Default answer
                        break
                else:
                    # Max attempts reached, use default
                    print("Max attempts reached. Using default answer 'A'.")
                    answers[f"q{i}"] = "A"
            
            elif question.type == QuestionType.TRUE_FALSE:
                # Store correct answer for debug
                correct_answers[f"q{i}"] = str(question.correct_answer)
                
                max_attempts = 3
                for attempt in range(max_attempts):
                    try:
                        answer = input("Your answer (True/False): ").strip().capitalize()
                        if answer in ['True', 'False']:
                            answers[f"q{i}"] = answer
                            break
                        print(f"Invalid input. Please enter True or False. ({max_attempts - attempt - 1} attempts left)")
                    except (EOFError, KeyboardInterrupt):
                        print("\nSkipping question...")
                        answers[f"q{i}"] = "True"  # Default answer
                        break
                else:
                    # Max attempts reached, use default
                    print("Max attempts reached. Using default answer 'True'.")
                    answers[f"q{i}"] = "True"
            
            elif question.type == QuestionType.SHORT_ANSWER:
                # Store correct answer info for debug
                correct_answers[f"q{i}"] = f"Key points: {', '.join(question.key_points[:3])}"
                
                try:
                    answer = input("Your answer: ").strip()
                    # Validate it's not empty or weird type
                    if not answer or not isinstance(answer, str):
                        print("Empty answer, using placeholder.")
                        answer = "No answer provided"
                    answers[f"q{i}"] = answer
                except (EOFError, KeyboardInterrupt):
                    print("\nUsing placeholder answer...")
                    answers[f"q{i}"] = "No answer provided"
        
        except Exception as e:
            print(f"Error processing question {i+1}: {e}")
            answers[f"q{i}"] = "Error"
    
    # Debug: Print correct answers
    print(f"\n{'='*70}")
    print("🔍 DEBUG - CORRECT ANSWERS:")
    for key, value in correct_answers.items():
        print(f"  {key}: {value}")
    print('='*70 + "\n")
    
    return answers


async def handle_assignment(state):
    """
    Handle assignment interaction with robust error handling.
    
    Displays assignment details and collects multi-line user submission.
    Users can enter multiple lines and press Enter twice to submit, or type
    'SKIP' to skip the assignment.
    
    Args:
        state: LearningState dictionary containing assignment
        
    Returns:
        str: User's assignment submission text
        
    Example:
        >>> submission = await handle_assignment(state)
        >>> print(submission)
        "Here is my solution to the assignment..."
    """
    # Validate state is a dict
    if not isinstance(state, dict):
        print(f"Error: Invalid state type: {type(state)}")
        return ""
    
    assignment = state.get("assignment")
    if not assignment:
        return ""
    
    # Header
    print(f"\n{'='*80}")
    print(f"📋 ASSIGNMENT: {assignment.title}")
    print('='*80 + "\n")
    
    # Background
    print("📖 BACKGROUND")
    print("-" * 80)
    background_wrapped = textwrap.fill(assignment.background, width=78, initial_indent="  ", subsequent_indent="  ")
    print(f"{background_wrapped}\n")
    
    # Objective
    print("🎯 OBJECTIVE")
    print("-" * 80)
    objective_wrapped = textwrap.fill(assignment.objective, width=78, initial_indent="  ", subsequent_indent="  ")
    print(f"{objective_wrapped}\n")
    
    # Instructions
    print("📝 INSTRUCTIONS")
    print("-" * 80)
    for i, step in enumerate(assignment.steps, 1):
        instruction_wrapped = textwrap.fill(
            step.instruction,
            width=76,
            initial_indent="  ",
            subsequent_indent="     "
        )
        print(f"{i}. {instruction_wrapped[3:]}")  # Remove initial indent, we add number
        print()
    
    # Success Criteria
    print("✅ SUCCESS CRITERIA")
    print("-" * 80)
    for criterion in assignment.success_criteria:
        criterion_wrapped = textwrap.fill(criterion, width=76, initial_indent="  ", subsequent_indent="     ")
        print(f"  • {criterion_wrapped[4:]}")  # Remove initial spaces, add bullet
    
    print("\n" + "=" * 80)
    print("📤 YOUR SUBMISSION")
    print("=" * 80)
    print("Type your answer below (press Enter twice when done, or type 'SKIP' to skip)")
    print("-" * 80)
    
    lines = []
    empty_count = 0
    
    try:
        while True:
            try:
                line = input()
                
                # Check for skip command
                if line.strip().upper() == "SKIP":
                    print("Skipping assignment with placeholder...")
                    return "Assignment skipped by user"
                
                if line == "":
                    empty_count += 1
                    if empty_count >= 2:
                        break
                else:
                    empty_count = 0
                    # Validate line is a string
                    if isinstance(line, str):
                        lines.append(line)
                    else:
                        print(f"Warning: Invalid input type {type(line)}, skipping line")
            
            except EOFError:
                print("\nEnd of input detected.")
                break
            except KeyboardInterrupt:
                print("\n\nAssignment interrupted. Using partial submission...")
                break
            except Exception as e:
                print(f"Error reading input: {e}")
                break
    
    except Exception as e:
        print(f"Error during assignment submission: {e}")
        return "Error occurred during submission"
    
    submission = "\n".join(lines).strip()
    
    # Validate submission is not empty or weird type
    if not submission:
        print("Empty submission, using placeholder.")
        return "No submission provided"
    
    if not isinstance(submission, str):
        print(f"Invalid submission type: {type(submission)}, converting to string.")
        return str(submission)
    
    return submission
