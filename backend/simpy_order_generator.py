import simpy
import numpy as np


class SimPyOrderGenerator:
    def __init__(self, shelves, env=None):
        self.shelves = list(shelves.keys())
        self.shelf_popularity = self._initialize_shelf_popularity()
        self.env = env or simpy.Environment()
        self.orders = []
        self.order_counter = 0
        
    def _initialize_shelf_popularity(self):
        """Initialize shelf popularity weights"""
        weights = np.random.exponential(scale=2, size=len(self.shelves))
        weights = weights / weights.sum()
        return dict(zip(self.shelves, weights))
    
    def order_arrival_process(self, arrival_rate=5.0, mean_items=3, std_items=1.5):
        """
        Poisson arrival process for orders
        
        Args:
            arrival_rate: Average orders per hour (lambda for Poisson process)
            mean_items: Average items per order
            std_items: Standard deviation for items per order
        """
        while True:
            # Inter-arrival time follows exponential distribution (Poisson process)
            inter_arrival_time = np.random.exponential(1.0 / arrival_rate) * 60  # Convert to minutes
            
            yield self.env.timeout(inter_arrival_time)
            
            # Generate order
            order = self._generate_order(mean_items, std_items)
            order['arrival_time'] = self.env.now
            order['arrival_time_formatted'] = self._format_simulation_time(self.env.now)
            
            self.orders.append(order)
            print(f"Time {self.env.now:.1f}: Order {order['order_id']} arrived with {len(order['pick_list'])} items")
    
    def batch_arrival_process(self, batch_rate=2.0, batch_size_mean=3, batch_size_std=1, 
                            order_mean_items=3, order_std_items=1.5):
        """
        Batch arrival process - orders arrive in groups (common in B2B scenarios)
        
        Args:
            batch_rate: Average batches per hour
            batch_size_mean: Average orders per batch
            batch_size_std: Standard deviation of batch size
        """
        while True:
            # Time between batches
            inter_batch_time = np.random.exponential(1.0 / batch_rate) * 60
            yield self.env.timeout(inter_batch_time)
            
            # Generate batch size
            batch_size = max(1, int(np.random.normal(batch_size_mean, batch_size_std)))
            
            print(f"Time {self.env.now:.1f}: Batch of {batch_size} orders arriving")
            
            # Generate orders in the batch with small delays between them
            for i in range(batch_size):
                if i > 0:
                    yield self.env.timeout(np.random.uniform(0.1, 2.0))  # Small delay between orders
                
                order = self._generate_order(order_mean_items, order_std_items)
                order['arrival_time'] = self.env.now
                order['arrival_time_formatted'] = self._format_simulation_time(self.env.now)
                order['batch_id'] = f"BATCH-{int(self.env.now)}"
                
                self.orders.append(order)
    
    def time_varying_arrival_process(self, base_rate=3.0, mean_items=3, std_items=1.5):
        """
        Time-varying arrival process that changes throughout the day
        """
        while True:
            # Get current hour of simulation (assuming simulation starts at midnight)
            current_hour = (self.env.now / 60) % 24
            
            # Time-dependent arrival rate
            time_multiplier = self._get_time_multiplier(current_hour)
            current_rate = base_rate * time_multiplier
            
            # Inter-arrival time based on current rate
            inter_arrival_time = np.random.exponential(1.0 / current_rate) * 60
            
            yield self.env.timeout(inter_arrival_time)
            
            order = self._generate_order(mean_items, std_items)
            order['arrival_time'] = self.env.now
            order['arrival_time_formatted'] = self._format_simulation_time(self.env.now)
            order['hour_of_day'] = int(current_hour)
            
            self.orders.append(order)
    
    def peak_hours_process(self, peak_hours=[9, 11, 14, 16], peak_rate=10.0, 
                          normal_rate=2.0, peak_duration=60):
        """
        Simulate peak hours with higher order rates
        
        Args:
            peak_hours: Hours when peaks occur
            peak_rate: Orders per hour during peaks
            normal_rate: Orders per hour during normal times
            peak_duration: Duration of each peak in minutes
        """
        peak_events = []
        
        # Schedule peak events
        for day in range(7):  # Simulate a week
            for hour in peak_hours:
                peak_start = (day * 24 + hour) * 60  # Convert to minutes
                peak_events.append(peak_start)
        
        peak_events.sort()
        
        current_rate = normal_rate
        next_peak_idx = 0
        
        while True:
            # Check if we need to change rate
            if (next_peak_idx < len(peak_events) and 
                self.env.now >= peak_events[next_peak_idx]):
                
                if current_rate == normal_rate:
                    current_rate = peak_rate
                    print(f"Time {self.env.now:.1f}: PEAK PERIOD STARTED - Rate: {current_rate}/hour")
                    self.env.process(self._end_peak(peak_duration, normal_rate))
                
                next_peak_idx += 1
            
            # Generate next order
            inter_arrival_time = np.random.exponential(1.0 / current_rate) * 60
            yield self.env.timeout(inter_arrival_time)
            
            order = self._generate_order()
            order['arrival_time'] = self.env.now
            order['arrival_time_formatted'] = self._format_simulation_time(self.env.now)
            order['rate_period'] = 'peak' if current_rate == peak_rate else 'normal'
            
            self.orders.append(order)
    
    def _end_peak(self, duration, normal_rate):
        """Helper process to end peak period"""
        yield self.env.timeout(duration)
        print(f"Time {self.env.now:.1f}: Peak period ended - Rate: {normal_rate}/hour")
    
    def _generate_order(self, mean_items=3, std_items=1.5, min_items=1, max_items=8):
        """Generate a single order"""
        self.order_counter += 1
        
        num_items = int(np.random.normal(mean_items, std_items))
        num_items = max(min_items, min(max_items, num_items))
        
        selected_shelves = np.random.choice(
            self.shelves,
            size=min(num_items, len(self.shelves)),
            replace=False,
            p=list(self.shelf_popularity.values())
        )
        
        return {
            "order_id": f"SIM-{self.order_counter:06d}",
            "pick_list": selected_shelves.tolist(),
            "num_items": len(selected_shelves),
            "simulation_id": id(self.env)
        }
    
    def _get_time_multiplier(self, hour):
        """Time-dependent multiplier for arrival rates"""
        if 9 <= hour <= 17:  # Business hours
            return 2.0
        elif 6 <= hour <= 8 or 18 <= hour <= 20:  # Shoulder hours
            return 1.2
        elif 21 <= hour <= 23:  # Evening
            return 0.5
        else:  # Night/early morning
            return 0.2
    
    def _format_simulation_time(self, sim_time):
        """Format simulation time as readable timestamp"""
        hours = int(sim_time // 60)
        minutes = int(sim_time % 60)
        return f"Day {hours // 24}, {hours % 24:02d}:{minutes:02d}"
    
    def run_simulation(self, duration_hours=24, process_type='poisson', **kwargs):
        """
        Run the simulation
        
        Args:
            duration_hours: How long to simulate (in hours)
            process_type: 'poisson', 'batch', 'time_varying', or 'peak_hours'
            **kwargs: Parameters for the chosen process
        """
        duration_minutes = duration_hours * 60
        
        # Start the appropriate process
        if process_type == 'poisson':
            self.env.process(self.order_arrival_process(**kwargs))
        elif process_type == 'batch':
            self.env.process(self.batch_arrival_process(**kwargs))
        elif process_type == 'time_varying':
            self.env.process(self.time_varying_arrival_process(**kwargs))
        elif process_type == 'peak_hours':
            self.env.process(self.peak_hours_process(**kwargs))
        else:
            raise ValueError(f"Unknown process type: {process_type}")
        
        # Run simulation
        print(f"Starting {process_type} simulation for {duration_hours} hours...")
        self.env.run(until=duration_minutes)
        print(f"Simulation completed. Generated {len(self.orders)} orders.")
        
        return self.orders
    
    def get_statistics(self):
        """Get detailed statistics about the simulation"""
        if not self.orders:
            return {}
        
        num_items = [order["num_items"] for order in self.orders]
        arrival_times = [order["arrival_time"] for order in self.orders]
        
        # Calculate inter-arrival times
        inter_arrivals = [arrival_times[i] - arrival_times[i-1] 
                         for i in range(1, len(arrival_times))]
        
        # Shelf popularity
        shelf_counts = {}
        for order in self.orders:
            for shelf in order["pick_list"]:
                shelf_counts[shelf] = shelf_counts.get(shelf, 0) + 1
        
        # Orders per hour analysis
        orders_by_hour = {}
        for order in self.orders:
            hour = int(order["arrival_time"] // 60)
            orders_by_hour[hour] = orders_by_hour.get(hour, 0) + 1
        
        return {
            "total_orders": len(self.orders),
            "simulation_duration_hours": max(arrival_times) / 60 if arrival_times else 0,
            "avg_orders_per_hour": len(self.orders) / (max(arrival_times) / 60) if arrival_times else 0,
            "avg_items_per_order": np.mean(num_items),
            "std_items_per_order": np.std(num_items),
            "avg_inter_arrival_time_minutes": np.mean(inter_arrivals) if inter_arrivals else 0,
            "std_inter_arrival_time_minutes": np.std(inter_arrivals) if inter_arrivals else 0,
            "most_popular_shelves": sorted(shelf_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "orders_by_hour": dict(sorted(orders_by_hour.items())),
            "first_order_time": self.orders[0]["arrival_time_formatted"] if self.orders else None,
            "last_order_time": self.orders[-1]["arrival_time_formatted"] if self.orders else None
        }


def demo_simulations():
    """Demonstrate different simulation types"""
    from utils import shelves
    
    print("=== SimPy Order Generation Demo ===\n")
    
    # 1. Basic Poisson Process
    print("1. Poisson Process (5 orders/hour average)")
    env1 = simpy.Environment()
    generator1 = SimPyOrderGenerator(shelves, env1)
    orders1 = generator1.run_simulation(duration_hours=8, process_type='poisson', arrival_rate=5.0)
    stats1 = generator1.get_statistics()
    print(f"Generated {stats1['total_orders']} orders, avg rate: {stats1['avg_orders_per_hour']:.2f}/hour\n")
    
    # 2. Batch Arrivals
    print("2. Batch Arrival Process")
    env2 = simpy.Environment()
    generator2 = SimPyOrderGenerator(shelves, env2)
    orders2 = generator2.run_simulation(duration_hours=8, process_type='batch', 
                                       batch_rate=2.0, batch_size_mean=4)
    stats2 = generator2.get_statistics()
    print(f"Generated {stats2['total_orders']} orders in batches\n")
    
    # 3. Time-varying arrivals
    print("3. Time-varying Arrival Process")
    env3 = simpy.Environment()
    generator3 = SimPyOrderGenerator(shelves, env3)
    orders3 = generator3.run_simulation(duration_hours=24, process_type='time_varying', base_rate=3.0)
    stats3 = generator3.get_statistics()
    print(f"Generated {stats3['total_orders']} orders with time-varying rates")
    print("Orders by hour:", {k: v for k, v in list(stats3['orders_by_hour'].items())[:12]})

if __name__ == "__main__":
    demo_simulations()