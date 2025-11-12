"""Streamlit dashboard for solar dataset exploration.

Usage: in the repo root run:

    streamlit run app/main.py

The app reads CSVs from the `data/` folder (local CSVs only). It presents a
country selector, lets you pick a numeric variable to inspect and shows a
boxplot and a top-regions table.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from typing import List
import utils
import numpy as np
from io import StringIO


st.set_page_config(page_title="Solar Data Dashboard", layout="wide")


def main():
    st.title("Solar Data — Interactive Dashboard")

    # Sidebar controls
    st.sidebar.header("Data & Filters")

    files_map = utils.get_files_by_country("data")
    countries = sorted(files_map.keys())
    if not countries:
        st.sidebar.warning("No CSV files found in `data/`. Add CSVs and refresh.")
    # File upload (takes precedence)
    uploaded_file = st.sidebar.file_uploader("Upload a CSV to use as data source", type=["csv"])

    # Random data generator options
    st.sidebar.markdown("---")
    st.sidebar.markdown("Or generate a small random dataset for demo/testing")
    gen_rows = st.sidebar.number_input("Rows to generate", min_value=10, max_value=20000, value=200, step=10)
    gen_countries_txt = st.sidebar.text_input("Countries (comma-separated)", value=", ".join(countries) if countries else "Benin, Togo, SierraLeone")
    gen_regions_per_country = st.sidebar.number_input("Regions per country", min_value=1, max_value=50, value=5)
    generate = st.sidebar.button("Generate random dataset")

    selected_countries: List[str] = st.sidebar.multiselect(
        "Select countries to include",
        options=countries,
        default=countries if countries else [],
    )

    # Data source priority: uploaded CSV -> generated data -> local CSV files
    df = pd.DataFrame()
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            # Add metadata if missing
            if "country" not in df.columns:
                df["country"] = "Uploaded"
            st.sidebar.success("Loaded uploaded CSV as data source")
        except Exception as e:
            st.sidebar.error(f"Could not read uploaded CSV: {e}")

    # If user requested generation, produce synthetic dataset
    if df.empty and generate:
        # Parse countries text
        gen_countries = [c.strip().capitalize() for c in gen_countries_txt.split(",") if c.strip()]
        if not gen_countries:
            gen_countries = ["Benin", "Togo"]
        rng = np.random.default_rng()
        rows = gen_rows
        country_choices = rng.choice(gen_countries, size=rows)
        regions = []
        sites = []
        for c in country_choices:
            reg = f"Region-{rng.integers(1, gen_regions_per_country+1)}"
            site = f"Site-{rng.integers(1,1000)}"
            regions.append(reg)
            sites.append(site)
        # Generate a plausible GHI-like numeric variable and a second metric
        ghi = np.abs(rng.normal(loc=300, scale=100, size=rows))  # Global Horizontal Irradiance-like
        temp = rng.normal(loc=28, scale=5, size=rows)
        df = pd.DataFrame({
            "country": country_choices,
            "region": regions,
            "site": sites,
            "GHI": ghi,
            "temperature": temp,
        })
        st.sidebar.success("Generated random dataset")

    # Otherwise load selected countries from local CSVs
    if df.empty and selected_countries:
        df = utils.load_data_for_countries(selected_countries, data_dir="data")

    if df.empty:
        st.info("No data loaded. Upload a CSV, generate random data, or choose countries from the sidebar (CSV files in `data/` required).")
        return

    numeric_cols = utils.infer_numeric_columns(df)
    if not numeric_cols:
        st.error("No numeric columns found in loaded data to visualize.")
        if st.checkbox("Show raw data"):
            st.dataframe(df)
        return

    variable = st.sidebar.selectbox("Variable (numeric)", options=numeric_cols, index=0)

    # Optional grouping column — prefer 'region', 'site', else 'country'
    if "region" in df.columns:
        group_col = "region"
    elif "site" in df.columns:
        group_col = "site"
    else:
        group_col = "country"

    # Main plots
    st.subheader(f"Distribution of {variable} by {group_col}")
    try:
        fig = px.box(df, x=group_col, y=variable, color="country", points="all", title=f"{variable} by {group_col}")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Could not create boxplot: {e}")

    # Top regions table
    st.subheader("Top regions by average")
    try:
        agg = (
            df.groupby([group_col, "country"])[variable]
            .agg(["mean", "count"])
            .reset_index()
            .rename(columns={"mean": f"mean_{variable}", "count": "n_points"})
        )
        top_n = st.sidebar.slider("Top N regions to show", min_value=3, max_value=30, value=10)
        top_table = agg.sort_values(f"mean_{variable}", ascending=False).head(top_n)
        st.dataframe(top_table)
    except Exception as e:
        st.error(f"Could not compute top regions: {e}")

    # Data download & raw view
    st.sidebar.markdown("---")
    if st.sidebar.checkbox("Show raw data"):
        st.subheader("Raw data sample")
        st.dataframe(df)

    csv = df.to_csv(index=False).encode("utf-8")
    st.sidebar.download_button("Download loaded data as CSV", data=csv, file_name="solar_selected_data.csv", mime="text/csv")


if __name__ == "__main__":
    main()
