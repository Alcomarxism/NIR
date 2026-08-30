from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from typing import Literal
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
import json


class BaseAgent():
    def __init__(self,prompt,response_type):
        self.parser=PydanticOutputParser(pydantic_object=response_type)
        self.prompt=prompt
        self.llm = ChatOllama(
            model="qwen2.5:3b",
            temperature=1
        )
        self.structured_llm = self.llm.with_structured_output(response_type)
        self.chain = self.prompt | self.structured_llm


class Agent(BaseAgent):
    class AgentDecision(BaseModel):
        thought: str = Field(description="Анализ карты и планирование следующего шага.")
        action: Literal["N", "S", "W", "E"] = Field(description="Действие: N, S, W или E.")
        updated_map_memory: str = Field(description="Обновленная краткая память о карте и развилках.")

    def __init__(self,pos):
        prompt=PromptTemplate(
            template="""Ты — тактический разведчик в лабиринте 20x20. Твоя цель — найти второго агента TARGET.
            Ты видишь только соседние клетки (Fog of War).
            
            старайся двигаться к центру поля

            Текущая позиция: {pos}
            Что видишь прямо сейчас: {visibility}
            Твоя память о карте с прошлого хода: {memory}
            Результат прошлого действия: {last_feedback}

            Заполни структуру ответа:
            - thought: краткие мысли и планирование
            - action: выбор направления (N, S, W, E)
            - updated_map_memory: обновленная память о развилках
            """,
            input_variables=["pos", "visibility", "memory", "last_feedback"]
        )
        self.memory = "Старт в [0,0]. Карта пока не исследована."
        self.last_feedback = "Начало миссии."
        self.pos=pos
        super().__init__(prompt,Agent.AgentDecision)

    async def make_desigion(self,env):
        visibility = env.get_fog_view(self.pos,1)
        decision: Agent.AgentDecision = await self.chain.ainvoke({
            "pos": str(self.pos),
            "visibility": json.dumps(visibility),
            "memory": self.memory,
            "last_feedback": self.last_feedback,
        })
        self.memory = decision.updated_map_memory
        print(f"Позиция: {self.pos}")
        print(f"Мысли: {decision.thought}")
        print(f"Действие: {decision.action}")
        r, c = self.pos
        dr, dc = {"N": (-1, 0), "S": (1, 0), "W": (0, -1), "E": (0, 1)}.get(decision.action, (0, 0))
        newpos = (r + dr, c + dc)
        success, feedback = env.step(self.pos,newpos)
        if success:
            self.last_feedback = feedback 
            self.pos=newpos      
    
