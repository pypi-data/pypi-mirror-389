"""Main invoke functionality for running agents via the orchestrator."""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .client import InvokeClient


@dataclass
class InvokeResult:
    """Result from a bot invocation."""

    success: bool
    bot_id: Optional[str] = None
    invocation_id: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    events: List[Dict[str, Any]] = field(default_factory=list)

    def __str__(self) -> str:
        if self.success:
            return f"✅ Invocation successful (ID: {self.invocation_id})"
        else:
            return f"❌ Invocation failed: {self.error}"

    def get_final_result(self) -> Optional[Any]:
        """Get the final result from the invocation."""
        return self.result

    def get_all_events(self) -> List[Dict[str, Any]]:
        """Get all events from the invocation."""
        return self.events


class Invoke:
    """Main class for invoking agents."""

    def __init__(
        self,
        agent: Optional[Any] = None,
        parameters: Optional[Dict[str, Any]] = None,
        dataset_slugs: Optional[list] = None,
        endpoint: Optional[str] = None,
        auth_token: Optional[str] = None,
        stream: bool = False,
        print_events: bool = False,
    ):
        """Initialize and optionally invoke an agent immediately.

        Args:
            agent: Optional Agent instance to invoke immediately
            parameters: Parameters to pass to the agent
            dataset_slugs: Dataset slugs to include (e.g. ["my-dataset"] or ["org.my-dataset"])
            endpoint: API endpoint URL
            auth_token: Authentication token
            stream: Whether to stream events
            print_events: Whether to print events as they arrive
        """
        self.client = InvokeClient(endpoint=endpoint, auth_token=auth_token)
        self.print_events = print_events
        self.result = None

        # If an agent is provided, invoke it immediately
        if agent:
            bot_key = getattr(agent, "key", None)
            if not bot_key:
                raise ValueError("Agent must have a 'key' attribute for invocation")

            self.result = self.invoke_by_key(
                bot_key,
                parameters=parameters,
                dataset_slugs=dataset_slugs,
                stream=stream,
            )

    def invoke_agent(
        self,
        agent: Any,
        parameters: Optional[Dict[str, Any]] = None,
        dataset_slugs: Optional[list] = None,
        stream: bool = False,
    ) -> InvokeResult:
        """Invoke an agent instance.

        Args:
            agent: Agent instance with a 'key' attribute
            parameters: Parameters to pass to the agent
            dataset_slugs: Dataset slugs to include (e.g. ["my-dataset"] or ["org.my-dataset"])
            stream: Whether to stream events

        Returns:
            InvokeResult with the outcome
        """
        bot_key = getattr(agent, "key", None)
        if not bot_key:
            raise ValueError("Agent must have a 'key' attribute for invocation")

        return self.invoke_by_key(
            bot_key, parameters=parameters, dataset_slugs=dataset_slugs, stream=stream
        )

    def invoke_by_key(
        self,
        bot_key: str,
        messages: Optional[List[Dict[str, str]]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        dataset_slugs: Optional[list] = None,
        mode: Optional[str] = None,
        stream: bool = False,
        output_format: str = "events",
        verbose: bool = False,
    ) -> InvokeResult:
        """Invoke a bot by its key.

        Args:
            bot_key: Bot key (e.g., "erdo.data-analyzer")
            messages: Messages in format [{"role": "user", "content": "..."}]
            parameters: Parameters to pass to the bot
            dataset_slugs: Dataset slugs to include (e.g. ["my-dataset"] or ["org.my-dataset"])
            mode: Invocation mode: "live" (default), "replay" (cached), or "mock" (synthetic)
            stream: Whether to stream events
            output_format: Output format: "events" (raw), "text" (formatted), "json" (summary)
            verbose: Show detailed steps (only for text format)

        Returns:
            InvokeResult with the outcome
        """
        try:
            response = self.client.invoke_bot(
                bot_key,
                messages=messages,
                parameters=parameters,
                dataset_slugs=dataset_slugs,
                mode=mode,
                stream=stream,
            )

            if stream:
                # Process SSE events
                events = []
                invocation_id = None

                # Type guard: response should be SSEClient when stream=True
                if not isinstance(response, dict):
                    # For formatted output, print as we stream
                    if output_format in ["text", "json"] and not self.print_events:
                        from ..formatting import parse_invocation_events

                        bot_name_printed = False
                        completed_steps = set()

                        for event in response.events():
                            events.append(event)

                            # Extract invocation ID and bot name from payload
                            payload = event.get("payload", {})
                            if isinstance(payload, dict):
                                if "invocation_id" in payload and not invocation_id:
                                    invocation_id = payload["invocation_id"]
                                if "bot_name" in payload and not bot_name_printed:
                                    bot_name = payload["bot_name"]
                                    if output_format == "text":
                                        print(f"Bot: {bot_name}")
                                        print(
                                            f"Invocation ID: {invocation_id or 'N/A'}"
                                        )
                                        if verbose:
                                            print("\nSteps:")
                                    bot_name_printed = True

                            # Print steps as they complete (verbose mode)
                            if (
                                verbose
                                and output_format == "text"
                                and payload.get("status") == "step finished"
                            ):
                                # Parse to get step info
                                summary = parse_invocation_events(
                                    events, bot_key, invocation_id
                                )
                                for step in summary.steps:
                                    if step.key and step.key not in completed_steps:
                                        print(f"  ✓ {step.key} ({step.action})")
                                        completed_steps.add(step.key)

                            # Print message content as it streams
                            if (
                                output_format == "text"
                                and isinstance(payload, str)
                                and len(payload) > 0
                            ):
                                # Check if this is actual content (not JSON)
                                if not payload.startswith(
                                    "{"
                                ) and not payload.startswith("["):
                                    print(payload, end="", flush=True)
                    else:
                        # For raw events or print_events mode, just collect
                        for event in response.events():
                            events.append(event)

                            if self.print_events:
                                self._print_event(event)

                            # Extract invocation ID from events
                            if "invocation_id" in event:
                                invocation_id = event["invocation_id"]

                # Format final result based on output_format
                formatted_result = self._format_result(
                    events, bot_key, invocation_id, output_format, verbose
                )

                return InvokeResult(
                    success=True,
                    bot_id=bot_key,
                    invocation_id=invocation_id,
                    result=formatted_result,
                    events=events,
                )
            else:
                # Non-streaming response - response is a dict with 'events' key
                response_dict = response if isinstance(response, dict) else {}
                # Extract the events list from the response
                events = response_dict.get("events", [])

                # Format result based on output_format
                formatted_result = self._format_result(
                    events, bot_key, None, output_format, verbose
                )

                return InvokeResult(
                    success=True,
                    bot_id=bot_key,
                    result=formatted_result,
                    events=events,
                )

        except Exception as e:
            return InvokeResult(success=False, bot_id=bot_key, error=str(e))

    def _format_result(
        self,
        events: List[Dict[str, Any]],
        bot_key: str,
        invocation_id: Optional[str],
        output_format: str,
        verbose: bool,
    ) -> Any:
        """Format the result based on output_format parameter.

        Args:
            events: List of events from the invocation
            bot_key: Bot key
            invocation_id: Invocation ID
            output_format: "events", "text", or "json"
            verbose: Show detailed steps (for text format)

        Returns:
            Formatted result based on output_format
        """
        if output_format == "events":
            # Return raw events (backwards compatible)
            return {"events": events}

        # Import formatting helpers
        from ..formatting import parse_invocation_events

        # Parse events into structured summary
        summary = parse_invocation_events(events, bot_key, invocation_id)

        if output_format == "text":
            # Format as human-readable text
            lines = []
            lines.append(f"Bot: {summary.bot_name or summary.bot_key or 'unknown'}")
            lines.append(f"Invocation ID: {summary.invocation_id or 'N/A'}")

            if verbose and summary.steps:
                lines.append("")
                lines.append("Steps:")
                for step in summary.steps:
                    status_icon = "✓" if step.status == "completed" else "•"
                    lines.append(f"  {status_icon} {step.key} ({step.action})")

            if summary.result:
                lines.append("")
                lines.append("Result:")
                try:
                    parsed = json.loads(summary.result)
                    lines.append(json.dumps(parsed, indent=2))
                except (json.JSONDecodeError, TypeError):
                    lines.append(summary.result)

            return "\n".join(lines)

        elif output_format == "json":
            # Return structured summary
            return {
                "bot_name": summary.bot_name,
                "bot_key": summary.bot_key,
                "invocation_id": summary.invocation_id,
                "steps": [
                    {"key": s.key, "action": s.action, "status": s.status}
                    for s in summary.steps
                ],
                "result": summary.result,
                "success": summary.success,
                "error": summary.error,
            }

        # Default: return events
        return {"events": events}

    def _print_event(self, event: Dict[str, Any]):
        """Print an event in a readable format."""
        event_type = event.get("type", "unknown")

        if event_type == "step_started":
            step_name = event.get("step_name", "Unknown step")
            print(f"🔄 Step started: {step_name}")
        elif event_type == "step_completed":
            step_name = event.get("step_name", "Unknown step")
            print(f"✅ Step completed: {step_name}")
        elif event_type == "llm_chunk":
            content = event.get("content", "")
            print(content, end="", flush=True)
        elif event_type == "invocation_completed":
            print("\n✨ Invocation completed")
        elif event_type == "error":
            error = event.get("error", "Unknown error")
            print(f"❌ Error: {error}")
        else:
            # Generic event printing
            print(f"📡 {event_type}: {json.dumps(event, indent=2)}")


# Convenience functions
def invoke(
    bot_key: str,
    messages: Optional[List[Dict[str, str]]] = None,
    parameters: Optional[Dict[str, Any]] = None,
    datasets: Optional[list] = None,
    mode: Optional[str] = None,
    stream: bool = False,
    output_format: str = "events",
    verbose: bool = False,
    print_events: bool = False,
    **kwargs,
) -> InvokeResult:
    """Invoke a bot with a clean API.

    Args:
        bot_key: Bot key (e.g., "erdo.data-analyzer")
        messages: Messages in format [{"role": "user", "content": "..."}]
        parameters: Parameters to pass to the bot
        datasets: Dataset slugs to include (e.g. ["my-dataset"] or ["org.my-dataset"])
        mode: Invocation mode: "live" (default), "replay" (cached), or "mock" (synthetic)
        stream: Whether to stream events
        output_format: Output format: "events" (raw), "text" (formatted), "json" (summary)
        verbose: Show detailed steps (only for text format)
        print_events: Whether to print events
        **kwargs: Additional arguments (endpoint, auth_token)

    Returns:
        InvokeResult with formatted result in response.result

    Example:
        >>> from erdo import invoke
        >>>
        >>> # Default: raw events (backwards compatible)
        >>> response = invoke("my_agent", messages=[...])
        >>> print(response.result)  # {"events": [...]}
        >>>
        >>> # Formatted text output
        >>> response = invoke("my_agent", messages=[...], output_format="text")
        >>> print(response.result)
        Bot: my agent
        Invocation ID: abc-123
        Result:
        The answer is 4
        >>>
        >>> # Formatted text with verbose steps
        >>> response = invoke("my_agent", messages=[...], output_format="text", verbose=True)
        >>>
        >>> # JSON summary
        >>> response = invoke("my_agent", messages=[...], output_format="json")
        >>> print(response.result)  # {"bot_name": ..., "steps": [...], "result": ...}
    """
    return invoke_by_key(
        bot_key=bot_key,
        messages=messages,
        parameters=parameters,
        dataset_slugs=datasets,
        mode=mode,
        stream=stream,
        output_format=output_format,
        verbose=verbose,
        print_events=print_events,
        **kwargs,
    )


def invoke_agent(
    agent: Any,
    parameters: Optional[Dict[str, Any]] = None,
    dataset_slugs: Optional[list] = None,
    stream: bool = False,
    print_events: bool = False,
    **kwargs,
) -> InvokeResult:
    """Invoke an agent instance.

    Args:
        agent: Agent instance with a 'key' attribute
        parameters: Parameters to pass to the agent
        dataset_slugs: Dataset slugs to include (e.g. ["my-dataset"] or ["org.my-dataset"])
        stream: Whether to stream events
        print_events: Whether to print events
        **kwargs: Additional arguments (endpoint, auth_token)

    Returns:
        InvokeResult with the outcome
    """
    invoke = Invoke(
        endpoint=kwargs.get("endpoint"),
        auth_token=kwargs.get("auth_token"),
        print_events=print_events,
    )
    return invoke.invoke_agent(agent, parameters, dataset_slugs, stream)


def invoke_by_key(
    bot_key: str,
    messages: Optional[List[Dict[str, str]]] = None,
    parameters: Optional[Dict[str, Any]] = None,
    dataset_slugs: Optional[list] = None,
    mode: Optional[str] = None,
    stream: bool = False,
    output_format: str = "events",
    verbose: bool = False,
    print_events: bool = False,
    **kwargs,
) -> InvokeResult:
    """Invoke a bot by its key.

    Args:
        bot_key: Bot key (e.g., "erdo.data-analyzer")
        messages: Messages in format [{"role": "user", "content": "..."}]
        parameters: Parameters to pass to the bot
        dataset_slugs: Dataset slugs to include (e.g. ["my-dataset"] or ["org.my-dataset"])
        mode: Invocation mode: "live" (default), "replay" (cached), or "mock" (synthetic)
        stream: Whether to stream events
        output_format: Output format: "events" (raw), "text" (formatted), "json" (summary)
        verbose: Show detailed steps (only for text format)
        print_events: Whether to print events
        **kwargs: Additional arguments (endpoint, auth_token)

    Returns:
        InvokeResult with the outcome
    """
    invoke = Invoke(
        endpoint=kwargs.get("endpoint"),
        auth_token=kwargs.get("auth_token"),
        print_events=print_events,
    )
    return invoke.invoke_by_key(
        bot_key, messages, parameters, dataset_slugs, mode, stream, output_format, verbose
    )
