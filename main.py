"""
main.py
Main entry point for Birchbox Product Assortment Optimization.
Allows solving with Original MIP, Reciprocating Integer Programming (RIP), or comparing both.
"""

import os
import sys
import argparse
import json

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_loader import load_data_from_directory
from src.original_mip import solve_original_mip
from src.rip_solver import RIPSolver

def print_banner():
    print("=" * 80)
    print("  BIRCHBOX PRODUCT ASSORTMENT OPTIMIZATION (INFORMS / IIT ROORKEE MSO)")
    print("  Mixed-Integer Programming vs Reciprocating Integer Programming (RIP)")
    print("=" * 80)

def display_solution(title: str, sol):
    print(f"\n--- {title} ---")
    print(f"Status:              {sol.status}")
    print(f"Solve Time:          {sol.solve_time_seconds:.3f} s")
    print(f"Boxes Built:         {sol.boxes_built}")
    print(f"Subscribers Served:  {sol.subscribers_served}")
    print(f"Product Shortage:    {sol.total_shortage}")

    print("\nAllocated Box Configurations:")
    for box in getattr(sol, "box_details", getattr(sol, "box_assignments", [])):
        print(f"  [{box['box_id']}] Size: {box['size_nb']} subscribers | Products ({len(box['products'])}): {', '.join(box['products'])}")
        print(f"       Items: {', '.join(box['product_names'])}")
        attrs = box.get("attribute_totals", {})
        attr_str = ", ".join(f"{k}: {v:.1f}" for k, v in attrs.items())
        print(f"       Totals: {attr_str}")
        print(f"       Subscribers: {', '.join(box['subscribers'])}")

def main():
    parser = argparse.ArgumentParser(description="Birchbox Assortment Optimization Runner")
    parser.add_argument("--data-dir", type=str, default="data", help="Directory containing problem CSVs")
    parser.add_argument("--mode", type=str, choices=["original", "rip", "compare"], default="original",
                        help="Optimization formulation to execute (default: original)")
    parser.add_argument("--time-limit", type=int, default=60, help="Solver time limit in seconds")
    parser.add_argument("--verbose", action="store_true", help="Print detailed solver logs")

    args = parser.parse_args()

    # Resolve data directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, args.data_dir) if not os.path.isabs(args.data_dir) else args.data_dir

    if not os.path.exists(data_path):
        print(f"Error: Data directory '{data_path}' not found.")
        sys.exit(1)

    print_banner()
    print(f"Loading data from: {data_path}")
    data = load_data_from_directory(data_path)
    print(f"Loaded: {len(data.products)} products, {len(data.subscribers)} subscribers, {len(data.attributes)} attributes.")
    print(f"Configuration limits: tau in [{data.tau_l}, {data.tau_u}], box capacity in [{data.gamma_l}, {data.gamma_u}].\n")

    if args.mode in ["original", "compare"]:
        print("Solving Original MIP formulation (Equations 1-23)...")
        sol_orig = solve_original_mip(data, time_limit=args.time_limit, msg=args.verbose)
        display_solution("ORIGINAL MIP FORMULATION", sol_orig)

    if args.mode in ["rip", "compare"]:
        print("\nSolving with Reciprocating Integer Programming (RIP)...")
        rip_solver = RIPSolver(data, hard_limit=True)
        sol_rip = rip_solver.solve(time_limit=args.time_limit, msg=args.verbose)
        display_solution("RECIPROCATING INTEGER PROGRAMMING (RIP)", sol_rip)

    if args.mode == "compare":
        print("\n" + "=" * 80)
        print("                        PERFORMANCE COMPARISON")
        print("=" * 80)
        print(f"{'Metric':<28} | {'Original MIP':<20} | {'RIP Approach':<20}")
        print("-" * 80)
        print(f"{'Status':<28} | {sol_orig.status:<20} | {sol_rip.status:<20}")
        print(f"{'Solve Time (s)':<28} | {sol_orig.solve_time_seconds:<20.3f} | {sol_rip.solve_time_seconds:<20.3f}")
        print(f"{'Boxes Built':<28} | {sol_orig.boxes_built:<20} | {sol_rip.boxes_built:<20}")
        print(f"{'Subscribers Served':<28} | {sol_orig.subscribers_served:<20} | {sol_rip.subscribers_served:<20}")
        print(f"{'Total Shortage (units)':<28} | {sol_orig.total_shortage:<20} | {sol_rip.total_shortage:<20}")
        print("=" * 80)

if __name__ == "__main__":
    main()
