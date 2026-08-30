import pygame
import asyncio

COLOR_FOG = (30, 30, 30)
COLOR_EMPTY = (230, 230, 230)
COLOR_WALL = (70, 70, 70)
COLOR_AGENT = (231, 76, 60)
COLOR_GRID = (180, 180, 180)

class Visualizator():
    def __init__(self, grid_size=20, cell_size=30):
        self.grid_size = grid_size
        self.cell_size = cell_size
        self.width = self.grid_size * cell_size
        self.height = self.grid_size * cell_size
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("window")
        self.clock = pygame.time.Clock()

    def draw_agent(self,agent_pos):
        agent_x = agent_pos[1] * self.cell_size + self.cell_size // 2
        agent_y = agent_pos[0] * self.cell_size + self.cell_size // 2
        pygame.draw.circle(self.screen, COLOR_AGENT, (agent_x, agent_y), self.cell_size // 3)

    def draw_field(self,field):
         for r in range(self.grid_size):
            for c in range(self.grid_size):
                rect = pygame.Rect(c * self.cell_size, r * self.cell_size, self.cell_size, self.cell_size)
                cell_type = field[r][c]
                if cell_type == 1:
                    pygame.draw.rect(self.screen, COLOR_WALL, rect)
                elif cell_type == 2:
                    pygame.draw.rect(self.screen, COLOR_EMPTY, rect)  
                    self.draw_agent((r,c))
                else:
                    pygame.draw.rect(self.screen, COLOR_EMPTY, rect)  
                pygame.draw.rect(self.screen, COLOR_GRID, rect, 1)

    def render(self,field):
        self.screen.fill(COLOR_FOG)
        self.draw_field(field)
        pygame.display.flip()

    async def run_async_visualization(self,sim):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False        
            self.render(sim.env.get_field())
            await asyncio.sleep(0) 
            self.clock.tick(60)