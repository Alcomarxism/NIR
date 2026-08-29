from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from typing import Literal
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
import settings
import json

class Agent():
    class AgentDecision(BaseModel):
        thought: str = Field(description="Анализ карты и планирование следующего шага.")
        action: Literal["UP", "DOWN", "LEFT", "RIGHT"] = Field(description="Действие: UP, DOWN, LEFT или RIGHT.")
        updated_map_memory: str = Field(description="Обновленная краткая память о карте и развилках.")

    def __init__(self):
        self.parser=PydanticOutputParser(pydantic_object=Agent.AgentDecision)
        self.prompt=PromptTemplate(
            template="""Ты — тактический разведчик в лабиринте 20x20. Твоя цель — дойти до TARGET [{target_pos}].
            Ты видишь только соседние клетки (Fog of War).

            Текущая позиция: {pos}
            Что видишь прямо сейчас: {visibility}
            Твоя память о карте с прошлого хода: {memory}
            Результат прошлого действия: {last_feedback}

            Заполни структуру ответа:
            - thought: краткие мысли и планирование
            - action: выбор направления (UP, DOWN, LEFT, RIGHT)
            - updated_map_memory: обновленная память о развилках
            """,
            input_variables=["pos", "visibility", "memory", "last_feedback", "target_pos"]
        )
        self.llm = ChatOllama(
            model=settings.model,
            temperature=0.3
        )
        self.structured_llm = self.llm.with_structured_output(self.AgentDecision)
        self.chain = self.prompt | self.structured_llm
        self.memory = "Старт в [0,0]. Карта пока не исследована."
        self.last_feedback = "Начало миссии."

    async def make_desigion(self,agent_pos,visibility,target_str):
        decision: Agent.AgentDecision = await self.chain.ainvoke({
            "pos": str(agent_pos),
            "visibility": json.dumps(visibility),
            "memory": self.memory,
            "last_feedback": self.last_feedback,
            "target_pos": target_str
        })
        self.memory = decision.updated_map_memory
        print(f"Позиция: {agent_pos}")
        print(f"Мысли: {decision.thought}")
        print(f"Действие: {decision.action}")
        return decision.action
    
    def get_feedback(self,feedback):
        self.last_feedback = feedback
