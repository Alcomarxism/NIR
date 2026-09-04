# 0 - пусто, 1 - стена
def generate_field():
    field=[
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1],
        [1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1],
        [1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1],
        [1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 1],
        [1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1],
        [1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1],
        [1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 0, 1],
        [1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1],
        [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    ]
    return field



class Enviroment:
    def __init__(self, grid_size=20):
        self.grid_size = grid_size
        self.grid = generate_field()
        self.explored_cells = set()
   
    def get_fog_view(self, agent_pos, radius=3):
        r, c = agent_pos
        view = {}
        def has_line_of_sight(r0, c0, r1, c1):
            dr = abs(r1 - r0)
            dc = abs(c1 - c0)
            sr = 1 if r0 < r1 else -1
            sc = 1 if c0 < c1 else -1
            err = dr - dc
            curr_r, curr_c = r0, c0
            while True:
                if curr_r == r1 and curr_c == c1:
                    return True
                if (curr_r, curr_c) != (r0, c0) and self.grid[curr_r][curr_c] == 1:
                    return False
                e2 = 2 * err
                if e2 > -dc:
                    err -= dc
                    curr_r += sr
                if e2 < dr:
                    err += dr
                    curr_c += sc
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                if dr * dr + dc * dc > radius * radius:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.grid_size and 0 <= nc < self.grid_size and not (nr == r and nc == c):
                    if has_line_of_sight(r, c, nr, nc):
                        self.explored_cells.add((nr, nc))
                        cell_type = self.grid[nr][nc]
                        view[f"[{nr},{nc}]"] = "WALL" if cell_type == 1 else ("EMPTY" if cell_type == 0 else cell_type)
        return view

    def step(self,agent, action):
        r,c=agent.pos
        newpos = action
        if 0 <= newpos[0] < self.grid_size and 0 <= newpos[1] < self.grid_size and self.grid[newpos[0]][newpos[1]] == 0:
            self.grid[r][c] = 0
            self.grid[newpos[0]][newpos[1]] = agent.squad.squad_name
            agent.pos=newpos
            return True, "Успешный шаг."
        else:
            self.grid[r][c] =  agent.squad.squad_name
            return False, "Ошибка, шаг невозможен"
    
    def get_field(self):
        return self.grid
    

    