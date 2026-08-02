import sys
import os

# Add backend directory to path
sys.path.insert(0, "/home/charan_derangula/projects/intelligentSystems/backend")

from app.main import app

routes = []
for route in app.routes:
    # Check if it has path and methods
    path = getattr(route, "path", None)
    methods = getattr(route, "methods", None)
    endpoint = getattr(route, "endpoint", None)
    endpoint_name = endpoint.__name__ if endpoint else None
    
    if path:
        routes.append((path, methods, endpoint_name))

print("Total routes found:", len(routes))
for p, m, e in sorted(routes, key=lambda x: x[0]):
    print(f"{p} | {m} | {e}")
