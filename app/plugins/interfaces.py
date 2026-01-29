from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class BasePlugin(ABC):
    name: str
    version: str
    api_version: str
    deps: list[str]
    schedule: Optional[str]
    permissions: list[str]

    @abstractmethod
    def init(self, config: dict[str, Any], services: dict[str, Any]) -> None:
        raise NotImplementedError


class CollectorPlugin(BasePlugin):
    @abstractmethod
    def run(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        raise NotImplementedError


class IndicatorPlugin(BasePlugin):
    @abstractmethod
    def compute(self, context: dict[str, Any], data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        raise NotImplementedError


class StrategyPlugin(BasePlugin):
    @abstractmethod
    def evaluate(
        self, context: dict[str, Any], indicators: list[dict[str, Any]], data: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        raise NotImplementedError


class NotifierPlugin(BasePlugin):
    @abstractmethod
    def send(self, message: str, severity: str, tags: list[str]) -> dict[str, Any]:
        raise NotImplementedError


class ReportPlugin(BasePlugin):
    @abstractmethod
    def generate(self, context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
