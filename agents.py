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
            model="gpt-oss:120b-cloud",
            temperature=0.1,
            format="json",
        )
        self.chain = self.prompt | self.llm | self.parser

class AgentRecoon(BaseAgent):
    class AgentDecision(BaseModel):
        thought: str = Field(description="Анализ карты и планирование следующего шага.")
        action: Literal["N", "S", "W", "E"] = Field(description="Действие: N, S, W или E.")
        updated_map_memory: str = Field(description="Обновленная краткая память о карте и развилках.")

    def __init__(self,pos):
        parser = PydanticOutputParser(pydantic_object=AgentRecoon.AgentDecision)
        prompt=PromptTemplate(
            template="""Ты — разведчик в лабиринте Твоя цель — изучить весь лабиринт.
            
            Текущая позиция: {pos}
            Твоя память о карте: {memory}
            Результат прошлого действия: {last_feedback}

            Заполни структуру ответа:
            - thought: краткие мысли и планирование
            - action: выбор направления (N, S, W, E)
            - updated_map_memory: обновленная память о развилках

            {format_instructions}
            """,
            input_variables=["pos", "memory", "last_feedback"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )
        self.memory = {f"[{i},{j}]": '?' for i in range(20) for j in range(20)}
        self.last_feedback = "Старт"
        self.pos=pos
        super().__init__(prompt,AgentRecoon.AgentDecision)

    async def make_desigion(self,env):
        visibility = env.get_fog_view(self.pos,1)
        for v in visibility:
            self.memory[v]=visibility[v]

        decision: AgentRecoon.AgentDecision = await self.chain.ainvoke({
            "pos": str(self.pos),
            "visibility": json.dumps(visibility),
            "memory": json.dumps(self.memory),
            "last_feedback": self.last_feedback,
        })
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
    
