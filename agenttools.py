import maptools
from langchain_core.tools import tool

def create_move_tool(agent,map):
    @tool
    def move_to_cell(x: int, y: int) -> str:
        """
        Инструмент для перемещения разведчика на смежную клетку лабиринта.
        Принимает целевые координаты x и y.
        Возвращает результат попытки перемещения (feedback).
        """
        if 0 <= x < len(map) and 0 <= y < len(map) and map[x][y] == 0:
            agent.pos=(x,y)
            agent.last_feedback = "Успешный шаг."
        else:
            agent.last_feedback = "Ошибка, шаг невозможен"
    
    return move_to_cell

def create_send_report_tool(agent,squad):
    @tool
    def send_report(report: str):
        """
        Инструмент для отправко отчета командиру
        """
        squad.reports[agent.name]=report
    return send_report

def create_shoot_enemy_tool(agent,simulation):
    @tool
    def shoot_enemy(x: int, y: int) -> str:
        """
        Инструмент для устранения вражеского разведчика.
        Принимает целевые координаты x и y.
        Возвращает результат устранения (feedback).
        """
        enemy_pos=(x,y)
        fb = "Промах"
        for sq in simulation.squads:
            for ag in simulation.squads[sq].agents:
                if ag.pos==enemy_pos:
                    simulation.squads[sq].kill_agent(ag.name)
                    fb = "Вражеский агент устранен"
        agent.last_feedback = fb 
        
    return shoot_enemy
