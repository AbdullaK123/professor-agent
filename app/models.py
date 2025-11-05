from pydantic import BaseModel, Field
from typing import Literal, Optional
from enum import Enum


# Enums for type safety
class DifficultyLevel(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"


class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"


class Decision(str, Enum):
    ADVANCE = "advance"
    REPEAT = "repeat"


class Confidence(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


# Models for Learning Plan
class Lesson(BaseModel):
    """Individual lesson in a learning plan"""
    lesson_number: int = Field(..., description="Sequential lesson number")
    title: str = Field(..., description="Descriptive lesson title")
    objectives: list[str] = Field(..., min_length=3, max_length=5, description="3-5 specific learning objectives")
    key_concepts: list[str] = Field(..., description="Main concepts covered in this lesson")
    duration_minutes: int = Field(..., ge=15, le=120, description="Estimated lesson duration in minutes")
    prerequisites: list[str] = Field(default_factory=list, description="Required knowledge from previous lessons")
    difficulty: DifficultyLevel = Field(..., description="Difficulty level of the lesson")


class LearningPlan(BaseModel):
    """Complete learning plan for a topic"""
    topic: str = Field(..., description="The main topic being taught")
    lessons: list[Lesson] = Field(..., min_length=5, max_length=8, description="5-8 progressive lessons")
    total_duration_minutes: int = Field(..., description="Total estimated time for all lessons")
    overall_difficulty: DifficultyLevel = Field(..., description="Overall difficulty of the course")


# Models for Lecture
class LectureSegment(BaseModel):
    """A segment of the lecture content"""
    segment_number: int = Field(..., description="Order of this segment")
    title: str = Field(..., description="Segment title")
    content: str = Field(..., description="The actual lecture content for this segment")
    duration_minutes: int = Field(..., ge=3, le=8, description="Duration of this segment")
    interaction_points: list[str] = Field(default_factory=list, description="Questions or reflection points")


class Lecture(BaseModel):
    """Complete lecture content"""
    lesson_title: str = Field(..., description="Title of the lesson")
    introduction: str = Field(..., description="2-3 minute introduction with overview and objectives")
    segments: list[LectureSegment] = Field(..., min_length=2, max_length=3, description="2-3 main content segments")
    conclusion: str = Field(..., description="2-3 minute conclusion with summary and next steps")
    total_duration_minutes: int = Field(..., ge=15, le=20, description="Total lecture duration")
    key_takeaways: list[str] = Field(..., description="Main points students should remember")


# Models for Quiz
class MultipleChoiceQuestion(BaseModel):
    """Multiple choice question"""
    question: str = Field(..., description="The question text")
    type: Literal[QuestionType.MULTIPLE_CHOICE] = QuestionType.MULTIPLE_CHOICE
    options: list[str] = Field(..., min_length=4, max_length=4, description="Exactly 4 answer options (A, B, C, D)")
    correct_answer: str = Field(..., description="The correct option (e.g., 'A', 'B', 'C', or 'D')")
    explanation: str = Field(..., description="Explanation of why the answer is correct")
    misconceptions: list[str] = Field(default_factory=list, description="Common wrong assumptions")


class TrueFalseQuestion(BaseModel):
    """True/False question with explanation requirement"""
    question: str = Field(..., description="The question text")
    type: Literal[QuestionType.TRUE_FALSE] = QuestionType.TRUE_FALSE
    correct_answer: bool = Field(..., description="True or False")
    explanation: str = Field(..., description="Detailed explanation of the correct answer")
    misconceptions: list[str] = Field(default_factory=list, description="Common wrong assumptions")


class ShortAnswerQuestion(BaseModel):
    """Short answer or application question"""
    question: str = Field(..., description="The question text")
    type: Literal[QuestionType.SHORT_ANSWER] = QuestionType.SHORT_ANSWER
    correct_answer: str = Field(..., description="Sample correct answer")
    key_points: list[str] = Field(..., description="Key points that should be in a correct answer")
    explanation: str = Field(..., description="Explanation of what makes a good answer")
    misconceptions: list[str] = Field(default_factory=list, description="Common wrong assumptions")


class Quiz(BaseModel):
    """Complete quiz with 5 questions"""
    lesson_title: str = Field(..., description="The lesson this quiz assesses")
    questions: list[MultipleChoiceQuestion | TrueFalseQuestion | ShortAnswerQuestion] = Field(
        ..., 
        min_length=5, 
        max_length=5, 
        description="Exactly 5 questions of mixed types"
    )
    passing_score: int = Field(default=70, ge=0, le=100, description="Minimum score to pass (default 70%)")


class QuizResults(BaseModel):
    """Results from a student's quiz attempt"""
    quiz_title: str = Field(..., description="Title of the quiz taken")
    total_questions: int = Field(..., description="Total number of questions")
    correct_answers: int = Field(..., description="Number of correct answers")
    score_percentage: float = Field(..., ge=0, le=100, description="Score as a percentage")
    passed: bool = Field(..., description="Whether the student passed")
    missed_concepts: list[str] = Field(default_factory=list, description="Concepts from missed questions")
    time_taken_minutes: Optional[int] = Field(None, description="Time taken to complete quiz")


# Models for Assignment
class AssignmentStep(BaseModel):
    """Individual step in an assignment"""
    step_number: int = Field(..., description="Sequential step number")
    instruction: str = Field(..., description="What the student needs to do")
    expected_outcome: str = Field(..., description="What should result from this step")
    hints: list[str] = Field(default_factory=list, description="Optional hints to help")


class Assignment(BaseModel):
    """Complete assignment"""
    title: str = Field(..., description="Assignment title")
    lesson_title: str = Field(..., description="Related lesson")
    objective: str = Field(..., description="What the assignment aims to achieve")
    background: str = Field(..., description="Context or scenario for the assignment")
    steps: list[AssignmentStep] = Field(..., min_length=5, max_length=8, description="5-8 step-by-step instructions")
    deliverables: list[str] = Field(..., description="What the student should submit")
    success_criteria: list[str] = Field(..., description="How the assignment will be evaluated")
    estimated_duration_minutes: int = Field(..., ge=30, le=60, description="Expected time to complete")
    resources: list[str] = Field(default_factory=list, description="Helpful resources or references")
    bonus_challenges: list[str] = Field(default_factory=list, description="Optional extra credit tasks")


# Models for Grading
class GradingResult(BaseModel):
    """Results from grading an assignment"""
    assignment_title: str = Field(..., description="Title of the graded assignment")
    score: float = Field(..., ge=0, le=100, description="Score out of 100")
    passed: bool = Field(..., description="Whether the student passed (score >= 70)")
    strengths: list[str] = Field(..., min_length=2, max_length=3, description="2-3 things done well")
    improvements: list[str] = Field(..., min_length=2, max_length=3, description="2-3 areas needing work")
    recommendations: list[str] = Field(..., description="Concrete steps for improvement")
    weak_points: list[str] = Field(default_factory=list, description="Concepts needing reinforcement")
    detailed_feedback: str = Field(..., description="Overall narrative feedback")
    grade_level: Literal["Exceeds", "Meets", "Partially Meets", "Does Not Meet"] = Field(
        ..., 
        description="Qualitative grade level"
    )


# Models for Progress Decision
class ProgressDecision(BaseModel):
    """Decision on whether to advance or repeat"""
    decision: Decision = Field(..., description="Whether to advance or repeat the lesson")
    reasoning: str = Field(..., description="Detailed explanation of the decision")
    focus_areas: list[str] = Field(default_factory=list, description="Areas to focus on (especially if repeating)")
    confidence: Confidence = Field(..., description="Confidence level in this decision")
    current_lesson: int = Field(..., description="Current lesson number")
    total_lessons: int = Field(..., description="Total lessons in the plan")
    quiz_score: float = Field(..., ge=0, le=100, description="Quiz score percentage")
    assignment_score: float = Field(..., ge=0, le=100, description="Assignment score percentage")
    attempt_count: int = Field(..., ge=1, le=3, description="Number of attempts at this lesson")


# Models for Student Messages
class RepeatMessage(BaseModel):
    """Encouraging message for repeating a lesson"""
    message: str = Field(..., description="Main encouraging message")
    acknowledgment: str = Field(..., description="Positive acknowledgment of effort")
    explanation: str = Field(..., description="Why repetition helps learning")
    focus_areas: list[str] = Field(..., min_length=2, max_length=3, description="2-3 specific areas to focus on")
    study_tips: list[str] = Field(..., description="Strategies for improvement")
    expectations: str = Field(..., description="What to expect in the repeated lesson")


class AdvanceMessage(BaseModel):
    """Congratulatory message for advancing"""
    message: str = Field(..., description="Main congratulatory message")
    celebration: str = Field(..., description="Specific celebration of success")
    key_achievements: list[str] = Field(..., description="Summary of what was mastered")
    next_lesson_preview: str = Field(..., description="What's coming next")
    motivation: str = Field(..., description="Encouragement for continued learning")
    progress_summary: str = Field(..., description="Overall progress through the course")


class ShortAnswerEvaluation(BaseModel):
    """Evaluation result for a short answer question"""
    is_correct: bool = Field(..., description="Whether the answer demonstrates sufficient understanding")
    reasoning: str = Field(..., description="Brief explanation of the evaluation")


# Models for State Management
class StudentProfile(BaseModel):
    """Profile information about the student"""
    student_id: Optional[str] = Field(None, description="Unique student identifier")
    background: str = Field(default="", description="Prior knowledge or experience")
    learning_style: Optional[str] = Field(None, description="Preferred learning style")
    goals: list[str] = Field(default_factory=list, description="Learning goals")


class LessonProgress(BaseModel):
    """Track progress through a specific lesson"""
    lesson_number: int = Field(..., description="Which lesson")
    attempts: int = Field(default=1, description="Number of attempts")
    quiz_results: Optional[QuizResults] = Field(None, description="Quiz performance")
    assignment_score: Optional[float] = Field(None, description="Assignment score")
    weak_points: list[str] = Field(default_factory=list, description="Identified weak areas")
    completed: bool = Field(default=False, description="Whether lesson was passed")
    time_spent_minutes: Optional[int] = Field(None, description="Total time on this lesson")