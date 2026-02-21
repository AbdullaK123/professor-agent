# Professor Agent

An autonomous AI teaching system built with LangGraph. Give it a topic and your background — it generates a curriculum, delivers lectures, quizzes you, assigns hands-on work, grades it, and decides if you should advance or review. No human instructor needed.

## How It Works

The system orchestrates 11 specialized AI agents through a stateful graph:

```
User Query
  → Extract topic & background
  → Generate learning plan (5-8 lessons)
  → For each lesson:
      → Deliver lecture (with web-enriched content)
      → Administer quiz (5 questions, mixed types)
      → [Human input: quiz answers]
      → Grade quiz (including LLM-evaluated short answers)
      → Create hands-on assignment
      → [Human input: submission]
      → Grade assignment
      → Decide: advance or repeat?
  → Course complete
```

The graph uses `interrupt_after` on quiz and assignment nodes to pause execution and wait for student input, then resumes processing from where it left off.

## Key Design Decisions

**Multi-agent architecture over monolithic prompts.** Each agent has a single responsibility (lecture, quiz, grading, etc.) with its own system prompt and structured Pydantic output. This keeps each call focused and the outputs predictable.

**Structured outputs everywhere.** Every agent returns validated Pydantic models — `LearningPlan`, `Lecture`, `Quiz`, `GradingResult`, `ProgressDecision`, etc. No parsing JSON from raw text.

**LLM-based short answer grading.** Instead of keyword matching, a dedicated evaluator agent assesses whether free-text answers demonstrate actual understanding.

**Natural language input parsing.** Students type answers however they want. Parser agents extract structured quiz answers (`q0`–`q4`) and assignment submissions from conversational messages.

**Stateful progression.** The graph tracks lesson index, attempt count, weak points, and scores across the full session. The decision engine uses quiz + assignment scores + weak points + attempt count to determine advancement.

## Architecture

```
app/
├── graph.py       # LangGraph state machine — nodes, edges, routing logic
├── agents.py      # 11 agent definitions + async invocation functions
├── models.py      # Pydantic models for all structured outputs
├── prompts.py     # System prompts and prompt templates
└── tools.py       # Tavily web search integration
main.py            # FastAPI server with LangServe
langgraph.json     # LangGraph deployment config
```

## Tech Stack

- **Orchestration:** LangGraph (stateful graph with human-in-the-loop)
- **LLM:** Claude Haiku 4.5 (all 11 agents)
- **Web Search:** Tavily (enriches lectures with current information)
- **Structured Output:** Pydantic models via LangChain's ToolStrategy
- **API:** FastAPI + LangServe
- **State:** InMemorySaver (with optional SQLite persistence)

## Setup

```bash
# Install dependencies
rye sync

# Set environment variables
cp .env.example .env
# Add your OPENAI_API_KEY and TAVILY_API_KEY

# Run the server
rye run python main.py
```

Or deploy with LangGraph:

```bash
langgraph up
```

## The 11 Agents

| Agent | Purpose | Output Model |
|-------|---------|-------------|
| Extraction | Parse topic + background from user query | `LearningInput` |
| Curriculum | Generate 5-8 lesson learning plan | `LearningPlan` |
| Lecture | Create 15-20 min structured lecture | `Lecture` |
| Quiz | Generate 5 mixed-type questions | `Quiz` |
| Quiz Parser | Extract answers from natural language | `QuizAnswersParsed` |
| Short Answer Evaluator | LLM-grade free-text responses | `ShortAnswerEvaluation` |
| Assignment | Design hands-on exercises | `Assignment` |
| Submission Parser | Extract work from student messages | `AssignmentSubmissionParsed` |
| Grading | Score + detailed feedback | `GradingResult` |
| Progress Check | Advance or repeat decision | `ProgressDecision` |
| Messaging | Encouragement or congratulations | `RepeatMessage` / `AdvanceMessage` |
