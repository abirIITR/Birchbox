"""
generate_sample_data.py
Generates clean, realistic sample CSV datasets for the Birchbox Product Assortment Optimization problem.
Now includes rich customer eligibility (MUST_RECEIVE) and ineligibility (CANNOT_RECEIVE) rules
across products and product categories for a majority of customers.
Based on the INFORMS 2021 Wagner Prize research paper by Lustig, Randall, and Randall.
"""

import os
import random
import csv
from typing import Dict, List, Tuple

def generate_dataset(output_dir: str, num_products: int = 10, num_subscribers: int = 50, seed: int = 42):
    os.makedirs(output_dir, exist_ok=True)
    random.seed(seed)

    # Scale box contents and bounds based on product count
    if num_products <= 6:
        gamma_l = 2
        gamma_u = 3
        tau_l = 2
        tau_u = 4
        attr_val_min = 20.0
        attr_val_max = 60.0
        attr_wt_min = 40.0
        attr_wt_max = 160.0
        attr_vol_min = 25.0
        attr_vol_max = 120.0
    elif num_products <= 12:
        gamma_l = 3
        gamma_u = 4
        tau_l = 2
        tau_u = 5
        attr_val_min = 35.0
        attr_val_max = 85.0
        attr_wt_min = 60.0
        attr_wt_max = 220.0
        attr_vol_min = 40.0
        attr_vol_max = 160.0
    else:
        gamma_l = 4
        gamma_u = 5
        tau_l = 2
        tau_u = 6
        attr_val_min = 40.0
        attr_val_max = 95.0
        attr_wt_min = 80.0
        attr_wt_max = 260.0
        attr_vol_min = 50.0
        attr_vol_max = 180.0

    sigma_l = 2
    sigma_u = num_subscribers

    # 1. Global Parameters
    parameters = [
        {"parameter": "tau_l", "value": tau_l, "description": "Minimum box configurations to build (tau_l)"},
        {"parameter": "tau_u", "value": tau_u, "description": "Maximum box configurations to build (tau_u)"},
        {"parameter": "sigma_l", "value": sigma_l, "description": "Minimum subscribers assigned per box configuration (sigma_l)"},
        {"parameter": "sigma_u", "value": sigma_u, "description": "Maximum subscribers assigned per box configuration (sigma_u)"},
        {"parameter": "gamma_l", "value": gamma_l, "description": "Minimum products per box (gamma_l)"},
        {"parameter": "gamma_u", "value": gamma_u, "description": "Maximum products per box (gamma_u)"},
        {"parameter": "big_m", "value": 100, "description": "Big-M constant for linearization"}
    ]

    with open(os.path.join(output_dir, "parameters.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["parameter", "value", "description"])
        writer.writeheader()
        writer.writerows(parameters)

    # 2. Attribute bounds
    attributes = [
        {"attribute": "value", "min_amount": attr_val_min, "max_amount": attr_val_max, "unit": "USD", "description": "Total estimated retail sample value"},
        {"attribute": "weight", "min_amount": attr_wt_min, "max_amount": attr_wt_max, "unit": "grams", "description": "Total box shipping weight"},
        {"attribute": "volume", "min_amount": attr_vol_min, "max_amount": attr_vol_max, "unit": "ml", "description": "Total liquid/cream fluid volume"}
    ]

    with open(os.path.join(output_dir, "attributes.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["attribute", "min_amount", "max_amount", "unit", "description"])
        writer.writeheader()
        writer.writerows(attributes)

    # 3. Beauty Products Pool
    product_templates = [
        ("Ultra Facial Cream", "Moisturizer", "Kiehl's", 12.0, 30.0, 20.0),
        ("Midnight Recovery Concentrate", "Serum", "Kiehl's", 18.0, 15.0, 15.0),
        ("Gold Lust Repair Shampoo", "Shampoo", "Oribe", 14.0, 60.0, 50.0),
        ("Gold Lust Repair Conditioner", "Conditioner", "Oribe", 15.0, 60.0, 50.0),
        ("Good Genes Lactic Acid Treatment", "Exfoliant", "Sunday Riley", 22.0, 25.0, 15.0),
        ("Luna Sleeping Night Oil", "Serum", "Sunday Riley", 20.0, 20.0, 15.0),
        ("Don't Despair Repair Mask", "Conditioner", "Briogeo", 11.0, 50.0, 40.0),
        ("Scalp Revival Charcoal Shampoo", "Shampoo", "Briogeo", 12.0, 55.0, 45.0),
        ("Boy Brow Grooming Pomade", "Mascara", "Glossier", 16.0, 10.0, 5.0),
        ("Cloud Paint Gel Cream Blush", "Lipstick", "Glossier", 14.0, 15.0, 10.0),
        ("Protini Polypeptide Cream", "Moisturizer", "Drunk Elephant", 19.0, 35.0, 30.0),
        ("B-Hydra Intensive Hydration Serum", "Serum", "Drunk Elephant", 17.0, 25.0, 20.0)
    ]

    products = []
    avg_demand_per_prod = (num_subscribers * ((gamma_l + gamma_u) / 2.0)) / num_products
    
    for i in range(min(num_products, len(product_templates))):
        p_name, p_cat, p_brand, val, wt, vol = product_templates[i]
        pid = f"P{i+1:02d}"
        phi_l = max(2, int(avg_demand_per_prod * 0.35))
        phi_u = max(phi_l + 5, int(avg_demand_per_prod * 1.8))
        products.append({
            "product_id": pid,
            "product_name": p_name,
            "category": p_cat,
            "brand": p_brand,
            "phi_l": phi_l,
            "phi_u": phi_u,
            "value": val,
            "weight": wt,
            "volume": vol
        })

    with open(os.path.join(output_dir, "products.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["product_id", "product_name", "category", "brand", "phi_l", "phi_u", "value", "weight", "volume"])
        writer.writeheader()
        writer.writerows(products)

    # 4. Subscribers (Clusters)
    subscribers = []
    cluster_profiles = [
        ("Dry Skin Hydration", "Moisturizer", "Exfoliant"),
        ("Oily & Acne Prone", "Shampoo", "Serum"),
        ("Sensitive Anti-Aging", "Serum", "Exfoliant"),
        ("Minimalist Clean Beauty", "Moisturizer", "Lipstick"),
        ("Glam Makeup Lover", "Lipstick", "Shampoo"),
        ("Fine Hair Scalp Health", "Shampoo", "Lipstick"),
        ("Fragrance & Luxury Lover", "Serum", "Conditioner"),
        ("Active Sun & Outdoor Care", "Moisturizer", "Exfoliant"),
        ("Daily Moisture Balance", "Moisturizer", "Serum"),
        ("Botanical & Vegan Preference", "Conditioner", "Exfoliant"),
        ("Combination Skin Routine", "Serum", "Lipstick"),
        ("Radiant Glow & Brightening", "Exfoliant", "Conditioner"),
        ("Color Treated Hair Care", "Conditioner", "Exfoliant"),
        ("Intense Winter Nourishment", "Moisturizer", "Serum"),
        ("Gentle pH Balancing Cleanse", "Moisturizer", "Exfoliant"),
        ("Nighttime Repair Priority", "Serum", "Lipstick"),
        ("Lightweight Day Protection", "Mascara", "Serum"),
        ("Exfoliation & Texture Smooth", "Exfoliant", "Conditioner"),
        ("Youthful Dewy Skin", "Lipstick", "Shampoo"),
        ("Purifying Charcoal Detox", "Shampoo", "Exfoliant"),
        ("Barrier Repair Focus", "Moisturizer", "Exfoliant"),
        ("Redness Relief Sensitive", "Serum", "Exfoliant"),
        ("Matte Sebum Control", "Mascara", "Serum"),
        ("Curl Definition Moisture", "Conditioner", "Lipstick"),
        ("Pre-Event Glam Routine", "Lipstick", "Shampoo")
    ]

    for i in range(num_subscribers):
        sid = f"S{i+1:02d}"
        profile_tuple = cluster_profiles[i % len(cluster_profiles)]
        cluster_name = f"{profile_tuple[0]} #{i+1:02d}"
        subscribers.append({
            "subscriber_id": sid,
            "cluster_name": cluster_name,
            "subscriber_count": 1
        })

    with open(os.path.join(output_dir, "subscribers.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["subscriber_id", "cluster_name", "subscriber_count"])
        writer.writeheader()
        writer.writerows(subscribers)

    # 5. Must-Ship-Together Pairs (R_hat)
    cooccur_pairs = []
    prod_ids = {p["product_id"] for p in products}
    if "P03" in prod_ids and "P04" in prod_ids:
        cooccur_pairs.append({"product_id_1": "P03", "product_id_2": "P04", "reason": "Oribe Shampoo & Conditioner bundle"})
    if "P07" in prod_ids and "P08" in prod_ids:
        cooccur_pairs.append({"product_id_1": "P07", "product_id_2": "P08", "reason": "Briogeo Mask & Charcoal Shampoo pair"})

    with open(os.path.join(output_dir, "product_pairs_cooccur.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["product_id_1", "product_id_2", "reason"])
        writer.writeheader()
        writer.writerows(cooccur_pairs)

    # 6. Incompatible / Conflicting Pairs (R_bar)
    conflict_pairs = []
    if "P05" in prod_ids and "P06" in prod_ids:
        conflict_pairs.append({"product_id_1": "P05", "product_id_2": "P06", "reason": "Avoid combining acid peel with retinol oil"})

    with open(os.path.join(output_dir, "product_pairs_conflict.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["product_id_1", "product_id_2", "reason"])
        writer.writeheader()
        writer.writerows(conflict_pairs)

    # 7. Rich Subscriber Eligibility / Requirements (P_hat_s and P_tilde_s)
    # Map products by category
    cat_to_prods: Dict[str, List[str]] = {}
    for p in products:
        c = p["category"]
        if c not in cat_to_prods:
            cat_to_prods[c] = []
        cat_to_prods[c].append(p["product_id"])

    reqs = []
    # Assign eligibility rules to majority of subscribers based on their profile
    for i in range(num_subscribers):
        sid = f"S{i+1:02d}"
        prof_name, preferred_cat, excluded_cat = cluster_profiles[i % len(cluster_profiles)]

        # 70% of customers have an ineligible/allergy category rule
        if i % 3 != 0 and excluded_cat in cat_to_prods:
            # Customer cannot receive items in this excluded category
            for pid in cat_to_prods[excluded_cat]:
                reqs.append({
                    "subscriber_id": sid,
                    "product_id": pid,
                    "requirement_type": "CANNOT_RECEIVE",
                    "category": excluded_cat,
                    "notes": f"Profile exclusion for {excluded_cat}"
                })

        # 60% of customers have a required hero product in their preferred category
        if (i % 2 == 0 or i % 5 == 0) and preferred_cat in cat_to_prods:
            chosen_pid = cat_to_prods[preferred_cat][i % len(cat_to_prods[preferred_cat])]
            # Ensure not in cannot_receive
            if not any(r["subscriber_id"] == sid and r["product_id"] == chosen_pid and r["requirement_type"] == "CANNOT_RECEIVE" for r in reqs):
                reqs.append({
                    "subscriber_id": sid,
                    "product_id": chosen_pid,
                    "requirement_type": "MUST_RECEIVE",
                    "category": preferred_cat,
                    "notes": f"Pre-selected hero item in {preferred_cat}"
                })

    with open(os.path.join(output_dir, "subscriber_requirements.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["subscriber_id", "product_id", "requirement_type", "category", "notes"])
        writer.writeheader()
        writer.writerows(reqs)

    unique_subs_with_rules = len(set(r["subscriber_id"] for r in reqs))
    print(f"Sample data successfully generated in: {output_dir}")
    print(f"- {len(products)} products ({', '.join(p['product_id'] for p in products)})")
    print(f"- {len(subscribers)} subscribers (S01 to S{num_subscribers:02d})")
    print(f"- {len(reqs)} customer preference rules defined across {unique_subs_with_rules}/{num_subscribers} subscribers!")
    print(f"- Box size: {gamma_l} to {gamma_u} items per box")
    print(f"- Box configs: {tau_l} to {tau_u} allowed")

if __name__ == "__main__":
    target_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    generate_dataset(target_dir, num_products=10, num_subscribers=50, seed=42)
