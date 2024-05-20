from dataclasses import dataclass, field


@dataclass
class AIResponse:
    type: str = field(init=False)


@dataclass
class AIResponseText(AIResponse):
    responseContent: str

    def __post_init__(self):
        self.type = "TEXT"
        
@dataclass
class AIRequest:
    type: str = field(init=False)


@dataclass
class AIRequestText(AIRequest):
    requestContent: str

    def __post_init__(self):
        self.type = "TEXT"