"""Data models for OpenSpec specifications."""

from dataclasses import dataclass, field


@dataclass
class Scenario:
    """Represents a scenario in a requirement."""

    name: str
    steps: list[str]


@dataclass
class Requirement:
    """Represents a requirement in a spec."""

    name: str
    description: str
    scenarios: list[Scenario] = field(default_factory=list)


@dataclass
class Spec:
    """Represents an OpenSpec specification."""

    id: str
    path: str
    purpose: str
    requirements: list[Requirement] = field(default_factory=list)
