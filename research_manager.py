import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import asyncio
from agents import Runner, trace, gen_trace_id
from clarifier_agent import clarifier_agent, ClarifyingQuestions
from planner_agent import planner_agent, refinement_planner_agent, WebSearchItem, WebSearchPlan
from search_agent import search_agent
from writer_agent import writer_agent, ReportData
from evaluator_agent import evaluator_agent, EvaluationResult
from email_agent import email_agent

MAX_RESEARCH_ITERATIONS = 3


class ResearchManager:
    """
    Autonomous deep research manager that orchestrates a multi-phase research pipeline:

    Phase 1: CLARIFY   - Generate clarifying questions for the user
    Phase 2: PLAN      - Design a comprehensive search strategy
    Phase 3: SEARCH    - Execute searches in parallel
    Phase 4: WRITE     - Synthesize findings into a comprehensive report
    Phase 5: EVALUATE  - Critically evaluate the report quality
    Phase 6: REFINE    - If evaluation fails, plan more searches and loop back (up to MAX iterations)
    Phase 7: DELIVER   - Send the final report via email

    The key innovation is the evaluate-refine loop: the system autonomously decides
    whether its output is good enough, and if not, it identifies gaps and does more research.
    """

    async def clarify(self, query: str):
        """Phase 1: Generate clarifying questions for the user."""
        print("Generating clarifying questions...")
        result = await Runner.run(
            clarifier_agent,
            f"Research query: {query}",
        )
        return result.final_output_as(ClarifyingQuestions)

    async def run(self, query: str, clarification_answers: str = ""):
        """
        Run the full autonomous research pipeline.
        Yields status updates and the final report.

        Args:
            query: The original research query
            clarification_answers: User's answers to clarifying questions (if any)
        """
        trace_id = gen_trace_id()
        with trace("Deep Research", trace_id=trace_id):
            trace_url = f"https://platform.openai.com/traces/trace?trace_id={trace_id}"
            print(f"View trace: {trace_url}")
            yield {"type": "status", "content": f"[Trace]({trace_url})"}

            # Build the enriched query incorporating clarifications
            if clarification_answers:
                enriched_query = (
                    f"Original query: {query}\n\n"
                    f"Additional context from user:\n{clarification_answers}"
                )
            else:
                enriched_query = query

            # ── Phase 2: PLAN initial searches ──
            yield {"type": "status", "content": "Planning research strategy..."}
            search_plan = await self._plan_searches(enriched_query)
            search_descriptions = [f"- {s.query} ({s.reason})" for s in search_plan.searches]
            yield {
                "type": "status",
                "content": f"Planned {len(search_plan.searches)} searches:\n" + "\n".join(search_descriptions),
            }

            # ── Phase 3: SEARCH ──
            yield {"type": "status", "content": f"Executing {len(search_plan.searches)} searches in parallel..."}
            all_search_results = await self._perform_searches(search_plan)
            yield {
                "type": "status",
                "content": f"Initial search complete. Got {len(all_search_results)} results.",
            }

            # ── Phase 4-6: WRITE → EVALUATE → REFINE loop ──
            report = None
            previous_evaluation = None

            for iteration in range(1, MAX_RESEARCH_ITERATIONS + 1):
                # ── Phase 4: WRITE ──
                yield {
                    "type": "status",
                    "content": f"Writing report (iteration {iteration}/{MAX_RESEARCH_ITERATIONS})...",
                }
                report = await self._write_report(
                    enriched_query, all_search_results, previous_evaluation
                )
                yield {
                    "type": "status",
                    "content": f"Draft {iteration} complete ({len(report.markdown_report.split())} words). Evaluating quality...",
                }

                # ── Phase 5: EVALUATE ──
                evaluation = await self._evaluate_report(enriched_query, report, all_search_results)
                scores = (
                    f"Completeness: {evaluation.completeness_score}/10 | "
                    f"Depth: {evaluation.depth_score}/10 | "
                    f"Accuracy: {evaluation.accuracy_score}/10 | "
                    f"Structure: {evaluation.structure_score}/10 | "
                    f"Insight: {evaluation.insight_score}/10"
                )
                yield {
                    "type": "status",
                    "content": f"Evaluation scores: {scores}\n{evaluation.summary_of_evaluation}",
                }

                if evaluation.is_acceptable:
                    yield {"type": "status", "content": "Report meets quality standards!"}
                    break

                # ── Phase 6: REFINE (if not last iteration) ──
                if iteration < MAX_RESEARCH_ITERATIONS:
                    yield {
                        "type": "status",
                        "content": (
                            f"Report needs improvement. Identified gaps:\n"
                            + "\n".join(f"- {g}" for g in evaluation.gaps)
                            + "\n\nPlanning additional research..."
                        ),
                    }

                    # Plan and execute additional searches targeting the gaps
                    refinement_plan = await self._plan_refinement_searches(
                        enriched_query, evaluation, all_search_results
                    )
                    yield {
                        "type": "status",
                        "content": f"Executing {len(refinement_plan.searches)} additional searches...",
                    }
                    new_results = await self._perform_searches(refinement_plan)
                    all_search_results.extend(new_results)
                    previous_evaluation = evaluation

                    yield {
                        "type": "status",
                        "content": f"Now have {len(all_search_results)} total search results. Rewriting report...",
                    }
                else:
                    yield {
                        "type": "status",
                        "content": "Max iterations reached. Proceeding with current report.",
                    }

            # ── Phase 7: DELIVER ──
            yield {"type": "status", "content": "Sending report via email..."}
            await self._send_email(report)
            yield {"type": "status", "content": "Email sent! Research complete."}

            # Yield the final report
            yield {"type": "report", "content": report.markdown_report}
            yield {"type": "follow_up", "content": report.follow_up_questions}

    # ──────────────────────────────────────────────────────────────────────
    # Internal methods
    # ──────────────────────────────────────────────────────────────────────

    async def _plan_searches(self, query: str) -> WebSearchPlan:
        """Plan the initial set of searches."""
        print("Planning searches...")
        result = await Runner.run(planner_agent, f"Query: {query}")
        plan = result.final_output_as(WebSearchPlan)
        print(f"Planned {len(plan.searches)} searches")
        return plan

    async def _plan_refinement_searches(
        self, query: str, evaluation: EvaluationResult, existing_results: list[str]
    ) -> WebSearchPlan:
        """Plan additional searches to address gaps found by the evaluator."""
        print("Planning refinement searches...")
        existing_summary = "\n---\n".join(existing_results[:5])  # Don't overflow context
        input_text = (
            f"Original query: {query}\n\n"
            f"The evaluator identified these gaps:\n"
            + "\n".join(f"- {g}" for g in evaluation.gaps)
            + f"\n\nEvaluator's suggested searches:\n"
            + "\n".join(f"- {q}" for q in evaluation.additional_search_queries)
            + f"\n\nRevision instructions: {evaluation.revision_instructions}\n\n"
            f"Summary of existing research (do NOT repeat these):\n{existing_summary[:3000]}"
        )
        result = await Runner.run(refinement_planner_agent, input_text)
        plan = result.final_output_as(WebSearchPlan)
        print(f"Planned {len(plan.searches)} refinement searches")
        return plan

    async def _perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """Execute searches in parallel and collect results."""
        print(f"Executing {len(search_plan.searches)} searches...")
        tasks = [asyncio.create_task(self._search(item)) for item in search_plan.searches]
        results = []
        num_completed = 0
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
            num_completed += 1
            print(f"Search progress: {num_completed}/{len(tasks)}")
        print(f"Completed {len(results)} successful searches")
        return results

    async def _search(self, item: WebSearchItem) -> str | None:
        """Execute a single search."""
        input_text = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(search_agent, input_text)
            return str(result.final_output)
        except Exception as e:
            print(f"Search failed for '{item.query}': {e}")
            return None

    async def _write_report(
        self,
        query: str,
        search_results: list[str],
        previous_evaluation: EvaluationResult | None = None,
    ) -> ReportData:
        """Write or revise the research report."""
        print("Writing report...")
        input_parts = [
            f"Original query: {query}",
            f"\nResearch results ({len(search_results)} sources):",
        ]
        for i, result in enumerate(search_results, 1):
            input_parts.append(f"\n--- Source {i} ---\n{result}")

        if previous_evaluation:
            input_parts.append(
                f"\n\n--- REVISION INSTRUCTIONS ---\n"
                f"A previous draft was evaluated and found wanting. Here is the feedback:\n"
                f"Evaluation: {previous_evaluation.summary_of_evaluation}\n"
                f"Gaps identified: {', '.join(previous_evaluation.gaps)}\n"
                f"Revision instructions: {previous_evaluation.revision_instructions}\n"
                f"Please write an IMPROVED version that addresses ALL of this feedback."
            )

        input_text = "\n".join(input_parts)
        result = await Runner.run(writer_agent, input_text)
        report = result.final_output_as(ReportData)
        print(f"Report written: {len(report.markdown_report.split())} words")
        return report

    async def _evaluate_report(
        self, query: str, report: ReportData, search_results: list[str]
    ) -> EvaluationResult:
        """Evaluate the quality of the research report."""
        print("Evaluating report...")
        search_summary = "\n---\n".join(search_results[:8])  # Cap to avoid context overflow
        input_text = (
            f"Original query: {query}\n\n"
            f"--- REPORT TO EVALUATE ---\n{report.markdown_report}\n\n"
            f"--- SEARCH RESULTS USED ---\n{search_summary[:5000]}"
        )
        result = await Runner.run(evaluator_agent, input_text)
        evaluation = result.final_output_as(EvaluationResult)
        avg_score = (
            evaluation.completeness_score
            + evaluation.depth_score
            + evaluation.accuracy_score
            + evaluation.structure_score
            + evaluation.insight_score
        ) / 5
        print(f"Evaluation complete. Average score: {avg_score:.1f}/10. Acceptable: {evaluation.is_acceptable}")
        return evaluation

    async def _send_email(self, report: ReportData) -> None:
        """Send the final report via email."""
        print("Sending email...")
        result = await Runner.run(email_agent, report.markdown_report)
        print("Email sent")
