from enum import Enum


class TaskState(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


VALID_TRANSITIONS = {
    TaskState.PENDING: {TaskState.READY, TaskState.CANCELLED},
    TaskState.READY: {TaskState.RUNNING, TaskState.CANCELLED},
    TaskState.RUNNING: {TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED},
    TaskState.FAILED: {TaskState.READY, TaskState.CANCELLED},  # Retry transitions to READY
    TaskState.COMPLETED: set(),
    TaskState.CANCELLED: set(),
}


class TaskStateMachine:
    """Validates and enforces deterministic task state transitions."""

    @staticmethod
    def can_transition(current: str, target: str) -> bool:
        try:
            curr_enum = TaskState(current)
            target_enum = TaskState(target)
            return target_enum in VALID_TRANSITIONS.get(curr_enum, set())
        except ValueError:
            return False

    @staticmethod
    def transition(current: str, target: str) -> str:
        if not TaskStateMachine.can_transition(current, target):
            raise ValueError(f"Invalid task transition from '{current}' to '{target}'.")
        return target
