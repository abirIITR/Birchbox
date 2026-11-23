"""
data_loader.py
Loads Birchbox assortment optimization data from CSV files and prepares mathematical sets and parameters.
"""

import os
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional

@dataclass
class Product:
    id: str
    name: str
    category: str
    brand: str
    phi_l: int  # Minimum desired units across boxes
    phi_u: int  # Maximum available inventory units
    attributes: Dict[str, float] = field(default_factory=dict)

@dataclass
class Subscriber:
    id: str
    cluster_name: str
    subscriber_count: int

@dataclass
class AttributeRule:
    name: str
    alpha_l: float
    alpha_u: float
    unit: str

@dataclass
class AssortmentProblemData:
    products: Dict[str, Product]
    subscribers: Dict[str, Subscriber]
    attributes: Dict[str, AttributeRule]
    
    # Global parameters
    tau_l: int  # Min box configurations
    tau_u: int  # Max box configurations
    sigma_l: int  # Min subscribers per box
    sigma_u: int  # Max subscribers per box
    gamma_l: int  # Min products per box
    gamma_u: int  # Max products per box
    big_m: float  # Big-M constant

    # Additional Customer & Assortment constraints
    max_brand_items: Optional[int] = None       # Limits products from the same brand per box
    max_category_items: Optional[int] = None    # Limits products from same category per box
    min_coverage_pct: Optional[float] = None    # Minimum % of customers that must receive a box

    # Pairing sets
    cooccur_pairs: List[Tuple[str, str]] = field(default_factory=list)  # R_hat
    conflict_pairs: List[Tuple[str, str]] = field(default_factory=list) # R_bar

    # Eligibility mappings
    must_receive_p: Dict[str, Set[str]] = field(default_factory=dict)   # s -> set of p (P_hat_s)
    cannot_receive_p: Dict[str, Set[str]] = field(default_factory=dict) # s -> set of p (P_bar_s)
    must_receive_s: Dict[str, Set[str]] = field(default_factory=dict)   # p -> set of s (S_hat_p)
    cannot_receive_s: Dict[str, Set[str]] = field(default_factory=dict) # p -> set of s (S_tilde_p)

def load_data_from_directory(data_dir: str) -> AssortmentProblemData:
    """Reads all CSVs from the specified data directory and builds the structured AssortmentProblemData object."""
    # 1. Parameters
    params_df = pd.read_csv(os.path.join(data_dir, "parameters.csv"))
    param_dict = dict(zip(params_df["parameter"], params_df["value"]))

    tau_l = int(param_dict.get("tau_l", 2))
    tau_u = int(param_dict.get("tau_u", 6))
    sigma_l = int(param_dict.get("sigma_l", 2))
    sigma_u = int(param_dict.get("sigma_u", 20))
    gamma_l = int(param_dict.get("gamma_l", 4))
    gamma_u = int(param_dict.get("gamma_u", 5))
    big_m = float(param_dict.get("big_m", 100))

    # 2. Attributes
    attrs_df = pd.read_csv(os.path.join(data_dir, "attributes.csv"))
    attributes: Dict[str, AttributeRule] = {}
    for _, row in attrs_df.iterrows():
        attr_name = str(row["attribute"]).strip()
        attributes[attr_name] = AttributeRule(
            name=attr_name,
            alpha_l=float(row["min_amount"]),
            alpha_u=float(row["max_amount"]),
            unit=str(row.get("unit", ""))
        )

    # 3. Products
    prods_df = pd.read_csv(os.path.join(data_dir, "products.csv"))
    products: Dict[str, Product] = {}
    for _, row in prods_df.iterrows():
        pid = str(row["product_id"]).strip()
        attr_vals = {}
        for attr in attributes.keys():
            if attr in row:
                attr_vals[attr] = float(row[attr])
        products[pid] = Product(
            id=pid,
            name=str(row["product_name"]),
            category=str(row.get("category", "")),
            brand=str(row.get("brand", "")),
            phi_l=int(row["phi_l"]),
            phi_u=int(row["phi_u"]),
            attributes=attr_vals
        )

    # 4. Subscribers
    subs_df = pd.read_csv(os.path.join(data_dir, "subscribers.csv"))
    subscribers: Dict[str, Subscriber] = {}
    for _, row in subs_df.iterrows():
        sid = str(row["subscriber_id"]).strip()
        subscribers[sid] = Subscriber(
            id=sid,
            cluster_name=str(row.get("cluster_name", sid)),
            subscriber_count=int(row.get("subscriber_count", 1))
        )

    # 5. Must-Ship-Together Pairs (R_hat)
    cooccur_pairs = []
    cooccur_path = os.path.join(data_dir, "product_pairs_cooccur.csv")
    if os.path.exists(cooccur_path):
        cooccur_df = pd.read_csv(cooccur_path)
        for _, row in cooccur_df.iterrows():
            p1, p2 = str(row["product_id_1"]).strip(), str(row["product_id_2"]).strip()
            if p1 in products and p2 in products:
                cooccur_pairs.append((p1, p2))

    # 6. Incompatible Pairs (R_bar)
    conflict_pairs = []
    conflict_path = os.path.join(data_dir, "product_pairs_conflict.csv")
    if os.path.exists(conflict_path):
        conflict_df = pd.read_csv(conflict_path)
        for _, row in conflict_df.iterrows():
            p1, p2 = str(row["product_id_1"]).strip(), str(row["product_id_2"]).strip()
            if p1 in products and p2 in products:
                conflict_pairs.append((p1, p2))

    # 7. Subscriber Eligibility Rules
    must_receive_p = {s: set() for s in subscribers}
    cannot_receive_p = {s: set() for s in subscribers}
    must_receive_s = {p: set() for p in products}
    cannot_receive_s = {p: set() for p in products}

    reqs_path = os.path.join(data_dir, "subscriber_requirements.csv")
    if os.path.exists(reqs_path):
        reqs_df = pd.read_csv(reqs_path)
        for _, row in reqs_df.iterrows():
            sid = str(row["subscriber_id"]).strip()
            pid = str(row["product_id"]).strip()
            rtype = str(row["requirement_type"]).strip().upper()
            if sid in subscribers and pid in products:
                if rtype == "MUST_RECEIVE":
                    must_receive_p[sid].add(pid)
                    must_receive_s[pid].add(sid)
                elif rtype == "CANNOT_RECEIVE":
                    cannot_receive_p[sid].add(pid)
                    cannot_receive_s[pid].add(sid)

    return AssortmentProblemData(
        products=products,
        subscribers=subscribers,
        attributes=attributes,
        tau_l=tau_l,
        tau_u=tau_u,
        sigma_l=sigma_l,
        sigma_u=sigma_u,
        gamma_l=gamma_l,
        gamma_u=gamma_u,
        big_m=big_m,
        cooccur_pairs=cooccur_pairs,
        conflict_pairs=conflict_pairs,
        must_receive_p=must_receive_p,
        cannot_receive_p=cannot_receive_p,
        must_receive_s=must_receive_s,
        cannot_receive_s=cannot_receive_s
    )
