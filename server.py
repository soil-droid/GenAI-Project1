from mcp.server.fastmcp import FastMCP
import sqlite3
import json

# 1. Initialize the MCP Server
mcp = FastMCP("RigBuilderServer")

# 2. Setup a mock SQLite database
def setup_database():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    cursor = conn.cursor()
    
    # Create the components table
    cursor.execute('''
        CREATE TABLE components (
            id INTEGER PRIMARY KEY,
            part_type TEXT,
            name TEXT,
            price INTEGER,
            target_workload TEXT
        )
    ''')
    
    # Insert mock inventory (You can expand this list!)
    inventory = [
        # 3D Modeling / Heavy Workload Parts
        ("CPU", "AMD Ryzen 9 7950X", 600, "3D modeling"),
        ("GPU", "NVIDIA RTX 4080 Super 16GB", 1000, "3D modeling"),
        ("RAM", "64GB Corsair Dominator DDR5", 200, "3D modeling"),
        ("Motherboard", "ASUS ROG X670E", 300, "3D modeling"),
        
        # Budget / Basic Gaming Parts
        ("CPU", "Intel Core i5-13400F", 200, "budget"),
        ("GPU", "NVIDIA RTX 4060 8GB", 300, "budget"),
        ("RAM", "16GB Kingston Fury DDR4", 50, "budget"),
        ("Motherboard", "MSI PRO B660M", 100, "budget"),
    ]
    
    cursor.executemany('''
        INSERT INTO components (part_type, name, price, target_workload) 
        VALUES (?, ?, ?, ?)
    ''', inventory)
    conn.commit()
    
    return conn

# Initialize the database when the script runs
db_connection = setup_database()

# 3. Define the MCP Tool
@mcp.tool()
def suggest_pc_build(budget: int, use_case: str) -> str:
    """
    Queries the database to suggest a PC build based on budget and use case.
    Valid use_cases in this mock DB are '3D modeling' and 'budget'.
    """
    cursor = db_connection.cursor()
    
    # Fetch all parts that match the requested use case
    cursor.execute(
        "SELECT part_type, name, price FROM components WHERE target_workload = ?", 
        (use_case,)
    )
    available_parts = cursor.fetchall()

    build = {}
    total_cost = 0

    # Simple logic to pick one of each component type that fits the budget
    for part_type, name, price in available_parts:
        if part_type not in build and (total_cost + price) <= budget:
            build[part_type] = {"name": name, "price": price}
            total_cost += price

    # If we couldn't assemble a build (e.g., budget too low)
    if not build or len(build) < 4:
        return json.dumps({
            "error": "Could not find a complete set of parts fitting that budget and use case.",
            "attempted_budget": budget
        })

    # Return the structured data back to the ADK agent
    result = {
        "status": "success",
        "suggested_build": build,
        "total_cost": total_cost,
        "remaining_budget": budget - total_cost
    }
    
    return json.dumps(result, indent=2)

# 4. Run the server via stdio (Standard for MCP)
if __name__ == "__main__":
    mcp.run()