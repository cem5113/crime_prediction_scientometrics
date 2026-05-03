# Crime Prediction Scientometrics: ESI & MEN

This repository provides code to analyze conceptual and methodological change in the crime prediction literature.

- **Epistemic Shift Index (ESI)** measures changes in keyword distributions between pre-AI and post-AI periods.  
- **Method Evolution Network (MEN)** builds method co-occurrence networks and computes centrality metrics over time.

---

## Repository Structure

.
├── data/        # Input data (Excel files)
├── esi/         # ESI script
├── men/         # MEN script
├── outputs/     # Generated results (ignored in Git)
├── requirements.txt
└── README.md

---

## Data

Place the following files in the `data/` folder:

- pre_ai.xlsx  
- post_ai.xlsx  
- Bibliometrix (WoS+Scopus).xlsx  

---

## Installation

pip install -r requirements.txt

---

## Usage

Run commands from the repository root directory.

### ESI

python esi/compute_esi.py

Output:
- outputs/ESI_results.xlsx

---

### MEN

python men/build_men.py

Outputs:
- Node tables (CSV)  
- Edge tables (CSV)  
- Network metrics (CSV)  
- Network visualizations (PNG)  
- GraphML files  

---

## Notes

- The outputs/ folder is excluded from version control.  
- Results are generated locally after running the scripts.  

---

## Author

Cem Eroglu
