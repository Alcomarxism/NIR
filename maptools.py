from collections import deque


def has_line_of_sight(grid,r0, c0, r1, c1):
    dr = abs(r1 - r0)
    dc = abs(c1 - c0)
    sr = 1 if r0 < r1 else -1
    sc = 1 if c0 < c1 else -1
    err = dr - dc
    curr_r, curr_c = r0, c0
    while True:
        if curr_r == r1 and curr_c == c1:
            return True
        if (curr_r, curr_c) != (r0, c0) and grid[curr_r][curr_c] == 1:
            return False
        e2 = 2 * err
        if e2 > -dc:
            err -= dc
            curr_r += sr
        if e2 < dr:
            err += dr
            curr_c += sc        

def get_frontier(mp):
        frontier = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for i in range(len(mp)):
            for j in range(len(mp)):
                if mp[i][j] == 'EMPTY': 
                    has_unknown_neighbor = False
                    for di, dj in directions:
                        ni, nj = i + di, j + dj
                        if mp[ni][nj]== '?':
                            has_unknown_neighbor = True
                            break
                    
                    if has_unknown_neighbor:
                        frontier.append((i,j))
        return frontier

def get_all_enemies(mp):
    enemies = []
    for i in range(len(mp)):
        for j in range(len(mp)):
            if mp[i][j] == 'ENEMY': 
                enemies.append((i,j))
    return enemies    

def get_enemies_in_radius(mp,pos,radius):
    enemies = []
    r, c = pos
    for dr in range(-radius, radius + 1):
        for dc in range(-radius, radius + 1):
            nr, nc = r + dr, c + dc
            if 0 <= nr < len(mp) and 0 <= nc < len(mp):
                if mp[nr][nc] == 'ENEMY': 
                    enemies.append((nr,nc))
    return enemies

def update_map(sim,squad, agent, radius):
        r, c = agent.pos
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                if dr * dr + dc * dc > radius * radius:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < len(sim.map) and 0 <= nc < len(sim.map):
                    if has_line_of_sight(sim.map,r, c, nr, nc):
                        squad.map[nr][nc] = "WALL" if sim.map[nr][nc] == 1 else "EMPTY"
                        for sq in sim.squads:
                            for ag in sim.squads[sq].agents:
                                if ag.pos[0]==nr and ag.pos[1]==nc:
                                    if sq==squad.squad_name:
                                        squad.map[ag.pos[0]][ag.pos[1]]="ALLY"
                                    else:
                                        squad.map[ag.pos[0]][ag.pos[1]]="ENEMY"



def get_view(mp, pos, radius):
    r, c = pos
    view = {}
    for dr in range(-radius, radius + 1):
        for dc in range(-radius, radius + 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < len(mp) and 0 <= nc < len(mp):
                    view[f"[{nr},{nc}]"] = mp[nr][nc]
    return view

def find_dangerous_cells(mp,pos,radius):
    r, c = pos
    enemy_positions = get_enemies_in_radius(mp,pos,radius)
    dangerous = {}
    for dr in range(-radius, radius + 1):
        for dc in range(-radius, radius + 1):
            nr, nc = r + dr, c + dc
            if 0 <= nr < len(mp) and 0 <= nc < len(mp):
                cell_type = mp[nr][nc]
                if cell_type == "WALL" or cell_type=="?":
                    continue
                dg = 0
                for er, ec in enemy_positions:
                    if  has_line_of_sight(mp,nr,nc, er,ec):
                        dist = abs(nr - er) + abs(nc - ec)
                        dg+=1/(dist+1)
                dangerous[f"[{nr},{nc}]"]=dg
    return dangerous
