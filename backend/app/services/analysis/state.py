from enum import Enum

class AnalysisState(str, Enum):
    CREATED = "created"
    UNDERSTANDING = "understanding"
    PLANNING = "planning"
    PLAN_VALIDATED = "plan_validated"
    DATA_RETRIEVAL = "data_retrieval"
    SPATIAL_ANALYSIS = "spatial_analysis"
    COMPUTER_VISION = "computer_vision"
    EVIDENCE_BUILDING = "evidence_building"
    AI_REASONING = "ai_reasoning"
    VALIDATION = "validation"
    COMPLETED = "completed"
    FAILED = "failed"

TRANSITIONS = {
    AnalysisState.CREATED: [AnalysisState.UNDERSTANDING],
    AnalysisState.UNDERSTANDING: [AnalysisState.PLANNING, AnalysisState.FAILED],
    AnalysisState.PLANNING: [AnalysisState.PLAN_VALIDATED, AnalysisState.FAILED],
    AnalysisState.PLAN_VALIDATED: [AnalysisState.DATA_RETRIEVAL, AnalysisState.FAILED],
    AnalysisState.DATA_RETRIEVAL: [AnalysisState.SPATIAL_ANALYSIS, AnalysisState.FAILED],
    AnalysisState.SPATIAL_ANALYSIS: [AnalysisState.COMPUTER_VISION, AnalysisState.EVIDENCE_BUILDING, AnalysisState.FAILED],
    AnalysisState.COMPUTER_VISION: [AnalysisState.EVIDENCE_BUILDING, AnalysisState.FAILED],
    AnalysisState.EVIDENCE_BUILDING: [AnalysisState.AI_REASONING, AnalysisState.FAILED],
    AnalysisState.AI_REASONING: [AnalysisState.VALIDATION, AnalysisState.FAILED],
    AnalysisState.VALIDATION: [AnalysisState.COMPLETED, AnalysisState.FAILED],
    AnalysisState.COMPLETED: [],
    AnalysisState.FAILED: [],
}

def can_transition(from_state: str | AnalysisState, to_state: str | AnalysisState) -> bool:
    try:
        f_enum = AnalysisState(from_state)
        t_enum = AnalysisState(to_state)
        return t_enum in TRANSITIONS.get(f_enum, [])
    except (ValueError, KeyError):
        return False
