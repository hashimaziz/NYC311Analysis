# NYC 311 Data Analysis Pipeline

This repository contains the data analysis pipeline, exploratory data analysis (EDA), and interactive dashboard for the NYC 311 Service Requests dataset (2020-Present). The goal of this project is to analyze millions of 311 complaint records by type, location, timestamp, and resolution time to identify systemic delays and geographical hotspots.

## Project Structure

- `fullAnalysis.ipynb`: Main Jupyter Notebook containing data loading, preprocessing, feature engineering, and the EDA pipeline.
- `requirements.txt`: Python package dependencies.
- Ensure you place the ~14GB `311_Service_Requests_from_2020_to_Present_20260401.csv` file in the root before running the notebooks (file is ignored by Git due to size).
- `app.py`: Streamlit application for interactive visualization.
- `narrative.docx`: Narrative of the data analysis and findings.

## Research Questions

1. **Category Prevalence**: Which complaint categories are most prevalent in each borough?
2. **Seasonality**: How do complaint volumes and types shift seasonally?
3. **Resolution Times**: Which neighborhoods or complaint types exhibit the largest amounts of unresolved or slow-to-resolve requests?

## How to Reproduce

1. Clone this repository.
2. Install the required dependencies: `pip install -r requirements.txt`
3. Download the dataset from [NYC Open Data](https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2020-to-Present/erm2-nwe9/about_data) and place it in the same directory.
4. Run all cells in `fullAnalysis.ipynb` for the data analysis or use the command `streamlit run app.py` for the interactive dashboard.

## Methodology

- **Data Cleaning**: Rows missing vital timestamps or complaint definitions were removed. Erroneous negative resolution times were filtered out.
- **Feature Engineering**: Derived fields including `ResolutionTimeHours`, temporal features (`Day of Week`, `Month`), and calculated bins (`Resolution_Category`) were added to enhance plotting.
- **EDA**: Visualizations explore frequency distributions, temporal trends, geographical spread (Borough), and time-to-close metrics.
- **Dashboard**: Streamlit and Plotly were used to create an interactive dashboard for exploring the data.
