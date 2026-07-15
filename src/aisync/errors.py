from __future__ import annotations


class AisyncError(Exception):
    code = "AISYNC_ERROR"
    level = "ERROR"

    def __init__(self, message: str, *, why: str | None = None, next_action: str | None = None):
        super().__init__(message)
        self.message = message
        self.why = why
        self.next_action = next_action


class DangerError(AisyncError):
    code = "DANGER"
    level = "DANGER"


class ConfigError(AisyncError):
    code = "CONFIG_ERROR"


class DependencyError(AisyncError):
    code = "DEPENDENCY_ERROR"


class ProfileError(AisyncError):
    code = "PROFILE_ERROR"


class GitError(AisyncError):
    code = "GIT_ERROR"


class CryptoError(AisyncError):
    code = "CRYPTO_ERROR"


class RestoreError(AisyncError):
    code = "RESTORE_ERROR"

