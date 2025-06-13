from collections import deque
from ortools.constraint_solver import routing_enums_pb2, pywrapcp

# Sample warehouse layout (0 = walkable, 1 = blocked)
# Let's make it more realistic with some blocked areas
layout = [[0 for _ in range(20)] for _ in range(10)]

starting_point = [9, 10]

for j in range(2, 18):
    layout[1][j] = 1  # Horizontal wall/aisle
    layout[3][j] = 1  # Another horizontal wall/aisle
    layout[5][j] = 1  # Another horizontal wall/aisle
    layout[7][j] = 1  # Another horizontal wall/aisle


# Add some blocked areas (aisles, walls, equipment)
for i in range(10):
    layout[i][0] = 1  # Vertical wall/aisle
    layout[i][19] = 1  # Another vertical wall/aisle


# # Add some openings in the walls
layout[7][10] = 0
layout[3][10] = 0


# Sample shelf locations - adjusted to be in walkable areas
shelves = {
    "start": starting_point,
    "A1": [0, 1],
    "A2": [1, 1],
    "A3": [2, 1],
    "A4": [3, 1],
    "A5": [4, 1],
    "A6": [5, 1],
    "A7": [6, 1],
    "A8": [7, 1],
    "A9": [8, 1],
    "A10": [9, 1],
    "B1": [0, 3],
    "B2": [0, 4],
    "B3": [0, 5],
    "B4": [0, 6],
    "B5": [0, 7],
    "B6": [0, 8],
    "B7": [0, 9],
    "B8": [0, 10],
    "B9": [0, 11],
    "B10": [0, 12],
    "C1": [4, 11],
    "C2": [4, 12],
    "C3": [4, 13],
    "C4": [4, 14],
    "C5": [4, 15],
    "C6": [4, 16],
    "D1": [8, 3],
    "D2": [8, 4],
    "D3": [8, 5],
    "D4": [8, 6],
    "E1": [0, 18],
    "E2": [1, 18],
    "E3": [2, 18],
    "E4": [3, 18],
    "E5": [4, 18],
    "E6": [5, 18],
    "E7": [6, 18],
    "E8": [7, 18],
    "E9": [8, 18],
    "E10": [9, 18],
}


def a_star_pathfinding(start, goal, layout):
    """
    A* pathfinding algorithm to find shortest path considering obstacles

    Args:
        start: [row, col] starting position
        goal: [row, col] goal position
        layout: 2D array where 0 = walkable, 1 = blocked

    Returns:
        List of [row, col] coordinates representing the path, or empty list if no path
    """
    rows, cols = len(layout), len(layout[0])

    # Convert to tuple for hashing
    start = tuple(start)
    goal = tuple(goal)

    if start == goal:
        return [list(start)]

    # Check if start and goal are valid and walkable
    if (
        start[0] < 0
        or start[0] >= rows
        or start[1] < 0
        or start[1] >= cols
        or goal[0] < 0
        or goal[0] >= rows
        or goal[1] < 0
        or goal[1] >= cols
        or layout[start[0]][start[1]] == 1
        or layout[goal[0]][goal[1]] == 1
    ):
        return []

    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])  # Manhattan distance

    def get_neighbors(pos):
        row, col = pos
        neighbors = []
        # 4-directional movement (can be changed to 8-directional if needed)
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            new_row, new_col = row + dr, col + dc
            if (
                0 <= new_row < rows
                and 0 <= new_col < cols
                and layout[new_row][new_col] == 0
            ):
                neighbors.append((new_row, new_col))
        return neighbors

    # A* algorithm
    open_set = [(0, start)]
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}

    import heapq

    while open_set:
        current = heapq.heappop(open_set)[1]

        if current == goal:
            # Reconstruct path
            path = []
            while current in came_from:
                path.append(list(current))
                current = came_from[current]
            path.append(list(start))
            return path[::-1]  # Reverse to get start-to-goal path

        for neighbor in get_neighbors(current):
            tentative_g_score = g_score[current] + 1

            if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))

    return []  # No path found


def create_distance_matrix_with_pathfinding(locations):
    """
    Create distance matrix using A* pathfinding that respects warehouse layout
    """

    def path_distance(start, goal):
        path = a_star_pathfinding(start, goal, layout)
        if not path:
            # If no path found, use large penalty distance
            return float("inf")
        return len(path) - 1  # Number of steps in the path

    return [[path_distance(a, b) for b in locations] for a in locations]


def create_distance_matrix(locations):
    """Updated distance matrix function that uses pathfinding"""
    return create_distance_matrix_with_pathfinding(locations)


# def create_distance_matrix(locations):
#     def euclidean(a, b):
#         return np.linalg.norm(np.array(a) - np.array(b))

#     return [[euclidean(a, b) for b in locations] for a in locations]


def solve_tsp(locations):
    dist_matrix = create_distance_matrix(locations)
    manager = pywrapcp.RoutingIndexManager(len(dist_matrix), 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(i, j):
        return int(dist_matrix[manager.IndexToNode(i)][manager.IndexToNode(j)] * 100)

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    solution = routing.SolveWithParameters(search_parameters)

    if not solution:
        return []

    index = routing.Start(0)
    path = []
    while not routing.IsEnd(index):
        path.append(manager.IndexToNode(index))
        index = solution.Value(routing.NextVar(index))
    path.append(manager.IndexToNode(index))
    return path
