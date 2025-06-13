# Warehouse Picking Optimization System

A warehouse picking route optimization system that uses the Traveling Salesman Problem (TSP) with A\* pathfinding to find the most efficient picking routes while respecting warehouse layout constraints.

## 🚀 Features

- **Layout-Aware TSP Optimization**: Routes consider actual warehouse obstacles (walls, aisles, blocked areas)
- **A\* Pathfinding**: Finds realistic walking paths between shelves
- **SimPy Order Generation**: Realistic order simulation with multiple arrival patterns
- **Real-time Visualization**: Interactive route visualization with direction indicators
- **Multiple Optimization Strategies**: Compare Euclidean vs pathfinding-based optimization
- **RESTful API**: Complete backend API for integration

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐
│    Frontend     │    │     Backend     │
│   (React/Vue)   │◄──►│     (Flask)     │
│                 │    │                 │
│ • Route Viz     │    │ • TSP Solver    │
│ • Order Input   │    │ • A* Pathfind   │
│ • Statistics    │    │ • SimPy Orders  │
└─────────────────┘    └─────────────────┘
                              │
                       ┌─────────────────┐
                       │   OR-Tools TSP  │
                       │   A* Algorithm  │
                       │   SimPy Events  │
                       └─────────────────┘
```

## 🛠️ Tech Stack

### Backend

- **Flask** - Web framework
- **OR-Tools** - Google's optimization library for TSP solving
- **SimPy** - Discrete event simulation for order generation
- **NumPy** - Numerical computations
- **A\* Algorithm** - Pathfinding with obstacle avoidance

### Frontend

- **Node.js** - Runtime environment
- **Vite** - Build tool and dev server
- **Modern JavaScript/TypeScript** - Frontend framework

### Infrastructure

- **Docker** - Containerization
- **Docker Compose** - Multi-service orchestration
- **Nginx** - Reverse proxy and static file serving

## 📦 Installation & Setup

### Prerequisites

- Docker & Docker Compose
- Git

### Quick Start

1. **Clone the repository**

   ```bash
   git clone https://github.com/victorac/picking-routes.git
   cd picking
   ```

2. **Run with Docker Compose (Development)**

   ```bash
   docker compose up --build
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000

### Manual Setup

#### Backend Setup

```bash
cd backend
poetry install
poetry run python server.py
```

#### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## 🎯 Usage

### API Endpoints

#### Order Optimization

```bash
# Basic TSP optimization
POST /api/solve
{
  "pick_list": ["A1", "B2", "C3"]
}

# Optimization with walking paths
POST /api/solve-with-paths
{
  "pick_list": ["A1", "B2", "C3"]
}
```

#### Route Visualization

```bash
# Get visualization data
POST /api/visualize-route
{
  "pick_list": ["A1", "B2", "C3"]
}
```

#### Order Simulation

```bash
# Generate orders using SimPy
POST /api/simulate-orders
{
  "duration_hours": 8,
  "process_type": "poisson",
  "arrival_rate": 5.0
}
```

#### Analysis & Debugging

```bash
# Compare optimization methods
POST /api/compare-optimizations
{
  "pick_list": ["A1", "B2", "C3"]
}

# Debug distance matrices
POST /api/debug-distances
{
  "pick_list": ["A1", "B2", "C3"]
}
```

### Example Pick Lists

```javascript
// Small order
["A1", "B2", "C1"][
  // Medium order
  ("A1", "A3", "B2", "B4", "C1", "D2")
][
  // Large order
  ("A1", "A2", "A3", "B1", "B2", "C1", "C2", "D1", "D2", "E1")
];
```

## 🏭 Warehouse Layout

The system uses a 10x20 grid warehouse layout:

```
Legend:
0 = Walkable space
1 = Blocked (walls, equipment)
2 = Shelf locations
```

### Shelf Locations

- **Section A**: A1-A6 (Left side)
- **Section B**: B1-B5 (Middle left)
- **Section C**: C1-C2 (Middle right)
- **Section D**: D1-D4 (Lower left)
- **Section E**: E1-E2 (Lower right)

## 🧮 Algorithms

### TSP Optimization

- **Solver**: Google OR-Tools with constraint programming
- **Distance Matrix**: A\* pathfinding distances (not Euclidean)
- **Strategy**: PATH_CHEAPEST_ARC with local search improvements

### A\* Pathfinding

- **Heuristic**: Manhattan distance
- **Movement**: 4-directional (up, down, left, right)
- **Obstacles**: Respects warehouse layout constraints

### Order Generation

- **Poisson Process**: Random arrivals with exponential inter-arrival times
- **Batch Arrivals**: Orders arrive in groups
- **Time-varying**: Arrival rates change throughout the day
- **Peak Hours**: Simulates rush periods

## 🔬 Performance Analysis

### Optimization Comparison

The system can compare different optimization approaches:

1. **Euclidean Distance**: Straight-line distances (unrealistic)
2. **Pathfinding Distance**: Actual walking distances (realistic)

Typical improvements with pathfinding-based optimization:

- **10-30% reduction** in total walking distance
- **Better route feasibility** (no walking through walls)
- **More realistic time estimates**

### Simulation Results

Order generation patterns:

```
Poisson Process (λ=5/hour):
- Average inter-arrival: 12 minutes
- Coefficient of variation: 1.0

Time-varying Process:
- Peak hours: 2x normal rate
- Off-hours: 0.3x normal rate
```

## 🐳 Docker Commands

```bash
# Development with hot reload
docker-compose -f docker-compose.yml up --build

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop services
docker-compose down

# Rebuild specific service
docker-compose build backend
```

## 📊 Configuration

### Environment Variables

#### Backend

```bash
FLASK_ENV=development          # Flask environment
FLASK_DEBUG=1                  # Enable debug mode
PYTHONPATH=/app               # Python path
```

#### Frontend

```bash
VITE_API_URL=http://localhost:5000  # Backend API URL
```

### Warehouse Configuration

Modify warehouse layout in `backend/utils.py`:

```python
# Customize warehouse dimensions
layout = [[0 for _ in range(WIDTH)] for _ in range(HEIGHT)]

# Add blocked areas
layout[row][col] = 1  # Block specific cells

# Define shelf locations
shelves = {
    "A1": [row, col],
    "A2": [row, col],
    # ...
}
```

## 🧪 Testing

### API Testing

```bash
# Test basic optimization
curl -X POST http://localhost:5000/api/solve \
  -H "Content-Type: application/json" \
  -d '{"pick_list": ["A1", "B2", "C1"]}'

# Test order simulation
curl -X POST http://localhost:5000/api/simulate-orders \
  -H "Content-Type: application/json" \
  -d '{"duration_hours": 2, "process_type": "poisson", "arrival_rate": 3.0}'
```

### Performance Testing

```bash
# Generate large order for testing
curl -X POST http://localhost:5000/api/solve \
  -H "Content-Type: application/json" \
  -d '{"pick_list": ["A1","A2","A3","B1","B2","B3","C1","C2","D1","D2","E1","E2"]}'
```

## 📈 Future Enhancements

- [ ] **Multi-picker optimization** (Vehicle Routing Problem)
- [ ] **Time windows** for shelf availability
- [ ] **Capacity constraints** for picking carts
- [ ] **Real-time order updates** with WebSocket
- [ ] **Machine learning** for demand prediction
- [ ] **3D warehouse** support (multiple floors)
- [ ] **Pick density optimization** (item grouping)
- [ ] **Integration APIs** for WMS systems
