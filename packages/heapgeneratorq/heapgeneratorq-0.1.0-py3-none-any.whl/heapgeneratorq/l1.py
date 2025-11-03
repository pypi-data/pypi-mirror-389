#LAB1 searching
# Student Record Search System
# Implements Linear and Binary Search



class Student:
    def __init__(self, prn, name, class_name, mobile, marks):
        self.prn = prn
        self.name = name
        self.class_name = class_name
        self.mobile = mobile
        self.marks = marks
    
    def display(self):
        print(f"\nPRN: {self.prn}")
        print(f"Name: {self.name}")
        print(f"Class: {self.class_name}")
        print(f"Mobile: {self.mobile}")
        print(f"Marks: {self.marks}")


def binary_search(students, prn):
    """Binary search for PRN (sorted field)"""
    low, high = 0, len(students) - 1
    
    while low <= high:
        mid = (low + high) // 2
        if students[mid].prn == prn:
            students[mid].display()
            return
        elif students[mid].prn < prn:
            low = mid + 1
        else:
            high = mid - 1
    
    print("Record not found.")


def linear_search(students, field, value):
    """Linear search for name, class, mobile, or marks"""
    found = False
    
    for student in students:
        match = False
        
        if field == "name" and student.name == value:
            match = True
        elif field == "class" and student.class_name == value:
            match = True
        elif field == "mobile" and student.mobile == value:
            match = True
        elif field == "marks" and student.marks == int(value):
            match = True
        
        if match:
            student.display()
            found = True
    
    if not found:
        print("Record not found.")


def load_records_from_csv(filename):
    """Load student records from CSV file"""
    students = []
    
    try:
        with open(filename, 'r') as file:
            for line in file:
                parts = line.strip().split(',')
                if len(parts) == 5:
                    prn = int(parts[0])
                    name = parts[1]
                    class_name = parts[2]
                    mobile = parts[3]
                    marks = int(parts[4])
                    students.append(Student(prn, name, class_name, mobile, marks))
        return students
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        exit(1)


def main():
    filename = "data.txt"
    students = load_records_from_csv(filename)
    
    while True:
        print("\nSearch by:")
        print("1. PRN")
        print("2. Name")
        print("3. Class")
        print("4. Mobile")
        print("5. Marks")
        print("6. Exit")
        
        try:
            choice = int(input("Choice: "))
        except ValueError:
            print("Invalid input. Please enter a number.")
            continue
        
        if choice == 1:
            prn_input = input("Enter PRN: ")
            try:
                prn = int(prn_input)
                binary_search(students, prn)
            except ValueError:
                print("Invalid PRN. Please enter a number.")
        
        elif choice == 2:
            name = input("Enter Name: ")
            linear_search(students, "name", name)
        
        elif choice == 3:
            class_name = input("Enter Class: ")
            linear_search(students, "class", class_name)
        
        elif choice == 4:
            mobile = input("Enter Mobile Number: ")
            linear_search(students, "mobile", mobile)
        
        elif choice == 5:
            marks = input("Enter Marks: ")
            linear_search(students, "marks", marks)
        
        elif choice == 6:
            print("Exiting...")
            break
        
        else:
            print("Invalid choice. Try again.")


if __name__ == "__main__":
    main()
########################################################################3
########################################################################
#LAB2 - sorting 
#####################
import random
import time
from datetime import datetime, timedelta

class Transaction:
    def __init__(self, txn_id, customer, amount, timestamp):
        self.txn_id = txn_id
        self.customer = customer
        self.amount = amount
        self.timestamp = timestamp
    
    def __repr__(self):
        return f"{self.txn_id}({self.amount:.2f})"
    
    def display(self):
        return f"{self.txn_id} | {self.customer} | ₹{self.amount:.2f} | {self.timestamp}"


def generate_transactions(n=50):
    """Generate random transaction records"""
    names = ["Alice", "Bob", "Charlie", "David", "Emma", "Fiona", "George", 
             "Hannah", "Ian", "Julia", "Kevin", "Laura", "Mike", "Nina", "Oscar"]
    
    transactions = []
    used_ids = set()
    
    for i in range(n):
        # Generate unique transaction ID
        while True:
            txn_id = f"TXN{random.randint(1000, 9999)}"
            if txn_id not in used_ids:
                used_ids.add(txn_id)
                break
        
        customer = random.choice(names)
        amount = round(random.uniform(100.00, 100000.00), 2)
        
        # Generate timestamp within last 30 days
        days_ago = random.randint(0, 30)
        hours = random.randint(0, 23)
        minutes = random.randint(0, 59)
        seconds = random.randint(0, 59)
        timestamp = (datetime.now() - timedelta(days=days_ago, hours=hours, 
                                                  minutes=minutes, seconds=seconds))
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        transactions.append(Transaction(txn_id, customer, amount, timestamp_str))
    
    return transactions


def save_transactions(transactions, filename="transactions.txt"):
    """Save transactions to file"""
    with open(filename, 'w') as f:
        for t in transactions:
            f.write(f"{t.txn_id},{t.customer},{t.amount},{t.timestamp}\n")


def load_transactions(filename="transactions.txt"):
    """Load transactions from file"""
    transactions = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) == 4:
                    txn_id, customer, amount, timestamp = parts
                    transactions.append(Transaction(txn_id, customer, float(amount), timestamp))
    except FileNotFoundError:
        print("No transactions file found.")
    return transactions


# Quick Sort Implementation
quick_sort_comparisons = 0
quick_sort_passes = 0

def print_partial_quick_sort(arr, pass_num):
    """Display partial pass for Quick Sort"""
    print(f"\n--- Quick Sort Pass {pass_num} ---")
    amounts = [f"₹{t.amount:.2f}" for t in arr]
    print(amounts[:20])  # Display first 20 for readability


def partition(arr, low, high):
    """Partition function for Quick Sort"""
    global quick_sort_comparisons
    pivot = arr[high].amount
    i = low - 1
    
    for j in range(low, high):
        quick_sort_comparisons += 1
        if arr[j].amount <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1


def quick_sort(arr, low, high):
    """Quick Sort algorithm with pass tracking"""
    global quick_sort_passes
    
    if low < high:
        pi = partition(arr, low, high)
        quick_sort_passes += 1
        
        if quick_sort_passes <= 5:
            print_partial_quick_sort(arr, quick_sort_passes)
        
        quick_sort(arr, low, pi - 1)
        quick_sort(arr, pi + 1, high)


# Merge Sort Implementation
merge_sort_comparisons = 0
merge_sort_passes = 0

def print_partial_merge_sort(arr, pass_num):
    """Display partial pass for Merge Sort"""
    print(f"\n--- Merge Sort Pass {pass_num} ---")
    amounts = [f"₹{t.amount:.2f}" for t in arr]
    print(amounts[:20])  # Display first 20 for readability


def merge(arr, left, mid, right):
    """Merge function for Merge Sort"""
    global merge_sort_comparisons
    
    n1 = mid - left + 1
    n2 = right - mid
    
    L = arr[left:mid+1]
    R = arr[mid+1:right+1]
    
    i = j = 0
    k = left
    
    while i < n1 and j < n2:
        merge_sort_comparisons += 1
        if L[i].amount <= R[j].amount:
            arr[k] = L[i]
            i += 1
        else:
            arr[k] = R[j]
            j += 1
        k += 1
    
    while i < n1:
        arr[k] = L[i]
        i += 1
        k += 1
    
    while j < n2:
        arr[k] = R[j]
        j += 1
        k += 1


def merge_sort(arr, left, right):
    """Merge Sort algorithm with pass tracking"""
    global merge_sort_passes
    
    if left < right:
        mid = left + (right - left) // 2
        
        merge_sort(arr, left, mid)
        merge_sort(arr, mid + 1, right)
        merge(arr, left, mid, right)
        
        merge_sort_passes += 1
        if merge_sort_passes <= 5:
            print_partial_merge_sort(arr, merge_sort_passes)


def print_transactions(transactions, limit=20):
    """Display transactions"""
    print("\n--- Transactions ---")
    for i, t in enumerate(transactions[:limit]):
        print(t.display())
    if len(transactions) > limit:
        print(f"... and {len(transactions) - limit} more")


def main():
    filename = "transactions.txt"
    
    while True:
        print("\n=== Transaction Sorting System ===")
        print("1. Generate New Transaction Records")
        print("2. View All Transactions")
        print("3. Quick Sort Transactions by Amount")
        print("4. Merge Sort Transactions by Amount")
        print("0. Exit")
        
        try:
            choice = int(input("\nEnter your choice: "))
        except ValueError:
            print("Invalid input. Please enter a number.")
            continue
        
        if choice == 1:
            n = int(input("How many transactions to generate? (min 50): "))
            if n < 50:
                n = 50
                print("Generating 50 transactions (minimum requirement)...")
            
            transactions = generate_transactions(n)
            save_transactions(transactions, filename)
            print(f"\n{n} transactions generated and saved successfully!")
            print_transactions(transactions)
        
        elif choice == 2:
            transactions = load_transactions(filename)
            if not transactions:
                print("No transactions found. Generate some first!")
            else:
                print_transactions(transactions, len(transactions))
        
        elif choice == 3:
            global quick_sort_comparisons, quick_sort_passes
            transactions = load_transactions(filename)
            
            if not transactions:
                print("No transactions to sort.")
                continue
            
            quick_sort_comparisons = 0
            quick_sort_passes = 0
            
            print("\n=== Starting Quick Sort ===")
            start_time = time.time()
            quick_sort(transactions, 0, len(transactions) - 1)
            end_time = time.time()
            
            elapsed = (end_time - start_time) * 1000  # Convert to milliseconds
            
            print("\n=== Quick Sort Completed ===")
            print(f"Total Comparisons: {quick_sort_comparisons}")
            print(f"Time Taken: {elapsed:.4f} milliseconds")
            print_transactions(transactions)
        
        elif choice == 4:
            global merge_sort_comparisons, merge_sort_passes
            transactions = load_transactions(filename)
            
            if not transactions:
                print("No transactions to sort.")
                continue
            
            merge_sort_comparisons = 0
            merge_sort_passes = 0
            
            print("\n=== Starting Merge Sort ===")
            start_time = time.time()
            merge_sort(transactions, 0, len(transactions) - 1)
            end_time = time.time()
            
            elapsed = (end_time - start_time) * 1000  # Convert to milliseconds
            
            print("\n=== Merge Sort Completed ===")
            print(f"Total Comparisons: {merge_sort_comparisons}")
            print(f"Time Taken: {elapsed:.4f} milliseconds")
            print_transactions(transactions)
        
        elif choice == 0:
            print("Exiting program...")
            break
        
        else:
            print("Invalid choice! Please try again.")


if __name__ == "__main__":
    main()


##lab-3 prims and krushkal

import sys

class Graph:
    def __init__(self, vertices):
        self.V = vertices
        self.graph = [[0 for _ in range(vertices)] for _ in range(vertices)]
    
    def read_from_file(self, filename):
        """Read graph from file (adjacency matrix format)"""
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    if i < self.V:
                        weights = list(map(int, line.strip().split()))
                        self.graph[i] = weights[:self.V]
            print(f"Graph loaded successfully from {filename}\n")
        except FileNotFoundError:
            print(f"File {filename} not found!")
            return False
        return True
    
    def print_graph(self):
        """Display the adjacency matrix"""
        print("\nAdjacency Matrix:")
        for row in self.graph:
            print(" ".join(f"{x:3}" for x in row))
        print()


def prim_algorithm(graph):
    """Prim's Algorithm for Minimum Spanning Tree"""
    V = graph.V
    selected = [False] * V                                                
    total_cost = 0
    comparisons = 0
    
    # Start from vertex 0
    selected[0] = True
    
    print("\n=== Prim's Algorithm ===")
    print(f"{'Stage':<8}{'Edge':<15}{'Cost':<12}{'Cumulative':<15}")
    print("-" * 50)
    
    for stage in range(1, V):
        min_edge = sys.maxsize
        x = -1
        y = -1
        
        # Find minimum edge connecting selected to unselected vertex
        for i in range(V):
            if selected[i]:
                for j in range(V):
                    comparisons += 1
                    if not selected[j] and graph.graph[i][j] != 0:
                        if graph.graph[i][j] < min_edge:
                            min_edge = graph.graph[i][j]
                            x = i
                            y = j
        
        # Add the edge to MST
        selected[y] = True
        total_cost += min_edge
        
        print(f"{stage:<8}{f'D{x+1}-D{y+1}':<15}{min_edge:<12}{total_cost:<15}")
    
    print(f"\nTotal cost of MST: {total_cost}")
    print(f"Total edge comparisons: {comparisons}")
    print()


def kruskal_algorithm(graph):
    """Kruskal's Algorithm for Minimum Spanning Tree"""
    V = graph.V
    edges = []
    comparisons = 0
    
    # Extract all edges from adjacency matrix
    for i in range(V):
        for j in range(i + 1, V):
            comparisons += 1
            if graph.graph[i][j] != 0:
                edges.append((i, j, graph.graph[i][j]))
    
    # Sort edges by weight
    edges.sort(key=lambda x: x[2])
    
    # Initialize parent array for Union-Find
    parent = [i for i in range(V)]
    
    def find(x):
        """Find with path compression"""
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    
    def union(x, y):
        """Union two sets"""
        parent[find(x)] = find(y)
    
    total_cost = 0
    edges_used = 0
    
    print("\n=== Kruskal's Algorithm ===")
    print(f"{'Stage':<8}{'Edge':<15}{'Cost':<12}{'Cumulative':<15}")
    print("-" * 50)
    
    for edge in edges:
        u, v, weight = edge
        
        # Check if adding this edge creates a cycle
        if find(u) != find(v):
            union(u, v)
            total_cost += weight
            edges_used += 1
            
            print(f"{edges_used:<8}{f'D{u+1}-D{v+1}':<15}{weight:<12}{total_cost:<15}")
            
            if edges_used == V - 1:
                break
    
    print(f"\nTotal cost of MST: {total_cost}")
    print(f"Total edge comparisons: {comparisons}")
    print()


def create_sample_graph_file():
    """Create a sample graph file for testing"""
    sample_data = """0 10 20 0 0 0
10 0 30 5 0 0
20 30 0 15 6 0
0 5 15 0 4 8
0 0 6 4 0 12
0 0 0 8 12 0"""
    
    with open('graph.txt', 'w') as f:
        f.write(sample_data)
    print("Sample graph file 'graph.txt' created!")


def main():
    print("=== Minimum Spanning Tree - University Network Cable Connection ===\n")
    
    while True:
        print("\n--- Menu ---")
        print("1. Create Sample Graph File")
        print("2. Load Graph from File")
        print("3. Run Prim's Algorithm")
        print("4. Run Kruskal's Algorithm")
        print("5. Run Both Algorithms")
        print("0. Exit")
        
        try:
            choice = int(input("\nEnter your choice: "))
        except ValueError:
            print("Invalid input!")
            continue
        
        if choice == 1:
            create_sample_graph_file()
        
        elif choice == 2:
            filename = input("Enter filename (default: graph.txt): ").strip()
            if not filename:
                filename = "graph.txt"
            
            vertices = int(input("Enter number of departments (vertices): "))
            graph = Graph(vertices)
            
            if graph.read_from_file(filename):
                graph.print_graph()
        
        elif choice == 3:
            try:
                if 'graph' not in locals():
                    print("Please load graph first (option 2)!")
                    continue
                prim_algorithm(graph)
            except Exception as e:
                print(f"Error: {e}")
        
        elif choice == 4:
            try:
                if 'graph' not in locals():
                    print("Please load graph first (option 2)!")
                    continue
                kruskal_algorithm(graph)
            except Exception as e:
                print(f"Error: {e}")
        
        elif choice == 5:
            try:
                if 'graph' not in locals():
                    print("Please load graph first (option 2)!")
                    continue
                prim_algorithm(graph)
                kruskal_algorithm(graph)
            except Exception as e:
                print(f"Error: {e}")
        
        elif choice == 0:
            print("Exiting program...")
            break
        
        else:
            print("Invalid choice!")


if __name__ == "__main__":
    main()
 
 
 
 
 
########################lab 4 - dijkstra
import heapq
import sys
from collections import defaultdict

class DeliveryNetwork:
    def __init__(self):
        self.graph = defaultdict(list)
        self.hubs = set()
    
    def add_road(self, hub1, hub2, time):
        """Add bidirectional road between hubs"""
        self.graph[hub1].append((hub2, time))
        self.graph[hub2].append((hub1, time))
        self.hubs.add(hub1)
        self.hubs.add(hub2)
    
    def dijkstra(self, start, end=None):
        """
        Dijkstra's algorithm to find shortest path
        Returns: distances dict and parent dict for path reconstruction
        """
        distances = {hub: sys.maxsize for hub in self.hubs}
        distances[start] = 0
        parent = {hub: None for hub in self.hubs}
        
        # Priority queue: (distance, hub)
        pq = [(0, start)]
        visited = set()
        
        while pq:
            current_dist, current_hub = heapq.heappop(pq)
            
            if current_hub in visited:
                continue
            
            visited.add(current_hub)
            
            # If we only need shortest path to specific end
            if end and current_hub == end:
                break
            
            # Explore neighbors
            for neighbor, weight in self.graph[current_hub]:
                distance = current_dist + weight
                
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    parent[neighbor] = current_hub
                    heapq.heappush(pq, (distance, neighbor))
        
        return distances, parent
    
    def get_path(self, parent, start, end):
        """Reconstruct path from parent dictionary"""
        if parent[end] is None and start != end:
            return None
        
        path = []
        current = end
        
        while current is not None:
            path.append(current)
            current = parent[current]
        
        path.reverse()
        return path
    
    def print_shortest_path(self, start, end):
        """Find and display shortest path between two hubs"""
        if start not in self.hubs:
            print(f"Error: Hub '{start}' does not exist!")
            return
        
        if end not in self.hubs:
            print(f"Error: Hub '{end}' does not exist!")
            return
        
        distances, parent = self.dijkstra(start, end)
        
        if distances[end] == sys.maxsize:
            print(f"\nNo path exists between '{start}' and '{end}'")
            return
        
        path = self.get_path(parent, start, end)
        
        print(f"\n{'='*60}")
        print(f"Shortest Route from '{start}' to '{end}'")
        print(f"{'='*60}")
        print(f"Shortest travel time: {distances[end]} minutes")
        print(f"Path: {' → '.join(path)}")
        print(f"{'='*60}\n")
    
    def print_all_distances(self, start):
        """Print shortest distances from start to all other hubs"""
        distances, _ = self.dijkstra(start)
        
        print(f"\n{'='*60}")
        print(f"Shortest distances from '{start}' to all hubs:")
        print(f"{'='*60}")
        
        sorted_hubs = sorted([h for h in self.hubs if h != start])
        
        for hub in sorted_hubs:
            if distances[hub] == sys.maxsize:
                print(f"{hub:<25}: Unreachable")
            else:
                print(f"{hub:<25}: {distances[hub]} minutes")
        
        print(f"{'='*60}\n")


def load_sample_pune_data(network):
    """Load sample Pune delivery hub data"""
    roads = [
        ('Shivaji Nagar', 'FC Road', 10),
        ('Shivaji Nagar', 'Kothrud', 15),
        ('FC Road', 'Kothrud', 5),
        ('FC Road', 'Viman Nagar', 20),
        ('Kothrud', 'Hadapsar', 30),
        ('Viman Nagar', 'Hadapsar', 10),
        ('Shivaji Nagar', 'Deccan', 8),
        ('Deccan', 'Kothrud', 12),
        ('Viman Nagar', 'Koregaon Park', 15),
        ('Hadapsar', 'Magarpatta', 12),
    ]
    
    for hub1, hub2, time in roads:
        network.add_road(hub1, hub2, time)
    
    print("Sample Pune delivery network loaded successfully!")


def main():
    network = DeliveryNetwork()
    
    print("=" * 60)
    print("Drone Delivery Routing System - Pune")
    print("=" * 60)
    
    while True:
        print("\n--- Menu ---")
        print("1. Load Sample Pune Network")
        print("2. Add Custom Road")
        print("3. Display All Hubs")
        print("4. Find Shortest Route (Two Hubs)")
        print("5. Show All Distances from a Hub")
        print("0. Exit")
        
        try:
            choice = int(input("\nEnter your choice: "))
        except ValueError:
            print("Invalid input!")
            continue
        
        if choice == 1:
            network = DeliveryNetwork()
            load_sample_pune_data(network)
        
        elif choice == 2:
            hub1 = input("Enter first hub name: ").strip()
            hub2 = input("Enter second hub name: ").strip()
            try:
                time = int(input("Enter travel time (minutes): "))
                network.add_road(hub1, hub2, time)
                print(f"Road added: {hub1} ↔ {hub2} ({time} min)")
            except ValueError:
                print("Invalid time value!")
        
        elif choice == 3:
            if not network.hubs:
                print("No hubs in network. Load sample data or add roads first.")
            else:
                print(f"\nAll Delivery Hubs ({len(network.hubs)}):")
                for i, hub in enumerate(sorted(network.hubs), 1):
                    print(f"{i}. {hub}")
        
        elif choice == 4:
            if not network.hubs:
                print("No hubs in network. Load sample data first.")
                continue
            
            start = input("Enter starting hub: ").strip()
            end = input("Enter destination hub: ").strip()
            network.print_shortest_path(start, end)
        
        elif choice == 5:
            if not network.hubs:
                print("No hubs in network. Load sample data first.")
                continue
            
            start = input("Enter starting hub: ").strip()
            network.print_all_distances(start)
        
        elif choice == 0:
            print("Exiting program...")
            break
        
        else:
            print("Invalid choice!")


if __name__ == "__main__":
    main()
#lab 5 - knapsack

def pack_suitcase(items, max_weight):
    """0/1 Knapsack using Dynamic Programming"""
    n = len(items)
    dp = [[0 for _ in range(max_weight + 1)] for _ in range(n + 1)]
    
    # Fill the DP table
    for i in range(1, n + 1):
        item_weight = items[i-1]['weight']
        item_value = items[i-1]['value']
        
        for w in range(max_weight + 1):
            # Don't take the current item
            dp[i][w] = dp[i-1][w]
            
            # Take the current item if it fits
            if item_weight <= w:
                value_with_item = dp[i-1][w - item_weight] + item_value
                dp[i][w] = max(dp[i][w], value_with_item)
    
    # Backtrack to find which items to take
    selected_items = []
    w = max_weight
    
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i-1][w]:
            selected_items.append(items[i-1])
            w -= items[i-1]['weight']
    
    return dp[n][max_weight], selected_items


def print_results(max_value, selected_items, max_weight):
    """Display the packing solution"""
    total_weight = sum(item['weight'] for item in selected_items)
    
    print("\n" + "=" * 50)
    print("PACKING SOLUTION")
    print("=" * 50)
    print(f"Maximum value you can pack: {max_value}")
    print(f"Total weight: {total_weight} kg (limit: {max_weight} kg)")
    print(f"Weight remaining: {max_weight - total_weight} kg")
    print("\nItems to pack:")
    
    for item in selected_items:
        print(f"- {item['name']}: {item['weight']} kg (value: {item['value']})")
    
    print("=" * 50)


def print_all_items(items):
    """Display all available items"""
    if not items:
        print("\nNo items available!")
        return
        
    print("\nAll available items:")
    print("-" * 40)
    print(f"{'Item':<15} {'Weight (kg)':<12} {'Value':<8}")
    print("-" * 40)
    for i, item in enumerate(items, 1):
        print(f"{i}. {item['name']:<12} {item['weight']:<12} {item['value']:<8}")
    print("-" * 40)


def add_item(items):
    """Add a new item to the list"""
    print("\n--- Add New Item ---")
    name = input("Enter item name: ").strip()
    
    if not name:
        print("Item name cannot be empty!")
        return items
    
    # Check if item already exists
    for item in items:
        if item['name'].lower() == name.lower():
            print(f"Item '{name}' already exists!")
            return items
    
    try:
        weight = int(input("Enter weight (kg): "))
        value = int(input("Enter value: "))
        
        if weight <= 0 or value <= 0:
            print("Weight and value must be positive numbers!")
            return items
            
        items.append({'name': name, 'weight': weight, 'value': value})
        print(f"Item '{name}' added successfully!")
        
    except ValueError:
        print("Please enter valid numbers for weight and value!")
    
    return items


def remove_item(items):
    """Remove an item from the list"""
    if not items:
        print("No items to remove!")
        return items
        
    print("\n--- Remove Item ---")
    print_all_items(items)
    
    try:
        choice = int(input("\nEnter item number to remove: ")) - 1
        
        if 0 <= choice < len(items):
            removed_item = items.pop(choice)
            print(f"Item '{removed_item['name']}' removed successfully!")
        else:
            print("Invalid item number!")
            
    except ValueError:
        print("Please enter a valid number!")
    
    return items


def update_item(items):
    """Update an existing item"""
    if not items:
        print("No items to update!")
        return items
        
    print("\n--- Update Item ---")
    print_all_items(items)
    
    try:
        choice = int(input("\nEnter item number to update: ")) - 1
        
        if 0 <= choice < len(items):
            item = items[choice]
            print(f"Updating '{item['name']}' (current: weight={item['weight']}, value={item['value']})")
            
            new_weight = input(f"Enter new weight (current: {item['weight']}, press Enter to keep): ").strip()
            new_value = input(f"Enter new value (current: {item['value']}, press Enter to keep): ").strip()
            
            if new_weight:
                try:
                    weight = int(new_weight)
                    if weight > 0:
                        item['weight'] = weight
                    else:
                        print("Weight must be positive!")
                except ValueError:
                    print("Invalid weight entered!")
            
            if new_value:
                try:
                    value = int(new_value)
                    if value > 0:
                        item['value'] = value
                    else:
                        print("Value must be positive!")
                except ValueError:
                    print("Invalid value entered!")
            
            print(f"Item '{item['name']}' updated successfully!")
        else:
            print("Invalid item number!")
            
    except ValueError:
        print("Please enter a valid number!")
    
    return items


def change_weight_limit():
    """Change the maximum weight limit"""
    print("\n--- Change Weight Limit ---")
    try:
        new_limit = int(input("Enter new weight limit (kg): "))
        if new_limit > 0:
            print(f"Weight limit changed to {new_limit} kg")
            return new_limit
        else:
            print("Weight limit must be positive!")
            return None
    except ValueError:
        print("Please enter a valid number!")
        return None


def solve_knapsack(items, max_weight):
    """Solve the knapsack problem"""
    if not items:
        print("No items available to pack!")
        return
        
    print("\n--- Solving Knapsack Problem ---")
    max_value, selected = pack_suitcase(items, max_weight)
    print_results(max_value, selected, max_weight)


def show_menu():
    """Display the main menu"""
    print("\n" + "=" * 50)
    print("KNAPSACK PROBLEM SOLVER")
    print("=" * 50)
    print("1. View all items")
    print("2. Solve knapsack problem")
    print("3. Add new item")
    print("4. Remove item")
    print("5. Update item")
    print("6. Change weight limit")
    print("7. Load sample items")
    print("8. Clear all items")
    print("9. Exit")
    print("=" * 50)


def load_sample_items():
    """Load the default sample items"""
    return [
        {'name': 'Laptop', 'weight': 3, 'value': 9},
        {'name': 'Headphones', 'weight': 1, 'value': 5},
        {'name': 'Jacket', 'weight': 5, 'value': 10},
        {'name': 'Camera', 'weight': 4, 'value': 7},
        {'name': 'Book', 'weight': 2, 'value': 4},
        {'name': 'Shoes', 'weight': 6, 'value': 6}
    ]


def main():
    # Start with sample items
    items = load_sample_items()
    max_weight = 15
    
    print("Welcome to the Knapsack Problem Solver!")
    print(f"Current weight limit: {max_weight} kg\n")
    
    while True:
        show_menu()
        
        try:
            choice = int(input("Enter your choice (1-9): "))
            
            if choice == 1:
                print_all_items(items)
                
            elif choice == 2:
                solve_knapsack(items, max_weight)
                
            elif choice == 3:
                items = add_item(items)
                
            elif choice == 4:
                items = remove_item(items)
                
            elif choice == 5:
                items = update_item(items)
                
            elif choice == 6:
                new_limit = change_weight_limit()
                if new_limit is not None:
                    max_weight = new_limit
                    
            elif choice == 7:
                items = load_sample_items()
                print("Sample items loaded!")
                
            elif choice == 8:
                items = []
                print("All items cleared!")
                
            elif choice == 9:
                print("Thank you for using Knapsack Problem Solver!")
                break
                
            else:
                print("Invalid choice! Please enter a number between 1-9.")
                
        except ValueError:
            print("Please enter a valid number!")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()

#lab-6 floyd warshal
import sys

INF = sys.maxsize // 2  # Use a large number to represent infinity


class CityNetwork:
    def __init__(self):
        self.n = 0
        self.dist = []
        self.next = []
        self.city_names = []
    
    def read_from_file(self, filename):
        """Read distance matrix from file"""
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
                
                # First line: number of cities
                self.n = int(lines[0].strip())
                
                # Initialize matrices
                self.dist = [[0] * self.n for _ in range(self.n)]
                self.next = [[-1] * self.n for _ in range(self.n)]
                
                # Read distance matrix
                for i in range(self.n):
                    row = list(map(int, lines[i + 1].strip().split()))
                    for j in range(self.n):
                        if row[j] == -1:  # -1 means no direct road
                            self.dist[i][j] = 0 if i == j else INF
                        else:
                            self.dist[i][j] = row[j]
                        
                        if self.dist[i][j] != INF and i != j:
                            self.next[i][j] = j
                
                # Generate default city names
                self.city_names = [f"City{chr(65 + i)}" for i in range(self.n)]
                
                print(f"Successfully loaded network with {self.n} cities from {filename}\n")
                return True
                
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found!")
            return False
        except Exception as e:
            print(f"Error reading file: {e}")
            return False
    
    def floyd_warshall(self):
        """Apply Floyd-Warshall algorithm"""
        print("\n" + "=" * 60)
        print("RUNNING FLOYD-WARSHALL ALGORITHM")
        print("=" * 60)
        
        # Floyd-Warshall Algorithm
        for k in range(self.n):
            print(f"Processing intermediate city: {self.city_names[k]}...")
            
            for i in range(self.n):
                for j in range(self.n):
                    if self.dist[i][k] + self.dist[k][j] < self.dist[i][j]:
                        self.dist[i][j] = self.dist[i][k] + self.dist[k][j]
                        self.next[i][j] = self.next[i][k]
        
        print("Algorithm completed!\n")
    
    def print_distance_matrix(self):
        """Display the all-pairs shortest distance matrix"""
        print("\n" + "=" * 60)
        print("ALL-PAIRS SHORTEST DISTANCE MATRIX")
        print("=" * 60)
        
        # Print header
        print(f"{'From/To':<12}", end="")
        for j in range(self.n):
            print(f"{self.city_names[j]:<10}", end="")
        print()
        print("-" * (12 + 10 * self.n))
        
        # Print matrix
        for i in range(self.n):
            print(f"{self.city_names[i]:<12}", end="")
            for j in range(self.n):
                if self.dist[i][j] == INF:
                    print(f"{'INF':<10}", end="")
                else:
                    print(f"{self.dist[i][j]:<10}", end="")
            print()
        print("=" * 60)
    
    def reconstruct_path(self, u, v):
        """Reconstruct the shortest path from u to v"""
        if self.next[u][v] == -1:
            return []
        
        path = [u]
        while u != v:
            u = self.next[u][v]
            path.append(u)
        
        return path
    
    def query_shortest_path(self, u, v):
        """Query shortest path between two cities"""
        if u < 0 or u >= self.n or v < 0 or v >= self.n:
            print("Invalid city indices!")
            return
        
        print("\n" + "=" * 60)
        print(f"SHORTEST PATH: {self.city_names[u]} → {self.city_names[v]}")
        print("=" * 60)
        
        if self.dist[u][v] == INF:
            print(f"No path exists between {self.city_names[u]} and {self.city_names[v]}")
        else:
            print(f"Shortest distance: {self.dist[u][v]} km")
            
            path = self.reconstruct_path(u, v)
            path_names = [self.city_names[i] for i in path]
            
            print(f"Route: {' → '.join(path_names)}")
            
            if len(path) > 2:
                intermediate = path_names[1:-1]
                print(f"Intermediate cities: {', '.join(intermediate)}")
            else:
                print("Direct route (no intermediate cities)")
        
        print("=" * 60)


def create_sample_file():
    """Create a sample graph file for testing"""
    sample_data = """5
0 10 -1 30 100
10 0 50 -1 -1
-1 50 0 20 10
30 -1 20 0 60
100 -1 10 60 0"""
    
    with open('cities.txt', 'w') as f:
        f.write(sample_data)
    
    print("Sample file 'cities.txt' created!")
    print("Cities: CityA, CityB, CityC, CityD, CityE")
    print("Format: First line = number of cities")
    print("        Following lines = distance matrix (-1 means no direct road)\n")


def main():
    network = CityNetwork()
    
    print("=" * 60)
    print("FLOYD-WARSHALL ALGORITHM - LOGISTICS OPTIMIZATION")
    print("=" * 60)
    print("Find shortest paths between all pairs of cities\n")
    
    while True:
        print("\n--- Menu ---")
        print("1. Create Sample Graph File")
        print("2. Load City Network from File")
        print("3. Run Floyd-Warshall Algorithm")
        print("4. Display Shortest Distance Matrix")
        print("5. Query Shortest Path Between Two Cities")
        print("6. Query All Paths from a City")
        print("0. Exit")
        
        try:
            choice = int(input("\nEnter your choice: "))
        except ValueError:
            print("Invalid input!")
            continue
        
        if choice == 1:
            create_sample_file()
        
        elif choice == 2:
            filename = input("Enter filename (default: cities.txt): ").strip()
            if not filename:
                filename = "cities.txt"
            network.read_from_file(filename)
        
        elif choice == 3:
            if network.n == 0:
                print("Please load a city network first (option 2)!")
                continue
            network.floyd_warshall()
        
        elif choice == 4:
            if network.n == 0:
                print("Please load a city network first (option 2)!")
                continue
            network.print_distance_matrix()
        
        elif choice == 5:
            if network.n == 0:
                print("Please load a city network first (option 2)!")
                continue
            
            print("\nAvailable cities:")
            for i, name in enumerate(network.city_names):
                print(f"{i}. {name}")
            
            try:
                u = int(input("\nEnter starting city index: "))
                v = int(input("Enter destination city index: "))
                network.query_shortest_path(u, v)
            except ValueError:
                print("Please enter valid numbers!")
        
        elif choice == 6:
            if network.n == 0:
                print("Please load a city network first (option 2)!")
                continue
            
            print("\nAvailable cities:")
            for i, name in enumerate(network.city_names):
                print(f"{i}. {name}")
            
            try:
                u = int(input("\nEnter starting city index: "))
                
                if u < 0 or u >= network.n:
                    print("Invalid city index!")
                    continue
                
                print(f"\n{'='*60}")
                print(f"ALL SHORTEST PATHS FROM {network.city_names[u]}")
                print(f"{'='*60}")
                
                for v in range(network.n):
                    if u != v:
                        if network.dist[u][v] == INF:
                            print(f"\n{network.city_names[v]:<10}: No path exists")
                        else:
                            path = network.reconstruct_path(u, v)
                            path_names = [network.city_names[i] for i in path]
                            print(f"\n{network.city_names[v]:<10}: Distance = {network.dist[u][v]} km")
                            print(f"             Route: {' → '.join(path_names)}")
                
                print(f"{'='*60}")
                
            except ValueError:
                print("Please enter a valid number!")
        
        elif choice == 0:
            print("Exiting program...")
            break
        
        else:
            print("Invalid choice!")


if __name__ == "__main__":
    main()


#lab7 - magic square
def generate_odd_magic_square(n):
    """
    Generate an odd-order magic square using Siamese method.
    Time Complexity: O(n²)
    """
    if n % 2 == 0 or n < 3:
        raise ValueError("n must be odd and >= 3")
    
    magic_square = [[0] * n for _ in range(n)]
    
    # Start position: middle of first row
    i = 0
    j = n // 2
    
    # Fill numbers from 1 to n²
    for num in range(1, n * n + 1):
        magic_square[i][j] = num
        
        # Calculate next position
        next_i = (i - 1) % n
        next_j = (j + 1) % n
        
        # If next position is occupied, move down instead
        if magic_square[next_i][next_j] != 0:
            i = (i + 1) % n
        else:
            i = next_i
            j = next_j
    
    return magic_square


def generate_doubly_even_magic_square(n):
    """
    Generate a doubly even magic square (n divisible by 4) using Strachey method.
    Time Complexity: O(n²)
    """
    if n % 4 != 0:
        raise ValueError("n must be divisible by 4")
    
    magic_square = [[0] * n for _ in range(n)]
    
    # Fill numbers 1 to n² row by row
    num = 1
    for i in range(n):
        for j in range(n):
            magic_square[i][j] = num
            num += 1
    
    # Apply complement on specific positions
    for i in range(n):
        for j in range(n):
            # Check if position is on main diagonals of 4x4 sub-squares
            is_diagonal = ((i % 4 == j % 4) or (i % 4 + j % 4 == 3))
            
            if not is_diagonal:
                magic_square[i][j] = n * n + 1 - magic_square[i][j]
    
    return magic_square


def generate_singly_even_magic_square(n):
    """
    Generate a singly even magic square (n = 4k+2) using 4-Quadrant method.
    Time Complexity: O(n²)
    """
    if n % 2 != 0 or n % 4 == 0:
        raise ValueError("n must be even but not divisible by 4")
    
    half = n // 2
    
    # Generate odd magic square of half size
    sub_square = generate_odd_magic_square(half)
    
    # Create four quadrants
    magic_square = [[0] * n for _ in range(n)]
    
    # Quadrant offsets
    offsets = [0, 2, 3, 1]
    
    for i in range(half):
        for j in range(half):
            val = sub_square[i][j]
            
            # Top-left (A) - offset 0
            magic_square[i][j] = val + offsets[0] * half * half
            
            # Top-right (B) - offset 2
            magic_square[i][j + half] = val + offsets[1] * half * half
            
            # Bottom-left (C) - offset 3
            magic_square[i + half][j] = val + offsets[2] * half * half
            
            # Bottom-right (D) - offset 1
            magic_square[i + half][j + half] = val + offsets[3] * half * half
    
    # Swap operations for balancing
    k = (n - 2) // 4
    
    # Swap columns in left quadrants
    for i in range(half):
        for j in range(k):
            if i == half // 2:
                # Special swap for middle row
                if j == 0:
                    continue
            magic_square[i][j], magic_square[i + half][j] = \
                magic_square[i + half][j], magic_square[i][j]
    
    # Swap middle row, first column
    magic_square[half // 2][0], magic_square[half + half // 2][0] = \
        magic_square[half + half // 2][0], magic_square[half // 2][0]
    
    # Swap columns in right quadrants
    for i in range(half):
        for j in range(n - k + 1, n):
            magic_square[i][j], magic_square[i + half][j] = \
                magic_square[i + half][j], magic_square[i][j]
    
    return magic_square


def print_magic_square(magic_square):
    """Display the magic square in formatted output"""
    n = len(magic_square)
    
    # Calculate magic constant
    magic_constant = n * (n * n + 1) // 2
    
    print(f"\nMagic Square of size {n}x{n}:")
    print(f"Magic Constant: {magic_constant}")
    print("-" * (6 * n))
    
    for row in magic_square:
        for val in row:
            print(f"{val:4}", end="  ")
        print()
    
    print("-" * (6 * n))
    
    # Verify the magic square
    verify_magic_square(magic_square, magic_constant)


def verify_magic_square(magic_square, magic_constant):
    """Verify if the square is a valid magic square"""
    n = len(magic_square)
    valid = True
    
    # Check row sums
    print("\nRow sums:", end=" ")
    for i in range(n):
        row_sum = sum(magic_square[i])
        print(row_sum, end=" ")
        if row_sum != magic_constant:
            valid = False
    
    # Check column sums
    print("\nColumn sums:", end=" ")
    for j in range(n):
        col_sum = sum(magic_square[i][j] for i in range(n))
        print(col_sum, end=" ")
        if col_sum != magic_constant:
            valid = False
    
    # Check diagonal sums
    diag1 = sum(magic_square[i][i] for i in range(n))
    diag2 = sum(magic_square[i][n - 1 - i] for i in range(n))
    print(f"\nDiagonal sums: {diag1} {diag2}")
    
    if diag1 != magic_constant or diag2 != magic_constant:
        valid = False
    
    if valid:
        print("\n✓ Valid Magic Square!")
    else:
        print("\n✗ Invalid Magic Square!")


def main():
    print("=" * 60)
    print("MAGIC SQUARE GENERATOR")
    print("=" * 60)
    
    while True:
        print("\n--- Menu ---")
        print("1. Generate Odd-Order Magic Square (Siamese Method)")
        print("2. Generate Doubly Even Magic Square (Strachey Method)")
        print("3. Generate Singly Even Magic Square (4-Quadrant Method)")
        print("4. Generate Magic Square (Auto-detect method)")
        print("0. Exit")
        
        try:
            choice = int(input("\nEnter your choice: "))
        except ValueError:
            print("Invalid input!")
            continue
        
        if choice == 0:
            print("Exiting program...")
            break
        
        if choice in [1, 2, 3, 4]:
            try:
                n = int(input("Enter the size of magic square (n): "))
                
                if n < 3:
                    print("Size must be at least 3!")
                    continue
                
                if choice == 1:
                    if n % 2 == 0:
                        print("For Siamese method, n must be odd!")
                        continue
                    magic_square = generate_odd_magic_square(n)
                
                elif choice == 2:
                    if n % 4 != 0:
                        print("For Strachey method, n must be divisible by 4!")
                        continue
                    magic_square = generate_doubly_even_magic_square(n)
                
                elif choice == 3:
                    if n % 2 != 0 or n % 4 == 0:
                        print("For 4-Quadrant method, n must be even but not divisible by 4!")
                        continue
                    magic_square = generate_singly_even_magic_square(n)
                
                elif choice == 4:
                    # Auto-detect which method to use
                    if n % 2 == 1:
                        print("Using Siamese Method (odd order)...")
                        magic_square = generate_odd_magic_square(n)
                    elif n % 4 == 0:
                        print("Using Strachey Method (doubly even)...")
                        magic_square = generate_doubly_even_magic_square(n)
                    else:
                        print("Using 4-Quadrant Method (singly even)...")
                        magic_square = generate_singly_even_magic_square(n)
                
                print_magic_square(magic_square)
                
            except ValueError as e:
                print(f"Error: {e}")
        
        else:
            print("Invalid choice!")


if __name__ == "__main__":
    main()


#lab-8 n queen
def solve_n_queens(n):
    """
    Solve N-Queens problem using backtracking.
    Returns all valid configurations.
    """
    solutions = []
    board = [-1] * n  # board[i] = column position of queen in row i
    
    def is_safe(board, row, col):
        """Check if placing queen at (row, col) is safe"""
        for prev_row in range(row):
            prev_col = board[prev_row]
            
            # Check column conflict
            if prev_col == col:
                return False
            
            # Check diagonal conflict
            if abs(row - prev_row) == abs(col - prev_col):
                return False
        
        return True
    
    def backtrack(row):
        """Recursively place queens row by row"""
        if row == n:
            # Found a solution
            solutions.append(list(board))
            return
        
        for col in range(n):
            if is_safe(board, row, col):
                board[row] = col
                backtrack(row + 1)
                # No need to reset board[row] as it will be overwritten
    
    backtrack(0)
    return solutions


def format_board(solution, n, symbol='S'):
    """Convert solution to board representation"""
    board = []
    for queen_col in solution:
        row = ['.'] * n
        row[queen_col] = symbol
        board.append(''.join(row))
    return board


def print_solution(solution, index, n, title="Server"):
    """Display a single solution"""
    print(f"\nConfiguration {index}:")
    board = format_board(solution, n)
    for row in board:
        print(f"  {row}")


def print_all_solutions(solutions, n, title="Server"):
    """Display all solutions"""
    print(f"\n{'='*50}")
    print(f"Found {len(solutions)} valid {title} placement configuration(s)")
    print(f"{'='*50}")
    
    for i, solution in enumerate(solutions, 1):
        print_solution(solution, i, n, title)
        if i < len(solutions):
            print("-" * 20)


def visualize_solution(solution, n):
    """Visualize solution with row and column labels"""
    board = format_board(solution, n)
    
    print("\n" + " " * 4, end="")
    for j in range(n):
        print(f" {j}", end="")
    print()
    
    print("   " + "+" + "-" * (n * 2 + 1) + "+")
    
    for i, row in enumerate(board):
        print(f" {i} |", end="")
        for char in row:
            print(f" {char}", end="")
        print(" |")
    
    print("   " + "+" + "-" * (n * 2 + 1) + "+")


def count_n_queens(n):
    """Count total solutions without storing them (optimized)"""
    count = 0
    cols = set()
    diag1 = set()  # row - col
    diag2 = set()  # row + col
    
    def backtrack(row):
        nonlocal count
        
        if row == n:
            count += 1
            return
        
        for col in range(n):
            if col in cols or (row - col) in diag1 or (row + col) in diag2:
                continue
            
            cols.add(col)
            diag1.add(row - col)
            diag2.add(row + col)
            
            backtrack(row + 1)
            
            cols.remove(col)
            diag1.remove(row - col)
            diag2.remove(row + col)
    
    backtrack(0)
    return count


def solve_4_queens():
    """
    Specific solution for 4-Queens (Server Deployment) problem
    """
    print("=" * 60)
    print("SECURE SERVER DEPLOYMENT - 4x4 GRID")
    print("=" * 60)
    print("\nConstraints:")
    print("1. Only one server per row")
    print("2. No two servers in the same column")
    print("3. No two servers on the same diagonal")
    print("\nFinding all valid configurations...\n")
    
    solutions = solve_n_queens(4)
    print_all_solutions(solutions, 4)
    
    # Show detailed visualization for first solution
    if solutions:
        print("\n" + "=" * 60)
        print("DETAILED VIEW - Configuration 1:")
        print("=" * 60)
        visualize_solution(solutions[0], 4)


def interactive_n_queens():
    """Interactive N-Queens solver"""
    print("=" * 60)
    print("N-QUEENS PROBLEM SOLVER")
    print("=" * 60)
    
    while True:
        print("\n--- Menu ---")
        print("1. Solve 4-Queens (Server Deployment)")
        print("2. Solve N-Queens (Custom Size)")
        print("3. Count Solutions Only (Fast)")
        print("4. Compare Solutions for Different N")
        print("0. Exit")
        
        try:
            choice = int(input("\nEnter your choice: "))
        except ValueError:
            print("Invalid input!")
            continue
        
        if choice == 0:
            print("Exiting program...")
            break
        
        elif choice == 1:
            solve_4_queens()
        
        elif choice == 2:
            try:
                n = int(input("Enter board size (n): "))
                
                if n < 1:
                    print("Size must be at least 1!")
                    continue
                
                if n == 2 or n == 3:
                    print(f"No solution exists for n = {n}")
                    continue
                
                print(f"\nSolving {n}-Queens problem...")
                solutions = solve_n_queens(n)
                print_all_solutions(solutions, n, "Queen")
                
                if solutions and n <= 8:
                    show_detail = input("\nShow detailed view of first solution? (y/n): ")
                    if show_detail.lower() == 'y':
                        visualize_solution(solutions[0], n)
                
            except ValueError:
                print("Please enter a valid number!")
        
        elif choice == 3:
            try:
                n = int(input("Enter board size (n): "))
                
                if n < 1:
                    print("Size must be at least 1!")
                    continue
                
                print(f"\nCounting solutions for {n}-Queens...")
                count = count_n_queens(n)
                print(f"Total solutions: {count}")
                
            except ValueError:
                print("Please enter a valid number!")
        
        elif choice == 4:
            print("\nSolutions for different board sizes:")
            print("-" * 40)
            print(f"{'n':<5} {'Solutions':<15} {'Time Complexity'}")
            print("-" * 40)
            
            for n in range(1, 13):
                if n == 2 or n == 3:
                    print(f"{n:<5} {'0':<15} O(n!)")
                else:
                    count = count_n_queens(n)
                    print(f"{n:<5} {count:<15} O(n!)")
            
            print("-" * 40)
        
        else:
            print("Invalid choice!")


if __name__ == "__main__":
    print("\nSelect Program:")
    print("1. Magic Square Generator")
    print("2. N-Queens Solver")
    
    try:
        program = int(input("\nEnter choice (1 or 2): "))
        
        if program == 1:
            main()
        elif program == 2:
            interactive_n_queens()
        else:
            print("Invalid choice!")
    except ValueError:
        print("Invalid input!")




