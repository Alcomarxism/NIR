import json
from typing import Literal
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

class GridWorld:
    def __init__(self):
        # 0: пусто, 1: стена, 2: цель
        self.grid = [
            [0, 0, 1, 0, 0],
            [0, 1, 1, 0, 0],
            [0, 0, 0, 0, 1],
            [1, 1, 0, 1, 1],
            [0, 0, 0, 0, 2] # Цель в [4, 4]
        ]
        self.agent_pos = [0, 0] # Старт в [0, 0]
        self.target_pos = [4, 4]
        
    def get_fog_view(self, radius=1):
        """Возвращает только то, что агент видит вокруг себя"""
        r, c = self.agent_pos
        view = {}
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < 5 and 0 <= nc < 5:
                    cell_type = self.grid[nr][nc]
                    view[f"[{nr},{nc}]"] = "WALL" if cell_type == 1 else ("TARGET" if cell_type == 2 else "EMPTY")
        return view

    def step(self, action: str):
        r, c = self.agent_pos
        moves = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}
        dr, dc = moves.get(action, (0, 0))
        nr, nc = r + dr, c + dc
        
        # Проверка границ и стен
        if 0 <= nr < 5 and 0 <= nc < 5 and self.grid[nr][nc] != 1:
            self.agent_pos = [nr, nc]
            return True, "Успешный шаг."
        return False, "Незрелая попытка: там стена или край карты!"

# ==========================================
# 2. СХЕМА ВЫХОДА И ПАРСЕР DLY OLLAMA
# ==========================================
class AgentDecision(BaseModel):
    thought: str = Field(description="Анализ карты и планирование следующего шага.")
    action: Literal["UP", "DOWN", "LEFT", "RIGHT"] = Field(description="Действие: UP, DOWN, LEFT или RIGHT.")
    updated_map_memory: str = Field(description="Обновленная память о карте.")

# Создаем парсер, который автоматически сгенерирует инструкции для Ollama
parser = PydanticOutputParser(pydantic_object=AgentDecision)

# ==========================================
# 3. АГЕНТ НА CHATOLLAMA
# ==========================================
llm = ChatOllama(
    model="gpt-oss:120b-cloud",
    temperature=0
)

# Для Ollama лучше использовать PromptTemplate с format_instructions
prompt = PromptTemplate(
    template="""Ты — тактический разведчик в сетке 5x5. Твоя цель — дойти до TARGET [4,4].
Ты видишь только соседние клетки (Fog of War).

Текущая позиция: {pos}
Что видишь прямо сейчас: {visibility}
Твоя память о карте с прошлого хода: {memory}
Результат прошлого действия: {last_feedback}

{format_instructions}
""",
    input_variables=["pos", "visibility", "memory", "last_feedback"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)

# Собираем цепочку: Промпт -> Ollama -> Pydantic Парсер
chain = prompt | llm | parser

# ==========================================
# 4. ЦИКЛ СИМУЛЯЦИИ
# ==========================================
env = GridWorld()
memory = "Карта пока пуста. Известно только, что старт в [0,0]."
last_feedback = "Начало миссии."

print("=== СТАРТ СИМУЛЯЦИИ ===")

for step_num in range(1, 15): # Ограничение на 15 ходов
    # 1. Считываем туман войны
    visibility = env.get_fog_view(radius=1)
    
    # 2. Вызов LangChain
    decision: AgentDecision = chain.invoke({
        "pos": str(env.agent_pos),
        "visibility": json.dumps(visibility),
        "memory": memory,
        "last_feedback": last_feedback
    })
    
    # 3. Обновляем память для следующего шага
    memory = decision.updated_map_memory
    
    print(f"\n--- Шаг {step_num} ---")
    print(f"Позиция: {env.agent_pos}")
    print(f"Мысли: {decision.thought}")
    print(f"Действие: {decision.action}")
    
    # 4. Шаг в среде
    success, last_feedback = env.step(decision.action)
    
    # Проверка победы
    if env.agent_pos == env.target_pos:
        print(f"\n🎯 УСПЕХ! Цель достигнута за {step_num} ходов!")
        break