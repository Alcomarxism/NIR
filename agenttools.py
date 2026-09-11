import maptools
from langchain_core.tools import tool

def create_move_tool(map, agent):
    @tool
    def move_to_cell(x: int, y: int) -> str:
        """
        Инструмент для перемещения разведчика на смежную клетку лабиринта.
        Принимает целевые координаты x и y.
        Возвращает результат попытки перемещения (feedback).
        """
        success, feedback = maptools.move_agent(map,agent, (x, y))
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
