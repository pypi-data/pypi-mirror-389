from pydantic import BaseModel, Field
from enum import Enum
from typing import Literal, List
from ..utils.extract import extract_events_string, default_extract_strings


class MemoryQueryType(Enum):
    NONE = "none"
    LONG_TERM_CACHED = "long_term_cached"
    LONG_TERM_FRESH = "long_term_fresh"


class MemoryQueryPlan(BaseModel):
    query_type: Literal["none", "long_term", "working_memory"] = Field(
        default="none",
        description="""
查询类型，根据当前消息判断：
- none: 不查询任何记忆
- long_term_cached: 需要长期记忆的相关信息
- long_term_fresh: 需要长期记忆的相关信息，要求最新信息或信息可能已变化
""",
    )

    query_triggers: List[str] = Field(
        default_factory=list,
        description="用于搜索记忆的关键词列表，应该是名词或核心概念",
    )

    time_range: List[int] = Field(
        default_factory=list, description="查询时间范围[起始天数, 结束天数]"
    )
    importance_score_filter: int = Field(
        default=0, description="重要性分数阈值(0-100)，只查询分数大于等于此值的记忆"
    )
    purpose: str = Field(..., description="说明查询记忆的目的")


class UnderstoodData(BaseModel):
    event_type: Literal["user_command", "sensor_alert", "object_detected", "other"] = (
        Field(
            default="other",
            description="事件类型: user_command(用户指令)、sensor_alert(传感器预警)、object_detected(识别到特定物体或人)、other(其他)",
        )
    )
    confidence: float = Field(
        default=0.5,
        description="对当前理解的确信程度，1.0表示完全确定，0.0表示完全不确定",
    )
    response_priority: Literal["low", "medium", "high", "critical"] = Field(
        ...,
        description="根据安全性、紧急性、与主人的关联度判断响应紧急程度: low(低)、medium(中)、high(高)、critical(极高)",
    )
    expected_response: Literal["verbal", "action", "both", "none"] = Field(
        ...,
        description="下一步最应该做的事情是什么: verbal(只需要语言回应)、action(只需要执行动作)、both(需要语言回应并执行动作)、none(无需响应)",
    )
    main_content: str = Field(..., description="用一句话清晰概括当前信息的核心内容")
    current_situation: str = Field(
        ...,
        description="综合当前信息与历史上下文，生成对整体情境的连贯理解。形成完整的情境认知",
    )
    event_entity: str = Field(..., description="触发事件的主体")
    key_entities: List[str] = Field(
        default_factory=list, description="从信息中提取的重要名词或实体"
    )
    importance_score: int = Field(
        default=0, description="当前事件的重要程度分数(0-100)"
    )
    memory_query_plan: MemoryQueryPlan = Field(
        ..., description="制定从长期记忆中查询相关信息的计划"
    )


understand_template = """
<|im_start|>system
下面是当前的信息，请根据你的角色将杂乱的多模态信息整理成一条结构化的“工作记忆”：

你可能会收到来自以下来源的原始信息：
- [ASR]： 自动语音识别文本，可能包含错误或歧义。
- [TEXT]： 文本信息，但可能有错别字。

【需要你理解的信息】
[{{understand_event_type}}]{{understand_event}}

【刚才的对话和事件】
{{recent_events}}

【你正在做的事】
{{active_goals}}

请简单总结需要你理解的多模态信息。
<|im_end|>
<|im_start|>assistant
"""


def understand_task_format_inputs(inputs):
    return {
        "understand_event_type": inputs.get("understand_event", {}).get("type", "未知"),
        "understand_event": inputs.get("understand_event", {}).get("text", "无"),
        "recent_events": extract_events_string(inputs.get("recent_events", [])),
        "active_goals": default_extract_strings(
            inputs.get("active_goals", []), "description"
        ),
    }
