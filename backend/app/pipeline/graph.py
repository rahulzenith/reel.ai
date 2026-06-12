from langgraph.graph import END, START, StateGraph

from .nodes.assembler import assembler
from .nodes.broll_selector import broll_selector
from .nodes.evaluator import evaluator
from .nodes.publisher import publisher
from .nodes.script_writer import script_writer
from .nodes.trend_scout import trend_scout
from .nodes.voice_generator import voice_generator
from .routing import route_after_eval
from .state import PipelineState


def build_graph():
    g = StateGraph(PipelineState)

    g.add_node("trend_scout", trend_scout)
    g.add_node("script_writer", script_writer)
    g.add_node("evaluator", evaluator)
    g.add_node("voice_generator", voice_generator)
    g.add_node("broll_selector", broll_selector)
    g.add_node("assembler", assembler)
    g.add_node("publisher", publisher)

    g.add_edge(START, "trend_scout")
    g.add_edge("trend_scout", "script_writer")
    g.add_edge("script_writer", "evaluator")

    # One conditional edge: retry loops back; pass fans out to BOTH parallel branches
    g.add_conditional_edges(
        "evaluator",
        route_after_eval,
        ["script_writer", "voice_generator", "broll_selector"],
    )

    # List-source edge = join: assembler waits for BOTH branches to finish
    g.add_edge(["voice_generator", "broll_selector"], "assembler")
    g.add_edge("assembler", "publisher")
    g.add_edge("publisher", END)

    return g.compile()


graph = build_graph()
