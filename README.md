# fuzzy-potato

Group project repository for Advanced Computing  
Group members: **Emily Chu, Elsie Zhang**

## Project Overview

This project studies patterns of police misconduct in New York City using two NYC public safety datasets.  
We focus on three questions:

1. how extreme the highest-complaint officers are relative to the overall distribution,
2. which officer groups show the highest complaint burden and substantiation intensity,
3. whether precincts with higher crime volume also tend to have more misconduct allegations.

## Live App

Main app:  
https://fuzzy-potato-kmst2vvnvebesjvs2b9kyh.streamlit.app/

## Data Sources

This project uses **two** NYC Open Data datasets.

### 1. Civilian Complaint Review Board: Police Officers
https://data.cityofnewyork.us/Public-Safety/Civilian-Complaint-Review-Board-Police-Officers/2fir-qns4/about_data

This dataset provides officer-level information from the CCRB, including officer identifiers, current rank, current command, and complaint-related variables.  
We use it for both officer-level and group-level analysis.

Key variables used in this project include:

- current command
- current rank
- total complaints
- total substantiated complaints
- officer demographic and status fields

### 2. NYPD Complaint Data Historic
https://data.cityofnewyork.us/Public-Safety/NYPD-Complaint-Data-Historic/qgea-i56i/about_data

This dataset contains historical NYPD complaint records related to crime incidents in New York City.  
We use it as a precinct-level measure of crime volume and compare it with misconduct allegation patterns.

Key variables used in this project include:

- `addr_pct_cd` for precinct identification
- offense description and category
- borough
- report date

## Research Questions

### RQ1
**How extreme are the highest-complaint officers relative to the overall distribution?**

We compare the most complained-about officers with the broader complaint distribution across all officers.  
This helps show whether the highest-complaint officers are simply above average or whether they are true outliers.

### RQ2
**Which groups show the highest complaint burden and substantiation intensity?**

We group officers by variables such as **Current Command** or **Current Rank** and compare:

- **Complaint burden** = average complaints per officer
- **Substantiation intensity** = substantiated complaints per 100 complaints

This allows us to identify which groups appear most exposed to complaints and which groups have relatively higher substantiation rates.

### RQ3
**Is crime volume associated with misconduct allegations across precincts?**

We aggregate Dataset 2 into **crime counts by precinct** and compare those counts with misconduct allegation counts derived from Dataset 1.  
This lets us examine whether precincts with more crime also tend to show more misconduct complaints.

## App Structure

### Proposal Page
Introduces the project motivation, datasets, updated research questions, analytical approach, known unknowns, and anticipated challenges.

### Page 2 — RQ1: Complaint Extremes
Focuses on officer-level complaint distribution.

Main outputs include:

- top officers by total complaints
- summary distribution metrics
- distribution plots showing how extreme high-complaint officers are relative to the full officer population

### Page 4 — RQ2: Group Risk Patterns
Focuses on group-level misconduct risk.

Main outputs include:

- a quadrant bubble chart comparing groups on burden and substantiation intensity
- ranked chart of groups by complaint burden
- ranked chart of groups by substantiation intensity

### Page 3 — RQ3: Crime and Misconduct by Precinct
Focuses on the precinct-level relationship between crime volume and misconduct allegations.

Main outputs include:

- crime counts by precinct
- merged precinct-level comparisons between crime volume and misconduct patterns

## Analytical Workflow

### Dataset 1 Workflow
1. Load officer-level complaint data from BigQuery.
2. Clean and standardize fields such as current command, current rank, and complaint variables.
3. Use the cleaned table for both officer-level and group-level analysis.

### Dataset 2 Workflow
1. Load the historic NYPD complaint dataset from BigQuery.
2. Aggregate records by precinct using `addr_pct_cd`.
3. Construct precinct-level crime count measures.

### Merging Logic for RQ3
1. Build misconduct counts by precinct from Dataset 1.
2. Build crime counts by precinct from Dataset 2.
3. Align the precinct identifiers and data types.
4. Merge the two aggregated tables for precinct-level comparison.

## Authentication and Secrets

### Local ingestion
For local ingestion and setup, authentication should be done with a **user account** following the course guidance for pandas-gbq / Google Cloud local authentication.

### Streamlit deployment
For the deployed Streamlit app, BigQuery access uses a **service account** stored in Streamlit secrets.

Important:
- `.streamlit/secrets.toml` must **not** be committed to GitHub
- it should be included in `.gitignore`

## Known Unknowns

### What we know
- Dataset 1 supports officer-level and group-level misconduct analysis.
- Dataset 2 supports precinct-level crime aggregation.
- Together, the datasets allow comparison across officer, group, and precinct levels.

### What we do not know yet
- Whether the highest-complaint officers are extreme relative to the full officer distribution.
- Which commands or ranks consistently show the highest burden and highest substantiation intensity.
- Whether the precinct-level relationship between crime and misconduct is strong, weak, or inconsistent.
- How much external factors such as policing intensity, reporting behavior, or neighborhood context affect these results.

## Anticipated Challenges

- **Data cleaning and standardization**  
  Command names, group labels, and complaint-related variables may require cleaning and alignment.

- **Interpretation**  
  Complaint burden and substantiation intensity measure different things, so both need to be interpreted carefully.

- **Precinct matching**  
  Precinct identifiers differ across datasets and must be aligned before merging.

- **Measurement bias**  
  Higher police activity or higher reporting rates may mechanically increase complaint counts.

- **Performance**  
  Large datasets can slow down loading, filtering, and visualization if not handled efficiently.

## Repository Purpose

This repository contains the Streamlit app, ingestion scripts, helper functions, and project materials for our Advanced Computing group project.