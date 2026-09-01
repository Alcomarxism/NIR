from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from typing import Literal
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
import json
from typing import List

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


class AgentComander(BaseAgent):
    class Order(BaseModel):
        name: str = Field(description="Имя агента, которому отдается приказ")
        order: str = Field(description="Текст приказа (целевая точка или маршрут)")

    class AgentDecision(BaseModel):
        thought: str = Field(description="Мысли")
        thought: str = Field(description="Общие мысли по координации всей группы и план")
        orders: List['AgentComander.Order'] = Field(
            description="Список приказов ДЛЯ КАЖДОГО разведчика из отряда"
        )
   
    def __init__(self,recoons):
        parser = PydanticOutputParser(pydantic_object=AgentComander.AgentDecision)
        prompt=PromptTemplate(
            template="""Ты — командир отряда разведчиков Твоя цель — изучить весь лабиринт.
            
            Ты отдваешь приказы каждомы разведчику в какую точку им двигаться
            Отдавай цразу цель к которой нужно двигаться, а не каждый шаг.
            Распределяй разведчиков по разным направлениям, чтобы они не сталкивались в узких коридорах и не шли в одну точку!
            
            Имена разведчиков: {names}
            Позиции разведчиков: {recoons_pos}
            Твоя память о карте: {memory}
            Отчеты от агентов: {agents_feedback}

            Требования к ответу:
            1. В 'thought' опиши общую стратегию распределения группы.
            2. В 'orders' сформируй массив приказов, содержащий РОВНО ПО ОДНОМУ ПРИКАЗУ ДЛЯ КАЖДОГО агента

            {format_instructions}
            """,
            input_variables=["names","recoons_pos","memory", "agents_feedback"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )
        self.recoons=recoons

        self.memory = {f"[{i},{j}]": '?' for i in range(20) for j in range(20)}
        self.agents_feedback = {r.name:"Нет отчета" for r in self.recoons}
        super().__init__(prompt,AgentComander.AgentDecision)

    async def make_desigion(self,env):
        decision: AgentRecoon.AgentDecision = await self.chain.ainvoke({
            "names": str({r.name for r in self.recoons}),
            "recoons_pos": str({r.pos for r in self.recoons}),
            "memory": json.dumps(self.memory),
            "agents_feedback": json.dumps(self.agents_feedback),
        })
        print(f"Мысли: {decision.thought}")
        orders_map = {single.name: single.order for single in decision.orders}
        for r in self.recoons:
            if r.name in orders_map:
                r.last_order = orders_map[r.name]
                print(f"-> Приказ для {r.name}: {r.last_order}")
            else:
                print(f"⚠️ Командир забыл отдать приказ для {r.name}!")   

class AgentRecoon(BaseAgent):
    class AgentDecision(BaseModel):
        thought: str = Field(description="Мысли")
        action: Literal["N", "S", "W", "E"] = Field(description="Действие: N, S, W или E.")
        report: str = Field(description="Отчет")

    def __init__(self,pos,name):
        parser = PydanticOutputParser(pydantic_object=AgentRecoon.AgentDecision)
        prompt=PromptTemplate(
            template="""Ты — разведчик в лабиринте.
            
            Ты получаешь приказы от командира и выполняешь их.
            После выполенеие приказа ты формируешь отчет о его выполенеии.
            При возникновении трудностей ты также формируешь отчет.
            Без необходимости не создавай отчет. Если отчета нет, заполняй его как "Нет отчета".

            Текущая позиция: {pos}
            Твое поле зрения: {visibility}
            Отданный тебе приказ: {last_order}
            Результат прошлого действия: {last_feedback}

            Заполни структуру ответа:
            - thought: краткие мысли и планирование
            - action: выбор направления (N, S, W, E)
            - report: отчет о выполнении приказа

            {format_instructions}
            """,
            input_variables=["pos","visibility", "last_order", "last_feedback"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )
        self.last_feedback = "Старт"
        self.pos=pos
        self.name=name
        self.last_order='Нет приказа'
        super().__init__(prompt,AgentRecoon.AgentDecision)

    async def make_desigion(self,env,commander):
        visibility = env.get_fog_view(self.pos,1)
        for v in visibility:
            commander.memory[v]=visibility[v]

        decision: AgentRecoon.AgentDecision = await self.chain.ainvoke({
            "pos": str(self.pos),
            "visibility": json.dumps(visibility),
            "last_order": str(self.last_order),
            "last_feedback": self.last_feedback,
        })
        print(f"Позиция: {self.pos}")
        print(f"Мысли: {decision.thought}")
        print(f"Действие: {decision.action}")
        print(f"Отчет: {decision.report}")
        success, feedback = env.step(self,decision.action)
        self.last_feedback = feedback 
        commander.agents_feedback[self.name]=decision.report
