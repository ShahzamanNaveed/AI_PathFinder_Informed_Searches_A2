import heapq
from heuristics import manhattan, euclidean


class AStarSearch:
    """
    A* Search: f(n) = g(n) + h(n)
    Uses a generator to yield one step at a time so the GUI
    can animate frontier / visited nodes frame by frame.
    """

    def __init__(self, grid, start, goal, heuristic="manhattan"):
        self.grid      = grid
        self.start     = start
        self.goal      = goal
        self.heuristic = manhattan if heuristic == "manhattan" else euclidean

        # Search state
        self.open_set  = []          # min-heap: (f, g, node)
        self.came_from = {}          # node -> parent node
        self.g_score   = {}          # node -> best g cost so far
        self.visited   = set()       # fully expanded nodes
        self.frontier  = set()       # nodes currently in open_set

        self.done      = False
        self.path      = []
        self.nodes_visited = 0

        # Initialise with start node
        g = 0
        h = self.heuristic(start, goal)
        f = g + h
        heapq.heappush(self.open_set, (f, g, start))
        self.g_score[start] = g
        self.frontier.add(start)

    # ------------------------------------------------------------------
    # Generator — call next() each frame from the GUI
    # Yields a dict describing what changed this step so the GUI can
    # update only the relevant cells instead of redrawing everything.
    # ------------------------------------------------------------------
    def step(self):
        """
        Each call to next() on this generator performs ONE expansion.

        Yields:
            {
                "type"    : "step" | "found" | "no_path",
                "current" : (r, c),          # node being expanded
                "visited" : set of (r,c),    # all expanded so far
                "frontier": set of (r,c),    # all nodes in open set
                "path"    : [(r,c), ...]     # only on "found"
            }
        """
        while self.open_set:
            _, g_cur, current = heapq.heappop(self.open_set)
            self.frontier.discard(current)

            # Skip stale entries (node was re-added with better g)
            if current in self.visited:
                continue

            self.visited.add(current)
            self.nodes_visited += 1

            # Goal reached
            if current == self.goal:
                self.path = self._reconstruct_path()
                self.done = True
                yield {
                    "type"    : "found",
                    "current" : current,
                    "visited" : self.visited,
                    "frontier": self.frontier,
                    "path"    : self.path
                }
                return

            # Expand neighbours
            for neighbour in self._neighbours(current):
                if neighbour in self.visited:
                    continue

                tentative_g = g_cur + 1   # uniform cost (each step = 1)

                if tentative_g < self.g_score.get(neighbour, float("inf")):
                    self.came_from[neighbour] = current
                    self.g_score[neighbour]   = tentative_g
                    h = self.heuristic(neighbour, self.goal)
                    f = tentative_g + h
                    heapq.heappush(self.open_set, (f, tentative_g, neighbour))
                    self.frontier.add(neighbour)

            yield {
                "type"    : "step",
                "current" : current,
                "visited" : self.visited,
                "frontier": self.frontier,
                "path"    : []
            }

        # Open set exhausted — no path exists
        self.done = True
        yield {
            "type"    : "no_path",
            "current" : None,
            "visited" : self.visited,
            "frontier": self.frontier,
            "path"    : []
        }

    # ------------------------------------------------------------------
    # Re-planning support
    # ------------------------------------------------------------------
    def notify_wall_added(self, cell):
        """
        Called by dynamic mode when a new wall is placed.
        If the wall is on the current path, signals that re-planning
        is needed. Returns True if a replan is required.
        """
        return cell in set(self.path)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _neighbours(self, node):
        """4-directional movement (no diagonals)."""
        r, c = node
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < self.grid.rows and 0 <= nc < self.grid.cols:
                if self.grid.cells[nr][nc] not in (1,):   # 1 = WALL
                    yield (nr, nc)

    def _reconstruct_path(self):
        path, node = [], self.goal
        while node in self.came_from:
            path.append(node)
            node = self.came_from[node]
        path.append(self.start)
        path.reverse()
        return path