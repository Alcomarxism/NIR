from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from typing import Literal
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
import json
from typing import List, Literal, Tuple
import maptools
import ast
import agenttools

LLM_MODEL="gpt-oss:120b-cloud"


class AgentComander():
    class Order(BaseModel):
        name: str = Field(description="Имя агента, которому отдается приказ")
        order: str = Field(description="Текст приказа (целевая точка или маршрут)")

    class AgentDecision(BaseModel):
        thought: str = Field(description="Мысли")
        orders: List['AgentComander.Order'] = Field(
            description="Список приказов ДЛЯ КАЖДОГО разведчика из отряда"
        )
    
    def __init__(self,squad):
        self.squad=squad
        self.parser = PydanticOutputParser(pydantic_object=AgentComander.AgentDecision)
        self.llm = ChatOllama(
            model="gpt-oss:120b-cloud",
            temperature=0.1,
            format="json",
        )
        self.prompt=PromptTemplate(
            template="""Ты — командир отряда разведчиков Твоя цель — изучить весь лабиринт.
            
            Ты отдваешь приказы разведчикам в какую точку им двигаться и по какому машруту
            Пока агент не отчитался о том что выполнили приказ или приказ невополним не давай нового приказа
            Распределяй разведчиков по разным направлениям, чтобы они не сталкивались в узких коридорах и не шли в одну точку!

            Твоя команда: {team}
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
            input_variables=["team","recoons_info", "agents_feedback","frontiers","paths_recoons_frontiers","last_orders"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        self.chain = self.prompt | self.llm | self.parser

    async def make_desigion(self):
        frontiers = maptools.get_frontier(self.squad.map)
        paths={}
        for r in self.squad.agents:
            for f in frontiers:
                paths[r.name+'->'+str(f)]=maptools.find_path_bfs(r.pos,f,self.squad.map)
        decision: AgentComander.AgentDecision = await self.chain.ainvoke({
            "team": self.squad.squad_name,
            "recoons_info": json.dumps([{"name": r.name, "pos": r.pos} for r in self.squad.agents]), 
            "agents_feedback": json.dumps(self.squad.reports),
            "frontiers": json.dumps(frontiers),
            "paths_recoons_frontiers":json.dumps(paths),
            "last_orders": json.dumps(self.squad.orders),
        })
        print(f"Мысли: {decision.thought}")
        orders_map = {single.name: single.order for single in decision.orders}
        for r in self.squad.agents:
            if r.name in orders_map:
                self.squad.orders[r.name] = orders_map[r.name]

class AgentRecoon():
    class AgentDecision(BaseModel):
        thought: str = Field(description="Мысли")
        report: str = Field(description="Отчет")

    def __init__(self,pos,name,squad,sim):
        self.squad=squad
        self.sim=sim
        self.move_tool = agenttools.create_move_tool(self,self.sim.map)
        self.send_report = agenttools.create_send_report_tool(self,squad)
        self.shoot_enemy = agenttools.create_shoot_enemy_tool(self,self.squad.sim)
        self.llm = ChatOllama(
            model=LLM_MODEL,
            temperature=0.1,
        ).bind_tools([self.move_tool,self.send_report,self.shoot_enemy])
        self.prompt=PromptTemplate(
            template="""Ты — разведчик в лабиринте.
            Ты можешь перемещаться только на соседние клетки (изменять x или y на ±1), используя доступный инструмент move_to_cell.

           Правила работы:
            1. Выполняй приказ: {last_order}.
            2. Для шага используй `move_to_cell`.
            3. Обязательно вызывай `send_report`, если:
            - Ты достиг целевой точки из приказа.
            - Путь заблокирован / приказ невыполним.
            4. При обнаружении вражеских агентов (тех, чья команда отличается от названия твоей) используй `shoot_enemy` для из устранения

            Твоя команда: {team}
            Текущая позиция: {pos}
            Твое поле зрения: {visibility}
            Вражеские агенты в поле зрения: {enemies}
            Отданный тебе приказ: {last_order}
            Результат прошлого действия: {last_feedback}
            """,
            input_variables=["team","pos","visibility", "last_order", "last_feedback","enemies"],
        )
        self.last_feedback = "Старт"
        self.pos=pos
        self.name=name

    async def make_desigion(self):
        visibility, enemies = maptools.get_fog_view(self.sim,self.squad,self)      
        prompt_text = self.prompt.format(
            team=self.squad.squad_name,
            pos=str(self.pos),
            visibility=json.dumps(visibility),
            enemies=json.dumps(enemies),
            last_order=str(self.squad.orders.get(self.name, "Нет приказа")),
            last_feedback=self.last_feedback
        )
        messages = [HumanMessage(content=prompt_text)]
        response = await self.llm.ainvoke(messages)
        messages.append(response)
        if response.tool_calls:
            for tool_call in response.tool_calls:
                if tool_call["name"] == "move_to_cell":
                   self.move_tool.invoke(tool_call["args"])
                elif tool_call["name"] == "send_report": 
                    self.send_report.invoke(tool_call["args"])
                elif tool_call["name"] == "shoot_enemy": 
                    self.shoot_enemy.invoke(tool_call["args"])
        maptools.get_fog_view(self.sim,self.squad,self) 