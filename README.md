# fuzzy-potato

Group project repository for Advanced Computing  
Group members: **Emily Chu, Elsie Zhang**

## Project Overview

This project studies patterns of police misconduct in New York City using two NYC public safety datasets.  
We focus on three questions: whether misconduct allegations are concentrated among a small group of officers, how allegation patterns vary across NYPD commands or ranks, and whether precincts with higher crime levels also have more misconduct allegations.

## Access our Live App! 

Main app:  
https://fuzzy-potato-kmst2vvnvebesjvs2b9kyh.streamlit.app/

## Data Sources

This project uses **two** NYC Open Data datasets.

### 1. Civilian Complaint Review Board: Police Officers
https://data.cityofnewyork.us/Public-Safety/Civilian-Complaint-Review-Board-Police-Officers/2fir-qns4/about_data

This dataset provides officer-level information from the CCRB, including officer identifiers, rank, command, and complaint-related variables.  
We use it to analyze how misconduct allegations are distributed across officers and how patterns differ across commands or ranks.

### 2. NYPD Complaint Data Historic
https://data.cityofnewyork.us/Public-Safety/NYPD-Complaint-Data-Historic/qgea-i56i/about_data

This dataset contains historical NYPD complaint records.  
We use it as a proxy for crime levels across precincts and compare those patterns with police misconduct allegations.

## Research Questions

1. **How concentrated are misconduct allegations across NYPD officers?**  
   We examine whether a small share of officers accounts for a large share of allegations.

2. **How do misconduct risks vary across commands or ranks?**  
   We compare officer groups to identify where allegations are more common.

3. **Are NYPD precincts with higher crime levels associated with higher numbers of police misconduct allegations?**  
   We explore whether precincts with more crime also tend to have more misconduct allegations.

## App Structure

### Proposal Page
Introduces the project motivation, datasets, research questions, known unknowns, and anticipated challenges.

https://fuzzy-potato-kmst2vvnvebesjvs2b9kyh.streamlit.app/proposal_page

### Page 2
Focuses on officer-level and command-level misconduct patterns, including concentration analysis and group comparisons.
https://fuzzy-potato-kmst2vvnvebesjvs2b9kyh.streamlit.app/page_2

### Page 3
Focuses on the relationship between crime levels and police misconduct allegations across precincts.

https://fuzzy-potato-kmst2vvnvebesjvs2b9kyh.streamlit.app/page_3


## Known Unknowns

### Known
- The number of misconduct allegations helps measure variation in allegation frequency.
- Officer rank and command information allow comparisons across organizational groups.
- Complaint dates allow us to examine patterns over time.

### Unknown
- The total number of officers in each command, which limits our ability to calculate allegation rates per officer.
- True policing activity levels by precinct or command.
- External factors such as neighborhood characteristics, enforcement intensity, and reporting behavior.

## Anticipated Challenges

- **Data cleaning and standardization**  
  Command names, officer identifiers, and other variables may have inconsistent formatting.

- **Data aggregation and interpretation**  
  Multiple allegations may be linked to the same complaint, so counts must be interpreted carefully.

- **Data integration**  
  Matching officer-level misconduct data with precinct-level complaint data requires additional cleaning and alignment.

- **Performance**  
  Large datasets may slow down loading and filtering in the dashboard.

## Repository Purpose

This repository contains the code, notebook work, and Streamlit app for our Advanced Computing group project.

## Data Loading Methods
To support an interactive Streamlit application while working with large NYC Open Data datasets, we implemented a combination of BigQuery storage, selective querying, and caching strategies to improve performance and responsiveness. Instead of loading raw data directly from APIs on every app run, we first ingested the CCRB officer dataset into Google BigQuery. This allows us to execute SQL queries directly on the server side, avoid repeatedly downloading large datasets, and improve query speed and reliability. We also constructed the SQL queries to retrieve only the required columns and optionally limit the number of rows to reduce unnecessary data transfer and speeds up initial load time.

## Selective Data Loading

To further improve performance, we avoid loading the entire dataset by default. Users can control the number of rows loaded via a sidebar input:

1. Smaller subsets are used during development and exploration
2. Larger datasets can be loaded when needed for full analysis

This approach balances flexibility with performance efficiency.

We use Streamlit’s caching mechanisms to minimize repeated computation and network calls, such as Cached BigQuery Client, Cached Data Loading, and Cached Data Export. This helps us to prevents re-initializing the BigQuery client on every run and avoids repeated authentication overhead, while storing query results after our first loads. This also leads to the speed improvement of our page loadings.

## UI Performance Optimization

We also made several UI-level improvements:
1. Replaced tabs with sidebar navigation to reduce unnecessary rendering
2. Removed loading spinners once caching was implemented
3. Limited preview tables to a fixed number of rows (head(50))

These changes reduce frontend rendering time and improve perceived responsiveness.

Through these optimizations, our initial load time was reduced from 8 seconds to 2 seconds and cached reruns are significantly faster. This allows our app to remain responsive even when working with large datasets.
