import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import argparse
import os

def create_sample_data(output_filepath="sample_historical_ahu.csv"):
    """
    Generates 30 days of synthetic historical AHU temperature data.
    """
    print(f"Generating 30 days of sample data into '{output_filepath}'...")
    pt_tz = pytz.timezone("Europe/Lisbon")
    end_date = datetime.now(pt_tz).replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = end_date - timedelta(days=30)
    
    # 5-minute frequency
    timestamps = pd.date_range(start=start_date, end=end_date, freq='5min')
    
    data = []
    for floor in ['Floor_1', 'Floor_2']:
        for ts in timestamps:
            # Base temp + some hourly sinusoidal variation + noise
            hour = ts.hour
            temp = 20.0 + 3.0 * np.sin(np.pi * (hour - 8) / 12) + np.random.normal(0, 0.5)
            data.append({
                'floor': floor,
                'timestamp': ts.strftime('%Y-%m-%d %H:%M:%S'),
                'supply_air_temperature': round(temp, 2)
            })
            
    df = pd.DataFrame(data)
    df.to_csv(output_filepath, index=False)
    print("Sample data generation complete.\n")
    return output_filepath

def generate_ahu_forecast(input_csv, target_date_str, output_csv="ahu_temp_floor_15min.csv"):
    """
    Core logic extracted to generate 15-minute average floor profiles
    based on the historical average of a given time of day.
    """
    print(f"Reading historical data from '{input_csv}'...")
    df_ahu_hist = pd.read_csv(input_csv)
    
    # Parse timestamps and localize to PT time (simulating the DB AT TIME ZONE 'Europe/Lisbon')
    df_ahu_hist['timestamp_pt'] = pd.to_datetime(df_ahu_hist['timestamp'])
    if df_ahu_hist['timestamp_pt'].dt.tz is None:
        df_ahu_hist['timestamp_pt'] = df_ahu_hist['timestamp_pt'].dt.tz_localize('Europe/Lisbon', ambiguous='NaT', nonexistent='shift_forward')
    
    # Extract temporal features for profiling
    df_ahu_hist['hour'] = df_ahu_hist['timestamp_pt'].dt.hour
    df_ahu_hist['minute'] = df_ahu_hist['timestamp_pt'].dt.minute
    
    print("Calculating historical average profiles per floor...")
    df_floor_profile = df_ahu_hist.groupby(['floor', 'hour', 'minute'])['supply_air_temperature'].mean().reset_index()
    
    # Setup target forecast window
    pt_tz = pytz.timezone("Europe/Lisbon")
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    target_start = pt_tz.localize(datetime.combine(target_date, datetime.min.time()))
    
    # Create target 5-minute range for the specified day
    target_5min_range = pd.date_range(
        start=target_start, 
        end=target_start + timedelta(days=1) - timedelta(minutes=5), 
        freq='5min'
    )
    
    forecast_records = []
    unique_floors = df_ahu_hist['floor'].unique()
    
    print(f"Mapping historical profiles to target date: {target_date_str}...")
    for ts in target_5min_range:
        for floor in unique_floors:
            match = df_floor_profile[
                (df_floor_profile['floor'] == floor) & 
                (df_floor_profile['hour'] == ts.hour) & 
                (df_floor_profile['minute'] == ts.minute)
            ]
            
            # Default to 15.0 if no historical match is found for that specific time/floor
            val = match['supply_air_temperature'].values[0] if not match.empty else 15.0 
            forecast_records.append({
                'timestamp': ts, 
                'floor': floor, 
                'forecasted_temp': val
            })
            
    df_ahu_forecast_5m = pd.DataFrame(forecast_records)
    df_ahu_forecast_5m.set_index('timestamp', inplace=True)
    
    print("Resampling to 15-minute intervals...")
    # Resample to 15min by taking the mean of the 5min slots
    df_floor_15m = df_ahu_forecast_5m.groupby('floor').resample('15min')['forecasted_temp'].mean().reset_index()
    
    # Format timestamp for clean CSV output (dropping timezone for standard representation if desired)
    df_floor_15m['timestamp'] = df_floor_15m['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    df_floor_15m.to_csv(output_csv, index=False)
    print(f"Success! 15-minute forecast saved to '{output_csv}'.")

def main():
    parser = argparse.ArgumentParser(description="Generate 15-min AHU Floor Temperature Forecasts")
    parser.add_argument("--target-date", type=str, required=True, help="Target date for the forecast (YYYY-MM-DD)")
    parser.add_argument("--use-sample", action="store_true", help="Option 1: Generate and use a sample dataset to test end-to-end")
    parser.add_argument("--input-file", type=str, help="Option 2: Provide your own CSV file with historical data")
    parser.add_argument("--output-file", type=str, default="ahu_temp_floor_15min.csv", help="Name of the output CSV file")
    
    args = parser.parse_args()
    
    if args.use_sample:
        input_csv = "sample_historical_ahu.csv"
        create_sample_data(input_csv)
    elif args.input_file:
        input_csv = args.input_file
        if not os.path.exists(input_csv):
            print(f"Error: Input file '{input_csv}' not found.")
            return
    else:
        print("Error: You must specify either --use-sample or --input-file.")
        parser.print_help()
        return

    generate_ahu_forecast(input_csv, args.target_date, args.output_file)

if __name__ == "__main__":
    main()