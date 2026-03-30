import json
import time
from typing import TypedDict
from langgraph.graph import StateGraph, END
from loguru import logger
from src.agents.base import BaseAgent
from src.agents.prompts import RETRIEVAL_PROMPT, ANALYSIS_PROMPT, SYNTHESIS_PROMPT
from src.rag.vector_store import CodeVectorStore

class ReviewState(TypedDict):
    diff: str
    search_queries: list[str]
    context: str
    analysis: dict
    review_comment: str
    error: str
    latency: dict

class ReviewOrchestrator(BaseAgent):
    def __init__(self, vector_store: CodeVectorStore):
        super().__init__()
        self.vector_store = vector_store
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(ReviewState)
        graph.add_node("retrieve", self._retrieve_node)
        graph.add_node("analyze", self._analyze_node)
        graph.add_node("synthesize", self._synthesize_node)
        graph.set_entry_point("retrieve")
        graph.add_edge("retrieve", "analyze")
        graph.add_edge("analyze", "synthesize")
        graph.add_edge("synthesize", END)
        return graph.compile()

    def _retrieve_node(self, state: ReviewState) -> ReviewState:
        logger.info("Agent: Retrieving relevant context...")
        t = time.time()
        try:
            prompt = RETRIEVAL_PROMPT.format(diff=state["diff"])
            queries_text = self.call_llm(prompt, max_tokens=300)
            queries = [
                line.strip().lstrip("0123456789.-) ")
                for line in queries_text.strip().split("\n")
                if line.strip()
            ][:5]

            all_results = []
            seen = set()
            for query in queries:
                results = self.vector_store.search(query, n_results=3)
                for r in results:
                    key = r["metadata"]["filepath"] + r["metadata"]["name"]
                    if key not in seen:
                        seen.add(key)
                        all_results.append(r)

            context = "\n\n".join([
                f"File: {r['metadata']['filepath']} | {r['metadata']['name']}\n{r['content']}"
                for r in all_results[:8]
            ])

            latency = {**state.get("latency", {}), "retrieve_ms": round((time.time() - t) * 1000)}
            logger.info(f"Retrieved {len(all_results)} chunks in {latency['retrieve_ms']}ms")
            return {**state, "search_queries": queries, "context": context, "latency": latency}

        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return {**state, "context": "", "error": str(e)}

    def _analyze_node(self, state: ReviewState) -> ReviewState:
        logger.info("Agent: Analyzing code changes...")
        t = time.time()
        try:
            prompt = ANALYSIS_PROMPT.format(
                diff=state["diff"],
                context=state["context"] or "No context available"
            )
            response = self.call_llm(prompt, max_tokens=1500)

            try:
                start = response.find("{")
                end = response.rfind("}") + 1
                analysis = json.loads(response[start:end])
            except json.JSONDecodeError:
                analysis = {
                    "bugs": [],
                    "security": [],
                    "performance": [],
                    "style": [],
                    "summary": response
                }

            latency = {**state.get("latency", {}), "analyze_ms": round((time.time() - t) * 1000)}
            logger.info(f"Analysis complete in {latency['analyze_ms']}ms")
            return {**state, "analysis": analysis, "latency": latency}

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {**state, "analysis": {}, "error": str(e)}

    def _synthesize_node(self, state: ReviewState) -> ReviewState:
        logger.info("Agent: Synthesizing review comment...")
        t = time.time()
        try:
            analysis_text = json.dumps(state["analysis"], indent=2)
            prompt = SYNTHESIS_PROMPT.format(analysis=analysis_text)
            review = self.call_llm(prompt, max_tokens=1000)

            latency = {**state.get("latency", {}), "synthesize_ms": round((time.time() - t) * 1000)}
            logger.info(f"Synthesis complete in {latency['synthesize_ms']}ms")
            return {**state, "review_comment": review, "latency": latency}

        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return {**state, "review_comment": "Review failed.", "error": str(e)}

    def review(self, diff: str) -> dict:
        logger.info("Starting review pipeline...")
        t = time.time()
        initial_state = ReviewState(
            diff=diff,
            search_queries=[],
            context="",
            analysis={},
            review_comment="",
            error="",
            latency={}
        )
        result = self.graph.invoke(initial_state)
        total_ms = round((time.time() - t) * 1000)
        result["latency"]["total_ms"] = total_ms
        logger.info(f"Review pipeline complete in {total_ms}ms")
        return result