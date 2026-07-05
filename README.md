# Crime Prediction Scientometrics: CSI & MEN

This repository provides code to analyze conceptual and methodological change in the crime prediction literature.

- **Conceptual Shift Index (CSI)** measures changes in keyword distributions between pre-AI and post-AI periods.  
- **Method Evolution Network (MEN)** builds method co-occurrence networks and computes centrality metrics over time.

---

## Repository Structure

.
├── data/        # Input data (Excel files)
├── csi/         # CSI script
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

Due to Web of Science and Scopus licensing restrictions, the original bibliographic dataset is not included in this repository. Users should export their own records and place the required Excel files in the data/ directory before running the scripts.
---

## Installation

pip install -r requirements.txt

---

## Usage

Run commands from the repository root directory.

### ESI

python csi/compute_csi.py

Output:
- outputs/CSI_results.xlsx

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
