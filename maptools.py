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


def find_path_bfs(start, target, squad_map):
    if start == target:
        return [start]
    queue = deque([[start]])
    visited = {start}
    while queue:
        path = queue.popleft()
        curr_x, curr_y = path[-1]
        if (curr_x, curr_y) == target:
            return path
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = curr_x + dx, curr_y + dy
            cell_val = squad_map[nx][ny]
            if (nx, ny) not in visited and (cell_val == "EMPTY" or (nx, ny) == target):
                visited.add((nx, ny))
                new_path = list(path)
                new_path.append((nx, ny))
                queue.append(new_path)
    return []

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


def get_fog_view(sim,squad, agent, radius=3):
        r, c = agent.pos
        view = {}
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                if dr * dr + dc * dc > radius * radius:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < len(sim.map) and 0 <= nc < len(sim.map):
                    if has_line_of_sight(sim.map,r, c, nr, nc):
                        cell_type = sim.map[nr][nc]
                        view[f"[{nr},{nc}]"] = "WALL" if cell_type == 1 else ("EMPTY" if cell_type == 0 else cell_type)     
                        squad.map[nr][nc]= view[f"[{nr},{nc}]"]

        for sq in sim.squads:
            for ag in sim.squads[sq].agents:
                key=f"[{ag.pos[0]},{ag.pos[1]}]"
                if key in view.keys():
                    view[key]=sq
                    squad.map[ag.pos[0]][ag.pos[1]]=sq
        return view

