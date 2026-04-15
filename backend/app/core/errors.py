from dataclasses import dataclass


@dataclass
class AppError(Exception):
    status_code: int
    error_class: str
    message: str
    recovery_guidance: str
    retryable: bool = False

    def to_dict(self) -> dict:
        return {
            "error_class": self.error_class,
            "message": self.message,
            "recovery_guidance": self.recovery_guidance,
            "retryable": self.retryable,
        }