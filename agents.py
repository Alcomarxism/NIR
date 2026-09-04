from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from typing import Literal
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
import json
from typing import List, Literal, Tuple
import maptools
import ast

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
        orders: List['AgentComander.Order'] = Field(
            description="Список приказов ДЛЯ КАЖДОГО разведчика из отряда"
        )
    
    def __init__(self,recoons,squad):
        self.squad=squad
        parser = PydanticOutputParser(pydantic_object=AgentComander.AgentDecision)
        prompt=PromptTemplate(
            template="""Ты — командир отряда разведчиков Твоя цель — изучить весь лабиринт.
            
            Ты отдваешь приказы разведчикам в какую точку им двигаться и по какому машруту
            Пока агент не отчитался о том что выполнили приказ или приказ невополним не давай нового приказа
            Распределяй разведчиков по разным направлениям, чтобы они не сталкивались в узких коридорах и не шли в одну точку!

            Имена и позиции разведчиков: {recoons_info} 
            Отчеты от агентов: {agents_feedback}
            Точки на границе неизвестного (ФРОНТИР): {frontiers}
            Маршруты от агентов до форнтира {paths_recoons_frontiers}
            ОТданные агентам приказы: {last_orders}

            Требования к ответу:
            1. В 'thought' опиши общую стратегию распределения группы.
            2. В 'orders' сформируй массив приказов

            {format_instructions}
            """,
            input_variables=["recoons_info", "agents_feedback","frontiers","paths_recoons_frontiers","last_orders"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )
        self.recoons=recoons
        self.agents_feedback = {r.name:"Нет отчета" for r in self.recoons}
        self.last_orders={r.name:"Нет приказа" for r in self.recoons}
        super().__init__(prompt,AgentComander.AgentDecision)

    async def make_desigion(self,env):
        frontiers = maptools.get_frontier(self.squad.map)
        paths={}
        for r in self.recoons:
            for f in frontiers:
                paths[r.name+'->'+str(f)]=maptools.find_path_bfs(r.pos,f,self.squad.map)
        decision: AgentRecoon.AgentDecision = await self.chain.ainvoke({
            "recoons_info": json.dumps([{"name": r.name, "pos": r.pos} for r in self.recoons]), 
            "agents_feedback": json.dumps(self.agents_feedback),
            "frontiers": json.dumps(frontiers),
            "paths_recoons_frontiers":json.dumps(paths),
            "last_orders": json.dumps(self.last_orders),
        })
        print(f"Мысли: {decision.thought}")
        orders_map = {single.name: single.order for single in decision.orders}
        for r in self.recoons:
            if r.name in orders_map:
                r.last_order = orders_map[r.name]
                self.last_orders[r.name] = orders_map[r.name]
                print(f"-> Приказ для {r.name}: {r.last_order}")   

class AgentRecoon(BaseAgent):
    class AgentDecision(BaseModel):
        thought: str = Field(description="Мысли")
        action: Tuple[int, int] = Field(description="Клетка на которую осуществляется перемещение")
        report: str = Field(description="Отчет")

    def __init__(self,pos,name,squad):
        self.squad=squad
        parser = PydanticOutputParser(pydantic_object=AgentRecoon.AgentDecision)
        prompt=PromptTemplate(
            template="""Ты — разведчик в лабиринте.
            ты можешь перемещаться только на соседние клетки, то кть увеличить или уменьшить x или y на 1

            Ты получаешь приказы от командира и выполняешь их.
            После выполенеие приказа ты формируешь отчет о его выполенеии.
            При возникновении трудностей ты также формируешь отчет.
            Создавай отчет только при полном выполнении приказа или если выполнение приказа невозможно. Если отчета нет, заполняй его как "Нет отчета".

            Текущая позиция: {pos}
            Твое поле зрения: {visibility}
            Отданный тебе приказ: {last_order}
            Результат прошлого действия: {last_feedback}

            Заполни структуру ответа:
            - thought: краткие мысли и планирование
            - action: координаты  [x, y] клетки на которую осуществляется перемещение
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

    async def make_desigion(self,env):
        visibility = env.get_fog_view(self.pos)
        for v in visibility:
            ceil=ast.literal_eval(v) if isinstance(v, str) else v
            self.squad.map[ceil[0]][ceil[1]]=visibility[v]

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
        self.squad.commander.agents_feedback[self.name]=decision.report