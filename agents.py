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


class AgentComander():
    class Order(BaseModel):
        name: str = Field(description="Имя агента, которому отдается приказ")
        order: str = Field(description="Текст приказа (целевая точка или маршрут)")

    class AgentDecision(BaseModel):
        thought: str = Field(description="Мысли")
        orders: List['AgentComander.Order'] = Field(
            description="Список приказов ДЛЯ КАЖДОГО разведчика из отряда"
        )
    
    def __init__(self,model,squad):
        self.squad=squad
        self.parser = PydanticOutputParser(pydantic_object=AgentComander.AgentDecision)
        self.llm = ChatOllama(
            model=model,
            temperature=0.1,
            format="json",
        )
        self.prompt=PromptTemplate(
            template="""Ты — командир отряда. Твоя цель — найти и уничтожить отряд противника.
            В твоем распоряжении 2 класса: Assault (штурмовик) и Recoon (Разведчик)

            Используй разведчиков для исследования карты. В случае если разведчик натыкается на протвника он отступает.
            Распределяй разведчиков по разным направлениям, чтобы они не сталкивались в узких коридорах и не шли в одну точку!

            Используй штурмовиков для устранения агентов противника.
            Старайся по возможности отправить несколько штурмовиков против одного противника для создания чичленного перевеса.

            Каждому агенту ты отдаешь приказы в какую точку двигаться и по какому машруту.
            В приказе пиши полный путь до целевой точки.
            Пока агент не отчитался о том что выполнили приказ или приказ невополним не давай нового приказа.

            Твоя команда: {team}
            Имена и позиции агентов: {agents_info} 
            Отчеты от агентов: {agents_feedback}
            Точки на границе неизвестного (ФРОНТИР): {frontiers}
            Маршруты от агентов до форнтира {paths_recoons_frontiers}
            Найденные противники {enemies}
            Маршруты от агентов до противников {paths_recoons_enemies}
            Отданные агентам приказы: {last_orders}

            Требования к ответу:
            1. В 'thought' опиши общую стратегию распределения группы.
            2. В 'orders' сформируй массив приказов

            {format_instructions}
            """,
            input_variables=["team","agents_info", "agents_feedback","frontiers","paths_recoons_frontiers","enemies","paths_recoons_enemies","last_orders"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        self.chain = self.prompt | self.llm | self.parser

    async def make_desigion(self):
        frontiers = maptools.get_frontier(self.squad.map)
        enemies = maptools.get_all_enemies(self.squad.map)
        paths_to_frontiers={}
        for r in self.squad.agents:
            for f in frontiers:
                paths_to_frontiers[r.name+'->'+str(f)]=maptools.find_path_bfs(r.pos,f,self.squad.map)
        paths_to_enemies={}
        for r in self.squad.agents:
            for e in enemies:
                paths_to_enemies[r.name+'->'+str(e)]=maptools.find_path_bfs(r.pos,e,self.squad.map)
        decision: AgentComander.AgentDecision = await self.chain.ainvoke({
            "team": self.squad.squad_name,
            "agents_info": json.dumps([{"name": r.name, "pos": r.pos,"class":r.agent_class} for r in self.squad.agents]), 
            "agents_feedback": json.dumps(self.squad.reports),
            "frontiers": json.dumps(frontiers),
            "paths_recoons_frontiers":json.dumps(paths_to_frontiers),
            "enemies":json.dumps(enemies),
            "paths_recoons_enemies":json.dumps(paths_to_enemies),
            "last_orders": json.dumps(self.squad.orders),
        })
        print(f"Мысли: {decision.thought}")
        orders_map = {single.name: single.order for single in decision.orders}
        for r in self.squad.agents:
            if r.name in orders_map:
                self.squad.orders[r.name] = orders_map[r.name]

class AgentSolder():
    def __init__(self,model,pos,name,squad,sim,prompt,agent_class):
        self.agent_class=agent_class
        self.squad=squad
        self.sim=sim
        self.move_tool = agenttools.create_move_tool(self,self.sim.map)
        self.send_report = agenttools.create_send_report_tool(self,squad)
        self.shoot_enemy = agenttools.create_shoot_enemy_tool(self,self.squad.sim)
        self.llm = ChatOllama(
            model=model,
            temperature=0.1,
        ).bind_tools([self.move_tool,self.send_report,self.shoot_enemy])
        self.prompt=prompt
        self.last_feedback = "Старт"
        self.pos=pos
        self.name=name

    async def make_desigion(self):
        maptools.update_map(self.sim,self.squad,self)
        prompt_text = self.prompt.format(
            team=self.squad.squad_name,
            pos=str(self.pos),
            visibility=json.dumps(maptools.get_view(self.squad.map,self.pos,3)),
            enemies=json.dumps(maptools.get_enemies_in_radius(self.squad.map,self.pos,3)),
            dangerous_cells=json.dumps(maptools.find_dangerous_cells(self.squad.map,self.pos,3)),
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
        maptools.update_map(self.sim,self.squad,self) 

class AgentRecoon(AgentSolder):
    def __init__(self,model,pos,name,squad,sim):
        prompt = PromptTemplate(
            template="""
            Ты — разведчик в лабиринте.
            Ты можешь перемещаться только на соседние клетки (изменять x или y на ±1), используя доступный инструмент `move_to_cell`.

            Твоя задача - выполнять приказы.
            Текущий  приказ: {last_order}.
            После выполенеия приказа ты отправляешь отчет используя `send_report`
            В случае если по какаким-либо причинам приказ не может быть выполнен ты также отправляешь отчет используя `send_report`

            Если в ходе разредки ты натыкаешся на вражеского агента (ENEMY), твоя задача - отступить.
            При отступлении перемещайся на клетки с меньшим уровнем опасности. 
            В случае, если отступление невозможно, используй `shoot_enemy` для выстрела по вражескому агенту. Но свступай в бой только в крайнем случае.
            После отступления в безопасную зону отправь отчет командиру. Пока ты находишься в опасности не отправляй отчет.

            Твоя команда: {team}
            Текущая позиция: {pos}
            Твое поле зрения: {visibility}
            Вражеские агенты в поле зрения: {enemies}
            Отданный тебе приказ: {last_order}
            Результат прошлого действия: {last_feedback}
            Уровень опасности клеток: {dangerous_cells}
            """,
            input_variables=["team","pos","visibility", "last_order", "last_feedback","enemies","dangerous_cells"],
        )
        super().__init__(model,pos,name,squad,sim,prompt,"Recoon")

class AgentAssault(AgentSolder):
    def __init__(self,model,pos,name,squad,sim):
        prompt = PromptTemplate(
            template="""
            Ты — штурмовик в лабиринте.
            Ты можешь перемещаться только на соседние клетки (изменять x или y на ±1), используя доступный инструмент `move_to_cell`.

            Твоя задача - выполнять приказы.
            Текущий  приказ: {last_order}.
            После выполенеия приказа ты отправляешь отчет используя `send_report`
            В случае если по какаким-либо причинам приказ не может быть выполнен ты также отправляешь отчет используя `send_report`

            Если в ходе разредки ты натыкаешся на вражеского агента (ENEMY), твоя задача - устранить его, используя `shoot_enemy`.
            После устранения ты должен отправить отчет.

            Твоя команда: {team}
            Текущая позиция: {pos}
            Твое поле зрения: {visibility}
            Вражеские агенты в поле зрения: {enemies}
            Отданный тебе приказ: {last_order}
            Результат прошлого действия: {last_feedback}
            Уровень опасности клеток: {dangerous_cells}
            """,
            input_variables=["team","pos","visibility", "last_order", "last_feedback","enemies","dangerous_cells"],
        )
        super().__init__(model,pos,name,squad,sim,prompt,"Assault")
