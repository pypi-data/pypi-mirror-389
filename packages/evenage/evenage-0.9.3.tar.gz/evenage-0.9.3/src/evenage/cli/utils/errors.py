"""
Error handling utilities for EvenAge CLI.

Provides structured exception hierarchy and rich-formatted error display.
"""

from __future__ import annotations


class EvenAgeError(Exception):
    """Base exception for all EvenAge CLI errors."""

    def __init__(self, message: str, hint: str | None = None):
        self.message = message
        self.hint = hint
        super().__init__(message)


class ProjectNotFoundError(EvenAgeError):
    """Raised when not in an EvenAge project directory."""

    def __init__(self, message: str = "Not in an EvenAge project directory"):
        super().__init__(
            message,
            hint="Run 'evenage init <project_name>' to create a new project",
        )


class ProjectExistsError(EvenAgeError):
    """Raised when trying to create a project that already exists."""

    def __init__(self, path: str):
        super().__init__(
            f"Directory {path} already contains an EvenAge project",
            hint="Use a different directory or delete the existing evenage.yml",
        )


class NestedProjectError(EvenAgeError):
    """Raised when trying to create a nested project."""

    def __init__(self, parent_path: str):
        super().__init__(
            f"Detected existing EvenAge project at {parent_path}",
            hint="Cannot create a nested project inside another EvenAge project",
        )


class InvalidConfigError(EvenAgeError):
    """Raised when configuration files are invalid."""

    def __init__(self, filename: str, details: str):
        super().__init__(
            f"Invalid configuration in {filename}: {details}",
            hint="Check the file syntax and ensure all required fields are present",
        )


class DockerNotFoundError(EvenAgeError):
    """Raised when Docker is not installed or not running."""

    def __init__(self):
        super().__init__(
            "Docker not found or not running",
            hint="Install Docker (https://docs.docker.com/get-docker/) and ensure it's running",
        )


class DockerComposeError(EvenAgeError):
    """Raised when Docker Compose operations fail."""

    def __init__(self, operation: str, details: str):
        super().__init__(
            f"Docker Compose {operation} failed: {details}",
            hint="Check docker-compose.yml and ensure all services are properly configured",
        )


class AgentNotFoundError(EvenAgeError):
    """Raised when an agent doesn't exist."""

    def __init__(self, agent_name: str):
        super().__init__(
            f"Agent '{agent_name}' not found",
            hint=f"Run 'evenage add agent {agent_name}' to create it",
        )


class InvalidInputError(EvenAgeError):
    """Raised when user input is invalid."""

    def __init__(self, field: str, details: str):
        super().__init__(
            f"Invalid {field}: {details}",
            hint="Check the command usage with --help",
        )


class FileGenerationError(EvenAgeError):
    """Raised when file generation fails."""

    def __init__(self, filename: str, details: str):
        super().__init__(
            f"Failed to generate {filename}: {details}",
            hint="Check file permissions and available disk space",
        )


class ServiceNotReadyError(EvenAgeError):
    """Raised when a service is not ready after startup."""

    def __init__(self, service: str, timeout: int):
        super().__init__(
            f"Service '{service}' did not become ready within {timeout} seconds",
            hint=f"Check logs with 'evenage logs {service}' or 'docker compose logs {service}'",
        )
