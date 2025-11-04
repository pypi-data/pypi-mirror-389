from enum import Enum
from typing import Optional, Union
from datetime import datetime

from pydantic import BaseModel


class OpenaiRealtimeModels(Enum):
    gpt_4o_realtime = "gpt-4o-realtime-preview"
    gpt_realtime = "gpt-realtime"


class OpenaiRealtimeVoices(Enum):
    alloy = "alloy"
    marin = "marin"
    cedar = "cedar"
    ash = "ash"
    ballad = "ballad"
    coral = "coral"
    echo = "echo"
    sage = "sage"
    shimmer = "shimmer"
    verse = "verse"


class GeminiRealtimeModels(Enum):
    gemini_2_5_flash_exp = "gemini-2.5-flash-exp-native-audio-thinking-dialog"
    gemini_2_0_flash_exp = "gemini-2.0-flash-exp"


class GeminiRealtimeVoices(Enum):
    Puck = "Puck"
    Charon = "Charon"
    Kore = "Kore"
    Fenrir = "Fenrir"
    Aoede = "Aoede"
    Leda = "Leda"
    Orus = "Orus"
    Zephyr = "Zephyr"


class AgentProvider(Enum):
    openai = "openai"
    gemini = "gemini"
    elevenlabs = "elevenlabs"


class OpenaiAgentConfig(BaseModel):
    instructions: str
    model: OpenaiRealtimeModels
    voice: OpenaiRealtimeVoices


class GeminiAgentConfig(BaseModel):
    instructions: str
    model: GeminiRealtimeModels
    voice: GeminiRealtimeVoices


class ElevenlabsAgentConfig(BaseModel):
    elevenlabsAgentId: str


class CreateEquosAgentRequest(BaseModel):
    provider: AgentProvider
    name: Optional[str] = None
    client: Optional[str] = None
    config: Union[OpenaiAgentConfig, GeminiAgentConfig, ElevenlabsAgentConfig]


class UpdateEquosAgentRequest(CreateEquosAgentRequest):
    id: str
    organizationId: str


class EquosAgent(BaseModel):
    id: str
    organizationId: str
    provider: AgentProvider
    name: Optional[str] = None
    client: Optional[str] = None
    config: Union[OpenaiAgentConfig, GeminiAgentConfig]
    createdAt: datetime
    updatedAt: datetime


class ListEquosAgentsResponse(BaseModel):
    skip: int
    take: int
    total: int
    agents: list[EquosAgent]
