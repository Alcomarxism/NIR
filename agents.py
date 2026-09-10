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


LLM_MODEL="gpt-oss:120b-cloud"


def create_move_tool(env, agent):
    @tool
    def move_to_cell(x: int, y: int) -> str:
        """
        Инструмент для перемещения разведчика на смежную клетку лабиринта.
        Принимает целевые координаты x и y.
        Возвращает результат попытки перемещения (feedback).
        """
        success, feedback = env.step(agent, (x, y))
        return feedback
    
    return move_to_cell

def create_send_report_tool(agent,squad):
    @tool
    def send_report(report: str):
        """
        Инструмент для отправко отчета командиру
        """
        squad.reports[agent.name]=report
    return send_report

def create_kill_enemy_tool(simulation):
    @tool
    def kill_enemy(x: int, y: int) -> str:
        """
        Инструмент для устранения вражеского разведчика.
        Принимает целевые координаты x и y.
        Возвращает результат устранения (feedback).
        """
        enemy_pos=(x,y)
        for sq in simulation.squads:
            for ag in simulation.squads[sq].agents:
                if ag.pos==enemy_pos:
                    simulation.squads[sq].kill_agent(ag.name)
                    return "Вражеский агент устранен"
        return "Промах"
    
    return kill_enemy


class AgentComander():
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
        self.recoons=recoons
        self.chain = self.prompt | self.llm | self.parser

    async def make_desigion(self,env):
        frontiers = maptools.get_frontier(self.squad.map)
        paths={}
        for r in self.recoons:
            for f in frontiers:
                paths[r.name+'->'+str(f)]=maptools.find_path_bfs(r.pos,f,self.squad.map)
        decision: AgentComander.AgentDecision = await self.chain.ainvoke({
            "team": self.squad.squad_name,
            "recoons_info": json.dumps([{"name": r.name, "pos": r.pos} for r in self.recoons]), 
            "agents_feedback": json.dumps(self.squad.reports),
            "frontiers": json.dumps(frontiers),
            "paths_recoons_frontiers":json.dumps(paths),
            "last_orders": json.dumps(self.squad.orders),
        })
        print(f"Мысли: {decision.thought}")
        orders_map = {single.name: single.order for single in decision.orders}
        for r in self.recoons:
            if r.name in orders_map:
                self.squad.orders[r.name] = orders_map[r.name]

class AgentRecoon():
    class AgentDecision(BaseModel):
        thought: str = Field(description="Мысли")
        report: str = Field(description="Отчет")

    def __init__(self,pos,name,squad,env):
        self.squad=squad
        self.env=env
        self.move_tool = create_move_tool(env, self)
        self.send_report = create_send_report_tool(self,squad)
        self.kill_enemy = create_kill_enemy_tool(self.squad.simulation)
        self.llm = ChatOllama(
            model=LLM_MODEL,
            temperature=0.1,
        ).bind_tools([self.move_tool,self.send_report,self.kill_enemy])
        self.prompt=PromptTemplate(
            template="""Ты — разведчик в лабиринте.
            Ты можешь перемещаться только на соседние клетки (изменять x или y на ±1), используя доступный инструмент move_to_cell.

           Правила работы:
            1. Выполняй приказ: {last_order}.
            2. Для шага используй `move_to_cell`.
            3. Обязательно вызывай `send_report`, если:
            - Ты достиг целевой точки из приказа.
            - Путь заблокирован / приказ невыполним.
            4. При обнаружении вражеских агентов (тех, чья команда отличается от названия твоей) используй `kill_enemy` для из устранения

            Твоя команда: {team}
            Текущая позиция: {pos}
            Твое поле зрения: {visibility}
            Отданный тебе приказ: {last_order}
            Результат прошлого действия: {last_feedback}
            """,
            input_variables=["team","pos","visibility", "last_order", "last_feedback"],
        )
        self.last_feedback = "Старт"
        self.pos=pos
        self.name=name

    async def make_desigion(self):
        visibility = self.env.get_fog_view(self.pos)
        for v in visibility:
            ceil=ast.literal_eval(v) if isinstance(v, str) else v
            self.squad.map[ceil[0]][ceil[1]]=visibility[v]
        
        prompt_text = self.prompt.format(
            team=self.squad.squad_name,
            pos=str(self.pos),
            visibility=json.dumps(visibility),
            last_order=str(self.squad.orders.get(self.name, "Нет приказа")),
            last_feedback=self.last_feedback
        )
        messages = [HumanMessage(content=prompt_text)]
        response = await self.llm.ainvoke(messages)
        messages.append(response)
        if response.tool_calls:
            for tool_call in response.tool_calls:
                name = tool_call["name"]
                args = tool_call["args"]
                if name == "move_to_cell":
                    self.last_feedback = self.move_tool.invoke(args)
                elif name == "send_report": 
                    self.send_report.invoke(args)
                elif name == "kill_enemy": 
                    self.kill_enemy.invoke(args)
        else:
            self.squad.print_to_logs(f"Агент {self.name} не вызывал инструментов.")
 
