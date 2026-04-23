# Futoshiki

🃏 FREECELL SOLVER

📋INSTALLATION

1. Install PYTHON

- Download Python via https://www.python.org/downloads/ (ver 3.8 or above)
  If you are working on Windows, make sure to click "Add Python to PATH".

2. Download source code

- Input following lines in terminal:
  git clone <https://github.com/Quanbro07/Futoshiki.git>
  cd freecell_

3. Install environment & libraries

- In case using Window as your operating system:
  python -m venv venv
  .\venv\Scripts\activate
  pip install pygame

- In case using Linux/macOS as your operating system:
  python3 -m venv venv
  source venv/bin/activate
  pip install pygame

4. Run

- After setting up, run the following command to start:
  python main.py

---

## 📁 PROJECT STRUCTURE

* **`algorithm/`**: Contains auto-solving algorithms (AC-3, A*, etc.).
* **`fol/`**: Contains the logical representation settings for the problem.
* **`GUI/`**: User interface, designed using Pygame.
* **`helperFunction/`**: Includes helper functions for data processing or algorithms.
* **`Inputs/`**: Contains input data files (e.g., Futoshiki grid maps).
* **`Outputs/`**: Contains output data and results after algorithm execution.
* **`state/`**: Defines the game states (Grid board, Empty cells, Greater/Less than constraints).
* **`testing/`**: Contains test cases to evaluate the system.
* **`main.py`**: Main execution file of the project (Initializes UI and Game).
* **`run_algorithms.py`**: File used to run algorithms separately and check performance.
* **`requirements.txt`**: Contains the list of required libraries to run the project.

---

✍️ AUTHOR

TRAN NGOC QUAN_24127518_24C10
NGUYEN THANH TRONG_24127136_24C10
GIAP DANG KHOA_24127186_24C10
NGUYEN HOANG NHI_24127478_24C10