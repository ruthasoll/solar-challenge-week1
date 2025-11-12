# Dashboard: Streamlit app

This directory contains notes for running and deploying the Streamlit dashboard added in `app/main.py`.

How to run locally

1. Create a virtual environment and install dependencies:

   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt

2. From the project root run:

   streamlit run app/main.py

Notes on deployment

- The app reads CSV files from the repository `data/` folder. Keep `data/` out of
  version control if it contains private data. For Streamlit Community Cloud, upload the dataset(s) to the repo or host them publicly and update the loading
  logic.

Commit & Branching

- Create a branch named `dashboard-dev` and commit the changes as a single commit with message:

  feat: basic Streamlit UI

Files added

- `app/main.py`: Streamlit app (UI + visuals)
- `app/utils.py`: helper functions to list and load local CSVs
