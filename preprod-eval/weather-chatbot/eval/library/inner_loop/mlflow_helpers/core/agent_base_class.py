# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from abc import abstractmethod
from typing import Any, Optional, Union
import mlflow


class AgentWrapper(mlflow.pyfunc.PythonModel):
    """
    Abstract base class for agent wrappers
    """
    @abstractmethod
    def predict(self, context: Any, agent_input: dict) -> Optional[Union[dict, str]]:
        pass

    @abstractmethod
    def measure(self, parameters: dict) -> dict:
        pass

    def seed_prompt(self) -> dict:
        """
        Returns the seed prompt of agent
        """
        return {}
