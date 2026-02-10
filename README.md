# Deep Research Agent

**An autonomous, multi-agent research system that clarifies, plans, searches, writes, evaluates, and iteratively refines comprehensive research reports — producing analyst-grade output that rivals hours of human work.**

---

## High-Level Overview

### The Problem

Traditional LLM-based research tools execute a single pass: take a query, search the web, summarize the results. The output is surface-level, misses nuance, and lacks the depth that comes from iterative exploration and critical self-assessment.

### Why an Agentic Approach

Real research is not linear. A human analyst would:
1. Ask clarifying questions before starting
2. Plan a multi-pronged search strategy
3. Execute searches and read the results
4. Draft a report, then *re-read it critically*
5. Identify gaps, go back and search more
6. Revise and polish until the quality bar is met

This agent replicates that entire cognitive workflow autonomously. It doesn't just call an LLM once — it orchestrates **6 specialized agents** in an autonomous loop with self-evaluation and iterative refinement.

### What Makes This Different

| Simple LLM App | This Agent |
|---|---|
| Single query, single response | Clarify, Plan, Search, Write, Evaluate, Refine loop |
| 5 searches, low context | 7+ searches with high context, plus refinement rounds |
| One-shot report writing | Iterative drafting with evaluator feedback |
| No quality control | 5-dimension scoring with autonomous rejection and retry |
| User gets whatever comes out | User gets a report that passed a quality gate |

---

## Key Features

- **Clarifying Questions** — Before any research begins, the agent asks 3 targeted questions to narrow scope, establish audience, and surface hidden assumptions (inspired by OpenAI's Deep Research UX)
- **Autonomous Research Loop** — The system plans, searches, writes, evaluates, and refines in a loop up to 3 iterations, autonomously deciding when the output is good enough
- **Multi-Dimensional Evaluation** — An independent evaluator agent scores every draft on 5 dimensions (completeness, depth, accuracy, structure, insight) with a strict quality gate
- **Gap-Targeted Refinement** — When a draft fails evaluation, the system identifies specific gaps, plans new targeted searches, and rewrites with explicit revision instructions
- **Parallel Search Execution** — All searches within a phase execute concurrently via `asyncio` for maximum throughput
- **Human-in-the-Loop** — The clarification phase keeps the human involved at the critical moment (defining the research direction) while the rest runs autonomously
- **Rich Progress Streaming** — The UI shows real-time updates: search plans, execution progress, evaluation scores, gap analysis, and iteration status
- **Email Delivery** — Final reports are automatically converted to HTML and emailed via SendGrid

---

## Agent Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        GRADIO UI (deep_research.py)                 │
│    State Machine: idle → clarifying → researching → done            │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│               RESEARCH MANAGER (research_manager.py)                │
│                    Autonomous Orchestrator                           │
│                                                                     │
│  Phase 1: CLARIFY ──→ ClarifierAgent                               │
│  Phase 2: PLAN    ──→ PlannerAgent                                  │
│  Phase 3: SEARCH  ──→ SearchAgent (x7, parallel)                   │
│  Phase 4: WRITE   ──→ WriterAgent                                   │
│  Phase 5: EVALUATE──→ EvaluatorAgent                               │
│  Phase 6: REFINE  ──→ RefinementPlanner → SearchAgent → WriterAgent│
│  Phase 7: DELIVER ──→ EmailAgent                                    │
│                                                                     │
│  ┌──────────────────────────────────────────┐                      │
│  │    AUTONOMOUS LOOP (max 3 iterations)    │                      │
│  │                                          │                      │
│  │  WRITE ──→ EVALUATE ──→ Pass? ──→ EXIT  │                      │
│  │                │                         │                      │
│  │                ▼ Fail                    │                      │
│  │    REFINE (plan + search) ──→ WRITE     │                      │
│  └──────────────────────────────────────────┘                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Breakdown

| Component | File | Model | Role |
|---|---|---|---|
| **ClarifierAgent** | `clarifier_agent.py` | `gpt-4o` | Generates 3 clarifying questions to sharpen the research query |
| **PlannerAgent** | `planner_agent.py` | `gpt-4o` | Designs a comprehensive 7-query search strategy covering multiple angles |
| **RefinementPlanner** | `planner_agent.py` | `gpt-4o` | Plans 3-5 targeted follow-up searches to fill gaps identified by the evaluator |
| **SearchAgent** | `search_agent.py` | `gpt-4o-mini` | Executes web searches and produces dense, information-rich summaries (300-500 words each) |
| **WriterAgent** | `writer_agent.py` | `gpt-4o` | Synthesizes all search results into a 2000-4000 word structured research report |
| **EvaluatorAgent** | `evaluator_agent.py` | `gpt-4o` | Scores reports on 5 dimensions (1-10 each), identifies gaps, suggests new searches |
| **EmailAgent** | `email_agent.py` | `gpt-4o-mini` | Converts the final markdown report to HTML and sends via SendGrid |
| **ResearchManager** | `research_manager.py` | — | Orchestrates all agents, manages the autonomous loop, streams progress |
| **Gradio UI** | `deep_research.py` | — | Chatbot-style interface with state management and real-time progress display |

---

## Agent Loop (Core Logic)

The research pipeline follows this step-by-step flow:

```
1. RECEIVE GOAL
   User enters a research query

2. CLARIFY (Human-in-the-Loop)
   ClarifierAgent generates 3 clarifying questions
   User answers (or skips)
   Query is enriched with user's context

3. PLAN
   PlannerAgent designs 7 search queries covering:
   • Multiple angles of the topic
   • Data and statistics
   • Expert opinions
   • Recent developments
   • Counterarguments
   • Comparative analysis

4. SEARCH (Parallel Execution)
   7 SearchAgents execute concurrently
   Each returns a 300-500 word dense summary
   Failed searches are gracefully skipped

5. WRITE
   WriterAgent synthesizes all results into a
   2000-4000 word structured report with:
   • Executive summary
   • Background and context
   • Key findings
   • Analysis and implications
   • Challenges and risks
   • Future outlook
   • Conclusions and recommendations

6. EVALUATE
   EvaluatorAgent scores the report:
   • Completeness (1-10)
   • Depth (1-10)
   • Accuracy (1-10)
   • Structure (1-10)
   • Insight (1-10)

   Pass criteria: average >= 7, no dimension < 5

7. DECIDE: REFINE or DELIVER
   IF acceptable → proceed to delivery
   IF NOT acceptable (up to 3 iterations):
     • Identify specific gaps
     • Plan 3-5 new targeted searches
     • Execute searches
     • Rewrite with evaluator feedback
     • Re-evaluate

8. DELIVER
   EmailAgent converts report to HTML
   Sends via SendGrid
   Report displayed in UI with follow-up questions
```

---

## Tools & Capabilities

### Available Tools

| Tool | Used By | Purpose |
|---|---|---|
| `WebSearchTool` (OpenAI built-in) | SearchAgent | Web search with high context extraction |
| `send_email` (custom function tool) | EmailAgent | HTML email delivery via SendGrid API |

### Tool Selection Strategy

- **SearchAgent** is configured with `tool_choice="required"` — it *must* use the web search tool on every invocation, ensuring no hallucinated results
- **WebSearchTool** uses `search_context_size="high"` for maximum information extraction from web pages
- **EmailAgent** uses a custom `@function_tool` decorated Python function for SendGrid integration

### Failure Handling

- Individual search failures are caught and logged; the pipeline continues with remaining results
- If a search returns `None`, it is excluded from the results list
- The evaluator-refine loop provides system-level resilience: if early searches miss key information, the evaluator catches the gap and triggers targeted follow-up searches

---

## Memory Design

### Short-Term Memory (Within a Research Session)

- **Search results accumulate** across iterations — refinement searches are *appended* to the existing results, never replacing them
- **Evaluation feedback** from the previous iteration is passed to the writer as explicit revision instructions
- **Enriched query** (original query + clarification answers) persists throughout all phases
- **Gradio State** tracks the conversation phase (`idle`, `clarifying`, `researching`, `done`) and session data

### Long-Term Memory

The current system is **stateless across sessions** — each research run starts fresh. Long-term memory (vector DB, conversation history) is a planned enhancement (see Roadmap).

### What Gets Stored (Per Session)

| Data | Lifetime | Purpose |
|---|---|---|
| Original query | Full session | Anchors all planning and evaluation |
| Clarification answers | Full session | Enriches query context |
| All search results | Full session, accumulating | Growing knowledge base for report writing |
| Previous evaluation | Per iteration | Guides refinement planning and report revision |
| Chat history | Full session (Gradio State) | UI display and conversation flow |

### Privacy Considerations

- Search queries are sent to OpenAI's API (subject to OpenAI's data usage policy)
- Email delivery routes through SendGrid
- No user data is stored persistently on disk
- OpenAI trace IDs are generated for debugging but contain no PII

---

## Models Used

| Model | Agent(s) | Why |
|---|---|---|
| **GPT-4o** | Clarifier, Planner, RefinementPlanner, Writer, Evaluator | Reasoning-heavy tasks requiring nuanced judgment, structured analysis, and long-form generation. GPT-4o provides the depth needed for quality research output. |
| **GPT-4o-mini** | SearchAgent, EmailAgent | Cost-optimized for tasks that are more mechanical: summarizing web search results and converting markdown to HTML. These tasks benefit from speed and cost efficiency over maximum reasoning capability. |

### Model Selection Rationale

The system uses a **tiered model strategy**: expensive, high-capability models (`gpt-4o`) for tasks where quality directly impacts the final output (planning, writing, evaluating), and fast, cost-efficient models (`gpt-4o-mini`) for high-volume or mechanical tasks (search summarization, email formatting). This balances output quality against operational cost.

---

## Installation

### System Requirements

- **Python** 3.12+
- **macOS**, Linux, or Windows
- **Internet connection** (for OpenAI API and web searches)

### Dependencies

```
requests
python-dotenv
gradio
pypdf
openai
openai-agents
pydantic
sendgrid
rich
email-validator
```

### Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd agents-main/2_openai/deep_research

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create a .env file with your API keys
cat > .env << 'EOF'
OPENAI_API_KEY=sk-your-openai-api-key-here
SENDGRID_API_KEY=SG.your-sendgrid-api-key-here
EOF
```

### Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | Yes | Authenticates all agent calls to OpenAI |
| `SENDGRID_API_KEY` | Yes | Authenticates email delivery via SendGrid |

> **Note:** You will also need to update the sender and recipient email addresses in `email_agent.py` to match your SendGrid verified sender and desired recipient.

---

## Usage

### Basic Usage

```bash
python deep_research.py
```

This launches a Gradio web UI at `http://127.0.0.1:7860`. The flow is:

1. **Enter a research topic** — e.g., "What is the current state of nuclear fusion energy?"
2. **Answer clarifying questions** — The agent asks 3 questions to sharpen the research (or type `skip`)
3. **Watch it work** — Real-time progress shows search plans, execution, evaluation scores, and refinement cycles
4. **Read the report** — A comprehensive markdown report appears in the chat
5. **Check your email** — The report is also delivered as a formatted HTML email

### Example Prompts

| Query | What Happens |
|---|---|
| "Impact of AI on healthcare" | Clarifies scope (diagnostics? drug discovery? admin?), then researches with 7+ searches |
| "Compare React vs Vue vs Svelte in 2025" | Plans comparative searches, builds a comparison table, evaluates for balance |
| "What caused the 2008 financial crisis?" | Searches for multiple perspectives, includes data, evaluates for depth and accuracy |

### Advanced Usage

- **Skip clarification** — Type `skip` when asked clarifying questions to proceed with the original query as-is
- **Multiple sessions** — After a report is delivered, enter a new query to start a fresh research session
- **Follow-up research** — The system suggests 5 follow-up questions after each report; use them as your next query

---

## Configuration

### Agent Parameters

| Parameter | Location | Default | Description |
|---|---|---|---|
| `MAX_RESEARCH_ITERATIONS` | `research_manager.py` | `3` | Maximum evaluate-refine cycles before accepting the report |
| `HOW_MANY_SEARCHES` | `planner_agent.py` | `7` | Number of initial search queries planned |
| `search_context_size` | `search_agent.py` | `"high"` | How much context to extract from web pages (`"low"`, `"medium"`, `"high"`) |
| Evaluator pass threshold | `evaluator_agent.py` | avg >= 7, min >= 5 | Scoring criteria for report acceptance |

### Tool Permissions

- **SearchAgent** has `tool_choice="required"` — it is forced to use the web search tool (no hallucination)
- **EmailAgent** has access to the `send_email` function tool only

### Customizing Models

Each agent's model can be changed independently by editing the `model` parameter in the respective agent file. For example, to use a cheaper model for planning:

```python
# In planner_agent.py
planner_agent = Agent(
    ...
    model="gpt-4o-mini",  # Changed from "gpt-4o"
)
```

---

## Evaluation & Metrics

### How Performance is Measured

The **EvaluatorAgent** scores every report draft on 5 dimensions:

| Dimension | What It Measures | Example of a Low Score |
|---|---|---|
| **Completeness** (1-10) | Does it address all aspects of the query? | Missing an entire sub-topic the user asked about |
| **Depth** (1-10) | Goes beyond surface-level? Data, examples, expert views? | Just paraphrasing search results without analysis |
| **Accuracy** (1-10) | Claims well-supported? No speculation presented as fact? | Making claims without source attribution |
| **Structure** (1-10) | Well-organized, logical flow, good formatting? | Wall of text without headers or sections |
| **Insight** (1-10) | Genuine analysis, not just summarization? | No synthesis, no implications, no takeaways |

### Pass/Fail Criteria

- **Pass**: Average score >= 7 AND no single dimension below 5
- **Fail**: Triggers a refinement cycle (new searches + rewrite) with specific feedback

### Known Limitations

- **Evaluator bias**: The evaluator and writer use the same model family, which may lead to inflated scores
- **Search coverage**: Limited to what OpenAI's web search tool returns; paywalled or niche sources may be missed
- **Context window**: Very long research sessions (many refinement rounds) may approach token limits
- **No cross-session learning**: Each research session starts from scratch

---

## Safety & Guardrails

### Prompt Constraints

- All agents have carefully scoped system prompts that constrain their behavior to their specific role
- The SearchAgent is instructed to flag unreliable information rather than presenting it as fact
- The WriterAgent is instructed to attribute claims to sources

### Iteration Limits

- **Maximum 3 research iterations** — prevents infinite loops and runaway API costs
- The system will accept the best available report after hitting the iteration cap, even if the evaluator is not fully satisfied

### Cost Controls

- SearchAgent uses `gpt-4o-mini` (the most frequently called agent) to minimize cost
- Refinement searches are capped at 3-5 queries per round (vs. 7 for initial searches)
- Context passed to the evaluator is truncated to prevent excessive token usage

### Human Approval Points

- **Clarification phase**: The user reviews and answers questions before any research begins
- **Query validation**: The user explicitly submits the research topic
- Email addresses are configured in code (not user-provided at runtime)

### Failure Modes and Mitigations

| Failure Mode | Mitigation |
|---|---|
| Search API failure | Graceful skip; pipeline continues with remaining results |
| All searches fail | Report is written with whatever data is available |
| Evaluator always rejects | Iteration cap (3) forces acceptance |
| API rate limiting | Individual search errors are caught and logged |
| Context overflow | Search results and evaluator input are truncated |

---

## Ethics & Responsible Use

### Intended Use Cases

- Academic and professional research
- Market analysis and competitive intelligence
- Technology landscape surveys
- Policy analysis and background research
- Due diligence and fact-finding

### Prohibited Uses

- Generating disinformation or misleading content
- Academic dishonesty (submitting AI-generated reports as original human work without disclosure)
- Automated surveillance or profiling
- Any use that violates OpenAI's usage policies

### Bias & Risk Considerations

- Search results reflect the biases of web sources and search algorithms
- The system may over-represent English-language and Western perspectives
- GPT-4o's training data cutoff means very recent events may be missed or inaccurate
- Source quality varies; the system attempts to flag unreliable information but cannot guarantee accuracy

### Transparency Commitments

- Every research run generates an OpenAI trace URL for full observability
- Evaluation scores are displayed to the user in real-time
- The system shows exactly which searches were planned and executed

---

## Project Structure

```
deep_research/
├── deep_research.py          # Gradio UI entry point, state machine, chat interface
├── research_manager.py       # Autonomous orchestrator, manages the full pipeline and loop
├── clarifier_agent.py        # Generates 3 clarifying questions (Phase 1)
├── planner_agent.py          # Plans initial and refinement search strategies (Phase 2/6)
├── search_agent.py           # Executes web searches with high-context extraction (Phase 3)
├── writer_agent.py           # Writes comprehensive research reports (Phase 4)
├── evaluator_agent.py        # Scores reports on 5 dimensions, identifies gaps (Phase 5)
├── email_agent.py            # Converts to HTML and sends via SendGrid (Phase 7)
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

---

## Roadmap

### Planned Features

- [ ] **Long-term memory** — Vector database (ChromaDB/Pinecone) for cross-session knowledge accumulation
- [ ] **Source verification** — Cross-reference claims across multiple sources with confidence scoring
- [ ] **PDF/document ingestion** — Allow users to upload documents as additional research context
- [ ] **Streaming report generation** — Show the report being written in real-time (token by token)
- [ ] **Configurable evaluation thresholds** — Let users set their own quality bar via the UI
- [ ] **Export formats** — PDF, DOCX, and Google Docs export in addition to markdown
- [ ] **Multi-query research** — Accept multiple related queries and produce a unified report
- [ ] **Agent tracing dashboard** — Visual timeline of agent actions, decisions, and costs

### Known Gaps

- No persistent storage between sessions
- No support for authenticated/paywalled sources
- Email configuration is hardcoded (should be user-configurable)
- No cost tracking or budget controls exposed to the user

### Future Research Directions

- Implementing a **tree-of-thought** search strategy where promising research paths are explored in depth
- Adding a **critic agent** that challenges the writer's conclusions with counterarguments
- Exploring **multi-model collaboration** (e.g., Claude for writing, GPT-4o for evaluation) to reduce same-model bias
- Implementing **confidence scoring** on individual claims within the report

---

## Contributing

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Run the application and verify it works end-to-end
5. Submit a pull request

### Coding Standards

- Python 3.12+ with type hints
- Pydantic models for all structured data
- Async/await throughout (no blocking calls)
- Each agent in its own file with clear instructions and output types
- Descriptive variable names and docstrings

### Issue & PR Process

- Open an issue describing the bug or feature request
- Reference the issue number in your PR
- Include a description of what changed and why
- Test with at least one full research query before submitting

---

## License

This project is provided as-is for educational and research purposes. See the repository root for license details.

### Third-Party Licenses

- [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) — MIT License
- [Gradio](https://github.com/gradio-app/gradio) — Apache 2.0
- [Pydantic](https://github.com/pydantic/pydantic) — MIT License
- [SendGrid](https://github.com/sendgrid/sendgrid-python) — MIT License

---

## Citation

If you use this project in academic work, please cite:

```bibtex
@software{deep_research_agent,
  title  = {Deep Research Agent: Autonomous Multi-Agent Research System},
  author = {Sudhire Rahul Karunakaran},
  year   = {2025},
  url    = {https://github.com/sudhirerahul/agents-main}
}
```

### Inspiration & Related Work

- [OpenAI Deep Research](https://openai.com/index/introducing-deep-research/) — The clarifying questions UX pattern
- [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) — The agent framework powering all agents
- Evaluator-Optimizer pattern from agentic AI design patterns literature

---

## Acknowledgments

- **OpenAI** — For the Agents SDK, GPT-4o, and built-in WebSearchTool
- **Gradio** — For the rapid UI prototyping framework
- **SendGrid** — For email delivery infrastructure
- **Duke University** — Academic context for this project

---

## Contact

- **Author**: Sudhire Rahul Karunakaran
- **Email**: sudhirerahul.karunakaran@duke.edu
- **Issues**: Open an issue on the GitHub repository
