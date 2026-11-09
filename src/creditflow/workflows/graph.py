from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from creditflow.workflows.agents.compliance import compliance_analysis
from creditflow.workflows.agents.financial import financial_analysis
from creditflow.workflows.agents.intake import (
    extract_financial_data,
    load_application,
    retrieve_policies,
    validate_documents,
    validate_extracted_information,
)
from creditflow.workflows.agents.report import generate_report
from creditflow.workflows.agents.review import audit_completion, human_review
from creditflow.workflows.agents.risk import risk_analysis
from creditflow.workflows.agents.verification import (
    bounded_correction,
    verification_route,
    verify,
)
from creditflow.workflows.state import UnderwritingState


def build_underwriting_graph(checkpointer: BaseCheckpointSaver[str] | None = None) -> Any:
    """Compose specialized agents into the durable underwriting state graph."""
    builder = StateGraph(UnderwritingState)
    builder.add_node("load_application", load_application)
    builder.add_node("validate_documents", validate_documents)
    builder.add_node("extract_financial_data", extract_financial_data)
    builder.add_node("validate_extracted_information", validate_extracted_information)
    builder.add_node("retrieve_policies", retrieve_policies)
    builder.add_node("financial_analysis", financial_analysis)
    builder.add_node("risk_analysis", risk_analysis)
    builder.add_node("compliance_analysis", compliance_analysis)
    builder.add_node("verify", verify)
    builder.add_node("correct", bounded_correction)
    builder.add_node("generate_report", generate_report)
    builder.add_node("human_review", human_review)
    builder.add_node("audit_completion", audit_completion)

    builder.add_edge(START, "load_application")
    builder.add_edge("load_application", "validate_documents")
    builder.add_edge("validate_documents", "extract_financial_data")
    builder.add_edge("extract_financial_data", "validate_extracted_information")
    builder.add_edge("validate_extracted_information", "retrieve_policies")
    builder.add_edge("retrieve_policies", "financial_analysis")
    builder.add_edge("financial_analysis", "risk_analysis")
    builder.add_edge("financial_analysis", "compliance_analysis")
    builder.add_edge(["risk_analysis", "compliance_analysis"], "verify")
    builder.add_conditional_edges("verify", verification_route)
    builder.add_edge("correct", "verify")
    builder.add_edge("generate_report", "human_review")
    builder.add_edge("human_review", "audit_completion")
    builder.add_edge("audit_completion", END)
    return builder.compile(checkpointer=checkpointer or InMemorySaver())
