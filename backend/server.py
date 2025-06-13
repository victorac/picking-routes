from collections import defaultdict
from flask import Flask, request, jsonify
from flask_cors import CORS
import simpy

from simpy_order_generator import SimPyOrderGenerator
from utils import layout, shelves, solve_tsp, a_star_pathfinding, starting_point

app = Flask(__name__)
CORS(app)


@app.route("/api/solve", methods=["POST"])
def api_solve():
    data = request.get_json()
    pick_list = data.get("pick_list", [])

    locations = [starting_point] + [shelves[sku] for sku in pick_list if sku in shelves]
    if not locations:
        return jsonify({"error": "No valid SKUs found"}), 400

    ordered_indices = solve_tsp(locations)
    ordered_path = [locations[i] for i in ordered_indices]

    return jsonify({"path": ordered_path})


@app.route("/api/get-path", methods=["POST"])
def get_path():
    """New endpoint to get the actual walking path between two points"""
    data = request.get_json()
    start = data.get("start", [0, 0])
    goal = data.get("goal", [0, 0])

    path = a_star_pathfinding(start, goal, layout)

    return jsonify(
        {
            "path": path,
            "distance": len(path) - 1 if path else -1,
            "found": len(path) > 0,
        }
    )


@app.route("/api/solve-with-paths", methods=["POST"])
def api_solve_with_paths():
    """Enhanced solve endpoint that returns both optimal order and actual paths"""
    data = request.get_json()
    pick_list = data.get("pick_list", [])
    pick_list = ["sp"] + pick_list

    locations = [shelves[sku] for sku in pick_list if sku in shelves]
    if not locations:
        return jsonify({"error": "No valid SKUs found"}), 400

    # Get optimal order using TSP with pathfinding distances
    ordered_indices = solve_tsp(locations)
    ordered_locations = [locations[i] for i in ordered_indices]

    # Get actual walking paths between consecutive points
    walking_paths = []
    total_distance = 0

    for i in range(len(ordered_locations) - 1):
        start = ordered_locations[i]
        goal = ordered_locations[i + 1]
        path = a_star_pathfinding(start, goal, layout)

        walking_paths.append(
            {
                "from": start,
                "to": goal,
                "path": path,
                "distance": len(path) - 1 if path else 0,
            }
        )

        if path:
            total_distance += len(path) - 1

    return jsonify(
        {
            "optimal_order": ordered_locations,
            "walking_paths": walking_paths,
            "total_distance": total_distance,
            "pick_list_with_locations": [
                {"sku": pick_list[ordered_indices[i]], "location": ordered_locations[i]}
                for i in range(len(ordered_locations))
            ],
        }
    )


@app.route("/api/visualize-route", methods=["POST"])
def visualize_route():
    """Create a visualization-friendly representation of the route"""
    data = request.get_json()
    pick_list = data.get("pick_list", [])
    pick_list = ["sp"] + pick_list

    if not pick_list:
        return jsonify({"error": "Empty pick list"}), 400

    locations = [shelves[sku] for sku in pick_list if sku in shelves]
    if not locations:
        return jsonify({"error": "No valid SKUs found"}), 400

    # Get optimal route
    ordered_indices = solve_tsp(locations)
    ordered_locations = [locations[i] for i in ordered_indices]

    # Create a visual grid showing the route
    visual_grid = [row[:] for row in layout]  # Copy layout

    # Mark shelf locations
    for sku, location in shelves.items():
        if visual_grid[location[0]][location[1]] == 0:  # Only if walkable
            visual_grid[location[0]][location[1]] = 2  # 2 = shelf

    # Mark picked shelves and route
    route_points = []
    for i, location in enumerate(ordered_locations):
        visual_grid[location[0]][location[1]] = 3 + i  # 3+ = picked shelf (numbered)

        route_points.append(
            {"position": location, "order": i, "sku": pick_list[ordered_indices[i]]}
        )

    # Mark the walking path
    all_path_points = set()
    all_path = []
    for i in range(len(ordered_locations) - 1):
        path = a_star_pathfinding(
            ordered_locations[i], ordered_locations[i + 1], layout
        )
        for point in path:
            all_path_points.add(tuple(point))
            all_path.append(tuple(point))

    path_len = len(all_path)
    direction_grid = defaultdict(list)
    for i, point in enumerate(all_path):
        if (i + 1) < path_len:
            next_point = all_path[i + 1]
            direction = "down"
            if next_point[0] - point[0] < 0:
                direction = "up"
            elif next_point[1] - point[1] < 0:
                direction = "left"
            elif next_point[1] - point[1] > 0:
                direction = "right"
            print(point, next_point)
            direction_grid[f"{point[0]},{point[1]}"].append(direction)

    # Mark path points (but don't overwrite shelves)
    for i, point in enumerate(all_path_points):
        if visual_grid[point[0]][point[1]] == 0:  # Only walkable areas
            visual_grid[point[0]][point[1]] = -1  # -1 = path

    return jsonify(
        {
            "visual_grid": visual_grid,
            "route_points": route_points,
            "directions": direction_grid,
            "legend": {
                "0": "walkable",
                "1": "blocked",
                "2": "shelf (not picked)",
                "-1": "walking path",
                "3+": "picked shelf (numbered by visit order)",
            },
        }
    )


@app.route("/api/layout", methods=["GET"])
def get_layout():
    return jsonify(
        {
            "layout": layout,
            "shelves": shelves,
            "dimensions": {"rows": len(layout), "cols": len(layout[0])},
        }
    )


@app.route("/api/simulate-orders", methods=["POST"])
def simulate_orders():
    data = request.get_json()

    # Simulation parameters
    duration_hours = data.get("duration_hours", 8)
    process_type = data.get("process_type", "poisson")

    # Create new environment for each simulation
    env = simpy.Environment()
    generator = SimPyOrderGenerator(shelves, env)

    # Process-specific parameters
    sim_params = {
        "poisson": {
            "arrival_rate": data.get("arrival_rate", 5.0),
            "mean_items": data.get("mean_items", 3),
            "std_items": data.get("std_items", 1.5),
        },
        "batch": {
            "batch_rate": data.get("batch_rate", 2.0),
            "batch_size_mean": data.get("batch_size_mean", 3),
            "batch_size_std": data.get("batch_size_std", 1),
            "order_mean_items": data.get("order_mean_items", 3),
            "order_std_items": data.get("order_std_items", 1.5),
        },
        "time_varying": {
            "base_rate": data.get("base_rate", 3.0),
            "mean_items": data.get("mean_items", 3),
            "std_items": data.get("std_items", 1.5),
        },
        "peak_hours": {
            "peak_hours": data.get("peak_hours", [9, 11, 14, 16]),
            "peak_rate": data.get("peak_rate", 10.0),
            "normal_rate": data.get("normal_rate", 2.0),
            "peak_duration": data.get("peak_duration", 60),
        },
    }

    if process_type not in sim_params:
        return jsonify({"error": f"Unknown process type: {process_type}"}), 400

    # Run simulation
    try:
        orders = generator.run_simulation(
            duration_hours=duration_hours,
            process_type=process_type,
            **sim_params[process_type],
        )

        stats = generator.get_statistics()

        return jsonify(
            {
                "orders": orders,
                "statistics": stats,
                "simulation_parameters": {
                    "duration_hours": duration_hours,
                    "process_type": process_type,
                    **sim_params[process_type],
                },
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
