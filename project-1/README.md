# UFC Fight Simulator

A simple statistical UFC fight simulator. Pick two fighters and get a predicted winner, win probability, and a brief matchup summary based on career statistics from `fighter.csv`.

## Features
- Compare any two UFC fighters from the dataset
- Predicted winner with win probability (logistic model on composite score)
- Tale of the Tape (height, weight, reach, stance)
- Side-by-side stat comparison table
- Statistical advantages highlighted for the predicted winner

## How it works

The simulator loads fighter career stats from `fighter.csv` (SLpM, striking accuracy/defense, takedowns, submissions, reach, weight, stance) and computes a composite 0–100 score for each fighter across four categories:

| Category | Weight |
|----------|--------|
| Striking | 40% |
| Grappling | 30% |
| Submissions | 15% |
| Physical (reach/weight) | 15% |

A logistic function converts the score difference into a win probability.

## Run locally

```bash
# Clone or open this folder
cd project-1

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # macOS/Linux
# venv\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app
streamlit run app.py
```

Then open `http://localhost:8501` in your browser.

## Data

The simulator reads `fighter.csv` from this directory. The CSV files in this repo come from the [Ultimate UFC Dataset](https://www.kaggle.com/datasets/mdabbert/ultimate-ufc-dataset) on Kaggle.

> **Note:** The large CSV dataset files are intentionally left untracked in `.gitignore` (uncomment `# *.csv` if you want to exclude them from git). You'll need to place `fighter.csv` in this folder before running the app.

## Files

| File | Purpose |
|------|---------|
| `app.py` | Streamlit frontend |
| `ufc_simulator.py` | Core scoring and prediction logic |
| `requirements.txt` | Python dependencies |
| `.gitignore` | Files to exclude from version control |

## License

MIT
