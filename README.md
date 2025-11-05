# 🎓 Professor Agent

An AI-powered teaching system built with LangGraph that provides personalized, adaptive learning experiences. The agent acts as an expert professor, creating customized learning plans, delivering lectures, administering assessments, and adapting to student progress.

## 🌟 Features

- **Personalized Learning Plans**: Creates customized curricula based on topic and student background
- **Interactive Lectures**: Delivers engaging, structured lectures with real-world examples
- **Adaptive Assessments**: Generates quizzes and assignments tailored to learning objectives
- **Intelligent Progress Tracking**: Determines when students should advance or review material
- **Supportive Feedback**: Provides encouraging messages and constructive guidance
- **Web-Enhanced Content**: Uses Tavily Search to incorporate current, relevant information

## 🏗️ Architecture

### LangGraph Workflow

```
generate_plan → check_progress → lecture → quiz → assignment → grade
                     ↑              ↑                              ↓
                     |              └─────── repeat ←────────── decision
                     └──────────────── advance ←─────────────────┘
```

### Components

1. **Learning Plan Generation**: Breaks down topics into progressive lessons
2. **Progress Checking**: Validates student is ready for next lesson
3. **Lecture Delivery**: Creates comprehensive, engaging content
4. **Quiz Administration**: Tests understanding with mixed question types
5. **Assignment Creation**: Generates hands-on practice exercises
6. **Grading**: Provides detailed feedback with scores
7. **Decision Engine**: Determines advance vs. repeat based on performance
8. **Messaging**: Delivers encouraging or congratulatory messages

## 📦 Installation

### Prerequisites

- Python 3.11+
- [Rye](https://rye-up.com/) package manager
- OpenAI API key
- Tavily API key (for web search)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd professor-agent
```

2. Install dependencies:
```bash
rye sync
```

3. Set up environment variables:
```bash
export OPENAI_API_KEY="your-openai-api-key"
export TAVILY_API_KEY="your-tavily-api-key"
```

Or create a `.env` file:
```
OPENAI_API_KEY=your-openai-api-key
TAVILY_API_KEY=your-tavily-api-key
```

## 🚀 Usage

### Run the Demo

```bash
rye run python main.py
```

This will demonstrate the complete learning flow for "Python Functions" topic.

### Run Tests

Test individual agents:
```bash
# Test curriculum generation
rye run python scripts/test_curriculum_agent.py

# Test lecture creation
rye run python scripts/test_lecture_agent.py

# Test full integration
rye run python scripts/test_main.py
```

### Use as a Library

```python
from main import app, LearningState

async def teach_topic():
    initial_state = {
        "topic": "Machine Learning Basics",
        "background": "Knows Python, no ML experience",
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
    
    config = {"configurable": {"thread_id": "session-123"}}
    
    async for event in app.astream(initial_state, config):
        # Process each step
        pass
```

## 📁 Project Structure

```
professor-agent/
├── app/
│   ├── __init__.py
│   ├── models.py          # Pydantic models for structured outputs
│   ├── prompts.py         # All prompt templates
│   ├── tools.py           # External tools (Tavily search)
│   └── agents.py          # Agent creation and invocation functions
├── scripts/
│   ├── test_curriculum_agent.py
│   ├── test_lecture_agent.py
│   └── test_main.py
├── main.py                # LangGraph workflow and entry point
├── pyproject.toml         # Project dependencies
└── README.md
```

## 🧩 Key Components

### Models (`app/models.py`)

Pydantic models ensuring structured, validated outputs:
- `LearningPlan`: Complete curriculum with lessons
- `Lecture`: Structured lecture content with segments
- `Quiz`: Assessment with multiple question types
- `Assignment`: Hands-on exercises with steps
- `GradingResult`: Detailed feedback and scores
- `ProgressDecision`: Advance or repeat determination
- `RepeatMessage` / `AdvanceMessage`: Student communications

### Prompts (`app/prompts.py`)

Eight specialized prompts for different teaching tasks:
- Learning plan creation
- Lecture development
- Quiz generation
- Assignment design
- Grading and feedback
- Progress evaluation
- Repeat/advance messaging

### Agents (`app/agents.py`)

Eight async functions using LangChain agents:
- `create_learning_plan()`: Generates personalized curricula
- `create_lecture()`: Develops engaging lectures
- `create_quiz()`: Creates assessments
- `create_assignment()`: Designs practical exercises
- `grade_assignment()`: Evaluates student work
- `check_progress()`: Determines advancement
- `create_repeat_message()`: Provides encouragement
- `create_advance_message()`: Celebrates success

## 🎯 Use Cases

1. **Self-Paced Learning**: Students learn topics at their own pace with adaptive feedback
2. **Corporate Training**: Automated onboarding and skill development
3. **Educational Platforms**: Integration into e-learning systems
4. **Tutoring Systems**: Supplemental instruction for challenging subjects
5. **Skill Assessment**: Evaluate and improve specific competencies

## 🔧 Configuration

### Model Selection

Change the LLM in `app/agents.py`:
```python
agent = create_agent(
    "openai:gpt-4o",  # or "openai:gpt-4o-mini", "anthropic:claude-3-5-sonnet-latest"
    tools=[...],
    system_prompt=...,
    response_format=...
)
```

### Search Configuration

Modify search parameters in `app/tools.py`:
```python
search = TavilySearch(
    max_results=10,  # Default: 5
    search_depth="basic"  # or "advanced"
)
```

## 🤝 Contributing

Contributions are welcome! Areas for enhancement:
- Additional question types (coding challenges, diagrams)
- Multi-modal content (images, videos)
- Real-time student interaction
- Progress analytics and reporting
- Support for multiple languages
- Integration with LMS platforms

## 📄 License

MIT License

## 🙏 Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph)
- Powered by [LangChain](https://github.com/langchain-ai/langchain)
- Search by [Tavily](https://tavily.com/)
- Models by [OpenAI](https://openai.com/)
