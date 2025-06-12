# warehouse_pick_optimizer/app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
from ortools.constraint_solver import routing_enums_pb2, pywrapcp
import numpy as np
import json

app = Flask(__name__)
CORS(app)

# Sample warehouse layout (0 = walkable, 1 = blocked)
layout = [[0 for _ in range(10)] for _ in range(20)]

# Sample shelf locations
shelves = {
    "A1": [2, 3],
    "B4": [5, 6],
    "C2": [2, 10],
    "D8": [8, 12],
    "E3": [1, 17]
}


def create_distance_matrix(locations):
    def euclidean(a, b):
        return np.linalg.norm(np.array(a) - np.array(b))
    return [[euclidean(a, b) for b in locations] for a in locations]


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
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

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


@app.route("/api/solve", methods=["POST"])
def api_solve():
    data = request.get_json()
    pick_list = data.get("pick_list", [])

    locations = [shelves[sku] for sku in pick_list if sku in shelves]
    if not locations:
        return jsonify({"error": "No valid SKUs found"}), 400

    ordered_indices = solve_tsp(locations)
    ordered_path = [locations[i] for i in ordered_indices]

    return jsonify({"path": ordered_path})


@app.route("/api/layout", methods=["GET"])
def get_layout():
    return jsonify({"layout": layout, "shelves": shelves})


if __name__ == "__main__":
    app.run(debug=True)
