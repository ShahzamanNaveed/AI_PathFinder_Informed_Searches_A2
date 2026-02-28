import heapq
from heuristics import manhattan, euclidean


class GBFSearch:
    """
    Greedy Best-First Search: f(n) = h(n)
    Only uses the heuristic — ignores path cost g(n).
    Faster than A* but not guaranteed to find the optimal path.
    Uses a generator to yield one step at a time for GUI animation.
    """

    def __init__(self, grid, start, goal, heuristic="manhattan"):
        self.grid      = grid
        self.start     = start
        self.goal      = goal
        self.heuristic = manhattan if heuristic == "manhattan" else euclidean

        # Search state
        self.open_set  = []          # min-heap: (h, node)
        self.came_from = {}          # node -> parent node
        self.visited   = set()       # fully expanded nodes
        self.frontier  = set()       # nodes currently in open_set

        self.done      = False
        self.path      = []
        self.nodes_visited = 0

        # Initialise with start node
        h = self.heuristic(start, goal)
        heapq.heappush(self.open_set, (h, start))
        self.frontier.add(start)

    # ------------------------------------------------------------------
    # Generator — call next() each frame from the GUI
    # ------------------------------------------------------------------
    def step(self):
        """
        Each call to next() on this generator performs ONE expansion.

        Yields:
            {
                "type"    : "step" | "found" | "no_path",
                "current" : (r, c),
                "visited" : set of (r,c),
                "frontier": set of (r,c),
                "path"    : [(r,c), ...]     # only on "found"
            }
        """
        while self.open_set:
            _, current = heapq.heappop(self.open_set)
            self.frontier.discard(current)

            # Skip stale entries
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
                if neighbour in self.visited or neighbour in self.frontier:
                    continue

                self.came_from[neighbour] = current
                h = self.heuristic(neighbour, self.goal)
                heapq.heappush(self.open_set, (h, neighbour))
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
        Returns True if the wall lands on the current path,
        meaning a replan is required.
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