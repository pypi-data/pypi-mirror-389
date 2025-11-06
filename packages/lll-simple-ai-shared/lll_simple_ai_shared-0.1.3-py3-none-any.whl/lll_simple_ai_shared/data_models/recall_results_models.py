from pydantic import BaseModel, Field
from ..utils.extract import extract_events_string, default_extract_strings


class RecallResultsModels(BaseModel):
    recalled_episode: str = Field(
        ...,
        description="从历史记忆中提取的与当前情况最相关的具体经验或模式",
    )
    current_situation: str = Field(
        ...,
        description="结合历史上下文后对当前情境的深化理解",
    )
    confidence: float = Field(
        default=0.5,
        description="对当前理解的确信程度，1.0表示完全确定，0.0表示完全不确定",
    )


associative_recall_template = """
<|im_start|>system
将**当前情况**与**历史记忆**进行智能关联，找出有用的经验和模式，更好地理解现状。

【当前情境】
{{current_situation}}

【刚才的对话和事件】
{{recent_events}}

【相关的历史记忆】
{{episodic_memories}}

【你正在做的事】
{{active_goals}}

<|im_end|>
<|im_start|>assistant
"""


def associative_recall_task_format_inputs(inputs):
    return {
        "current_situation": inputs.get("current_situation", "未知"),
        # TODO: 增加时间
        "recent_events": extract_events_string(inputs.get("recent_events", [])),
        "episodic_memories": default_extract_strings(
            inputs.get("episodic_memories", []), "content"
        ),
        "active_goals": default_extract_strings(
            inputs.get("active_goals", []), "description"
        ),
    }
