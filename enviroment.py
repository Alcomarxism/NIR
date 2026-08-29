import random

def generate_maze(size=20):
    grid = [[1 for _ in range(size)] for _ in range(size)]
    
    def walk(r, c):
        grid[r][c] = 0
        # Разрешенные направления: шаг на 2 клетки в стороны
        directions = [(0, 2), (0, -2), (2, 0), (-2, 0)]
        random.shuffle(directions)
        
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < size and 0 <= nc < size and grid[nr][nc] == 1:
                # Пробиваем стену между текущей и новой клеткой
                grid[r + dr // 2][c + dc // 2] = 0
                walk(nr, nc)

    # Начинаем генерацию со старта [0, 0]
    walk(0, 0)
    
    # Гарантируем свободу на старте и финише
    grid[0][0] = 0
    grid[size - 1][size - 1] = 2  # Target
    
    # Если финиш оказался в стене из-за четного размера, пробиваем соседей
    if grid[size - 1][size - 2] == 1 and grid[size - 2][size - 1] == 1:
        grid[size - 1][size - 2] = 0

    return grid


class Enviroment:
    def __init__(self, grid_size=20):
        self.grid_size = grid_size
        self.grid = generate_maze(grid_size)
        self.agent_pos = [0, 0]
        self.target_pos = [grid_size - 1, grid_size - 1]
        self.explored_cells = set()
   
    def get_fog_view(self, radius=1):
        r, c = self.agent_pos
        view = {}
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.grid_size and 0 <= nc < self.grid_size:
                    self.explored_cells.add((nr, nc))
                    cell_type = self.grid[nr][nc]
                    view[f"[{nr},{nc}]"] = "WALL" if cell_type == 1 else ("TARGET" if cell_type == 2 else "EMPTY")
        return view

    def step(self, action: str):
        r, c = self.agent_pos
        moves = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}
        dr, dc = moves.get(action, (0, 0))
        nr, nc = r + dr, c + dc
        
        if 0 <= nr < self.grid_size and 0 <= nc < self.grid_size and self.grid[nr][nc] != 1:
            self.agent_pos = [nr, nc]
            return True, "Успешный шаг."
        return False, "Незрелая попытка: там стена или край карты!"
    
    def get_field(self):
        return self.grid
    
    def get_agent_pos(self):
        return self.agent_pos

    