from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class TokensInfo(BaseModel):
    prompt: int
    completion: int
    total: int

class ConfigInfo(BaseModel):
    model: str
    temperature: float
    vision: bool = False
    reasoning: bool = False
    reflection: bool = False
    debug: bool = False

class UIStateInfo(BaseModel):
    a11y_tree: str
    phone_state: Dict[str, Any]

class ChatHistoryMessage(BaseModel):
    role: str
    content: str

class AgentStepDTO(BaseModel):
    step_number: int
    reasoning: Optional[str] = None
    code: Optional[str] = None
    tokens_used: TokensInfo
    cost: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SessionDTO(BaseModel):
    session_id: str
    api_key: str
    task: str
    device_serial: str
    config: ConfigInfo
    chat_history: List[ChatHistoryMessage] = []
    steps: List[AgentStepDTO] = []
    ui_state: Optional[UIStateInfo] = None
