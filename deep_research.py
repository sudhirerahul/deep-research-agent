import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)

manager = ResearchManager()

# State machine: "idle" → "clarifying" → "researching" → "done"
# We store state per-session using Gradio's State component.


async def handle_submit(user_message: str, chat_history: list, state: dict):
    """Handle user input at any stage of the research flow."""
    if not user_message.strip():
        yield chat_history, state, ""
        return

    phase = state.get("phase", "idle")

    if phase == "idle":
        # ── New research query ──
        state["query"] = user_message
        state["phase"] = "clarifying"
        chat_history.append({"role": "user", "content": user_message})
        chat_history.append({
            "role": "assistant",
            "content": "Let me think about what I need to know to research this thoroughly..."
        })
        yield chat_history, state, ""

        # Generate clarifying questions
        questions = await manager.clarify(user_message)
        questions_text = "Before I dive in, I have a few questions to sharpen my research:\n\n"
        for i, q in enumerate(questions.questions, 1):
            questions_text += f"**{i}.** {q}\n\n"
        questions_text += (
            "*Please answer these questions (or type **skip** to proceed without clarification).*"
        )

        chat_history[-1] = {"role": "assistant", "content": questions_text}
        state["questions"] = questions.questions
        yield chat_history, state, ""

    elif phase == "clarifying":
        # ── User answering clarifying questions ──
        chat_history.append({"role": "user", "content": user_message})

        if user_message.strip().lower() == "skip":
            clarification_answers = ""
        else:
            clarification_answers = user_message

        state["phase"] = "researching"
        chat_history.append({
            "role": "assistant",
            "content": "Starting deep research. This may take several minutes as I search, analyze, evaluate, and refine..."
        })
        yield chat_history, state, ""

        # ── Run the full autonomous research pipeline ──
        status_messages = []
        async for update in manager.run(state["query"], clarification_answers):
            if update["type"] == "status":
                status_messages.append(update["content"])
                # Build a rich progress display
                progress = _build_progress_display(status_messages)
                chat_history[-1] = {"role": "assistant", "content": progress}
                yield chat_history, state, ""

            elif update["type"] == "report":
                # Show the final report
                state["phase"] = "done"
                chat_history.append({
                    "role": "assistant",
                    "content": update["content"],
                })
                yield chat_history, state, ""

            elif update["type"] == "follow_up":
                # Show follow-up questions
                follow_up = "**Suggested follow-up research:**\n\n"
                for i, q in enumerate(update["content"], 1):
                    follow_up += f"{i}. {q}\n"
                follow_up += "\n*Enter a new query to start another research session.*"
                chat_history.append({"role": "assistant", "content": follow_up})
                state["phase"] = "idle"  # Ready for next query
                yield chat_history, state, ""

    elif phase == "done":
        # Reset for a new query
        state["phase"] = "idle"
        # Recurse to handle as a new query
        async for result in handle_submit(user_message, chat_history, state):
            yield result


def _build_progress_display(status_messages: list[str]) -> str:
    """Build a nicely formatted progress display from status updates."""
    lines = ["**Deep Research in Progress**\n"]
    for msg in status_messages:
        if "\n" in msg:
            first_line, *rest = msg.split("\n")
            lines.append(f"> {first_line}")
            for line in rest:
                lines.append(f"  {line}")
        else:
            lines.append(f"> {msg}")

    lines.append("\n*Working...*")
    return "\n\n".join(lines)


# ── Gradio UI (compatible with Gradio 6+) ──

with gr.Blocks() as ui:
    gr.Markdown(
        "# Deep Research Agent\n"
        "An autonomous research system that clarifies, searches, writes, evaluates, "
        "and refines until it produces a comprehensive report."
    )

    chatbot = gr.Chatbot(
        label="Research Assistant",
        height=650,
    )

    with gr.Row():
        msg_input = gr.Textbox(
            label="Your message",
            placeholder="Enter a research topic or answer the clarifying questions...",
            scale=9,
            show_label=False,
        )
        send_btn = gr.Button("Send", variant="primary", scale=1)

    session_state = gr.State(value={"phase": "idle"})

    # Wire up the submit handlers
    send_btn.click(
        fn=handle_submit,
        inputs=[msg_input, chatbot, session_state],
        outputs=[chatbot, session_state, msg_input],
    )
    msg_input.submit(
        fn=handle_submit,
        inputs=[msg_input, chatbot, session_state],
        outputs=[chatbot, session_state, msg_input],
    )


ui.launch(inbrowser=True)
