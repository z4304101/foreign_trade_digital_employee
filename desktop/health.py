from enum import Enum


class AppStatus(str, Enum):
    WAITING_INITIALIZATION = "waiting_initialization"
    RUNNING = "running"
    PAUSED = "paused"
    NEEDS_ATTENTION = "needs_attention"
    SERVICE_ERROR = "service_error"


class ServiceName(str, Enum):
    MAIL = "mail"
    AI = "ai"
    WECOM = "wecom"
    HISTORY = "history"


class HealthTracker:
    NEEDS_ATTENTION_THRESHOLD = 3
    SERVICE_ERROR_THRESHOLD = 5

    def __init__(self) -> None:
        self._failures = {
            service: 0
            for service in ServiceName
        }

        self._unrecoverable = {
            service: False
            for service in ServiceName
        }

    def record_failure(
        self,
        service: ServiceName,
        *,
        unrecoverable: bool = False,
    ) -> None:
        self._failures[service] += 1

        if unrecoverable:
            self._unrecoverable[service] = True

    def record_success(
        self,
        service: ServiceName,
    ) -> None:
        self._failures[service] = 0
        self._unrecoverable[service] = False

    def status(
        self,
        base_status: AppStatus,
    ) -> AppStatus:
        if base_status in (
            AppStatus.WAITING_INITIALIZATION,
            AppStatus.PAUSED,
        ):
            return base_status

        if any(
            self._unrecoverable.values()
        ):
            return AppStatus.SERVICE_ERROR

        max_failures = max(
            self._failures.values(),
            default=0,
        )

        if (
            max_failures
            >= self.SERVICE_ERROR_THRESHOLD
        ):
            return AppStatus.SERVICE_ERROR

        if (
            max_failures
            >= self.NEEDS_ATTENTION_THRESHOLD
        ):
            return AppStatus.NEEDS_ATTENTION

        return base_status
