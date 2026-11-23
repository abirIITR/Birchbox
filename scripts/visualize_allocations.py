"""
visualize_allocations.py
Generates visual representations of the Birchbox assortment allocations strictly using the
Original MIP Formulation (Equations 1-23).
"""

import os
import sys
import json
import matplotlib.pyplot as plt
import numpy as np

# Ensure src can be loaded
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import load_data_from_directory
from src.original_mip import solve_original_mip

def generate_static_charts(data, sol_orig, output_dir: str):
    """Generates clean matplotlib visual figures for the Original MIP allocations."""
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Product x Box Composition Heatmap for Original MIP
    products = list(data.products.keys())
    prod_names = [f"{p}: {data.products[p].name[:20]}" for p in products]
    orig_boxes = [b['box_id'] for b in sol_orig.box_details]

    orig_matrix = np.zeros((len(products), len(orig_boxes)))
    for col_idx, b in enumerate(sol_orig.box_details):
        for row_idx, p in enumerate(products):
            if p in b['products']:
                orig_matrix[row_idx, col_idx] = 1

    fig, ax = plt.subplots(figsize=(9, 6))
    im = ax.imshow(orig_matrix, cmap='Blues', aspect='auto', vmin=0, vmax=1)
    ax.set_title(f"Original MIP Formulation: Box Composition Matrix\n({sol_orig.boxes_built} Boxes Built across {len(data.subscribers)} Customers, Solve Time: {sol_orig.solve_time_seconds:.2f}s)", fontsize=12, fontweight='bold', pad=14)
    ax.set_xticks(range(len(orig_boxes)))
    ax.set_xticklabels([f"{b['box_id']}\n(n={b['size_nb']})" for b in sol_orig.box_details], fontsize=10, fontweight='bold')
    ax.set_yticks(range(len(products)))
    ax.set_yticklabels(prod_names, fontsize=10)
    ax.set_xlabel("Box Configurations Built", fontweight='bold', labelpad=8)
    ax.set_ylabel("Products", fontweight='bold', labelpad=8)

    # Add text checkmarks
    for i in range(len(products)):
        for j in range(len(orig_boxes)):
            if orig_matrix[i, j] == 1:
                ax.text(j, i, "✓", ha="center", va="center", color="white", fontweight='bold', fontsize=12)

    plt.tight_layout()
    chart_path = os.path.join(output_dir, "original_allocation_heatmap.png")
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Static chart generated: {chart_path}")

    # 2. Customer Volume Allocation Bar Chart
    fig, ax = plt.subplots(figsize=(8, 4.5))
    labels = [f"{b['box_id']}" for b in sol_orig.box_details]
    sizes = [b['size_nb'] for b in sol_orig.box_details]
    colors = ['#2563EB', '#3B82F6', '#60A5FA', '#93C5FD', '#1D4ED8'][:len(labels)]

    bars = ax.bar(labels, sizes, color=colors, edgecolor='#1E293B', linewidth=1.2, width=0.55)
    ax.set_ylabel("Assigned Subscribers", fontweight='bold')
    ax.set_xlabel("Box Configuration", fontweight='bold')
    ax.set_title(f"Original MIP: Subscriber Volume per Box Recipe (Total: {len(data.subscribers)} Customers)", fontweight='bold', fontsize=12)
    ax.grid(axis='y', linestyle='--', alpha=0.5)

    for bar in bars:
        h = bar.get_height()
        if h > 0:
            ax.annotate(f"{int(h)} ({int(h/len(data.subscribers)*100)}%)",
                        xy=(bar.get_x() + bar.get_width() / 2, h),
                        xytext=(0, 4),
                        textcoords="offset points",
                        ha='center', va='bottom', fontweight='bold', fontsize=10)

    plt.tight_layout()
    bar_path = os.path.join(output_dir, "original_subscriber_distribution.png")
    plt.savefig(bar_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Static chart generated: {bar_path}")

def generate_interactive_dashboard(data, sol_orig, output_html_path: str):
    """Generates a standalone, clean HTML dashboard exclusively for Original MIP allocations."""

    orig_data = [
        {
            "id": b["box_id"],
            "size": b["size_nb"],
            "pct": round(b["size_nb"] / len(data.subscribers) * 100, 1),
            "products": [
                {
                    "id": p,
                    "name": data.products[p].name,
                    "brand": data.products[p].brand,
                    "category": data.products[p].category,
                    "value": data.products[p].attributes.get("value", 0),
                    "weight": data.products[p].attributes.get("weight", 0),
                    "volume": data.products[p].attributes.get("volume", 0)
                } for p in b["products"]
            ],
            "subscribers": b["subscribers"],
            "attributes": b["attribute_totals"]
        } for b in sol_orig.box_details
    ]

    payload = {
        "summary": {
            "num_products": len(data.products),
            "num_subscribers": len(data.subscribers),
            "orig_time": sol_orig.solve_time_seconds,
            "orig_boxes": sol_orig.boxes_built,
        },
        "boxes": orig_data
    }

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Birchbox Assortment Allocations (Original MIP Formulation)</title>
<style>
  :root {{
    --bg: #F8FAFC;
    --card-bg: #FFFFFF;
    --text-primary: #0F172A;
    --text-muted: #64748B;
    --border: #E2E8F0;
    --brand-primary: #2563EB;
    --brand-dark: #1E293B;
    --accent-blue: #3B82F6;
    --accent-green: #059669;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
  body {{ background: var(--bg); color: var(--text-primary); line-height: 1.5; padding: 24px; }}
  .container {{ max-width: 1250px; margin: 0 auto; }}
  
  header {{
    background: linear-gradient(135deg, #1E293B, #0F172A);
    color: white;
    padding: 30px 34px;
    border-radius: 16px;
    margin-bottom: 24px;
    box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1);
  }}
  .badge {{
    background: var(--brand-primary);
    color: white;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 4px 10px;
    border-radius: 9999px;
    display: inline-block;
    margin-bottom: 12px;
  }}
  h1 {{ font-size: 25px; font-weight: 800; letter-spacing: -0.02em; margin-bottom: 6px; }}
  p.subtitle {{ color: #94A3B8; font-size: 14px; max-width: 800px; }}

  .metric-strip {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
    margin-bottom: 28px;
  }}
  .metric-card {{
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 18px 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.02);
  }}
  .metric-label {{ font-size: 12px; text-transform: uppercase; font-weight: 700; color: var(--text-muted); letter-spacing: 0.05em; }}
  .metric-val {{ font-size: 26px; font-weight: 800; color: var(--text-primary); margin-top: 4px; }}
  .metric-sub {{ font-size: 12px; color: var(--accent-green); font-weight: 600; margin-top: 2px; }}

  .box-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
    gap: 20px;
    margin-bottom: 40px;
  }}
  .box-card {{
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 22px;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.04);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }}
  .box-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(0,0,0,0.08);
  }}
  .box-card-header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 16px;
    border-bottom: 1px solid #F1F5F9;
    padding-bottom: 12px;
  }}
  .box-id {{ font-size: 18px; font-weight: 800; color: var(--text-primary); }}
  .box-badge {{
    background: #DBEAFE;
    color: #1E40AF;
    font-weight: 700;
    font-size: 12px;
    padding: 5px 12px;
    border-radius: 8px;
  }}
  .product-list {{ list-style: none; margin-bottom: 16px; }}
  .product-item {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 10px;
    border-radius: 8px;
    background: #F8FAFC;
    margin-bottom: 6px;
    font-size: 13px;
  }}
  .prod-name {{ font-weight: 600; color: #1E293B; }}
  .prod-brand {{ font-size: 11px; color: var(--text-muted); }}
  .prod-meta {{ font-size: 11px; font-weight: 700; color: var(--brand-primary); }}

  .attr-summary {{
    background: #F1F5F9;
    border-radius: 10px;
    padding: 10px 12px;
    font-size: 12px;
    display: flex;
    justify-content: space-between;
    font-weight: 600;
    margin-bottom: 16px;
  }}

  .subs-section {{ margin-top: 8px; }}
  .subs-title {{ font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--text-muted); margin-bottom: 6px; letter-spacing: 0.05em; }}
  .subs-pills {{ display: flex; flex-wrap: wrap; gap: 4px; max-height: 85px; overflow-y: auto; }}
  .sub-pill {{
    background: #E2E8F0;
    color: #334155;
    font-size: 10px;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 4px;
  }}
</style>
</head>
<body>
<div class="container">
  <header>
    <div class="badge">Original MIP Model (Equations 1–23)</div>
    <h1>Birchbox Assortment Allocation Dashboard</h1>
    <p class="subtitle">Complete allocation breakdown for 10 products across 50 customers generated directly by the Original Mixed-Integer Programming Formulation.</p>
  </header>

  <div class="metric-strip">
    <div class="metric-card">
      <div class="metric-label">Total Customers</div>
      <div class="metric-val">{len(data.subscribers)}</div>
      <div class="metric-sub">100% Assigned</div>
    </div>
    <div class="metric-card">
      <div class="metric-label">Products in Catalog</div>
      <div class="metric-val">{len(data.products)} Items</div>
      <div class="metric-sub">4 Items per Box Recipe</div>
    </div>
    <div class="metric-card">
      <div class="metric-label">Boxes Built</div>
      <div class="metric-val">{sol_orig.boxes_built} Recipes</div>
      <div class="metric-sub">Active Production Lines</div>
    </div>
    <div class="metric-card">
      <div class="metric-label">Solve Time</div>
      <div class="metric-val">{sol_orig.solve_time_seconds:.3f} s</div>
      <div class="metric-sub">Optimal Solution Found</div>
    </div>
  </div>

  <div id="boxes-container" class="box-grid"></div>
</div>

<script>
const data = {json.dumps(payload)};

function renderBoxes() {{
  const container = document.getElementById('boxes-container');
  container.innerHTML = '';

  data.boxes.forEach(box => {{
    const card = document.createElement('div');
    card.className = 'box-card';

    let prodsHtml = '';
    box.products.forEach(p => {{
      prodsHtml += `
        <li class="product-item">
          <div>
            <div class="prod-name">${{p.name}}</div>
            <div class="prod-brand">${{p.brand}} • ${{p.category}}</div>
          </div>
          <div class="prod-meta">$$${{p.value.toFixed(1)}}</div>
        </li>
      `;
    }});

    let subsHtml = '';
    box.subscribers.forEach(s => {{
      subsHtml += `<span class="sub-pill">${{s}}</span>`;
    }});

    card.innerHTML = `
      <div>
        <div class="box-card-header">
          <div>
            <div class="box-id">${{box.id}}</div>
            <div style="font-size: 12px; color: #64748B; font-weight: 600;">Production Line</div>
          </div>
          <div class="box-badge">${{box.size}} Subscribers (${{box.pct}}%)</div>
        </div>

        <ul class="product-list">
          ${{prodsHtml}}
        </ul>

        <div class="attr-summary">
          <span>Value: $$${{box.attributes.value.toFixed(1)}}</span>
          <span>Weight: ${{box.attributes.weight.toFixed(0)}}g</span>
          <span>Vol: ${{box.attributes.volume.toFixed(0)}}ml</span>
        </div>
      </div>

      <div class="subs-section">
        <div class="subs-title">Assigned Customer Clusters (${{box.subscribers.length}})</div>
        <div class="subs-pills">
          ${{subsHtml}}
        </div>
      </div>
    `;
    container.appendChild(card);
  }});
}}

renderBoxes();
</script>
</body>
</html>
"""

    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Interactive dashboard generated: {output_html_path}")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    output_dir = os.path.join(base_dir, "visualizations")
    os.makedirs(output_dir, exist_ok=True)

    print(f"Loading problem data from: {data_dir}...")
    data = load_data_from_directory(data_dir)

    print("Solving Original MIP formulation (Equations 1-23)...")
    sol_orig = solve_original_mip(data, time_limit=60)

    # 1. Generate Static figures for Original MIP
    generate_static_charts(data, sol_orig, output_dir)

    # 2. Generate Interactive HTML dashboard for Original MIP
    html_out = os.path.join(output_dir, "original_allocation_dashboard.html")
    generate_interactive_dashboard(data, sol_orig, html_out)

    print("\nOriginal MIP visualization assets successfully created!")

if __name__ == "__main__":
    main()
