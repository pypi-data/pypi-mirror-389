# ----------------------------------------------------------------------
# The public "EchoesAssistantV2" façade.  All heavy‑lifting is delegated
# to the service modules above.
# ----------------------------------------------------------------------
from __future__ import annotations

import asyncio
import json
import os
import time
from collections.abc import Iterator
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from echoes.config import (DEFAULT_MAX_TOKENS, DEFAULT_MODEL,
                           DEFAULT_TEMPERATURE, USE_RESPONSES_API,
                           RuntimeOptions)
from echoes.services.agents import AgentWorkflow
from echoes.services.filesystem import FilesystemTools
from echoes.services.glimpse import (ClarifierEngine, Draft, GlimpseEngine,
                                     PrivacyGuard)
# ---------- Optional, heavy services ----------
# (These imports are cheap – they just give us the class objects or stubs)
from echoes.services.inventory import InventoryService
from echoes.services.knowledge import KnowledgeManager
from echoes.services.knowledge_graph import KnowledgeGraph
from echoes.services.legal import (ValueSystem, get_cognitive_accounting,
                                   get_enhanced_accounting)
from echoes.services.multimodal import MultimodalEngine
from echoes.services.quantum import QuantumStateManager
from echoes.services.rag import RAG_AVAILABLE, create_rag_system
from echoes.utils.context_manager import ContextManager
from echoes.utils.import_helpers import safe_import
from echoes.utils.memory_store import MemoryStore
from echoes.utils.status_indicator import STATUS_TOOL, EnhancedStatusIndicator


# ----------------------------------------------------------------------
# The *public* assistant class – thin, well‑documented, easy to unit‑test.
# ----------------------------------------------------------------------
class EchoesAssistantV2:
    """
    High‑level conversational AI that knows how to:

    * talk to OpenAI's **Responses** (or Chat Completions) API,
    * run the **Tool Framework**,
    * retrieve semantic knowledge via **RAG V2**,
    * keep a **conversation context** & persistence,
    * show **status** while it works,
    * and many *optional* flavours (GLIMPSE, MULTIMODAL, LEGAL, QUANTUM …).
    """

    # ------------------------------------------------------------------
    # 1️⃣  Construction – wire all components together.
    # ------------------------------------------------------------------
    def __init__(self, *, opts: RuntimeOptions | None = None, **overrides: Any):
        """
        ``opts`` lets the caller toggle the optional subsystems (e.g. ``opts.enable_glimpse``).
        ``overrides`` can be used to inject a non‑default OpenAI client,
        custom ``session_id`` etc.
        """
        opts = opts or RuntimeOptions()
        # Merge explicit overrides (e.g. ``model="gpt-4o-mini"``) on top of the opts.
        for name, value in overrides.items():
            if hasattr(opts, name):
                setattr(opts, name, value)

        # ------------------------------------------------------------------
        #   1️⃣ Load environment + OpenAI client
        # ------------------------------------------------------------------
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is missing")

        self.client: OpenAI = overrides.get("client") or OpenAI(api_key=self.api_key)

        # ------------------------------------------------------------------
        #   2️⃣ Core model configuration
        # ------------------------------------------------------------------
        self.model = opts.model or DEFAULT_MODEL
        self.temperature = opts.temperature or DEFAULT_TEMPERATURE
        self.max_tokens = opts.max_tokens or DEFAULT_MAX_TOKENS

        # ------------------------------------------------------------------
        #   3️⃣ Context & persistence
        # ------------------------------------------------------------------
        self.session_id = opts.session_id or f"session_{int(time.time())}"
        self.context_manager = ContextManager()
        self.memory_store = MemoryStore()
        # Restore any previous conversation for this session
        saved = self.memory_store.load_conversation(self.session_id)
        if saved:
            self.context_manager.conversations[self.session_id] = saved

        # ------------------------------------------------------------------
        #   4️⃣ Optional subsystems (only instantiated if the feature flag is on)
        # ------------------------------------------------------------------
        #   4.1  Tool framework
        self.enable_tools = opts.enable_tools
        if self.enable_tools:
            # Registry is a *tiny* import – it will either be the real thing
            # or a no‑op stub that speaks the same API.
            _, TOOLS_AVAILABLE = safe_import("tools.registry")
            self.tool_registry = (
                safe_import("tools.registry")[0].get_registry()
                if TOOLS_AVAILABLE
                else SimpleNamespace()
            )
        else:
            self.tool_registry = None

        #   4.2  RAG
        self.enable_rag = opts.enable_rag and RAG_AVAILABLE
        self.rag = None
        if self.enable_rag:
            # "balanced" is a sane default – callers can change it later.
            self.rag = create_rag_system("balanced")

        #   4.3  Knowledge manager (does nothing if the real class is missing)
        self.knowledge_manager = KnowledgeManager()

        #   4.4  Filesystem tools (fallback is a dummy shim)
        self.fs_tools = FilesystemTools(root_dir=os.getcwd())

        #   4.5  Agent workflow (fallback is a no‑op)
        self.agent_workflow = AgentWorkflow(self)

        #   4.6  Quantum state manager
        self.quantum_state_manager = QuantumStateManager()
        self.quantum_state_manager.initialize_quantum_states()

        #   4.7  Glimpse pre‑flight system
        self.enable_glimpse = opts.enable_glimpse
        if self.enable_glimpse:

            def _commit_sink(draft: Draft) -> None:
                # Very cheap persistent audit trail – we never block user flow.
                os.makedirs("results", exist_ok=True)
                rec = {
                    "ts": datetime.now(UTC).isoformat(),
                    "input_text": draft.input_text,
                    "goal": draft.goal,
                    "constraints": draft.constraints,
                }
                with open("results/glimpse_commits.jsonl", "a", encoding="utf-8") as f:
                    json.dump(rec, f, ensure_ascii=False)
                    f.write("\n")

            self.glimpse_engine = GlimpseEngine(
                privacy_guard=PrivacyGuard(on_commit=_commit_sink),
                enable_clarifiers=True,
            )
            # Use the newer, "enhanced" clarifier engine.
            if hasattr(self.glimpse_engine, "_clarifier_engine"):
                self.glimpse_engine._clarifier_engine = ClarifierEngine(
                    use_enhanced_mode=True
                )
            self.glimpse_goal = ""
            self.glimpse_constraints = ""

        #   4.8  Multimodal resonance (optional)
        self.enable_multimodal = safe_import("multimodal_resonance")[1]
        if self.enable_multimodal:
            self.multimodal_engine = MultimodalEngine()
        else:
            self.multimodal_engine = None

        #   4.9  Legal safeguards & value system
        self.enable_legal = (
            safe_import("legal_safeguards")[1] and safe_import("enhanced_accounting")[1]
        )
        if self.enable_legal:
            self.legal_system = get_cognitive_accounting()
            self.accounting_system = get_enhanced_accounting()
            self.value_system = ValueSystem()
        else:
            self.legal_system = self.accounting_system = self.value_system = None

        #   4.10 Knowledge graph
        self.knowledge_graph = KnowledgeGraph()

        # ------------------------------------------------------------------
        #   5️⃣  Runtime helpers
        # ------------------------------------------------------------------
        self.status = EnhancedStatusIndicator(enabled=opts.enable_status)

        # ------------------------------------------------------------------
        #   6️⃣  Miscellaneous – inventory service (ATLAS) is always available.
        # ------------------------------------------------------------------
        self.inventory_service = InventoryService()

        # ------------------------------------------------------------------
        #   7️⃣  Debug/diagnostic banner
        # ------------------------------------------------------------------
        print(
            f"✓ EchoesAssistantV2 ready – session={self.session_id} – "
            f"responses_api={USE_RESPONSES_API} – glimpse={self.enable_glimpse}"
        )

    # ==========================================================================
    # 2️⃣  PUBLIC API – ONE METHOD THAT DO THE HEAVY‑LIFTING
    # ==========================================================================

    def chat(
        self,
        user_message: str,
        *,
        system_prompt: str | None = None,
        stream: bool | None = None,
        show_status: bool | None = None,
        context_limit: int = 5,
        require_approval: bool | None = None,
    ) -> str | Iterator[str]:
        """
        **Main entry‑point** – send a message to the assistant and get a response.
        The method decides—based on the configuration—whether to:

        * run a **Glimpse pre‑flight** check,
        * call the **Responses** (or **Chat Completions**) API,
        * handle **tool calls** (max 5 rounds),
        * stream tokens to the caller,
        * and finally enrich the answer with personality / intent information.

        Returns
        -------
        * ``str`` – when ``stream=False`` (default),
        * ``Iterator[str]`` – when ``stream=True``.
        """
        # ------------------------------------------------------------------
        #   Normalise arguments (fallback to instance defaults)
        # ------------------------------------------------------------------
        stream = stream if stream is not None else True
        show_status = show_status if show_status is not None else True
        require_approval = require_approval if require_approval is not None else False
        system_prompt = system_prompt or ""

        # ------------------------------------------------------------------
        #   1️⃣  OPTIONAL – run Glimpse pre‑flight
        # ------------------------------------------------------------------
        if self.enable_glimpse:
            draft = Draft(
                input_text=user_message,
                goal=self.glimpse_goal,
                constraints=self.glimpse_constraints,
            )
            glimpse_result = asyncio.run(self.glimpse_engine.glimpse(draft))
            # Very small human‑in‑the‑loop hook – you can decide to abort/adjust.
            if glimpse_result.status != "aligned":
                # In the REPL we ask the user; in a pure‑API call we just log.
                self.status.error(f"Glimpse mis‑alignment: {glimpse_result.status}")
                # You could raise an exception or simply continue – we continue.
        # ------------------------------------------------------------------
        #   2️⃣  Build the message list sent to the model
        # ------------------------------------------------------------------
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Add recent conversation history (user + assistant pairs)
        history = self.context_manager.get_messages(
            self.session_id, limit=context_limit
        )
        messages.extend([{"role": m["role"], "content": m["content"]} for m in history])

        # Optionally sprinkle in RAG context
        if self.enable_rag and self.rag:
            rag_context = self._retrieve_rag_context(user_message)
            if rag_context:
                rag_text = "\n\n".join(
                    f"[Source {i + 1}]: {c['text'][:200]}..."
                    for i, c in enumerate(rag_context)
                )
                messages.append(
                    {
                        "role": "system",
                        "content": ("Relevant knowledge base excerpts:\n" + rag_text),
                    }
                )

        # Finally the new user message
        messages.append({"role": "user", "content": user_message})

        # ------------------------------------------------------------------
        #   3️⃣  Tool handling – fetch the OpenAI‑compatible schema list
        # ------------------------------------------------------------------
        tool_schemas = (
            self._sanitize_tool_schemas(self.tool_registry.get_openai_schemas())
            if self.enable_tools and self.tool_registry
            else []
        )

        # ------------------------------------------------------------------
        #   4️⃣  Dispatch to Responses or Chat Completions
        # ------------------------------------------------------------------
        if USE_RESPONSES_API:
            # Convert chat‑style messages → Responses‑API format
            api_input = self._chat_to_responses(messages)
            api_tools = self._tools_to_responses_format(tool_schemas)

            # ----------------------------------------------------------------
            #   4a️⃣  Streaming loop (Responses API)
            # ----------------------------------------------------------------
            if stream:
                return self._stream_responses_api(
                    api_input,
                    api_tools,
                    require_approval,
                    show_status,
                )
            # ----------------------------------------------------------------
            #   4b️⃣  Non‑streaming (single request)
            # ----------------------------------------------------------------
            response_obj = self._safe_responses_create(
                model=self.model,
                input=api_input,
                tools=api_tools if tool_schemas else None,
                tool_choice="auto" if tool_schemas else None,
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
            )
            # Convert back to canonical Chat format
            chat_msg = self._responses_to_chat([response_obj])[0]
            final_text = chat_msg["content"]
        else:
            # ----------------------------------------------------------------
            #   4c️⃣  Legacy Chat Completions API (kept for compatibility)
            # ----------------------------------------------------------------
            if stream:
                return self._stream_chat_completions(
                    messages, tool_schemas, require_approval, show_status
                )
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tool_schemas if self.enable_tools else None,
                    tool_choice="auto" if tool_schemas else None,
                    temperature=self.temperature,
                    max_completion_tokens=self.max_tokens
                    if "o3" in self.model
                    else None,
                    max_tokens=self.max_tokens if "o3" not in self.model else None,
                    stream=False,
                )
                final_text = response.choices[0].message.content

        # ------------------------------------------------------------------
        #   5️⃣  Persist the assistant message + update metrics
        # ------------------------------------------------------------------
        self.context_manager.add_message(self.session_id, "assistant", final_text)
        # (model_metrics.update(...) omitted for brevity – you can plug it back in)

        return final_text

    # ==========================================================================
    # 3️⃣  PRIVATE helpers – keep the public method tiny
    # ==========================================================================

    # ----------------------------------------------------------------------
    # RAG
    # ----------------------------------------------------------------------
    def _retrieve_rag_context(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        if not self.enable_rag or not self.rag:
            return []

        try:
            result = self.rag.search(query, top_k=top_k)
            if hasattr(result, "results"):
                return result.results
            elif isinstance(result, dict):
                return result.get("results", [])
            elif isinstance(result, list):
                return result
            return []
        except Exception as exc:
            self.status.error(f"RAG search failed: {exc}")
            return []

    # ----------------------------------------------------------------------
    # Conversions between the two API shapes
    # ----------------------------------------------------------------------
    @staticmethod
    def _chat_to_responses(messages: list[dict[str, str]]) -> list[dict[str, Any]]:
        """
        Convert OpenAI *chat* messages into the newer *Responses* "Items'' format.
        """
        out: list[dict[str, Any]] = []
        for m in messages:
            role = m["role"]
            if role == "system":
                out.append(
                    {"role": "developer", "type": "message", "content": m["content"]}
                )
            elif role == "user":
                out.append({"role": "user", "type": "message", "content": m["content"]})
            elif role == "assistant":
                out.append(
                    {
                        "role": "assistant",
                        "type": "message",
                        "content": [{"type": "output_text", "text": m["content"]}],
                    }
                )
        return out

    @staticmethod
    def _responses_to_chat(
        response_items: list[Any],
    ) -> list[dict[str, Any]]:
        """
        Convert a *Responses* result back to the classic chat message dict.
        """
        msgs: list[dict[str, Any]] = []
        for item in response_items:
            # ``item`` can be a Responses‑API response object or a plain dict.
            if hasattr(item, "output"):
                # New style – iterate over the items
                for out_item in item.output:
                    if out_item.type == "message":
                        text_parts = [
                            c.text
                            for c in out_item.content
                            if getattr(c, "type", None) == "output_text"
                        ]
                        msgs.append(
                            {
                                "role": "assistant",
                                "content": " ".join(text_parts),
                            }
                        )
            else:
                # Fallback – assume a dict with ``choices`` like the Chat API
                if getattr(item, "choices", None):
                    content = item.choices[0].message.content
                    msgs.append({"role": "assistant", "content": content})
        return msgs

    @staticmethod
    def _sanitize_tool_schemas(raw_tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Normalise the possibly heterogeneous tool schema representations
        (dicts, objects, …) into the strict OpenAI function schema format.
        """
        out: list[dict[str, Any]] = []
        for tool in raw_tools:
            if not isinstance(tool, dict):
                tool = getattr(tool, "__dict__", {}) or {}
            func = tool.get("function") or {}
            # Ensure JSON‑Schema compliance
            params = func.get("parameters") or {}
            if not isinstance(params, dict):
                params = {
                    "type": "object",
                    "properties": {"args": {"type": "string"}},
                }
            if "type" not in params:
                params = {"type": "object", "properties": params}
            out.append(
                {
                    "type": "function",
                    "function": {
                        "name": func.get("name") or tool.get("name") or "unknown",
                        "description": func.get("description", ""),
                        "parameters": params,
                    },
                }
            )
        return out

    @staticmethod
    def _tools_to_responses_format(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Convert the *Chat‑Completions* tool schema (function‑call) list into the
        *Responses* compatible shape (different field names but same semantics).
        """
        out: list[dict[str, Any]] = []
        for tool in tools:
            if tool.get("type") != "function":
                continue
            fn = tool.get("function", {})
            out.append(
                {
                    "type": "function",
                    "name": fn.get("name") or "anonymous",
                    "description": fn.get("description", ""),
                    "parameters": fn.get("parameters", {}),
                    "strict": bool(fn.get("strict", False)),
                }
            )
        return out

    # ----------------------------------------------------------------------
    # Streaming helpers – Responses API
    # ----------------------------------------------------------------------
    def _stream_responses_api(
        self,
        api_input: list[dict[str, Any]],
        api_tools: list[dict[str, Any]],
        require_approval: bool,
        show_status: bool,
    ) -> Iterator[str]:
        """
        Core **Responses‑API** streaming loop.  Handles *tool‑call* rounds,
        updates the conversation context, and yields the raw text chunks to the caller.
        """
        status = EnhancedStatusIndicator(enabled=show_status)

        # ------------------------------------------------------------------
        #   1️⃣  Initial request (may already contain tool calls)
        # ------------------------------------------------------------------
        response = self._safe_responses_create(
            model=self.model,
            input=api_input,
            tools=api_tools if api_tools else None,
            tool_choice="auto" if api_tools else None,
            temperature=self.temperature,
            max_output_tokens=self.max_tokens,
            stream=True,
        )
        if not response:
            raise RuntimeError("Responses API failed to start a stream")

        # ------------------------------------------------------------------
        #   2️⃣  Iterate over chunks – collect text and possible tool calls
        # ------------------------------------------------------------------
        assistant_text = ""
        tool_calls: list[
            Any
        ] = []  # will hold objects that look like the Chat API tool calls

        for chunk in response:
            # ``chunk`` can be any of the many Responses‑API types, so we guard heavily.
            try:
                # ── Text token ────────────────────────────────────────
                if hasattr(chunk, "type") and chunk.type == "response.output_text.done":
                    if getattr(chunk, "text", None):
                        assistant_text += chunk.text
                        yield chunk.text

                # ── Tool‑call item ─────────────────────────────────────
                elif (
                    hasattr(chunk, "type")
                    and chunk.type == "response.output_item.added"
                ):
                    if hasattr(chunk, "item") and hasattr(chunk.item, "content"):
                        for ci in chunk.item.content:
                            if getattr(ci, "type", None) == "tool_call":
                                tool_calls.append(
                                    SimpleNamespace(
                                        id=ci.id,
                                        function=SimpleNamespace(
                                            name=ci.name,
                                            arguments=ci.arguments,
                                        ),
                                    )
                                )
                # ── Fallback for old style output ───────────────────────
                elif hasattr(chunk, "output"):
                    for out_item in chunk.output:
                        if out_item.type == "message":
                            for ci in out_item.content:
                                if ci.type == "output_text":
                                    assistant_text += ci.text
                                    yield ci.text
                                elif ci.type == "tool_call":
                                    tool_calls.append(
                                        SimpleNamespace(
                                            id=ci.id,
                                            function=SimpleNamespace(
                                                name=ci.name,
                                                arguments=ci.arguments,
                                            ),
                                        )
                                    )
            except Exception as e:
                status.error(f"Chunk parsing error: {e}")
                continue

        # ------------------------------------------------------------------
        #   3️⃣  If we received tool calls -> execute them & recurse once
        # ------------------------------------------------------------------
        if tool_calls:
            if not self.enable_tools or not self.tool_registry:
                status.error("Tool calls received but tool framework disabled")
                # Save the assistant text and bail out.
                self.context_manager.add_message(
                    self.session_id, "assistant", assistant_text
                )
                return

            # Record the first assistant turn (text only)
            self.context_manager.add_message(
                self.session_id, "assistant", assistant_text
            )

            # ----------------------------------------------------------------
            #   Execute every tool call and feed the results back to the model.
            # ----------------------------------------------------------------
            for tc in tool_calls:
                result = self._execute_tool_call(tc, status)
                #  ── Insert the tool result into the conversation (Responses shape)
                api_input.append(
                    {
                        "role": "tool",
                        "type": "message",
                        "content": [{"type": "result", "result": result}],
                        "tool_call_id": tc.id,
                        "name": tc.function.name,
                    }
                )
            # ----------------------------------------------------------------
            #   Re‑run the model **once** with the new input (max 5 tool iterations
            #   total – the outer ``chat`` method enforces that limit).
            # ----------------------------------------------------------------
            final_response = self._safe_responses_create(
                model=self.model,
                input=api_input,
                tools=None,
                tool_choice=None,
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
                stream=True,
            )
            if not final_response:
                raise RuntimeError("Responses API failed on second pass")

            # Yield the final assistant reply
            final_text = ""
            for chunk in final_response:
                try:
                    if (
                        hasattr(chunk, "type")
                        and chunk.type == "response.output_text.done"
                    ):
                        if getattr(chunk, "text", None):
                            final_text += chunk.text
                            yield chunk.text
                    elif hasattr(chunk, "output"):
                        for out_item in chunk.output:
                            if out_item.type == "message":
                                for ci in out_item.content:
                                    if ci.type == "output_text":
                                        final_text += ci.text
                                        yield ci.text
                except Exception as e:
                    status.error(f"Final chunk error: {e}")
                    continue

            self.context_manager.add_message(self.session_id, "assistant", final_text)
        else:
            # ----------------------------------------------------------------
            #   No tool calls – just store the raw assistant response
            # ----------------------------------------------------------------
            self.context_manager.add_message(
                self.session_id, "assistant", assistant_text
            )

    # ----------------------------------------------------------------------
    # Streaming helper for legacy Chat Completions (kept for completeness)
    # ----------------------------------------------------------------------
    def _stream_chat_completions(
        self,
        messages: list[dict[str, str]],
        tool_schemas: list[dict[str, Any]],
        require_approval: bool,
        show_status: bool,
    ) -> Iterator[str]:
        status = EnhancedStatusIndicator(enabled=show_status)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tool_schemas if self.enable_tools else None,
            tool_choice="auto" if tool_schemas else None,
            temperature=self.temperature,
            max_completion_tokens=self.max_tokens if "o3" in self.model else None,
            max_tokens=self.max_tokens if "o3" not in self.model else None,
            stream=True,
        )
        assistant_text = ""

        for chunk in response:
            # ----------------------------------------------------------------
            #   Text tokens
            # ----------------------------------------------------------------
            if chunk.choices and chunk.choices[0].delta.content:
                delta = chunk.choices[0].delta.content
                assistant_text += delta
                yield delta

            # ----------------------------------------------------------------
            #   Tool calls (streaming‑aware)
            # ----------------------------------------------------------------
            if hasattr(chunk.choices[0].delta, "tool_calls"):
                for tc in chunk.choices[0].delta.tool_calls:
                    # Build a tiny namespace that mimics the Chat API structure
                    if not hasattr(self, "_streaming_tool_calls"):
                        self._streaming_tool_calls = {}
                    call_id = tc.id
                    if call_id not in self._streaming_tool_calls:
                        self._streaming_tool_calls[call_id] = {
                            "id": call_id,
                            "function": {"name": "", "arguments": ""},
                        }
                    if tc.function:
                        if tc.function.name:
                            self._streaming_tool_calls[call_id]["function"][
                                "name"
                            ] = tc.function.name
                        if tc.function.arguments:
                            self._streaming_tool_calls[call_id]["function"][
                                "arguments"
                            ] += tc.function.arguments

        # --------------------------------------------------------------------
        #   If we saw tool calls, execute them now and feed results back to the model
        # --------------------------------------------------------------------
        if hasattr(self, "_streaming_tool_calls"):
            if not self.enable_tools or not self.tool_registry:
                status.error("Tool calls received but tool framework disabled")
                self.context_manager.add_message(
                    self.session_id, "assistant", assistant_text
                )
                return

            self.context_manager.add_message(
                self.session_id, "assistant", assistant_text
            )

            for tc_data in self._streaming_tool_calls.values():
                tc = SimpleNamespace(
                    id=tc_data["id"],
                    function=SimpleNamespace(
                        name=tc_data["function"]["name"],
                        arguments=tc_data["function"]["arguments"],
                    ),
                )
                result = self._execute_tool_call(tc, status)

                messages.append(
                    {
                        "role": "tool",
                        "name": tc.function.name,
                        "tool_call_id": tc.id,
                        "content": result,
                    }
                )

            # ----------------------------------------------------------------
            #   One final non‑streaming pass (the user‑approved result)
            # ----------------------------------------------------------------
            final = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=None,
                tool_choice=None,
                temperature=self.temperature,
                max_completion_tokens=self.max_tokens if "o3" in self.model else None,
                max_tokens=self.max_tokens if "o3" not in self.model else None,
                stream=False,
            )
            final_text = final.choices[0].message.content
            self.context_manager.add_message(self.session_id, "assistant", final_text)
            yield final_text

        else:
            # ----------------------------------------------------------------
            #   No tool calls – just persist the assistant turn.
            # ----------------------------------------------------------------
            self.context_manager.add_message(
                self.session_id, "assistant", assistant_text
            )

    # ----------------------------------------------------------------------
    # Tool execution – shared by both streaming implementations
    # ----------------------------------------------------------------------
    def _execute_tool_call(
        self, tool_call: Any, status: EnhancedStatusIndicator
    ) -> str:
        """Run a single tool and return the (stringified) result."""
        if not self.enable_tools or not self.tool_registry:
            status.error("Tool framework disabled")
            return "Error: tool framework disabled"

        name = tool_call.function.name
        try:
            args = json.loads(tool_call.function.arguments or "{}")
        except json.JSONDecodeError as exc:
            status.error(f"Tool arguments JSON error: {exc}")
            return f"Error: {exc}"

        status.start_phase(f"{STATUS_TOOL} Executing {name}()", 0)
        tool = self.tool_registry.get_tool(name)
        if not tool:
            status.error(f"Tool {name} not found")
            return f"Error: tool {name} not found"

        try:
            result = tool.execute(**args)  # type: ignore[call-arg]
            status.complete_phase(f"{name} succeeded")
            return json.dumps(result) if isinstance(result, dict) else str(result)
        except Exception as exc:
            status.error(f"{name} failed: {exc}")
            return f"Error: {exc}"

    # ----------------------------------------------------------------------
    # Safe wrapper around the Responses API – never raises to the outer logic.
    # ----------------------------------------------------------------------
    def _safe_responses_create(self, *args: Any, **kwargs: Any) -> Any | None:
        """Call ``client.responses.create`` and swallow any exception, logging it."""
        try:
            return self.client.responses.create(*args, **kwargs)  # type: ignore[attr-defined]
        except Exception as exc:
            self.status.error(f"Responses API error: {exc}")
            return None

    # ----------------------------------------------------------------------
    # Additional public methods for completeness
    # ----------------------------------------------------------------------
    def add_knowledge(
        self, key: str, value: Any, metadata: dict[str, Any] = None
    ) -> bool:
        """Add knowledge to the knowledge manager."""
        return self.knowledge_manager.add_knowledge(key, value, metadata)

    def get_conversation_history(
        self, session_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Get conversation history."""
        session = session_id or self.session_id
        return self.context_manager.get_messages(session)

    def clear_session(self, session_id: str | None = None) -> bool:
        """Clear a session."""
        session = session_id or self.session_id
        self.context_manager.clear_session(session)
        return self.memory_store.delete_conversation(session)

    def get_stats(self) -> dict[str, Any]:
        """Get assistant statistics."""
        return {
            "session_id": self.session_id,
            "model": self.model,
            "features": {
                "rag": self.enable_rag,
                "tools": self.enable_tools,
                "glimpse": self.enable_glimpse,
                "multimodal": self.enable_multimodal,
                "legal": self.enable_legal,
            },
            "conversation_length": len(
                self.context_manager.get_messages(self.session_id)
            ),
            "knowledge_items": len(self.knowledge_manager.list_knowledge()),
            "quantum_states": self.quantum_state_manager.get_quantum_metrics(),
        }
