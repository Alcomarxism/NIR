import ast
import asyncio
import pygame

COLOR_FOG = (30, 30, 30)
COLOR_EMPTY = (230, 230, 230)
COLOR_WALL = (70, 70, 70)
COLOR_AGENT = (231, 76, 60)
COLOR_GRID = (180, 180, 180)
COLOR_FRONTIER = (255, 0, 0)
COLOR_TEXT_BG = (20, 20, 20)
COLOR_TEXT = (220, 220, 220)


class Visualizator:

    def __init__(self, grid_size=20, cell_size=20, padding=20):
        self.grid_size = grid_size
        self.cell_size = cell_size
        self.padding = padding
        self.field_width = self.grid_size * cell_size
        self.field_height = self.grid_size * cell_size
        self.width = self.field_width * 2 + self.padding
        self.height = self.field_height * 2 + self.padding

        pygame.init()
        pygame.font.init()
        self.font = pygame.font.SysFont("Consolas", 14)
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Simulation & Teams Memory")
        self.clock = pygame.time.Clock()

    def draw_agent(self, agent_pos, offset_x=0, offset_y=0):
        agent_x = (
            offset_x + agent_pos[1] * self.cell_size + self.cell_size // 2
        )
        agent_y = (
            offset_y + agent_pos[0] * self.cell_size + self.cell_size // 2
        )
        pygame.draw.circle(
            self.screen, COLOR_AGENT, (agent_x, agent_y), self.cell_size // 3
        )

    def draw_field(self, field, offset_x=0, offset_y=0):
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                rect = pygame.Rect(
                    offset_x + c * self.cell_size,
                    offset_y + r * self.cell_size,
                    self.cell_size,
                    self.cell_size,
                )
                cell_type = field[r][c]
                if cell_type == 1:
                    pygame.draw.rect(self.screen, COLOR_WALL, rect)
                elif cell_type == 2:
                    pygame.draw.rect(self.screen, COLOR_EMPTY, rect)
                    self.draw_agent((r, c), offset_x, offset_y)
                else:
                    pygame.draw.rect(self.screen, COLOR_EMPTY, rect)
                pygame.draw.rect(self.screen, COLOR_GRID, rect, 1)

    def draw_memory(self, memory, offset_x=0, offset_y=0):
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                rect = pygame.Rect(
                    offset_x + c * self.cell_size,
                    offset_y + r * self.cell_size,
                    self.cell_size,
                    self.cell_size,
                )
                cell_type = memory[r][c]
                if cell_type == "?":
                    pygame.draw.rect(self.screen, COLOR_FOG, rect)
                elif cell_type == "WALL":
                    pygame.draw.rect(self.screen, COLOR_WALL, rect)
                else:
                    pygame.draw.rect(self.screen, COLOR_EMPTY, rect)
                pygame.draw.rect(self.screen, COLOR_GRID, rect, 1)

    def draw_frontiers(self, frontiers, offset_x=0, offset_y=0):
        for f in frontiers:
            cell = ast.literal_eval(f) if isinstance(f, str) else f
            rect = pygame.Rect(
                offset_x + cell[1] * self.cell_size,
                offset_y + cell[0] * self.cell_size,
                self.cell_size,
                self.cell_size,
            )
            pygame.draw.rect(self.screen, COLOR_FRONTIER, rect)

    def draw_info_panel(self, lines, offset_x=0, offset_y=0):
        rect = pygame.Rect(
            offset_x, offset_y, self.field_width, self.field_height
        )
        pygame.draw.rect(self.screen, COLOR_TEXT_BG, rect)
        pygame.draw.rect(self.screen, COLOR_GRID, rect, 1)
        padding_internal = 10
        line_height = 20
        max_lines = (self.field_height - 2 * padding_internal) // line_height
        for i, line in enumerate(lines[-max_lines:]):
            text_surface = self.font.render(str(line), True, COLOR_TEXT)
            self.screen.blit(
                text_surface,
                (
                    offset_x + padding_internal,
                    offset_y + padding_internal + i * line_height,
                ),
            )

    def render(self, field, memory_team1, memory_team2, logs=None):
        self.screen.fill((10, 10, 10))
        memory_offset_x = self.field_width + self.padding
        memory_offset_y = self.field_height + self.padding
        self.draw_field(field, offset_x=0, offset_y=0)
        self.draw_memory(memory_team1, offset_x=memory_offset_x, offset_y=0)
        self.draw_memory(memory_team2, offset_x=0, offset_y=memory_offset_y)
        if logs is None:
            logs = ["--- INFO PANEL ---"]
        self.draw_info_panel(
            logs, offset_x=memory_offset_x, offset_y=memory_offset_y
        )
        pygame.display.flip()

    async def run_async_visualization(self, sim):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            map1 = sim.squad1.map
            map2 = sim.squad2.map
            logs = getattr(sim, "logs", [
                "Simulation Running...",
                f"Step: {getattr(sim, 'step_count', 0)}",
                f"Team 1 status: Active",
                f"Team 2 status: Active",
            ])
            self.render(sim.env.get_field(), map1, map2, logs)
            await asyncio.sleep(0)
            self.clock.tick(60)