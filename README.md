# Gym Membership Operational Dashboard

![Project Header](assets/Project%20Header.jpg)

Experimenting with running metabase locally with Docker. The dataset used is this project is Gym Membership Dataset from [Kaggle](https://www.kaggle.com/datasets/ka66ledata/gym-membership-dataset/data). This project is done mainly to refresh my knowledge and learn several new things about Metabase that I got from my previous work experience.

## Project Overview

This project creates a comprehensive operational dashboard for gym membership analytics using PostgreSQL and Metabase. The dashboard provides insights into member demographics, usage patterns, facility preferences, and operational metrics to support data-driven decision making for gym management.

## Dashboard Components

### Key Performance Indicators (KPIs)
- **Total Members**: 1,000 active gym members
- **Active Personal Trainers**: 4 certified trainers
- **Group Lessons**: 11 different group fitness classes

### Member Demographics Analysis
- **Membership Type Distribution**: Pie chart showing Standard (50.7%) vs Premium (49.3%) memberships
- **Gender Distribution**: Balanced distribution with slight female majority (55.3% Female, 44.7% Male)
- **Personal Training Usage**: Shows utilization of personal training services

### Facility Usage Metrics
- **Group Lesson Attendance**: Visual representation of members attending group classes
- **Sauna Usage**: Distribution of sauna facility utilization
- **Drink Package Adoption**: Analysis of beverage subscription uptake

### Operational Analytics
- **Visit Frequency Statistics**: 
  - Least visits per week: 1
  - Average visits per week: 3
  - Most visits per week: 5

- **Session Duration Analysis**:
  - Shortest session: 30 minutes
  - Average session: 106 minutes
  - Longest session: 180 minutes

### Time-Based Analysis
- **Check-in/Check-out Trends**: Area chart showing hourly patterns of gym usage throughout the day
- **Weekly Activity Patterns**: Member attendance by day of the week

### Popularity Rankings
- **Most Popular Facilities/Services**:
  - Group Lessons: BodyPump, LesMills (top choices)
  - Drinks: Coconut pineapple, Orange (most popular)
  - Personal Trainers: Chloe, Mike (highest demand)

### Member Detail Table
Complete member information including:
- Demographics (ID, Gender, Age)
- Membership details (Type, Personal training, Group lessons)
- Usage patterns (Visit frequency, Check-in/out times, Session duration)
- Preferences (Favorite drinks, Group lessons, Personal trainers)
- Facility usage (Sauna, Drink packages)

## Technical Implementation

### Database Queries
The dashboard is powered by optimized PostgreSQL queries that handle:
- **Aggregation queries** for KPI calculations
- **String array operations** for multi-value fields (group lessons, drinks, trainers)
- **Time-based analytics** using date/time functions
- **Statistical calculations** (MIN, MAX, AVG, CEIL functions)
- **Complex JOINs and CTEs** for data transformation

### Key SQL Techniques Used
- Common Table Expressions (CTEs) for complex data transformations
- `UNNEST(string_to_array())` for expanding comma-separated values
- Window functions with `RANK()` for popularity analysis
- Time extraction functions for hourly/daily trends
- Conditional aggregation for demographic breakdowns

## Data Processing Features
- **Data Cleaning**: Handled in `value_fixing.ipynb` notebook
- **Error Handling**: Documented approaches in `Error Handling Notes.txt`
- **Data Exploration**: SQL-based analysis in `Exploring and Editing the Data.sql`

## Files Structure
- `metabase_question_generation.sql`: All dashboard queries and metrics
- `Create Table in Postgres.sql`: Database schema setup
- `data/`: Raw and cleaned datasets
- `Metabase_Parameter_Types_Reference.txt`: Parameter configuration guide
- `value_fixing.ipynb`: Data cleaning and preprocessing notebook

## Dashboard Features
- **Interactive Filters**: Gender, Membership Type, Personal Training usage, Group Lesson attendance, Drink packages, Sauna usage
- **Real-time KPIs**: Instant overview of key business metrics
- **Drill-down Capabilities**: From high-level metrics to individual member details
- **Visual Variety**: Pie charts, bar charts, area charts, and detailed tables
- **Responsive Design**: Optimized layout for operational monitoring

## Business Value
This dashboard enables gym management to:
- Monitor membership trends and facility utilization
- Optimize staffing based on peak usage times
- Identify popular services and trainers for resource allocation
- Track member engagement and retention indicators
- Make data-driven decisions for facility improvements

## Dashboard Screenshot
![Dashboard Screenshot](assets/Gym%20Membership%20Operational%20Dashboard_page-0001.jpg)