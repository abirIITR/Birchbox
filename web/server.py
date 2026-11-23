"""
server.py
Lightweight HTTP backend for the Birchbox Live Interactive Assortment Solver.
Uses Python's standard library http.server, connecting PuLP Original MIP to an interactive web frontend.
"""

import os
import sys
import json
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler, ThreadingHTTPServer
import urllib.parse

# Ensure src modules are imported correctly
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

from src.data_loader import load_data_from_directory, AssortmentProblemData, AttributeRule, Product, Subscriber
from src.original_mip import solve_original_mip

DATA_DIR = os.path.join(base_dir, "data")
BASE_DATA = load_data_from_directory(DATA_DIR)

class LiveSolverHandler(SimpleHTTPRequestHandler):
    """Handles static files and dynamic live solver API endpoints."""

    def __init__(self, *args, **kwargs):
        web_dir = os.path.join(base_dir, "web")
        super().__init__(*args, directory=web_dir, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/data":
            self._handle_get_data()
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/solve":
            self._handle_solve()
        else:
            self.send_error(404, "Endpoint not found")

    def _handle_get_data(self):
        """Returns baseline dataset details to initialize sliders and inputs."""
        base_data = load_data_from_directory(DATA_DIR)
        cats = sorted(list(set(p.category for p in base_data.products.values() if p.category)))
        payload = {
            "parameters": {
                "tau_l": base_data.tau_l,
                "tau_u": base_data.tau_u,
                "sigma_l": base_data.sigma_l,
                "sigma_u": base_data.sigma_u,
                "gamma_l": base_data.gamma_l,
                "gamma_u": base_data.gamma_u,
                "big_m": base_data.big_m
            },
            "categories": cats,
            "attributes": {
                name: {
                    "min": rule.alpha_l,
                    "max": rule.alpha_u,
                    "unit": rule.unit
                } for name, rule in base_data.attributes.items()
            },
            "products": [
                {
                    "id": p.id,
                    "name": p.name,
                    "category": p.category,
                    "brand": p.brand,
                    "phi_l": p.phi_l,
                    "phi_u": p.phi_u,
                    "attributes": p.attributes
                } for p in base_data.products.values()
            ],
            "subscribers": [
                {
                    "id": s.id,
                    "cluster_name": s.cluster_name,
                    "count": s.subscriber_count,
                    "must_receive": list(base_data.must_receive_p.get(s.id, [])),
                    "cannot_receive": list(base_data.cannot_receive_p.get(s.id, []))
                } for s in base_data.subscribers.values()
            ],
            "cooccur_pairs": base_data.cooccur_pairs,
            "conflict_pairs": base_data.conflict_pairs
        }
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def _handle_solve(self):
        """Receives custom slider values, runs Original MIP live, and returns the solution."""
        base_data = load_data_from_directory(DATA_DIR)
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        
        try:
            params = json.loads(body.decode("utf-8"))
        except Exception as e:
            self.send_error(400, f"Invalid JSON payload: {str(e)}")
            return

        # Clone baseline data with user-overridden constraint values
        custom_attrs = {}
        for name, rule in base_data.attributes.items():
            min_val = float(params.get(f"attr_{name}_min", rule.alpha_l))
            max_val = float(params.get(f"attr_{name}_max", rule.alpha_u))
            custom_attrs[name] = AttributeRule(name=name, alpha_l=min_val, alpha_u=max_val, unit=rule.unit)

        enforce_pairs = bool(params.get("enforce_pairs", True))
        enforce_conflicts = bool(params.get("enforce_conflicts", True))
        enforce_preferences = bool(params.get("enforce_preferences", True))

        # 1. Custom or Baseline Products
        inv_multiplier = float(params.get("inv_multiplier", 1.0))
        custom_products = {}
        if "products" in params and isinstance(params["products"], list) and len(params["products"]) > 0:
            for p_dict in params["products"]:
                pid = str(p_dict.get("id", "")).strip()
                if not pid: continue
                custom_products[pid] = Product(
                    id=pid,
                    name=str(p_dict.get("name", pid)),
                    category=str(p_dict.get("category", "Skincare")),
                    brand=str(p_dict.get("brand", "Generic")),
                    phi_l=int(p_dict.get("phi_l", 2)),
                    phi_u=max(1, int(round(int(p_dict.get("phi_u", 20)) * inv_multiplier))),
                    attributes=p_dict.get("attributes", {})
                )
        else:
            for pid, p in base_data.products.items():
                custom_products[pid] = Product(
                    id=p.id,
                    name=p.name,
                    category=p.category,
                    brand=p.brand,
                    phi_l=p.phi_l,
                    phi_u=max(1, int(round(p.phi_u * inv_multiplier))),
                    attributes=p.attributes
                )

        # 2. Custom or Baseline Pairings
        custom_cooccur = []
        if "cooccur_pairs" in params and isinstance(params["cooccur_pairs"], list):
            for pair in params["cooccur_pairs"]:
                if isinstance(pair, (list, tuple)) and len(pair) == 2:
                    p1, p2 = str(pair[0]), str(pair[1])
                    if p1 in custom_products and p2 in custom_products:
                        custom_cooccur.append((p1, p2))
                elif isinstance(pair, dict) and "product_id_1" in pair and "product_id_2" in pair:
                    p1, p2 = str(pair["product_id_1"]), str(pair["product_id_2"])
                    if p1 in custom_products and p2 in custom_products:
                        custom_cooccur.append((p1, p2))
        else:
            custom_cooccur = [pair for pair in base_data.cooccur_pairs if pair[0] in custom_products and pair[1] in custom_products]
        if not enforce_pairs:
            custom_cooccur = []

        custom_conflict = []
        if "conflict_pairs" in params and isinstance(params["conflict_pairs"], list):
            for pair in params["conflict_pairs"]:
                if isinstance(pair, (list, tuple)) and len(pair) == 2:
                    p1, p2 = str(pair[0]), str(pair[1])
                    if p1 in custom_products and p2 in custom_products:
                        custom_conflict.append((p1, p2))
                elif isinstance(pair, dict) and "product_id_1" in pair and "product_id_2" in pair:
                    p1, p2 = str(pair["product_id_1"]), str(pair["product_id_2"])
                    if p1 in custom_products and p2 in custom_products:
                        custom_conflict.append((p1, p2))
        else:
            custom_conflict = [pair for pair in base_data.conflict_pairs if pair[0] in custom_products and pair[1] in custom_products]
        if not enforce_conflicts:
            custom_conflict = []

        # 3. Eligibility rules
        custom_must_receive_p = {s: set(p for p in base_data.must_receive_p.get(s, []) if p in custom_products) for s in base_data.subscribers} if enforce_preferences else {s: set() for s in base_data.subscribers}
        custom_cannot_receive_p = {s: set(p for p in base_data.cannot_receive_p.get(s, []) if p in custom_products) for s in base_data.subscribers} if enforce_preferences else {s: set() for s in base_data.subscribers}

        # Override with dynamic user-edited subscriber rules if supplied
        if enforce_preferences and "subscriber_rules" in params and isinstance(params["subscriber_rules"], dict):
            for sid, rule in params["subscriber_rules"].items():
                if sid in custom_must_receive_p:
                    m_list = [p for p in rule.get("must_receive", []) if p in custom_products]
                    c_list = [p for p in rule.get("cannot_receive", []) if p in custom_products]
                    custom_must_receive_p[sid] = set(m_list)
                    custom_cannot_receive_p[sid] = set(c_list)
            
        # Rebuild reverse lookups
        custom_must_receive_s = {p: set() for p in custom_products}
        custom_cannot_receive_s = {p: set() for p in custom_products}
        for sid, p_set in custom_must_receive_p.items():
            for p in p_set:
                if p in custom_must_receive_s:
                    custom_must_receive_s[p].add(sid)
        for sid, p_set in custom_cannot_receive_p.items():
            for p in p_set:
                if p in custom_cannot_receive_s:
                    custom_cannot_receive_s[p].add(sid)

        max_brand = int(params["max_brand_items"]) if params.get("max_brand_items") and int(params["max_brand_items"]) > 0 else None
        max_cat = int(params["max_category_items"]) if params.get("max_category_items") and int(params["max_category_items"]) > 0 else None
        min_cov = float(params["min_coverage_pct"]) if params.get("min_coverage_pct") and float(params["min_coverage_pct"]) > 0 else None

        problem_data = AssortmentProblemData(
            products=custom_products,
            subscribers=base_data.subscribers,
            attributes=custom_attrs,
            tau_l=int(params.get("tau_l", base_data.tau_l)),
            tau_u=int(params.get("tau_u", base_data.tau_u)),
            sigma_l=int(params.get("sigma_l", base_data.sigma_l)),
            sigma_u=int(params.get("sigma_u", base_data.sigma_u)),
            gamma_l=int(params.get("gamma_l", base_data.gamma_l)),
            gamma_u=int(params.get("gamma_u", base_data.gamma_u)),
            big_m=float(params.get("big_m", base_data.big_m)),
            max_brand_items=max_brand,
            max_category_items=max_cat,
            min_coverage_pct=min_cov,
            cooccur_pairs=custom_cooccur,
            conflict_pairs=custom_conflict,
            must_receive_p=custom_must_receive_p,
            cannot_receive_p=custom_cannot_receive_p,
            must_receive_s=custom_must_receive_s,
            cannot_receive_s=custom_cannot_receive_s
        )

        time_limit = int(params.get("time_limit", 30))

        # Solve live using Original MIP Formulation
        start_t = time.time()
        solution = solve_original_mip(problem_data, time_limit=time_limit, msg=False)
        duration = time.time() - start_t

        response_payload = {
            "status": solution.status,
            "objective_value": solution.objective_value,
            "solve_time_seconds": round(duration, 3),
            "boxes_built": solution.boxes_built,
            "subscribers_served": solution.subscribers_served,
            "total_subscribers": len(BASE_DATA.subscribers),
            "total_shortage": solution.total_shortage,
            "boxes": solution.box_details,
            "shortages": solution.shortages,
            "applied_parameters": {
                "tau_l": problem_data.tau_l,
                "tau_u": problem_data.tau_u,
                "sigma_l": problem_data.sigma_l,
                "sigma_u": problem_data.sigma_u,
                "gamma_l": problem_data.gamma_l,
                "gamma_u": problem_data.gamma_u,
                "enforce_pairs": enforce_pairs,
                "enforce_conflicts": enforce_conflicts,
                "enforce_preferences": enforce_preferences
            }
        }

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response_payload).encode("utf-8"))

def run_server(port=8050):
    server_address = ("0.0.0.0", port)
    httpd = ThreadingHTTPServer(server_address, LiveSolverHandler)
    httpd.daemon_threads = True
    print(f"============================================================")
    print(f"  BIRCHBOX LIVE MIP SOLVER SERVER RUNNING AT:")
    print(f"  http://localhost:{port} (or http://127.0.0.1:{port})")
    print(f"============================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8050
    run_server(port)
