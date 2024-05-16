from abc import abstractmethod
from typing import Any, Optional, Union
import mlflow


class ComponentWrapper(mlflow.pyfunc.PythonModel):
    """
    Abstract base class for component wrappers
    """
    @abstractmethod
    def predict(self, context: Any, component_input: dict) -> Optional[Union[dict, str]]:
        pass

    @abstractmethod
    def measure(self, parameters: dict) -> dict:
        pass

    def seed_prompt(self) -> dict:
        """
        Returns the seed prompt of component
        """
        return {}
