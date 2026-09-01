import asyncio
import ast
import pygame

COLOR_FOG = (30, 30, 30)
COLOR_EMPTY = (230, 230, 230)
COLOR_WALL = (70, 70, 70)
COLOR_AGENT = (231, 76, 60)
COLOR_GRID = (180, 180, 180)


class Visualizator:
    def __init__(self, grid_size=20, cell_size=30, padding=20):
        self.grid_size = grid_size
        self.cell_size = cell_size
        self.padding = padding
        self.field_width = self.grid_size * cell_size
        self.field_height = self.grid_size * cell_size
        self.width = self.field_width * 2 + self.padding
        self.height = self.field_height
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Simulation & Agent Memory")
        self.clock = pygame.time.Clock()

    def draw_agent(self, agent_pos, offset_x=0):
        agent_x = (
            offset_x + agent_pos[1] * self.cell_size + self.cell_size // 2
        )
        agent_y = agent_pos[0] * self.cell_size + self.cell_size // 2
        pygame.draw.circle(
            self.screen, COLOR_AGENT, (agent_x, agent_y), self.cell_size // 3
        )

    def draw_field(self, field, offset_x=0):
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                rect = pygame.Rect(
                    offset_x + c * self.cell_size,
                    r * self.cell_size,
                    self.cell_size,
                    self.cell_size,
                )
                cell_type = field[r][c]
                if cell_type == 1:
                    pygame.draw.rect(self.screen, COLOR_WALL, rect)
                elif cell_type == 2:
                    pygame.draw.rect(self.screen, COLOR_EMPTY, rect)
                    self.draw_agent((r, c), offset_x)
                else:
                    pygame.draw.rect(self.screen, COLOR_EMPTY, rect)
                pygame.draw.rect(self.screen, COLOR_GRID, rect, 1)

    def draw_memory(self, memory, offset_x=0):
        fog_rect = pygame.Rect(
            offset_x, 0, self.field_width, self.field_height
        )
        pygame.draw.rect(self.screen, COLOR_FOG, fog_rect)
        for m, status in memory.items():
            cell = ast.literal_eval(m) if isinstance(m, str) else m
            rect = pygame.Rect(
                offset_x + cell[1] * self.cell_size,
                cell[0] * self.cell_size,
                self.cell_size,
                self.cell_size,
            )
            if status == "?":
                pygame.draw.rect(self.screen, COLOR_FOG, rect)
            elif status == "WALL":
                pygame.draw.rect(self.screen, COLOR_WALL, rect)
            else:
                pygame.draw.rect(self.screen, COLOR_EMPTY, rect)

            pygame.draw.rect(self.screen, COLOR_GRID, rect, 1)

    def render(self, field, memory):
        self.screen.fill((10, 10, 10))
        self.draw_field(field, offset_x=0)
        memory_offset = self.field_width + self.padding
        self.draw_memory(memory, offset_x=memory_offset)
        pygame.display.flip()

    async def run_async_visualization(self, sim):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            self.render(sim.env.get_field(), sim.comander.memory)
            await asyncio.sleep(0)
            self.clock.tick(60)