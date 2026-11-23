"""
rip_solver.py
Implementation of the Reciprocating Integer Programming (RIP) technique for Birchbox
product assortment optimization, following Lustig, Randall, and Randall (INFORMS 2021).
"""

import time
import math
import pulp
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple, Optional, Any
from src.data_loader import AssortmentProblemData
from src.pattern_generator import PatternGenerator

@dataclass
class Pattern:
    id: str
    products: Set[str]
    eligible_subscribers: Set[str]

@dataclass
class RIPSolverResult:
    status: str
    phase_reached: str
    solve_time_seconds: float
    total_patterns_generated: int
    boxes_built: int
    subscribers_served: int
    total_shortage: int
    box_assignments: List[Dict[str, Any]]
    shortages: Dict[str, int]

class RIPSolver:
    """
    Executes the RIP decomposition loop:
    1. Bootstrap: Generate initial patterns via subproblem MIP
    2. Relax & Sift: LP relaxation rounds with reduced costs / dual guidance
    3. Master MIP: Hierarchical optimization (Assign subscribers -> Minimize boxes -> Satisfy product mins)
    """

    def __init__(self, data: AssortmentProblemData, hard_limit: bool = True):
        self.data = data
        self.hard_limit = hard_limit
        self.generator = PatternGenerator(data)
        self.patterns: List[Pattern] = []

    def _is_subscriber_eligible(self, pattern_products: Set[str], sub_id: str) -> bool:
        """Checks if a pattern meets subscriber must-receive and cannot-receive conditions."""
        must_recv = self.data.must_receive_p.get(sub_id, set())
        cannot_recv = self.data.cannot_receive_p.get(sub_id, set())

        if not must_recv.issubset(pattern_products):
            return False
        if len(cannot_recv.intersection(pattern_products)) > 0:
            return False
        return True

    def bootstrap(self, target_patterns_per_sub: int = 2, max_total_patterns: int = 30) -> int:
        """
        Bootstrap phase: generate an initial pool of valid box patterns.
        Dynamically prioritizes subscribers with fewer patterns and products with high inventory.
        """
        P = list(self.data.products.keys())
        S = list(self.data.subscribers.keys())

        pat_cnt = {s: 0 for s in S}
        prod_cnt = {p: 0 for p in P}

        pattern_idx = 0

        while any(pat_cnt[s] < target_patterns_per_sub for s in S) and len(self.patterns) < max_total_patterns:
            # Pick subscriber with smallest pattern count
            s = min(S, key=lambda sub: pat_cnt[sub])

            # Dynamic weights pi_p based on inventory and product frequency (Equation 32)
            max_prod_cnt = max(prod_cnt.values()) if max(prod_cnt.values()) > 0 else 1
            pi_weights = {}
            for p in P:
                inv = self.data.products[p].phi_u
                pi_weights[p] = inv * (max_prod_cnt / (1.0 + prod_cnt[p]))

            pat_products = self.generator.generate_pattern_for_subscriber(s, pi_weights=pi_weights)
            if pat_products is None:
                # If subscriber cannot generate more patterns, break or continue
                pat_cnt[s] += 1
                continue

            # Check eligibility across all subscribers
            eligible_subs = {sub for sub in S if self._is_subscriber_eligible(pat_products, sub)}

            # Must satisfy minimum subscribers per box (sigma_l)
            if len(eligible_subs) >= self.data.sigma_l:
                pattern_idx += 1
                pat_id = f"Pat_{pattern_idx:03d}"
                new_pat = Pattern(id=pat_id, products=pat_products, eligible_subscribers=eligible_subs)
                self.patterns.append(new_pat)

                # Update counters
                for sub in eligible_subs:
                    pat_cnt[sub] += 1
                for p in pat_products:
                    prod_cnt[p] += 1
            else:
                pat_cnt[s] += 1

        return len(self.patterns)

    def solve(self, time_limit: int = 60, msg: bool = False) -> RIPSolverResult:
        """Runs the complete RIP optimization workflow."""
        start_time = time.time()

        # Step 1: Bootstrap
        num_patterns = self.bootstrap()
        if num_patterns == 0:
            return RIPSolverResult(
                status="Infeasible",
                phase_reached="Bootstrap",
                solve_time_seconds=round(time.time() - start_time, 3),
                total_patterns_generated=0,
                boxes_built=0,
                subscribers_served=0,
                total_shortage=0,
                box_assignments=[],
                shortages={}
            )

        # Step 2: Solve Master Problem
        # Sets
        P = list(self.data.products.keys())
        S = list(self.data.subscribers.keys())
        B = [pat.id for pat in self.patterns]
        pat_by_id = {pat.id: pat for pat in self.patterns}

        # B_p: patterns containing product p
        B_p = {p: [pat.id for pat in self.patterns if p in pat.products] for p in P}
        # B_s: patterns subscriber s is eligible for
        B_s = {s: [pat.id for pat in self.patterns if s in pat.eligible_subscribers] for s in S}

        # Master MIP Problem
        prob = pulp.LpProblem("RIP_Master_Problem", pulp.LpMaximize)

        # Decision Variables
        y = pulp.LpVariable.dicts("y", B, cat=pulp.LpBinary)
        n = pulp.LpVariable.dicts("n", B, lowBound=0, cat=pulp.LpInteger)
        w = {}
        for s in S:
            for b in B_s[s]:
                w[(s, b)] = pulp.LpVariable(f"w_{s}_{b}", cat=pulp.LpBinary)

        # q_pb only for p in P_b
        q = {}
        for pat in self.patterns:
            for p in pat.products:
                q[(p, pat.id)] = pulp.LpVariable(f"q_{p}_{pat.id}", lowBound=0, cat=pulp.LpInteger)

        z = pulp.LpVariable.dicts("z", P, lowBound=0, cat=pulp.LpInteger)

        # Objective: Hierarchical / Blended Phase 1
        # Maximize subscribers receiving box + minimize box count + penalize shortage
        obj_subs = 100.0 * pulp.lpSum(w[(s, b)] for s in S for b in B_s[s])
        obj_boxes = - 5.0 * pulp.lpSum(y[b] for b in B)
        obj_shortage = - pulp.lpSum((2.0 / (self.data.products[p].phi_l + 1.0)) * z[p] for p in P)
        prob += obj_subs + obj_boxes + obj_shortage, "Master_Hierarchical_Objective"

        # Constraints
        # (1r) Product upper capacity
        for p in P:
            prob += pulp.lpSum(q[(p, b)] for b in B_p[p]) <= self.data.products[p].phi_u, f"MaxInv_{p}"

        # (2r) Product lower requirement with slack z_p
        for p in P:
            prob += pulp.lpSum(q[(p, b)] for b in B_p[p]) + z[p] >= self.data.products[p].phi_l, f"MinDemand_{p}"

        # (3) Slack bound
        for p in P:
            prob += z[p] <= self.data.products[p].phi_u, f"SlackBound_{p}"

        # (4r) Minimum box configurations
        prob += pulp.lpSum(y[b] for b in B) >= self.data.tau_l, "MinBoxesBuilt"

        # (28) Hard constraint on max box configurations
        if self.hard_limit:
            prob += pulp.lpSum(y[b] for b in B) <= self.data.tau_u, "MaxBoxesBuilt"

        # (5r) & (6r) Box size bounds [sigma_l * y_b, sigma_u * y_b]
        for b in B:
            prob += n[b] <= self.data.sigma_u * y[b], f"MaxBoxSize_{b}"
            prob += n[b] >= self.data.sigma_l * y[b], f"MinBoxSize_{b}"

        # (9r) q_pb == n_b for all p in P_b
        for pat in self.patterns:
            for p in pat.products:
                prob += q[(p, pat.id)] == n[pat.id], f"ProductQtyEqualsBoxSize_{p}_{pat.id}"

        # (10r) q_pb <= phi_u * y_b
        for pat in self.patterns:
            for p in pat.products:
                prob += q[(p, pat.id)] <= self.data.products[p].phi_u * y[pat.id], f"QtyBoundedByInv_{p}_{pat.id}"

        # (11r) Each subscriber assigned to at most one box
        for s in S:
            prob += pulp.lpSum(w[(s, b)] for b in B_s[s]) <= 1, f"SubscriberAtMostOneBox_{s}"

        # (12r) Box size equals assigned eligible subscribers
        for b in B:
            eligible_s = pat_by_id[b].eligible_subscribers
            prob += pulp.lpSum(w[(s, b)] for s in eligible_s) == n[b], f"BoxSizeMatchesSubs_{b}"

        # (24) Cut: Total boxes containing p bounded by phi_u / sigma_l
        for p in P:
            max_boxes_p = math.floor(self.data.products[p].phi_u / self.data.sigma_l)
            prob += pulp.lpSum(y[b] for b in B_p[p]) <= max_boxes_p, f"MaxBoxesForProduct_{p}"

        # Solve Master
        solver = pulp.PULP_CBC_CMD(timeLimit=time_limit, msg=msg)
        prob.solve(solver)
        duration = time.time() - start_time

        status_str = pulp.LpStatus[prob.status]

        box_assignments = []
        subs_served = 0
        boxes_built = 0

        for b in B:
            yb_val = int(round(pulp.value(y[b]) or 0))
            nb_val = int(round(pulp.value(n[b]) or 0))
            if yb_val == 1 and nb_val > 0:
                boxes_built += 1
                assigned_subs = [s for s in pat_by_id[b].eligible_subscribers if round(pulp.value(w[(s, b)]) or 0) == 1]
                subs_served += len(assigned_subs)
                pat = pat_by_id[b]
                box_assignments.append({
                    "box_id": b,
                    "size_nb": nb_val,
                    "products": sorted(list(pat.products)),
                    "product_names": [self.data.products[p].name for p in sorted(list(pat.products))],
                    "subscribers": assigned_subs,
                    "attribute_totals": {
                        a: sum(self.data.products[p].attributes.get(a, 0.0) for p in pat.products)
                        for a in self.data.attributes.keys()
                    }
                })

        shortages = {p: int(round(pulp.value(z[p]) or 0)) for p in P}

        return RIPSolverResult(
            status=status_str,
            phase_reached="Master_MIP_Completed",
            solve_time_seconds=round(duration, 3),
            total_patterns_generated=len(self.patterns),
            boxes_built=boxes_built,
            subscribers_served=subs_served,
            total_shortage=sum(shortages.values()),
            box_assignments=box_assignments,
            shortages=shortages
        )
