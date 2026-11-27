# Birchbox Product Assortment Optimization

This repository implements the mathematical models and algorithms described in the research paper:

> **Formulation Matters: Reciprocating Integer Programming for Birchbox Product Assortment**  
> *Irvin Lustig, Patricia Randall, Robert Randall*  
> **INFORMS Journal on Applied Analytics**, Vol. 51, No. 5, September–October 2021, pp. 347–360.  
> *Wagner Prize for Excellence in the Practice of Advanced Analytics and Operations Research*

---

## Problem Summary

Each month, Birchbox delivers personalized beauty boxes containing $5$ to $6$ product samples to hundreds of thousands of subscribers (clustered into $1{,}000$ to $5{,}000$ subscriber segments). 

The goal is to determine an assortment of distinct box configurations that:
1. **Assigns every subscriber** to a valid box configuration.
2. **Minimizes the number of distinct configurations** built ($\tau^\ell \le \sum y_b \le \tau^u$) to control warehouse packing costs.
3. **Respects business and curation constraints**:
   - Box size limits ($\sigma^\ell \le n_b \le \sigma^u$)
   - Number of items per box ($\gamma^\ell \le \sum x_p \le \gamma^u$)
   - Box attribute limits (retail value, shipping weight, fluid volume: $\alpha^\ell_a \le \sum \mu_{ap} x_p \le \alpha^u_a$)
   - Must-ship-together product bundles ($\hat{R}$)
   - Incompatible product exclusions ($\bar{R}$)
   - Subscriber profile requirements ($\hat{P}_s$) and allergy exclusions ($\bar{P}_s$)
   - Product inventory availability ($\phi^u_p$) and target shipment minimums ($\phi^\ell_p$).

---

##  Repository Structure

```
birchbox_assortment/
├── data/                               # Sample business dataset (CSVs)
│   ├── parameters.csv                  # Global model limits (tau, sigma, gamma, big-M)
│   ├── attributes.csv                  # Box-level attribute constraints (value, weight, volume)
│   ├── products.csv                    # Product catalog with demand & inventory limits
│   ├── subscribers.csv                 # Subscriber profiles / cluster segments
│   ├── subscriber_requirements.csv     # Subscriber mandatory items and allergy exclusions
│   ├── product_pairs_cooccur.csv       # Complementary items that must be shipped together (R_hat)
│   └── product_pairs_conflict.csv      # Incompatible items that cannot appear in same box (R_bar)
│
├── src/                                # Core algorithmic modules
│   ├── data_loader.py                  # CSV ingestion and mathematical set definitions
│   ├── original_mip.py                 # Original Big-M MIP formulation (Equations 1-23)
│   ├── pattern_generator.py            # Subproblem MIP for valid box generation (Equations 16r-22r, 29)
│   └── rip_solver.py                   # Reciprocating Integer Programming (RIP) decomposition
│
├── scripts/
│   └── generate_sample_data.py         # Synthetic data generator for benchmarks
│
├── tests/
│   └── test_data_and_models.py         # Automated unit test suite
│
├── main.py                             # Main CLI runner
├── requirements.txt                    # Project Python dependencies
└── README.md                           # Documentation
```

---

##  Quick Start

### 1. Installation

Ensure Python 3.9+ is installed, then install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Generate Sample CSV Data

To generate fresh sample data or re-seed the test instances:
```bash
python scripts/generate_sample_data.py
```

### 3. Launch Live Interactive Web Solver

Run the live web server to interactively manipulate sliders and resolve the Original MIP live:
```bash
python birchbox_assortment/web/server.py 8050
```
Open **`http://localhost:8050`** in any browser.

#### Live Features:
* **Constraint Sliders:** Adjust box capacity ($\gamma^\ell, \gamma^u$), configuration bounds ($\tau^\ell, \tau^u$), min box size ($\sigma^\ell$), and attribute limits (Value, Weight, Volume).
* **Rule Toggles:** Turn mandatory bundles ($\hat{R}$), conflict exclusions ($\bar{R}$), and customer preferences on/off.
* **Instant MIP Re-solve:** Runs PuLP live on the backend in ~0.2s.
* **Interactive Views:** Unboxing cards, 2D matrix heatmap, customer search directory, and equation audit checklist.

---

### 4. Run Optimization from CLI

#### Compare Original MIP vs. Reciprocating Integer Programming (RIP):
```bash
python main.py --mode compare
```

#### Run RIP Solver only:
```bash
python main.py --mode rip
```

#### Run Original MIP only:
```bash
python main.py --mode original --time-limit 60
```

### 4. Run Unit Tests
```bash
python -m unittest tests/test_data_and_models.py
```
