import pygame, sys, random

pygame.init()
_info    = pygame.display.Info()
SCREEN_W = min(1400, _info.current_w  - 20)
SCREEN_H = min(860,  _info.current_h  - 80)

# ── Colours ──────────────────────────────────
BG         = (13,  15,  23)
PANEL_BG   = (19,  22,  34)
PANEL_DARK = (14,  17,  27)
BORDER     = (38,  44,  68)

CELL_EMPTY = (20,  25,  42)
CELL_WALL  = (42,  46,  62)
CELL_START = (32, 160, 110)
CELL_GOAL  = (180,  58,  62)
CELL_FRONT = (180, 148,  40)
CELL_VISIT = (45,  95, 170)
CELL_PATH  = (38, 190, 120)
CELL_AGENT = (220, 240, 255)  # bright white-cyan for agent position
CELL_GRID  = (45,  52,  80)

A_TEAL   = (60,  200, 160)
A_BLUE   = (80,  140, 220)
A_AMBER  = (210, 165,  55)
A_RED    = (200,  75,  80)
A_PURPLE = (130,  90, 210)
A_GREEN  = (60,  185, 110)

WHITE    = (205, 215, 230)
GREY     = (90,  105, 135)
DIM      = (50,   58,  84)

BTN_BASE    = (24,  28,  44)
BTN_HOVER   = (30,  36,  56)
BTN_ACTIVE  = (28,  34,  52)

PANEL_W         = 300
GRID_AREA_W     = SCREEN_W - PANEL_W
GRID_AREA_H     = SCREEN_H
LEGEND_H        = 40
GRID_AREA_H_USE = GRID_AREA_H - LEGEND_H
DEFAULT_ROWS    = 20
DEFAULT_COLS    = 30
GRID_PAD        = 28
PANEL_PAD       = 18
FPS             = 60

def rrect(surf, color, rect, r=8, bw=0, bc=None):
    pygame.draw.rect(surf, color, rect, border_radius=r)
    if bw and bc:
        pygame.draw.rect(surf, bc, rect, bw, border_radius=r)


class Button:
    def __init__(self, x, y, w, h, label, color=A_TEAL,
                 toggle=False, active=False, always_lit=False, font=None):
        self.rect       = pygame.Rect(x, y, w, h)
        self.label      = label
        self.color      = color
        self.toggle     = toggle
        self.active     = active
        self.always_lit = always_lit
        self.hovered    = False
        self.font       = font

    def draw(self, surf):
        if self.hovered:
            fill, border_w = BTN_HOVER, 1
        elif self.active and self.toggle:
            fill, border_w = BTN_ACTIVE, 2
        else:
            fill, border_w = BTN_BASE, 1
        accent = self.color
        border_col = accent if (self.hovered or self.active) else BORDER
        rrect(surf, fill, self.rect, r=6, bw=border_w, bc=border_col)
        if self.active and self.toggle:
            bar = pygame.Rect(self.rect.x+1, self.rect.y+4, 3, self.rect.h-8)
            pygame.draw.rect(surf, accent, bar, border_radius=2)
        if self.font:
            tc = WHITE if not (self.hovered or self.active) else self.color
            t = self.font.render(self.label, True, tc)
            surf.blit(t, t.get_rect(center=self.rect.center))

    def handle(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.toggle: self.active = not self.active
                return True
        return False


class Dropdown:
    def __init__(self, x, y, w, h, options, label="", color=A_TEAL, font=None):
        self.rect    = pygame.Rect(x, y, w, h)
        self.options = options
        self.label   = label
        self.color   = color
        self.font    = font
        self.selected = 0
        self.open    = False
        self.hovered = -1

    @property
    def value(self): return self.options[self.selected]

    def _item_rect(self, i):
        return pygame.Rect(self.rect.x, self.rect.bottom + i*self.rect.h, self.rect.w, self.rect.h)

    def draw(self, surf):
        if self.label and self.font:
            surf.blit(self.font.render(self.label, True, WHITE), (self.rect.x, self.rect.y-16))
        # Darker, more visible background
        rrect(surf, (30, 36, 56), self.rect, r=6, bw=2, bc=self.color if self.open else self.color)
        if self.font:
            t = self.font.render(self.options[self.selected], True, WHITE)
            surf.blit(t, t.get_rect(midleft=(self.rect.x+12, self.rect.centery)))
        ax, ay = self.rect.right-18, self.rect.centery
        pts = [(ax,ay+4),(ax+8,ay+4),(ax+4,ay-4)] if self.open else [(ax,ay-4),(ax+8,ay-4),(ax+4,ay+4)]
        pygame.draw.polygon(surf, self.color, pts)
        if self.open:
            for i, opt in enumerate(self.options):
                ir = self._item_rect(i)
                bg = (40, 50, 75) if i==self.hovered else (30, 36, 56)
                rrect(surf, bg, ir, r=4, bw=1, bc=self.color if i==self.selected else self.color)
                if self.font:
                    t = self.font.render(opt, True, self.color if i==self.selected else WHITE)
                    surf.blit(t, t.get_rect(midleft=(ir.x+12, ir.centery)))

    def handle(self, event):
        if event.type == pygame.MOUSEMOTION and self.open:
            self.hovered = next((i for i in range(len(self.options))
                                 if self._item_rect(i).collidepoint(event.pos)), -1)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.open = not self.open; return True
            if self.open:
                for i in range(len(self.options)):
                    if self._item_rect(i).collidepoint(event.pos):
                        self.selected = i; self.open = False; return True
                self.open = False
        return False

    def close(self): self.open = False


class NumberInput:
    def __init__(self, x, y, w, h, label, val=10, mn=5, mx=60, color=A_TEAL, font=None):
        self.rect   = pygame.Rect(x, y, w, h)
        self.label  = label
        self.val    = val
        self.mn, self.mx = mn, mx
        self.color  = color
        self.font   = font
        self.active = False
        self.text   = str(val)
        self.btn_minus  = pygame.Rect(x, y, h, h)
        self.btn_plus   = pygame.Rect(x+w-h, y, h, h)
        self.value_rect = pygame.Rect(x+h+2, y, w-h*2-4, h)

    def draw(self, surf):
        if self.font:
            surf.blit(self.font.render(self.label, True, GREY), (self.rect.x, self.rect.y-16))
        rrect(surf, BTN_BASE, self.rect, r=6, bw=1, bc=self.color if self.active else BORDER)
        for btn, sym in ((self.btn_minus,"−"), (self.btn_plus,"+")):
            rrect(surf, PANEL_DARK, btn, r=4)
            if self.font:
                t = self.font.render(sym, True, GREY)
                surf.blit(t, t.get_rect(center=btn.center))
        if self.font:
            txt = self.text if self.active else str(self.val)
            t = self.font.render(txt, True, self.color if self.active else WHITE)
            surf.blit(t, t.get_rect(center=self.value_rect.center))

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_minus.collidepoint(event.pos):
                self.val = max(self.mn, self.val-1); self.text = str(self.val); return True
            if self.btn_plus.collidepoint(event.pos):
                self.val = min(self.mx, self.val+1); self.text = str(self.val); return True
            self.active = self.value_rect.collidepoint(event.pos)
            if self.active: self.text = ""
            else: self._commit()
        if event.type == pygame.KEYDOWN and self.active:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER): self._commit(); self.active = False
            elif event.key == pygame.K_BACKSPACE: self.text = self.text[:-1]
            elif event.unicode.isdigit(): self.text += event.unicode
        return False

    def _commit(self):
        try: self.val = max(self.mn, min(self.mx, int(self.text)))
        except ValueError: pass
        self.text = str(self.val)


class Slider:
    def __init__(self, x, y, w, label, mn=0, mx=100, val=30, color=A_TEAL, font=None):
        self.x, self.y, self.w = x, y, w
        self.label = label
        self.mn, self.mx, self.val = mn, mx, val
        self.color = color
        self.font  = font
        self.drag  = False
        self.track = pygame.Rect(x, y+22, w, 6)

    @property
    def norm(self): return (self.val-self.mn)/(self.mx-self.mn)

    def draw(self, surf):
        if self.font:
            surf.blit(self.font.render(f"{self.label}: {self.val}", True, WHITE), (self.x, self.y))
        pygame.draw.rect(surf, CELL_WALL, self.track, border_radius=3)
        pygame.draw.rect(surf, self.color,
                         pygame.Rect(self.track.x, self.track.y, int(self.norm*self.track.w), self.track.h),
                         border_radius=3)
        kx = int(self.track.x + self.norm*self.track.w)
        pygame.draw.circle(surf, BG, (kx, self.track.centery), 9)
        pygame.draw.circle(surf, self.color, (kx, self.track.centery), 7)

    def handle(self, event):
        kx = int(self.track.x + self.norm*self.track.w)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if pygame.Rect(kx-10, self.track.centery-10, 20, 20).collidepoint(event.pos) \
               or self.track.collidepoint(event.pos): self.drag = True
        if event.type == pygame.MOUSEBUTTONUP: self.drag = False
        if event.type == pygame.MOUSEMOTION and self.drag:
            self.val = int(self.mn + max(0.0, min(1.0,
                (event.pos[0]-self.track.x)/self.track.w)) * (self.mx-self.mn))


class Grid:
    EMPTY=0; WALL=1; START=2; GOAL=3; FRONT=4; VISIT=5; PATH=6; AGENT=7

    def __init__(self, rows, cols):
        self.rows, self.cols = rows, cols
        self.cells = [[self.EMPTY]*cols for _ in range(rows)]
        self.start = (rows-2, 1)
        self.goal  = (1, cols-2)
        self.cells[self.start[0]][self.start[1]] = self.START
        self.cells[self.goal[0]][self.goal[1]]   = self.GOAL

    def set(self, r, c, val):
        if (r,c) not in (self.start, self.goal):
            self.cells[r][c] = val

    def clear_path(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.cells[r][c] in (self.FRONT, self.VISIT, self.PATH, self.AGENT):
                    self.cells[r][c] = self.EMPTY

    def generate_random(self, density):
        for r in range(self.rows):
            for c in range(self.cols):
                if (r,c) not in (self.start, self.goal):
                    self.cells[r][c] = self.WALL if random.random() < density else self.EMPTY


class MetricsBox:
    def __init__(self, x, y, w, font):
        self.x, self.y, self.w = x, y, w
        self.font = font
        self.nodes_visited = 0
        self.path_cost     = 0
        self.exec_time_ms  = 0.0
        self.status        = "IDLE"

    def draw(self, surf):
        box = pygame.Rect(self.x, self.y, self.w, 115)
        rrect(surf, PANEL_DARK, box, r=10, bw=1, bc=BORDER)
        t = self.font.render("─── METRICS ───", True, GREY)
        surf.blit(t, t.get_rect(centerx=box.centerx, y=box.y+10))
        sc = {"IDLE":GREY,"RUNNING":A_AMBER,"MOVING":A_TEAL,"FOUND":A_GREEN,"NO PATH":A_RED}.get(self.status, WHITE)
        st = self.font.render(self.status, True, sc)
        surf.blit(st, st.get_rect(centerx=box.centerx, y=box.y+32))
        for i, (lbl, val, col) in enumerate([
            ("Nodes Visited", str(self.nodes_visited), A_AMBER),
            ("Path Cost",     str(self.path_cost),     A_GREEN),
            ("Exec Time",     f"{self.exec_time_ms:.1f} ms", A_TEAL),
        ]):
            y = box.y + 65 + i*16
            surf.blit(self.font.render(lbl, True, GREY), (box.x+14, y))
            v = self.font.render(val, True, col)
            surf.blit(v, (box.x+self.w-v.get_width()-14, y))


def draw_legend(surf, x, y, w, h, font):
    items = [(CELL_START,"Start"),(CELL_GOAL,"Goal"),(CELL_WALL,"Wall"),
             (CELL_FRONT,"Frontier"),(CELL_VISIT,"Visited"),(CELL_PATH,"Path"),(CELL_AGENT,"Agent")]
    rrect(surf, PANEL_DARK, pygame.Rect(x,y,w,h), r=6, bw=1, bc=BORDER)
    iw, sq = w//len(items), h-14
    for i, (col, lbl) in enumerate(items):
        ix, iy = x+i*iw+iw//2, y+h//2
        pygame.draw.rect(surf, col, pygame.Rect(ix-sq//2-2, iy-sq//2, sq, sq), border_radius=3)
        t = font.render(lbl, True, WHITE)
        surf.blit(t, t.get_rect(midleft=(ix-sq//2+sq+4, iy)))


class ContextMenu:
    IH, W, PAD = 30, 160, 8

    def __init__(self):
        self.visible = False
        self.cell    = None
        self.x = self.y = 0
        self.items   = []
        self.hovered = -1

    def _item_rect(self, i):
        return pygame.Rect(self.x, self.y+self.PAD+i*self.IH, self.W, self.IH)

    def show(self, sx, sy, cell, grid):
        self.visible, self.cell, self.hovered = True, cell, -1
        r, c = cell
        self.items = []
        if (r,c) != grid.start:                                       self.items.append(("📍  Set as Start", CELL_START, 'start'))
        if (r,c) != grid.goal:                                        self.items.append(("🎯  Set as Goal",  CELL_GOAL,  'goal'))
        if grid.cells[r][c] != Grid.WALL:                             self.items.append(("✏   Place Wall",  A_TEAL,  'wall'))
        if grid.cells[r][c] == Grid.WALL:                             self.items.append(("⌫   Remove Wall", A_RED,   'clear'))
        if grid.cells[r][c] not in (Grid.WALL,Grid.START,Grid.GOAL,Grid.EMPTY):
                                                                      self.items.append(("✕   Clear Cell",  GREY,       'clear'))
        mh = len(self.items)*self.IH + self.PAD*2
        self.x = min(sx, GRID_AREA_W-self.W-4)
        self.y = min(sy, SCREEN_H-mh-4)

    def hide(self): self.visible = False; self.cell = None

    def draw(self, surf, font):
        if not self.visible: return
        mh = len(self.items)*self.IH + self.PAD*2
        sh = pygame.Surface((self.W+6, mh+6), pygame.SRCALPHA)
        sh.fill((0,0,0,80)); surf.blit(sh, (self.x+3, self.y+3))
        rrect(surf, PANEL_BG, pygame.Rect(self.x,self.y,self.W,mh), r=8, bw=1, bc=BORDER)
        for i, (label, color, _) in enumerate(self.items):
            ir = self._item_rect(i)
            if i == self.hovered:
                rrect(surf, BTN_HOVER, ir, r=5)
                pygame.draw.rect(surf, color, (self.x+4, ir.y+4, 3, self.IH-8), border_radius=2)
            t = font.render(label, True, color if i==self.hovered else GREY)
            surf.blit(t, t.get_rect(midleft=(self.x+14, ir.centery)))

    def handle(self, event):
        if not self.visible: return None, None
        if event.type == pygame.MOUSEMOTION:
            self.hovered = next((i for i in range(len(self.items))
                                 if self._item_rect(i).collidepoint(event.pos)), -1)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                for i, (_, _, action) in enumerate(self.items):
                    if self._item_rect(i).collidepoint(event.pos):
                        cell = self.cell; self.hide(); return action, cell
                self.hide()
            if event.button == 3: self.hide()
        return None, None


# ── Main App ─────────────────────────────────
class PathfinderApp:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Dynamic Pathfinding Agent")
        self.font_title = pygame.font.SysFont("consolas", 18, bold=True)
        self.font       = pygame.font.SysFont("consolas", 11)
        self.clock      = pygame.time.Clock()
        self.grid_rows  = DEFAULT_ROWS
        self.grid_cols  = DEFAULT_COLS
        self._recompute_layout()
        self.grid         = Grid(self.grid_rows, self.grid_cols)
        self.context_menu = ContextMenu()
        self.scroll_y     = 0
        self.panel_surf   = pygame.Surface((PANEL_W, 1100))

        # ── Search state ──────────────────────────────
        self.searcher    = None
        self.search_gen  = None
        self.searching   = False
        self.start_time  = 0.0
        self.frame_count = 0

        # ── Agent movement state ──────────────────────
        self.agent_pos     = None   # current cell agent is on
        self.agent_path    = []     # remaining path ahead of agent
        self.agent_moving  = False  # True when agent is walking path

        self._build_ui()

    def _recompute_layout(self):
        uw, uh = GRID_AREA_W-GRID_PAD*2, GRID_AREA_H_USE-GRID_PAD*2
        self.cell_size  = max(8, min(uw//self.grid_cols, uh//self.grid_rows)-1)
        self.grid_off_x = (GRID_AREA_W - self.grid_cols*self.cell_size)//2
        self.grid_off_y = (GRID_AREA_H_USE - self.grid_rows*self.cell_size)//2

    def _build_ui(self):
        px, pw = PANEL_PAD, PANEL_W-PANEL_PAD*2
        cy = 58
        dh, ih, bh = 30, 28, 26
        g1, g2, lh = 14, 5, 14

        cy += lh
        self.dd_algo = Dropdown(px, cy, pw, dh, ["A* Search","Greedy Best-First (GBFS)"],
                                "ALGORITHM", A_TEAL, self.font)
        cy += dh+g1; cy += lh
        self.dd_heur = Dropdown(px, cy, pw, dh, ["Manhattan Distance","Euclidean Distance"],
                                "HEURISTIC", A_AMBER, self.font)
        cy += dh+g1; cy += lh

        half = (pw-6)//2
        self.in_rows = NumberInput(px, cy, half, ih, "ROWS", DEFAULT_ROWS, 5, 60, A_TEAL, self.font)
        self.in_cols = NumberInput(px+half+6, cy, half, ih, "COLS", DEFAULT_COLS, 5, 80, A_TEAL, self.font)
        cy += ih+g2
        self.btn_apply = Button(px, cy, pw, bh, "⊞  Apply Grid Size", A_TEAL, font=self.font)
        cy += bh+g1; cy += lh

        self.sl_density = Slider(px, cy, pw, "Density %", 5, 65, 30, A_PURPLE, self.font)
        cy += 28+g1

        self.btn_generate = Button(px, cy, pw, bh, "⟳  Generate Maze",  A_PURPLE, font=self.font); cy += bh+g2
        self.btn_clear    = Button(px, cy, pw, bh, "✕  Clear Grid",      A_RED,    font=self.font); cy += bh+g2
        self.btn_start    = Button(px, cy, pw, bh, "▶  Start Search",    A_GREEN,  font=self.font); cy += bh+g2
        self.btn_pause    = Button(px, cy, pw//2-3, bh, "⏸  Pause",
                                   A_AMBER, toggle=True, always_lit=True, font=self.font)
        self.btn_reset    = Button(px+pw//2+3, cy, pw//2-3, bh, "↺  Reset", A_TEAL, font=self.font)
        cy += bh+g1
        self.btn_dynamic  = Button(px, cy, pw, bh, "⚡  Dynamic Mode: OFF",
                                   A_AMBER, toggle=True, always_lit=True, font=self.font)
        cy += bh+g1
        self.metrics = MetricsBox(px, cy, pw, self.font)
        cy += 120

        self.panel_content_h = cy+PANEL_PAD
        self.all_buttons   = [self.btn_apply, self.btn_generate, self.btn_clear,
                               self.btn_start, self.btn_pause, self.btn_reset, self.btn_dynamic]
        self.all_sliders   = [self.sl_density]
        self.all_dropdowns = [self.dd_algo, self.dd_heur]
        self.all_inputs    = [self.in_rows, self.in_cols]

    # ── Search wiring ─────────────────────────────────
    def _start_search(self, start=None, replan=False):
        """Instantiate the selected algorithm and kick off the generator."""
        from Astar import AStarSearch
        from Gbfs  import GBFSearch

        # Clear previous visual state unless replanning (keep walls)
        if not replan:
            self.grid.clear_path()

        heuristic = "manhattan" if "Manhattan" in self.dd_heur.value else "euclidean"
        s = start if start else self.grid.start

        if "A*" in self.dd_algo.value:
            self.searcher = AStarSearch(self.grid, s, self.grid.goal, heuristic)
        else:
            self.searcher = GBFSearch(self.grid, s, self.grid.goal, heuristic)

        self.search_gen  = self.searcher.step()
        self.searching   = True
        self.start_time  = pygame.time.get_ticks()
        self.btn_pause.active = False
        self.metrics.status        = "RUNNING"
        self.metrics.nodes_visited = 0
        self.metrics.path_cost     = 0
        self.metrics.exec_time_ms  = 0.0
        # Reset agent movement
        self.agent_pos    = None
        self.agent_path   = []
        self.agent_moving = False

    def _search_step(self):
        """
        Called once per frame from the main loop.
        Advances the generator by sl_speed.val steps and updates the grid.
        """
        if not self.searching or self.btn_pause.active:
            return
        if self.search_gen is None:
            return

        # Throttle: advance 1 step every 2 frames for visible animation
        if self.frame_count % 2 != 0:
            return
        for _ in range(1):
            try:
                result = next(self.search_gen)
            except StopIteration:
                self.searching = False
                return

            # Update cell colours for frontier and visited
            # Frontier painted first (amber), visited overrides it (blue)
            for cell in result["frontier"]:
                r, c = cell
                if self.grid.cells[r][c] not in (Grid.START, Grid.GOAL, Grid.WALL, Grid.VISIT):
                    self.grid.cells[r][c] = Grid.FRONT

            for cell in result["visited"]:
                r, c = cell
                if self.grid.cells[r][c] not in (Grid.START, Grid.GOAL, Grid.WALL):
                    self.grid.cells[r][c] = Grid.VISIT

            # Update metrics
            self.metrics.nodes_visited = self.searcher.nodes_visited
            elapsed = pygame.time.get_ticks() - self.start_time
            self.metrics.exec_time_ms  = float(elapsed)

            if result["type"] == "found":
                # Draw final path
                for cell in result["path"]:
                    r, c = cell
                    if self.grid.cells[r][c] not in (Grid.START, Grid.GOAL):
                        self.grid.cells[r][c] = Grid.PATH
                self.metrics.path_cost    = len(result["path"]) - 1
                self.metrics.exec_time_ms = float(pygame.time.get_ticks() - self.start_time)
                self.metrics.status       = "FOUND"
                self.searching    = False
                # Kick off agent movement along the found path
                self.agent_path   = list(result["path"])[1:]  # skip start node
                self.agent_pos    = self.grid.start
                self.agent_moving = True
                return

            elif result["type"] == "no_path":
                self.metrics.status = "NO PATH"
                self.searching = False
                return

    # ── Dynamic mode obstacle spawning ───────────────
    def _agent_step(self):
        """
        Move the agent one cell forward along agent_path.
        Uses the same 2-frame throttle as the search animation.
        """
        if not self.agent_moving or self.btn_pause.active:
            return
        if not self.agent_path:
            return

        self.frame_count += 1
        if self.frame_count % 2 != 0:
            return

        # Leave green trail behind the agent
        if self.agent_pos and self.agent_pos not in (self.grid.start, self.grid.goal):
            self.grid.cells[self.agent_pos[0]][self.agent_pos[1]] = Grid.PATH

        # Advance to next cell
        self.agent_path.pop(0)

        if not self.agent_path:
            # Reached the goal
            self.agent_pos    = self.grid.goal
            self.agent_moving = False
            self.metrics.status = "FOUND"
            return

        self.agent_pos = self.agent_path[0]
        r, c = self.agent_pos

        # Mark agent position visually (don't overwrite start/goal)
        if self.agent_pos not in (self.grid.start, self.grid.goal):
            self.grid.cells[r][c] = Grid.AGENT

    def _dynamic_step(self):
        """
        Spawns walls only while search is actively running.
        Stops as soon as path is found or no path exists.
        """
        if not self.btn_dynamic.active:
            return
        # Only spawn while search is actively running
        if not self.searching:
            return

        # ~2% chance per frame to spawn a new obstacle
        if random.random() > 0.02:
            return

        r = random.randint(0, self.grid.rows-1)
        c = random.randint(0, self.grid.cols-1)
        cell = (r, c)

        # Only spawn on empty/visited/frontier cells
        if self.grid.cells[r][c] in (Grid.EMPTY, Grid.VISIT, Grid.FRONT):
            self.grid.cells[r][c] = Grid.WALL

            if self.searcher and self.searcher.notify_wall_added(cell):
                self._start_search(start=self.grid.start, replan=True)

    def _draw_grid(self):
        surf = self.screen
        g, cs, ox, oy = self.grid, self.cell_size, self.grid_off_x, self.grid_off_y
        CMAP = {Grid.EMPTY:CELL_EMPTY, Grid.WALL:CELL_WALL, Grid.START:CELL_START,
                Grid.GOAL:CELL_GOAL, Grid.FRONT:CELL_FRONT, Grid.VISIT:CELL_VISIT,
                Grid.PATH:CELL_PATH, Grid.AGENT:CELL_AGENT}
        pygame.draw.rect(surf, BG, (0, 0, GRID_AREA_W, GRID_AREA_H))
        for r in range(g.rows):
            for c in range(g.cols):
                rect = pygame.Rect(ox+c*cs, oy+r*cs, cs, cs)
                pygame.draw.rect(surf, CMAP[g.cells[r][c]], rect)
                if g.cells[r][c] == Grid.WALL and cs >= 12:
                    pygame.draw.rect(surf, (55,65,95), rect, border_radius=max(1,cs//8))
        for r in range(g.rows+1):
            pygame.draw.line(surf, CELL_GRID, (ox, oy+r*cs), (ox+g.cols*cs, oy+r*cs))
        for c in range(g.cols+1):
            pygame.draw.line(surf, CELL_GRID, (ox+c*cs, oy), (ox+c*cs, oy+g.rows*cs))
        if cs >= 14:
            for (r,c), lbl in [(g.start,"S"),(g.goal,"G")]:
                t = self.font.render(lbl, True, BG)
                surf.blit(t, t.get_rect(center=(ox+c*cs+cs//2, oy+r*cs+cs//2)))
        draw_legend(surf, 8, GRID_AREA_H_USE+6, GRID_AREA_W-16, LEGEND_H-10, self.font)

    def _draw_panel(self):
        surf, ps, pw = self.screen, self.panel_surf, PANEL_W
        ps.fill(BG)
        rrect(ps, PANEL_BG, pygame.Rect(4,4,pw-8,self.panel_content_h-4), r=12, bw=1, bc=BORDER)
        t = self.font_title.render("PATHFINDER", True, WHITE)
        ps.blit(t, t.get_rect(centerx=pw//2, y=10))
        t = self.font.render("Dynamic Agent  v1.0", True, GREY)
        ps.blit(t, t.get_rect(centerx=pw//2, y=32))
        pygame.draw.line(ps, BORDER, (14,52), (pw-14,52), 1)
        t = self.font.render("Right-click any cell to edit", True, DIM)
        ps.blit(t, t.get_rect(centerx=pw//2, y=56))

        self.btn_dynamic.label = "⚡  Dynamic Mode: ON" if self.btn_dynamic.active else "⚡  Dynamic Mode: OFF"
        for w in self.all_buttons+self.all_sliders+self.all_inputs: w.draw(ps)
        self.metrics.draw(ps)
        # Draw only the closed (header) part of each dropdown on panel_surf
        for dd in self.all_dropdowns:
            was_open = dd.open
            dd.open = False
            dd.draw(ps)
            dd.open = was_open

        self.scroll_y = max(0, min(self.scroll_y, max(0, self.panel_content_h-SCREEN_H)))
        pygame.draw.rect(surf, BG, (GRID_AREA_W, 0, pw, SCREEN_H))
        pygame.draw.line(surf, BORDER, (GRID_AREA_W,0), (GRID_AREA_W,SCREEN_H), 2)
        surf.blit(ps, (GRID_AREA_W,0), pygame.Rect(0, self.scroll_y, pw, SCREEN_H))
        if self.panel_content_h > SCREEN_H:
            bh = int(SCREEN_H*SCREEN_H/self.panel_content_h)
            by = int(self.scroll_y*SCREEN_H/self.panel_content_h)
            pygame.draw.rect(surf, A_TEAL, (GRID_AREA_W+pw-5, by, 3, bh), border_radius=2)

    def _cell_at(self, mx, my):
        c = (mx-self.grid_off_x)//self.cell_size
        r = (my-self.grid_off_y)//self.cell_size
        return (r,c) if 0<=r<self.grid.rows and 0<=c<self.grid.cols else None

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or \
               (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit(); sys.exit()

            if event.type == pygame.MOUSEWHEEL and pygame.mouse.get_pos()[0] >= GRID_AREA_W:
                self.scroll_y = max(0, min(self.scroll_y-event.y*25,
                                           max(0, self.panel_content_h-SCREEN_H)))

            pe = event
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                if hasattr(event,'pos') and event.pos[0] >= GRID_AREA_W:
                    pe = pygame.event.Event(event.type,
                                            {**{k:v for k,v in event.__dict__.items() if k!='pos'},
                                             'pos':(event.pos[0]-GRID_AREA_W, event.pos[1]+self.scroll_y)})

            for ni in self.all_inputs:  ni.handle(pe)
            for sl in self.all_sliders: sl.handle(pe)
            for dd in self.all_dropdowns:
                dd.handle(pe)
                if dd.open:
                    for other in self.all_dropdowns:
                        if other is not dd: other.close()
            for btn in self.all_buttons:
                if btn.handle(pe): self._on_button(btn); break

            action, cell = self.context_menu.handle(event)
            if action and cell:
                r, c = cell
                if action == 'start':
                    self.grid.cells[self.grid.start[0]][self.grid.start[1]] = Grid.EMPTY
                    self.grid.start = (r,c); self.grid.cells[r][c] = Grid.START
                elif action == 'goal':
                    self.grid.cells[self.grid.goal[0]][self.grid.goal[1]] = Grid.EMPTY
                    self.grid.goal  = (r,c); self.grid.cells[r][c] = Grid.GOAL
                elif action == 'wall':  self.grid.set(r,c, Grid.WALL)
                elif action == 'clear': self.grid.set(r,c, Grid.EMPTY)

            if event.type == pygame.MOUSEBUTTONDOWN and event.pos[0] < GRID_AREA_W:
                if event.button == 3:
                    cell = self._cell_at(*event.pos)
                    if cell: self.context_menu.show(*event.pos, cell, self.grid)
                elif event.button == 1: self.context_menu.hide()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.context_menu.hide()

    def _on_button(self, btn):
        if btn is self.btn_apply:
            self.in_rows._commit(); self.in_cols._commit()
            self.grid_rows, self.grid_cols = self.in_rows.val, self.in_cols.val
            self._recompute_layout()
            self.grid = Grid(self.grid_rows, self.grid_cols)
            self.searching  = False
            self.searcher   = None
            self.search_gen = None
            self.metrics.nodes_visited = self.metrics.path_cost = 0
            self.metrics.exec_time_ms  = 0; self.metrics.status = "IDLE"

        elif btn is self.btn_generate:
            self.grid.generate_random(self.sl_density.val/100)
            self.searching = False; self.searcher = None; self.search_gen = None; self.agent_moving = False; self.agent_pos = None; self.agent_path = []
            self.metrics.status = "IDLE"

        elif btn is self.btn_clear:
            self.grid = Grid(self.grid_rows, self.grid_cols)
            self.searching = False; self.searcher = None; self.search_gen = None; self.agent_moving = False; self.agent_pos = None; self.agent_path = []
            self.metrics.nodes_visited = self.metrics.path_cost = 0
            self.metrics.exec_time_ms  = 0; self.metrics.status = "IDLE"

        elif btn is self.btn_start:
            self._start_search()

        elif btn is self.btn_reset:
            self.grid.clear_path()
            self.searching = False; self.searcher = None; self.search_gen = None; self.agent_moving = False; self.agent_pos = None; self.agent_path = []
            self.metrics.nodes_visited = self.metrics.path_cost = 0
            self.metrics.exec_time_ms  = 0; self.metrics.status = "IDLE"
            self.btn_pause.active = False

    def _draw_open_dropdowns(self):
        """
        Draw the open dropdown item lists directly on self.screen so they
        always appear on top of every other widget (fixes z-order bug).
        Coordinates are shifted by GRID_AREA_W and adjusted for scroll.
        """
        for dd in self.all_dropdowns:
            if not dd.open:
                continue
            # Temporarily shift the dropdown rect into screen space
            ox = GRID_AREA_W
            oy = -self.scroll_y
            for i, opt in enumerate(dd.options):
                ir = pygame.Rect(
                    dd.rect.x + ox,
                    dd.rect.bottom + i * dd.rect.h + oy,
                    dd.rect.w,
                    dd.rect.h
                )
                bg = (40, 50, 75) if i == dd.hovered else (30, 36, 56)
                rrect(self.screen, bg, ir, r=4, bw=1,
                      bc=dd.color if i == dd.selected else dd.color)
                if dd.font:
                    t = dd.font.render(opt, True, dd.color if i == dd.selected else WHITE)
                    self.screen.blit(t, t.get_rect(midleft=(ir.x + 12, ir.centery)))

    def run(self):
        scan = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for y in range(0, SCREEN_H, 4):
            pygame.draw.line(scan, (0,0,0,18), (0,y), (SCREEN_W,y))
        while True:
            self._handle_events()
            self.frame_count += 1        # single increment drives all throttles
            self._search_step()
            self._agent_step()
            self._dynamic_step()
            self.screen.fill(BG)
            self._draw_grid()
            self._draw_panel()
            self.screen.blit(scan, (0,0))
            # Draw open dropdown lists directly on screen (fixes z-order)
            self._draw_open_dropdowns()
            self.context_menu.draw(self.screen, self.font)
            self.screen.blit(self.font.render("Dynamic Pathfinding Agent", True, DIM), (8, SCREEN_H-18))
            pygame.display.flip()
            self.clock.tick(FPS)


if __name__ == "__main__":
    PathfinderApp().run()