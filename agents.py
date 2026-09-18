from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, AIMessage
from langchain_core.tools import tool
from typing import Literal
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
import json
from typing import List, Literal, Tuple
import maptools
import agenttools
import metrics

MAX_CONTEXT = 3

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
            template="""Ты - командир отряда. Твоя цель - найти и уничтожить отряд противника.
            В твоем распоряжении 2 класса: Assault (штурмовик) и Recon (Разведчик)
            Каждый агент может ходить ровно на одну клетку зат один ход.

            Используй разведчиков для исследования карты. В случае, если разведчик натыкается на противника, он отступает.
            Основными клетками для разведки являются границы разведанной карты (фронтир).
            Также важными областями разведки являются области с ранее найденным противником.
            Распределяй разведчиков по разным направлениям.

            Используй штурмовиков для устранения агентов противника.
            Старайся по возможности отправить несколько штурмовиков против одного противника для создания численного перевеса.

            Каждому агенту ты отдаешь приказы в какую точку двигаться и по какому маршруту.
            Для построения маршрута используй изученную карту.
            В приказе пиши полный путь до целевой точки. В путь пиши все точки, через которые должен пройти агент
            Пока агент не отчитался о том, что выполнили приказ или приказ невыполним, не давай нового приказа.

            Требования к ответу:
            1. В 'thought' опиши общую стратегию распределения группы.
            2. В 'orders' сформируй массив приказов

            {format_instructions}
            """,
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        self.chat_history = InMemoryChatMessageHistory()

    async def make_desigion(self):
        frontiers = maptools.get_frontier(self.squad.map)
        enemies = maptools.get_all_enemies(self.squad.map)
        map_dict={}
        for i in range(len(self.squad.map)):
            for j in range(len(self.squad.map)):
                map_dict[f"[{i},{j}]"]=self.squad.map[i][j]

        prompt_str = self.prompt.format()
        system_msg = SystemMessage(content=prompt_str)
        current_human_msg = HumanMessage(f"""Текущее состояние обстановки:
        - Изученная карта: {json.dumps(map_dict)}
        - Имена и позиции агентов: {json.dumps([{"name": r.name, "pos": r.pos, "class": r.agent_class} for r in self.squad.agents])}
        - Точки на границе неизвестного (фронтир): {json.dumps(frontiers)}
        - Найденные противники: {json.dumps(enemies)}
        - Отданные агентам приказы: {json.dumps(self.squad.orders)}
        - Отчеты от агентов: {json.dumps(self.squad.reports)}

        Оцени динамику изменений и отдай приказ на следующий ход.
        """)
        MAX_MESSAGES = MAX_CONTEXT * 2
        if len(self.chat_history.messages) > MAX_MESSAGES:
            self.chat_history.messages = self.chat_history.messages[-MAX_MESSAGES:]
        messages = [system_msg] + self.chat_history.messages + [current_human_msg]
        response = await self.llm.ainvoke(messages)
        info = response.response_metadata.get("info", response.response_metadata)
        self.squad.metrics_collector.record_tokens(info)
        self.chat_history.add_message(current_human_msg)
        self.chat_history.add_message(response)
        decision = await self.parser.ainvoke(response)
        print(f"Мысли: {decision.thought}")
        orders_map = {single.name: single.order for single in decision.orders}
        for r in self.squad.agents:
            if r.name in orders_map:
                self.squad.orders[r.name] = orders_map[r.name]

class AgentSolder():
    def __init__(self,model,pos,name,squad,sim,prompt,agent_class,recognise_radius,view_radius,shoot_max_radius):
        self.recognise_radius=recognise_radius
        self.view_radius=view_radius
        self.shoot_max_radius=shoot_max_radius
        self.agent_class=agent_class
        self.squad=squad
        self.sim=sim
        self.move_tool = agenttools.create_move_tool(self,self.squad,self.sim.map)
        self.send_report = agenttools.create_send_report_tool(self,self.squad)
        self.shoot_enemy = agenttools.create_shoot_enemy_tool(self,self.squad,self.squad.sim,self.shoot_max_radius)
        self.llm = ChatOllama(
            model=model,
            temperature=0.1,
        ).bind_tools([self.move_tool,self.send_report,self.shoot_enemy])
        self.prompt=prompt
        self.last_feedback = "Старт"
        self.pos=pos
        self.name=name
        self.chat_history = InMemoryChatMessageHistory()
        
    async def make_desigion(self):
        maptools.update_map(self.sim,self.squad,self,self.recognise_radius)
        prompt_str = self.prompt.format()
        system_msg = SystemMessage(content=prompt_str)

        current_human_msg = HumanMessage(f"""Текущее состояние на ходу:
        - Текущая позиция: {self.pos}
        - Поле зрения: {json.dumps(maptools.get_view(self.squad.map, self.pos, self.view_radius))}
        - Враги в поле зрения: {json.dumps(maptools.get_enemies_in_radius(self.squad.map, self.pos, self.view_radius))}
        - Уровень опасности клеток: {json.dumps(maptools.find_dangerous_cells(self.squad.map, self.pos, self.view_radius))}
        - Текущий приказ от командира: {self.squad.orders.get(self.name, "Нет приказа")}
        - Результат прошлого действия: {self.last_feedback}

        Оцени обстановку и выполни подходящее действие.""")
        MAX_MESSAGES = MAX_CONTEXT * 3
        if len(self.chat_history.messages) > MAX_MESSAGES:
            self.chat_history.messages = self.chat_history.messages[-MAX_MESSAGES:]

        messages = [system_msg] + self.chat_history.messages + [current_human_msg]
        response = await self.llm.ainvoke(messages)
        info = response.response_metadata.get("info", response.response_metadata)
        self.squad.metrics_collector.record_tokens(info)
        self.chat_history.add_message(current_human_msg)
        self.chat_history.add_message(response)
        if response.tool_calls:
            for tool_call in response.tool_calls:
                if tool_call["name"] == "move_to_cell":
                   tool_result = self.move_tool.invoke(tool_call["args"])
                elif tool_call["name"] == "send_report": 
                    tool_result = self.send_report.invoke(tool_call["args"])
                elif tool_call["name"] == "shoot_enemy": 
                    tool_result = self.shoot_enemy.invoke(tool_call["args"])
                self.chat_history.add_message(ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"]))
        maptools.update_map(self.sim,self.squad,self,self.recognise_radius)

class AgentRecon(AgentSolder):
    def __init__(self,model,pos,name,squad,sim):
        prompt = PromptTemplate(
            template="""
            Ты - разведчик в лабиринте.
            Ты можешь перемещаться только на соседние клетки (изменять x или y на ±1), используя доступный инструмент `move_to_cell`.

            Твоя задача - выполнять приказы.
            После выполнения приказа ты отправляешь отчет используя `send_report`
            В случае если по каким-либо причинам приказ не может быть выполнен ты также отправляешь отчет используя `send_report`

            Если в ходе разведки ты натыкаешься на вражеского агента (ENEMY), твоя задача - отступить.
            При отступлении перемещайся на клетки с меньшим уровнем опасности. 
            В случае, если отступление невозможно, используй `shoot_enemy` для выстрела по вражескому агенту.
            Твой максимальный радиус стрельбы - одна клетка.
            После отступления в безопасную зону отправь отчет командиру. Пока ты находишься в опасности не отправляй отчет.

            """,
        )
        super().__init__(model,pos,name,squad,sim,prompt,"Recon",3,1,1)

class AgentAssault(AgentSolder):
    def __init__(self,model,pos,name,squad,sim):
        prompt = PromptTemplate(
            template="""
            Ты - штурмовик в лабиринте.
            Ты можешь перемещаться только на соседние клетки (изменять x или y на ±1), используя доступный инструмент `move_to_cell`.

            Твоя задача - выполнять приказы.
            После выполенеия приказа ты отправляешь отчет используя `send_report`
            В случае если по каким-либо причинам приказ не может быть выполнен ты также отправляешь отчет используя `send_report`

            Если ты натыкаешся на вражеского агента (ENEMY), твоя задача - устранить его, используя `shoot_enemy`.
            Твой максимальный радиус стрельбы - три клетки по прямой.
            После устранения ты должен отправить отчет.
            """,
        )
        super().__init__(model,pos,name,squad,sim,prompt,"Assault",1,1,3)
