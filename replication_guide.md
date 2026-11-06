# AHU Temperature 15-Min Profiler

This module processes historical Air Handling Unit (AHU) temperatures to generate a forecasted 15-minute interval average temperature profile per floor for a specified target date. *Note: The output of this pipeline serves as a foundational data input for the downstream flexibility bid suggestion process.*

## Prerequisites

To run this code on any machine, ensure you have Python 3.8+ installed.

1. Clone the repository:

```bash
git clone https://github.com/sreeram29/weforming-ahu-forecast.git
cd ahu_forecast_files
```

2. Install the required dependencies:

```bash
pip install pandas numpy pytz
```

## How It Works

The algorithm isolates the historical trends of AHU `supply_air_temperature` over the past 30 days. It groups this data by `floor`, `hour`, and `minute` to create an average "daily profile." It then maps this profile to a target date in 5-minute increments before finally resampling and averaging the data into strict 15-minute blocks.

## Execution Options

You can test this setup effectively on your local machine using one of two methods.

### Option 1: Run End-to-End with Sample Data
If you don't have historical data readily available, you can use the built-in data generator. This will create a synthetic 30-day CSV dataset and immediately process it.

```bash
python ahu_temp_generator.py --target-date 2026-12-01 --use-sample
```
* **What happens:** 
  1. Generates `sample_historical_ahu.csv` with simulated sinusoidal temperature data for 2 floors.
  2. Processes the data and outputs the forecast to `ahu_temp_floor_15min.csv`.

### Option 2: Bring Your Own Data (BYOD)
If you have your own data extract (e.g., exported from a database), you can feed it directly into the script.

```bash
python ahu_temp_generator.py --target-date 2026-12-01 --input-file your_historical_data.csv --output-file custom_output.csv
```

#### Required Input Data Format
If you are bringing your own data, ensure your CSV (`your_historical_data.csv`) contains at least the following three columns:

| floor   | timestamp           | supply_air_temperature |
|---------|---------------------|------------------------|
| Floor_1 | 2024-04-20 08:00:00 | 18.5                   |
| Floor_2 | 2024-04-20 08:05:00 | 19.2                   |

* **floor**: String or Integer identifying the location.
* **timestamp**: Date and time (preferably `YYYY-MM-DD HH:MM:SS`). The script assumes the local timezone equivalent to `Europe/Lisbon` as per the original design.
* **supply_air_temperature**: Float value of the recorded temperature.

## Output
The resulting CSV file will contain the grouped and averaged data, ready for downstream processing:
* `timestamp`: The 15-minute interval start time.
* `floor`: The floor identifier.
* `forecasted_temp`: The calculated 15-minute average temperature.