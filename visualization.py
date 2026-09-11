import ast
import asyncio
import pygame
import textwrap

COLOR_FOG = (30, 30, 30)
COLOR_EMPTY = (230, 230, 230)
COLOR_WALL = (70, 70, 70)
COLOR_AGENT_RED = (255, 0, 0)
COLOR_AGENT_BLUE = (0, 0, 255)
COLOR_GRID = (180, 180, 180)
COLOR_FRONTIER = (255, 0, 0)
COLOR_TEXT_BG = (20, 20, 20)
COLOR_TEXT = (220, 220, 220)


class Visualizator:

    def __init__(self, padding=20):
        self.padding = padding
        self.field_width = 400
        self.field_height = 400
        self.width = self.field_width * 2 + self.padding
        self.height = self.field_height * 2 + self.padding

        pygame.init()
        pygame.font.init()
        self.font = pygame.font.SysFont("Consolas", 12)
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Simulation & Teams Memory")
        self.clock = pygame.time.Clock()

    def draw_agent(self, cell_size, agent_pos, color, offset_x=0, offset_y=0):
        agent_x = (
            offset_x + agent_pos[1] * cell_size + cell_size // 2
        )
        agent_y = (
            offset_y + agent_pos[0] * cell_size + cell_size // 2
        )
        pygame.draw.circle(
            self.screen, color, (agent_x, agent_y), cell_size // 3
        )

    def draw_field(self, sim, offset_x=0, offset_y=0):
        cell_size=self.field_width/len(sim.map)
        for r in range(len(sim.map)):
            for c in range(len(sim.map)):
                rect = pygame.Rect(offset_x + c * cell_size,offset_y + r * cell_size, cell_size, cell_size)
                cell_type = sim.map[r][c]
                if cell_type == 1:
                    pygame.draw.rect(self.screen, COLOR_WALL, rect)
                else:
                    pygame.draw.rect(self.screen, COLOR_EMPTY, rect)
                pygame.draw.rect(self.screen, COLOR_GRID, rect, 1)
        for sq in sim.squads:
            for ag in sim.squads[sq].agents:
                if sq=="RED":
                    self.draw_agent(cell_size,ag.pos, COLOR_AGENT_RED, offset_x, offset_y)
                elif sq=="BLUE":
                    self.draw_agent(cell_size,ag.pos, COLOR_AGENT_BLUE, offset_x, offset_y)


    def draw_memory(self, memory, offset_x=0, offset_y=0):
        cell_size=self.field_width/len(memory)
        for r in range(len(memory)):
            for c in range(len(memory)):
                rect = pygame.Rect( offset_x + c * cell_size, offset_y + r * cell_size, cell_size, cell_size)
                cell_type = memory[r][c]
                if cell_type == "?":
                    pygame.draw.rect(self.screen, COLOR_FOG, rect)
                elif cell_type == "WALL":
                    pygame.draw.rect(self.screen, COLOR_WALL, rect)
                elif cell_type == "RED":
                    pygame.draw.rect(self.screen, COLOR_EMPTY, rect)
                    self.draw_agent(cell_size,(r, c), COLOR_AGENT_RED, offset_x, offset_y)
                elif cell_type == "BLUE":
                    pygame.draw.rect(self.screen, COLOR_EMPTY, rect)
                    self.draw_agent(cell_size,(r, c), COLOR_AGENT_BLUE, offset_x, offset_y)
                else:
                    pygame.draw.rect(self.screen, COLOR_EMPTY, rect)
                pygame.draw.rect(self.screen, COLOR_GRID, rect, 1)


    def draw_split_info_panel(self, logs_team1, logs_team2, offset_x=0, offset_y=0):
        panel_rect = pygame.Rect(offset_x, offset_y, self.field_width, self.field_height)
        pygame.draw.rect(self.screen, COLOR_TEXT_BG, panel_rect)
        pygame.draw.rect(self.screen, COLOR_GRID, panel_rect, 1)
        half_width = self.field_width // 2
        pygame.draw.line(
            self.screen,
            COLOR_GRID,
            (offset_x + half_width, offset_y),
            (offset_x + half_width, offset_y + self.field_height),
            1,
        )

        padding_internal = 6
        line_height = 16
        col_width = half_width - (padding_internal * 2)
        def draw_column(title, logs, col_color, col_offset_x):
            col_rect = pygame.Rect(
                col_offset_x, offset_y, half_width, self.field_height
            )
            self.screen.set_clip(col_rect)
            title_surface = self.font.render(title, True, col_color)
            self.screen.blit(
                title_surface,
                (col_offset_x + padding_internal, offset_y + padding_internal),
            )
            char_width = self.font.size("A")[0] or 7
            max_chars_per_line = max(1, col_width // char_width)
            wrapped_lines = []
            for log in logs or []:
                wrapped = textwrap.wrap(str(log), width=max_chars_per_line)
                wrapped_lines.extend(wrapped if wrapped else [""])
            max_visible_lines = (
                self.field_height - 2 * padding_internal - line_height
            ) // line_height
            visible_lines = wrapped_lines[-max_visible_lines:]
            for i, line in enumerate(visible_lines):
                text_surface = self.font.render(line, True, COLOR_TEXT)
                self.screen.blit(
                    text_surface,
                    (
                        col_offset_x + padding_internal,
                        offset_y
                        + padding_internal
                        + line_height
                        + i * line_height,
                    ),
                )
            self.screen.set_clip(None)
        draw_column("--- RED TEAM ---", logs_team1, COLOR_AGENT_RED, offset_x)
        draw_column(
            "--- BLUE TEAM ---", logs_team2, COLOR_AGENT_BLUE, offset_x + half_width
        )

    def render(self,sim):
        self.screen.fill((10, 10, 10))
        memory_offset_x = self.field_width + self.padding
        memory_offset_y = self.field_height + self.padding
        self.draw_field(sim, offset_x=0, offset_y=0)
        self.draw_memory(sim.squads['RED'].map, offset_x=memory_offset_x, offset_y=0)
        self.draw_memory(sim.squads['BLUE'].map, offset_x=0, offset_y=memory_offset_y)
        self.draw_split_info_panel(sim.squads['RED'].get_logs(),sim.squads['BLUE'].get_logs(), offset_x=memory_offset_x, offset_y=memory_offset_y,)
        pygame.display.flip()

    async def run_async_visualization(self, sim):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            self.render(sim)
            await asyncio.sleep(0)
            self.clock.tick(60)