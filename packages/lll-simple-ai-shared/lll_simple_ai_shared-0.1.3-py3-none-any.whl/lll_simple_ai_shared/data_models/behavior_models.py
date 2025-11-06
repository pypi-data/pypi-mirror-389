from pydantic import BaseModel, Field
from typing import List, Literal, Union
from ..utils.extract import extract_events_string, default_extract_strings


class SpeechParameters(BaseModel):
    action: Literal["speak", "pause", "emphasize"] = Field(
        ..., description="语音动作类型：speak(说话)、pause(暂停)、emphasize(强调)"
    )
    text: str = Field(..., description="要说的具体文本内容")
    emotion: str = "neutral"
    voice_type: str = "default"
    speed: float = Field(default=1.0, description="语速0.5-2.0")


class BehaviorPlan(BaseModel):
    plan: List[Union[SpeechParameters]] = Field(..., description="行为计划序列")
    current_situation: str = Field(
        ...,
        description="根据你的行为计划，更新你对当前情境认知",
    )


behavior_template = """
<|im_start|>system
下面是当前的信息，请根据你的角色生成语音、动作行为计划：

【当前情境】
{{current_situation}}

【刚才的对话和事件】
{{recent_events}}

【相关的历史记忆】
{{episodic_memories}}

【你正在做的事】
{{active_goals}}

【社交规范】
{{social_norms}}
<|im_end|>
<|im_start|>assistant
"""


def behavior_task_format_inputs(inputs):
    return {
        "current_situation": inputs.get("current_situation", "未知"),
        "recent_events": extract_events_string(inputs.get("recent_events", [])),
        # TODO: 增加时间
        "episodic_memories": inputs.get(
            "episodic_memories_text",
            default_extract_strings(inputs.get("episodic_memories", []), "content"),
        ),
        "active_goals": default_extract_strings(
            inputs.get("active_goals", []), "description"
        ),
        "social_norms": default_extract_strings(inputs.get("social_norms", [])),
    }
