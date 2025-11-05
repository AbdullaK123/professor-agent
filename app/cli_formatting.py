"""
CLI Formatting Utilities for Professor Agent

This module contains all formatting and display functions for the interactive CLI,
including text wrapping, visual separators, and node output rendering.
"""
import time
import textwrap


def print_slow(text, delay=0.02):
    """
    Print text character by character with a delay for dramatic effect.
    
    Args:
        text: Text to print
        delay: Delay between characters in seconds (default: 0.02)
    """
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)


def print_box(text, border='='):
    """
    Print text in a bordered box for emphasis.
    
    Args:
        text: Text to display in the box (supports multi-line with \\n)
        border: Border character to use (default: '=')
        
    Example:
        >>> print_box("Hello World", "=")
        ===================
        = Hello World     =
        ===================
    """
    lines = text.split('\n')
    max_len = max(len(line) for line in lines) if lines else 0
    border_line = border * (max_len + 4)
    print(border_line)
    for line in lines:
        print(f"{border} {line.ljust(max_len)} {border}")
    print(border_line)


def format_lecture_content(content, width=78, indent="  "):
    """
    Format lecture content while preserving markdown structure.
    
    Intelligently handles different markdown elements:
    - Preserves blank lines for paragraph separation
    - Preserves markdown headings (#, ##, ###)
    - Preserves code blocks (``` fenced blocks)
    - Preserves lists (lines starting with -, *, numbers)
    - Wraps regular paragraphs to specified width
    - Preserves blockquotes (>)
    - Preserves bold/italic markdown syntax
    
    Args:
        content: Raw lecture content text with markdown
        width: Maximum line width for wrapped text (default: 78)
        indent: Indentation prefix for formatted text (default: "  ")
        
    Returns:
        Formatted content string with markdown structure preserved
    """
    lines = content.split('\n')
    formatted_lines = []
    i = 0
    in_code_block = False
    
    while i < len(lines):
        line = lines[i]
        
        # Handle code block fences
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            formatted_lines.append(indent + line.strip())
            i += 1
            continue
        
        # Preserve code block content as-is
        if in_code_block:
            formatted_lines.append(indent + line)
            i += 1
            continue
        
        # Preserve blank lines
        if not line.strip():
            formatted_lines.append('')
            i += 1
            continue
        
        # Preserve markdown headings
        if line.strip().startswith('#'):
            formatted_lines.append(indent + line.strip())
            i += 1
            continue
        
        # Preserve blockquotes
        if line.strip().startswith('>'):
            wrapped = textwrap.fill(line.strip(), width=width-2, initial_indent=indent + "> ", subsequent_indent=indent + "> ")
            formatted_lines.append(wrapped)
            i += 1
            continue
        
        # Preserve list items (markdown lists)
        stripped = line.strip()
        if (stripped.startswith(('-', '*', '+', '•')) or 
            (stripped and len(stripped) > 1 and stripped[0].isdigit() and stripped[1] in '.)')):
            # Wrap list item content while preserving list marker
            wrapped = textwrap.fill(line, width=width-2, initial_indent=indent, subsequent_indent=indent + "  ")
            formatted_lines.append(wrapped)
            i += 1
            continue
        
        # Preserve indented code (4 spaces or tab)
        if line.startswith(('    ', '\t')):
            formatted_lines.append(indent + line)
            i += 1
            continue
        
        # Regular paragraph - collect consecutive non-special lines
        paragraph_lines = [line]
        i += 1
        while i < len(lines):
            next_line = lines[i]
            # Stop if we hit a special element
            if (not next_line.strip() or 
                next_line.strip().startswith(('#', '```', '>', '-', '*', '+', '•')) or
                next_line.startswith(('    ', '\t')) or
                (next_line.strip() and len(next_line.strip()) > 1 and 
                 next_line.strip()[0].isdigit() and next_line.strip()[1] in '.)')):
                break
            paragraph_lines.append(next_line)
            i += 1
        
        # Join and wrap the paragraph (preserve markdown formatting like **bold** and *italic*)
        paragraph = ' '.join(line.strip() for line in paragraph_lines)
        wrapped = textwrap.fill(paragraph, width=width, initial_indent=indent, subsequent_indent=indent)
        formatted_lines.append(wrapped)
    
    return '\n'.join(formatted_lines)


def display_learning_plan(plan, topic):
    """
    Display a formatted learning plan.
    
    Args:
        plan: LearningPlan object
        topic: Topic string
    """
    print(f"\n{'='*80}")
    print(f"📚 LEARNING PLAN: {topic}")
    print('='*80)
    print(f"Total Duration: {plan.total_duration_minutes} minutes")
    print(f"Difficulty: {plan.overall_difficulty}")
    print(f"Lessons: {len(plan.lessons)}\n")
    
    for i, lesson in enumerate(plan.lessons, 1):
        print(f"{i}. {lesson.title}")
        print(f"   Duration: {lesson.duration_minutes} min | Difficulty: {lesson.difficulty}")
        print(f"   Objectives:")
        for obj in lesson.objectives[:3]:  # Show first 3 objectives
            obj_wrapped = textwrap.fill(obj, width=70, initial_indent="     • ", subsequent_indent="       ")
            print(obj_wrapped)
        print()
    
    print('='*80 + "\n")


def display_lecture(lecture):
    """
    Display a formatted lecture with streaming text.
    
    Args:
        lecture: Lecture object with lesson_title, introduction, segments, conclusion, key_takeaways
    """
    # Header
    print(f"\n{'='*80}")
    print(f"🎤 LECTURE: {lecture.lesson_title}")
    print('='*80 + "\n")
    
    # Introduction
    print("📖 INTRODUCTION")
    print("-" * 80)
    intro_formatted = format_lecture_content(lecture.introduction, width=78, indent="  ")
    print_slow(f"{intro_formatted}\n\n")
    
    # Content segments
    for i, segment in enumerate(lecture.segments, 1):
        print(f"{'─'*80}")
        print(f"📚 PART {i}: {segment.title}")
        print(f"{'─'*80}")
        
        # Format content preserving structure
        content_formatted = format_lecture_content(segment.content, width=78, indent="  ")
        print_slow(f"{content_formatted}\n\n")
    
    # Conclusion
    print(f"{'='*80}")
    print("🎯 CONCLUSION")
    print('='*80)
    conclusion_formatted = format_lecture_content(lecture.conclusion, width=78, indent="  ")
    print_slow(f"{conclusion_formatted}\n")
    
    # Key takeaways
    if hasattr(lecture, 'key_takeaways') and lecture.key_takeaways:
        print("\n💡 KEY TAKEAWAYS:")
        for j, takeaway in enumerate(lecture.key_takeaways, 1):
            takeaway_wrapped = textwrap.fill(takeaway, width=74, initial_indent="", subsequent_indent="    ")
            print_slow(f"  {j}. {takeaway_wrapped}\n")
    
    print(f"{'='*80}\n")


def display_quiz_score(score):
    """
    Display quiz score with appropriate styling.
    
    Args:
        score: Quiz score as integer percentage
    """
    print_box(f"📊 QUIZ SCORE: {score}%", "=" if score >= 70 else "!")


def display_grading_result(result):
    """
    Display assignment grading results with consistent formatting.
    
    Args:
        result: GradingResult object with score, grade_level, strengths, improvements
    """
    print(f"\n{'='*80}")
    print(f"✏️  ASSIGNMENT GRADED: {result.score}% ({result.grade_level})")
    print('='*80 + "\n")
    
    print("✅ STRENGTHS")
    print("-" * 80)
    for i, strength in enumerate(result.strengths, 1):
        # Wrap with proper indentation
        strength_wrapped = textwrap.fill(
            strength, 
            width=76, 
            initial_indent="  ", 
            subsequent_indent="  "
        )
        print(f"{i}. {strength_wrapped[3:]}")  # Remove initial indent from first line since we add number
        print()
    
    print("📝 AREAS FOR IMPROVEMENT")
    print("-" * 80)
    for i, improvement in enumerate(result.improvements, 1):
        # Wrap with proper indentation
        improvement_wrapped = textwrap.fill(
            improvement,
            width=76,
            initial_indent="  ",
            subsequent_indent="  "
        )
        print(f"{i}. {improvement_wrapped[3:]}")  # Remove initial indent from first line
        print()
    
    print('='*80 + "\n")


def display_advance_message(message):
    """
    Display message when advancing to next lesson.
    
    Args:
        message: Message string
    """
    if message:
        print_box(f"🎉 {message}", "=")


def display_repeat_message(message):
    """
    Display message when repeating a lesson.
    
    Args:
        message: Message string
    """
    if message:
        print_box(f"🔄 {message}", "!")
