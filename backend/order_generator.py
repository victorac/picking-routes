import numpy as np
import random
from datetime import datetime, timedelta

class OrderGenerator:
    def __init__(self, shelves):
        self.shelves = list(shelves.keys())
        self.shelf_popularity = self._initialize_shelf_popularity()
    
    def _initialize_shelf_popularity(self):
        """Initialize shelf popularity weights (some shelves are picked more often)"""
        # Create a realistic distribution where some shelves are more popular
        weights = np.random.exponential(scale=2, size=len(self.shelves))
        weights = weights / weights.sum()  # Normalize to probabilities
        return dict(zip(self.shelves, weights))
    
    def generate_single_order(self, mean_items=3, std_items=1.5, min_items=1, max_items=8):
        """
        Generate a single order with normally distributed number of items
        
        Args:
            mean_items: Average number of items per order
            std_items: Standard deviation for number of items
            min_items: Minimum items per order
            max_items: Maximum items per order
        """
        # Generate number of items following normal distribution
        num_items = int(np.random.normal(mean_items, std_items))
        num_items = max(min_items, min(max_items, num_items))
        
        # Select shelves based on popularity weights
        selected_shelves = np.random.choice(
            self.shelves, 
            size=min(num_items, len(self.shelves)), 
            replace=False,
            p=list(self.shelf_popularity.values())
        )
        
        return {
            "order_id": self._generate_order_id(),
            "pick_list": selected_shelves.tolist(),
            "timestamp": datetime.now().isoformat(),
            "num_items": len(selected_shelves)
        }
    
    def generate_orders_batch(self, num_orders=10, **kwargs):
        """Generate multiple orders"""
        return [self.generate_single_order(**kwargs) for _ in range(num_orders)]
    
    def generate_time_based_orders(self, hours=24, orders_per_hour_mean=5, orders_per_hour_std=2):
        """
        Generate orders over a time period with varying intensity
        
        Args:
            hours: Time period in hours
            orders_per_hour_mean: Average orders per hour
            orders_per_hour_std: Standard deviation for orders per hour
        """
        orders = []
        start_time = datetime.now()
        
        for hour in range(hours):
            # Vary order intensity throughout the day (more orders during business hours)
            time_multiplier = self._get_time_multiplier(hour)
            adjusted_mean = orders_per_hour_mean * time_multiplier
            
            # Generate number of orders for this hour (normal distribution)
            orders_this_hour = max(0, int(np.random.normal(adjusted_mean, orders_per_hour_std)))
            
            for order_num in range(orders_this_hour):
                # Distribute orders randomly within the hour
                minutes_offset = random.randint(0, 59)
                order_time = start_time + timedelta(hours=hour, minutes=minutes_offset)
                
                order = self.generate_single_order()
                order["timestamp"] = order_time.isoformat()
                order["hour"] = hour
                orders.append(order)
        
        return sorted(orders, key=lambda x: x["timestamp"])
    
    def _get_time_multiplier(self, hour):
        """Simulate realistic order patterns throughout the day"""
        # Business hours (9 AM - 5 PM) have more orders
        if 9 <= hour <= 17:
            return 1.5
        elif 6 <= hour <= 8 or 18 <= hour <= 20:
            return 0.8
        else:
            return 0.3
    
    def _generate_order_id(self):
        """Generate a unique order ID"""
        timestamp = int(datetime.now().timestamp() * 1000)
        random_suffix = random.randint(100, 999)
        return f"ORD-{timestamp}-{random_suffix}"
    
    def get_statistics(self, orders):
        """Get statistics about generated orders"""
        if not orders:
            return {}
        
        num_items = [order["num_items"] for order in orders]
        shelf_counts = {}
        
        for order in orders:
            for shelf in order["pick_list"]:
                shelf_counts[shelf] = shelf_counts.get(shelf, 0) + 1
        
        return {
            "total_orders": len(orders),
            "avg_items_per_order": np.mean(num_items),
            "std_items_per_order": np.std(num_items),
            "min_items_per_order": min(num_items),
            "max_items_per_order": max(num_items),
            "most_popular_shelves": sorted(shelf_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "total_picks": sum(num_items)
        }


# Usage example and testing functions
def test_order_generator():
    """Test the order generator with sample data"""
    from server import shelves  # Import shelves from your main server
    
    generator = OrderGenerator(shelves)
    
    # Generate single order
    print("=== Single Order ===")
    single_order = generator.generate_single_order()
    print(json.dumps(single_order, indent=2))
    
    # Generate batch of orders
    print("\n=== Batch of Orders (Normal Distribution) ===")
    batch_orders = generator.generate_orders_batch(num_orders=10, mean_items=4, std_items=2)
    
    for order in batch_orders:
        print(f"Order {order['order_id']}: {len(order['pick_list'])} items - {order['pick_list']}")
    
    # Generate time-based orders
    print("\n=== Time-based Orders (24 hours) ===")
    time_orders = generator.generate_time_based_orders(hours=8, orders_per_hour_mean=3)
    
    for order in time_orders[:10]:  # Show first 10
        print(f"{order['timestamp'][:19]} - {order['order_id']}: {order['pick_list']}")
    
    # Statistics
    print("\n=== Statistics ===")
    stats = generator.get_statistics(batch_orders + time_orders)
    for key, value in stats.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    import json
    test_order_generator()