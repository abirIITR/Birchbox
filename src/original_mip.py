"""
original_mip.py
Direct mathematical implementation of Birchbox's Original Mixed-Integer Programming (MIP)
formulation as published in Lustig, Randall, Randall (INFORMS 2021).
Equations (1) through (23).
"""

import time
import pulp
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from src.data_loader import AssortmentProblemData

@dataclass
class MIPSolution:
    status: str
    objective_value: float
    solve_time_seconds: float
    boxes_built: int
    subscribers_served: int
    total_shortage: int
    box_details: List[Dict[str, Any]]
    shortages: Dict[str, int]

def solve_original_mip(data: AssortmentProblemData, time_limit: Optional[int] = 60, msg: bool = False) -> MIPSolution:
    """
    Constructs and solves the Original Birchbox MIP model using PuLP (default CBC solver).
    Enforces equations (1) to (23).
    """
    start_time = time.time()
    
    # Model definition
    prob = pulp.LpProblem("Birchbox_Original_MIP", pulp.LpMaximize)

    # Sets
    P = list(data.products.keys())
    S = list(data.subscribers.keys())
    B = [f"Box_{b+1:02d}" for b in range(data.tau_u)]
    A = list(data.attributes.keys())

    # Decision Variables
    y = pulp.LpVariable.dicts("y", B, cat=pulp.LpBinary)
    n = pulp.LpVariable.dicts("n", B, lowBound=0, cat=pulp.LpInteger)
    x = pulp.LpVariable.dicts("x", (P, B), cat=pulp.LpBinary)
    q = pulp.LpVariable.dicts("q", (P, B), lowBound=0, cat=pulp.LpInteger)
    w = pulp.LpVariable.dicts("w", (S, B), cat=pulp.LpBinary)
    z = pulp.LpVariable.dicts("z", P, lowBound=0, cat=pulp.LpInteger)

    # Objective Function (Equation 23)
    # maximize 0.5 * sum(n_b) + 0.5 * sum(w_sb) + sum(x_pb / 3600) - sum(2 * z_p / (phi_l_p + 1))
    obj_boxes = 0.5 * pulp.lpSum(n[b] for b in B)
    obj_subs = 0.5 * pulp.lpSum(w[s][b] for s in S for b in B)
    obj_pert = pulp.lpSum(x[p][b] / 3600.0 for p in P for b in B)
    obj_penalty = pulp.lpSum(2.0 / (data.products[p].phi_l + 1.0) * z[p] for p in P)
    prob += obj_boxes + obj_subs + obj_pert - obj_penalty, "Blended_Objective"

    # Constraints

    # (1) Total quantity assigned <= maximum inventory phi_u
    for p in P:
        prob += pulp.lpSum(q[p][b] for b in B) <= data.products[p].phi_u, f"MaxInv_{p}"

    # (2) Total quantity assigned + slack zp >= minimum requirement phi_l
    for p in P:
        prob += pulp.lpSum(q[p][b] for b in B) + z[p] >= data.products[p].phi_l, f"MinReq_{p}"

    # (3) Shortage slack bounded by phi_u
    for p in P:
        prob += z[p] <= data.products[p].phi_u, f"SlackBound_{p}"

    # (4) Minimum box configurations built
    prob += pulp.lpSum(y[b] for b in B) >= data.tau_l, "MinBoxesBuilt"

    # (5) & (6) Number of boxes built per configuration within [sigma_l * y_b, sigma_u * y_b]
    for b in B:
        prob += n[b] <= data.sigma_u * y[b], f"MaxBoxSize_{b}"
        prob += n[b] >= data.sigma_l * y[b], f"MinBoxSize_{b}"

    # (7) & (8) Total product units in box bounded by [gamma_l * n_b, gamma_u * n_b]
    for b in B:
        prob += pulp.lpSum(q[p][b] for p in P) >= data.gamma_l * n[b], f"MinProductsCount_{b}"
        prob += pulp.lpSum(q[p][b] for p in P) <= data.gamma_u * n[b], f"MaxProductsCount_{b}"

    # (9) Quantity of product in box cannot exceed box size
    for b in B:
        for p in P:
            prob += q[p][b] <= n[b], f"Q_le_Nb_{p}_{b}"

    # (10) Quantity bounded by product inventory and box activation
    for b in B:
        for p in P:
            prob += q[p][b] <= data.products[p].phi_u * y[b], f"Q_le_PhiU_Yb_{p}_{b}"

    # (11) Subscriber can be assigned to at most one box
    for s in S:
        prob += pulp.lpSum(w[s][b] for b in B) <= 1, f"SubscriberAtMostOneBox_{s}"

    # (12) Box size equals total assigned subscribers
    for b in B:
        prob += pulp.lpSum(w[s][b] for s in S) == n[b], f"BoxSizeEqualsSubscribers_{b}"

    # (13) If product p is in box b, q_pb >= n_b - M(1 - x_pb)
    for b in B:
        for p in P:
            prob += q[p][b] >= n[b] - data.big_m * (1 - x[p][b]), f"BigM_Q_ge_N_{p}_{b}"

    # (14) Quantity is zero if product is not in box
    for b in B:
        for p in P:
            prob += q[p][b] <= data.products[p].phi_u * x[p][b], f"Q_le_PhiU_X_{p}_{b}"

    # (15) Product cannot be assigned if box is not built
    for b in B:
        for p in P:
            prob += x[p][b] <= y[b], f"X_le_Y_{p}_{b}"

    # (16) Subscriber must-receive requirements
    for b in B:
        for p in P:
            s_hat = data.must_receive_s[p]
            if len(s_hat) > 0:
                prob += pulp.lpSum(w[s][b] for s in s_hat) <= len(s_hat) * x[p][b], f"MustReceiveReq_{p}_{b}"

    # (17) Subscriber cannot-receive exclusions
    for b in B:
        for p in P:
            s_tilde = data.cannot_receive_s[p]
            if len(s_tilde) > 0:
                prob += pulp.lpSum(w[s][b] for s in s_tilde) <= len(s_tilde) * (1 - x[p][b]), f"CannotReceiveReq_{p}_{b}"

    # (18) Attribute constraints (e.g. value, weight, volume)
    for b in B:
        for a, rule in data.attributes.items():
            attr_sum = pulp.lpSum(data.products[p].attributes.get(a, 0.0) * x[p][b] for p in P)
            prob += attr_sum >= rule.alpha_l * y[b], f"AttrMin_{a}_{b}"
            prob += attr_sum <= rule.alpha_u * y[b], f"AttrMax_{a}_{b}"

    # (19) & (20) Number of products per box between [gamma_l, gamma_u] if box built
    for b in B:
        prob += pulp.lpSum(x[p][b] for p in P) <= data.gamma_u * y[b], f"MaxDistinctProducts_{b}"
        prob += pulp.lpSum(x[p][b] for p in P) >= data.gamma_l * y[b], f"MinDistinctProducts_{b}"

    # (21) Co-occurring pairs (must be shipped together)
    for idx, (p1, p2) in enumerate(data.cooccur_pairs):
        for b in B:
            prob += x[p1][b] == x[p2][b], f"Cooccur_{idx}_{b}"

    # (22) Conflicting pairs (cannot be in the same box)
    for idx, (p1, p2) in enumerate(data.conflict_pairs):
        for b in B:
            prob += x[p1][b] + x[p2][b] <= 1, f"Conflict_{idx}_{b}"

    # (23a) Brand Diversity Constraint: Max products from same brand in a box
    if data.max_brand_items is not None and data.max_brand_items > 0:
        brands = set(data.products[p].brand for p in P if data.products[p].brand)
        for br in brands:
            brand_prods = [p for p in P if data.products[p].brand == br]
            if len(brand_prods) > data.max_brand_items:
                for b in B:
                    prob += pulp.lpSum(x[p][b] for p in brand_prods) <= data.max_brand_items * y[b], f"MaxBrand_{br}_{b}"

    # (23b) Category Diversity Constraint: Max products from same category in a box
    if data.max_category_items is not None and data.max_category_items > 0:
        categories = set(data.products[p].category for p in P if data.products[p].category)
        for cat in categories:
            cat_prods = [p for p in P if data.products[p].category == cat]
            if len(cat_prods) > data.max_category_items:
                for b in B:
                    prob += pulp.lpSum(x[p][b] for p in cat_prods) <= data.max_category_items * y[b], f"MaxCategory_{cat}_{b}"

    # (23c) Minimum Customer Service Level Coverage
    if data.min_coverage_pct is not None and data.min_coverage_pct > 0:
        min_subs = int(round((data.min_coverage_pct / 100.0) * len(S)))
        prob += pulp.lpSum(w[s][b] for s in S for b in B) >= min_subs, "MinCustomerCoverageLevel"

    # Solve
    solver = pulp.PULP_CBC_CMD(timeLimit=time_limit, msg=msg)
    prob.solve(solver)
    solve_duration = time.time() - start_time

    status_str = pulp.LpStatus[prob.status]
    obj_val = pulp.value(prob.objective) if prob.objective is not None else 0.0

    boxes_built_count = 0
    subs_assigned_count = 0
    box_details = []

    for b in B:
        yb_val = int(round(pulp.value(y[b]) or 0))
        nb_val = int(round(pulp.value(n[b]) or 0))
        if yb_val == 1 and nb_val > 0:
            boxes_built_count += 1
            assigned_prods = [p for p in P if round(pulp.value(x[p][b]) or 0) == 1]
            assigned_subs = [s for s in S if round(pulp.value(w[s][b]) or 0) == 1]
            subs_assigned_count += len(assigned_subs)
            box_details.append({
                "box_id": b,
                "size_nb": nb_val,
                "products": assigned_prods,
                "product_names": [data.products[p].name for p in assigned_prods],
                "subscribers": assigned_subs,
                "attribute_totals": {
                    a: sum(data.products[p].attributes.get(a, 0.0) for p in assigned_prods)
                    for a in A
                }
            })

    shortages = {p: int(round(pulp.value(z[p]) or 0)) for p in P}
    total_shortage_val = sum(shortages.values())

    return MIPSolution(
        status=status_str,
        objective_value=round(obj_val, 4),
        solve_time_seconds=round(solve_duration, 3),
        boxes_built=boxes_built_count,
        subscribers_served=subs_assigned_count,
        total_shortage=total_shortage_val,
        box_details=box_details,
        shortages=shortages
    )
