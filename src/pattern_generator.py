"""
pattern_generator.py
Subproblem MIP for generating valid single box configurations (patterns)
as described in Equations (16r)-(22r), (29), and (30) of the RIP algorithm.
"""

import pulp
from typing import Dict, List, Set, Optional, Tuple
from src.data_loader import AssortmentProblemData

class PatternGenerator:
    """Solves the subproblem MIP to generate feasible box patterns satisfying all business rules."""

    def __init__(self, data: AssortmentProblemData):
        self.data = data
        self.existing_patterns: List[Set[str]] = []

    def generate_pattern_for_subscriber(
        self,
        subscriber_id: str,
        pi_weights: Optional[Dict[str, float]] = None,
        msg: bool = False
    ) -> Optional[Set[str]]:
        """
        Solves pattern subproblem for subscriber s:
        max sum(pi_p * x_p)
        s.t.
          (16r) x_p = 1 for p in P_hat_s
          (17r) x_p = 0 for p in P_bar_s
          (18r) alpha_l_a <= sum(mu_ap * x_p) <= alpha_u_a
          (19r) sum(x_p) <= gamma_u
          (20r) sum(x_p) >= gamma_l
          (21r) x_p1 == x_p2 for (p1, p2) in R_hat
          (22r) x_p1 + x_p2 <= 1 for (p1, p2) in R_bar
          (29)  sum_{p in P_b} x_p - sum_{p not in P_b} x_p <= |P_b| - 1 for all previous patterns
        """
        prob = pulp.LpProblem(f"PatternSubproblem_{subscriber_id}", pulp.LpMaximize)
        P = list(self.data.products.keys())

        # Decision variable: x_p in {0, 1}
        x = pulp.LpVariable.dicts("x", P, cat=pulp.LpBinary)

        # Objective Function (30): max sum(pi_p * x_p)
        if pi_weights is None:
            # Default: favor products with high inventory phi_u (Bootstrap phase)
            pi_weights = {p: float(self.data.products[p].phi_u) for p in P}

        prob += pulp.lpSum(pi_weights.get(p, 0.0) * x[p] for p in P), "Subproblem_Obj"

        # (16r) Subscriber must receive
        must_recv = self.data.must_receive_p.get(subscriber_id, set())
        for p in must_recv:
            prob += x[p] == 1, f"MustRecv_{p}"

        # (17r) Subscriber cannot receive
        cannot_recv = self.data.cannot_receive_p.get(subscriber_id, set())
        for p in cannot_recv:
            prob += x[p] == 0, f"CannotRecv_{p}"

        # (18r) Attributes bounds
        for a, rule in self.data.attributes.items():
            attr_sum = pulp.lpSum(self.data.products[p].attributes.get(a, 0.0) * x[p] for p in P)
            prob += attr_sum >= rule.alpha_l, f"AttrMin_{a}"
            prob += attr_sum <= rule.alpha_u, f"AttrMax_{a}"

        # (19r) & (20r) Product count per box
        prob += pulp.lpSum(x[p] for p in P) <= self.data.gamma_u, "MaxProducts"
        prob += pulp.lpSum(x[p] for p in P) >= self.data.gamma_l, "MinProducts"

        # (21r) Must-ship-together pairs
        for idx, (p1, p2) in enumerate(self.data.cooccur_pairs):
            prob += x[p1] == x[p2], f"Cooccur_{idx}"

        # (22r) Conflicting pairs
        for idx, (p1, p2) in enumerate(self.data.conflict_pairs):
            prob += x[p1] + x[p2] <= 1, f"Conflict_{idx}"

        # (29) Elimination cut to prevent regenerating existing patterns
        for idx, pat in enumerate(self.existing_patterns):
            in_pat = [x[p] for p in pat]
            out_pat = [x[p] for p in P if p not in pat]
            prob += pulp.lpSum(in_pat) - pulp.lpSum(out_pat) <= len(pat) - 1, f"NoDupPattern_{idx}"

        # Solve
        solver = pulp.PULP_CBC_CMD(msg=msg)
        prob.solve(solver)

        if prob.status == pulp.LpStatusOptimal:
            pattern = {p for p in P if round(pulp.value(x[p]) or 0) == 1}
            self.existing_patterns.append(pattern)
            return pattern
        return None
