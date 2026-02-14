# fuzzy-potato
Group project repository: Elsie, Emily

Project 1 Part 1: Proposal
Group fuzzy-potato: Emily Chu, Elsie Zhang

1. Dataset

Name: Air Quality Data - Updated Hourly
This website provides global air quality data updated hourly on the pollutants of PM2.5, PM10, O3 (Ozone), NO2 (Nitrogen dioxide), SO2 (Sulfur dioxide), CO (Carbon monoxide)

2. Research Questions

How do hourly air pollution patterns (PM₂.₅, NO₂, O₃) vary across major cities, and when do cities experience statistically significant spikes relative to their typical baseline?
We will focus on 6 major cities that allows us to have strong diversity for meaningful comparison across the globe
NYC
London
Hong Kong
Delhi
São Paulo
Tokyo

3. Notebook Link
<a target="_blank" href="https://colab.research.google.com/github/advanced-computing/fuzzy-potato/blob/main/GroupProject.ipynb">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>

4. Target Visualization
To be updated
5. Known Unknowns

Known:
Timestamped hourly pollutant readings for (PM2.5, NO2, O3), which allows us to conduct pattern analysis and produce day-of week comparisons, spike detection, and form rolling averages
All pollutants share the same measurement of µg/m³
Geographic coordinates, which allows us to monitor stations for cross-city comparisons, spatial clustering, and mapping in Streamlit
Clearly specified pollutant types allows us to compare traffic-related and climate-related patterns
Real-time data enables a live dashboard for trend and monitoring applications in our application development

Unknown:
Data Quality may vary as OpenAQ aggregates from multiple providers, such as government monitors, low-cost sensors, and private contributors. We are unsure if all monitors are calibrated equally, which may reflect monitoring quality difference when using the data for cross-city comparisons
Station placement bias because the stations are not randomly distributed, as they may be placed near highways, industrial zones, residential areas, etc. that may not represent the entire city fairly. This affects spike interpretation and baseline calculation. We may need to consider pulling data from multiple locations within a city with city-level aggregates, using median values and standard deviations to make the cities more comparable
The definition of spike needs to be constructed
No direct causal variables of traffic counts, weather (temperature and wind), policy changes, industrial output, wildfire data. We may need another set of data(s) to identify the direct causes

6. Anticipated Challenges

Making sure the time stamps are consistent across the data and making sure the time zones are correct
Computing the baseline and spikes correctly, by using city-level hourly aggregation, rolling baseline, and rolling variability estimates. This requires computing the z-score or robust z-score
Need to code to log data pull times and timestamps of a specific time to produce live data on our application