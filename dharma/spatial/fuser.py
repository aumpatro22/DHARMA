import os
import re
import sys
import time
import logging
import numpy as np
import pandas as pd
import geopandas as gpd
from scipy.spatial import KDTree
import h3
from concurrent.futures import ProcessPoolExecutor, as_completed

try:
    from dharma.config import LOGS_DIR, DATA_DIR, PROCESSED_DIR, EXTERNAL_DATASET_DIR
    fuser_log = LOGS_DIR / "fuser.log"
except ImportError:
    from pathlib import Path
    _root = Path(__file__).resolve().parents[2]
    LOGS_DIR = _root / "logs"
    DATA_DIR = _root / "data"
    PROCESSED_DIR = _root / "processed"
    EXTERNAL_DATASET_DIR = DATA_DIR
    fuser_log = LOGS_DIR / "fuser.log"

fuser_log.parent.mkdir(parents=True, exist_ok=True)

# Set up logging format and outputs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(fuser_log), mode='w')
    ]
)
logger = logging.getLogger("spatial_fuser")

# Globals for worker processes (leveraging Linux fork copy-on-write)
global_tracts = None
global_bgs = None
global_kdtree = None
global_stops_df = None
global_local_crs = None

def clean_numeric(val):
    if pd.isna(val):
        return None
    val_str = str(val).strip().upper()
    val_str = re.sub(r'[^0-9.\-]', '', val_str)
    try:
        return float(val_str) if val_str else None
    except ValueError:
        return None

def clean_precip(val):
    if pd.isna(val):
        return None
    val_str = str(val).strip().upper()
    if 'T' in val_str:
        return 0.01 * 25.4  # Trace precipitation (0.01 in -> 0.254 mm)
    val_str = re.sub(r'[^0-9.]', '', val_str)
    try:
        return float(val_str) * 25.4 if val_str else 0.0
    except ValueError:
        return 0.0

def get_census_boundaries(cache_dir, state_fips, county_fips, boundary_type="tract"):
    """
    Downloads and caches Census boundaries for a specific state and county.
    boundary_type: 'tract' or 'bg'
    """
    os.makedirs(cache_dir, exist_ok=True)
    cache_filename = f"tl_2022_{state_fips}_{county_fips}_{boundary_type}.geojson"
    cache_filepath = os.path.join(cache_dir, cache_filename)
    
    if os.path.exists(cache_filepath):
        logger.info(f"Loading {boundary_type} boundaries from offline cache: {cache_filepath}")
        return gpd.read_file(cache_filepath)
    
    logger.info(f"Cache miss for {boundary_type} (State: {state_fips}, County: {county_fips}). Fetching from Census Bureau...")
    if boundary_type == "tract":
        url = f"https://www2.census.gov/geo/tiger/TIGER2022/TRACT/tl_2022_{state_fips}_tract.zip"
    else:
        url = f"https://www2.census.gov/geo/tiger/TIGER2022/BG/tl_2022_{state_fips}_bg.zip"
        
    try:
        # Geopandas reads directly from zip URL
        gdf = gpd.read_file(url)
        # Filter to target county FIPS
        gdf = gdf[gdf['COUNTYFP'] == county_fips]
        
        # Save to cache as GeoJSON
        gdf.to_file(cache_filepath, driver="GeoJSON")
        logger.info(f"Successfully cached filtered boundaries to {cache_filepath}")
        return gdf
    except Exception as e:
        logger.error(f"Error downloading boundaries from {url}: {e}")
        raise e

def parallel_spatial_worker(chunk_df):
    """
    Worker function to process spatial tasks on a chunk of the DataFrame.
    """
    global global_tracts, global_bgs, global_kdtree, global_stops_df, global_local_crs
    
    try:
        # 1. Convert to GeoDataFrame (WGS84)
        gdf = gpd.GeoDataFrame(
            chunk_df.copy(),
            geometry=gpd.points_from_xy(chunk_df['longitude'], chunk_df['latitude']),
            crs="EPSG:4326"
        )
        
        # 2. Point-in-Polygon Tract Join
        # Keep spatial tract index columns clean
        tract_join = gpd.sjoin(gdf, global_tracts[['GEOID', 'geometry']], how="left", predicate="within")
        chunk_df['tract_id'] = tract_join['GEOID']
        
        # 3. Point-in-Polygon Block Group Join
        bg_join = gpd.sjoin(gdf, global_bgs[['GEOID', 'geometry']], how="left", predicate="within")
        chunk_df['block_group_id'] = bg_join['GEOID']
        
        # 4. Project coordinates to local CRS for KDTree distance profiling
        gdf_projected = gdf.to_crs(global_local_crs)
        coords = np.column_stack((gdf_projected.geometry.x, gdf_projected.geometry.y))
        
        # Query KDTree
        distances, indices = global_kdtree.query(coords)
        chunk_df['distance_to_transit_meters'] = distances
        chunk_df['closest_transit_stop_id'] = global_stops_df.iloc[indices]['stop_id'].values
        
        # Mark out-of-bounds rows
        chunk_df['out_of_bounds'] = chunk_df['tract_id'].isna() | chunk_df['block_group_id'].isna()
        
        return chunk_df
    except Exception as e:
        logger.error(f"Error in spatial worker: {e}")
        chunk_df['tract_id'] = None
        chunk_df['block_group_id'] = None
        chunk_df['distance_to_transit_meters'] = -1.0
        chunk_df['closest_transit_stop_id'] = None
        chunk_df['out_of_bounds'] = True
        return chunk_df

def process_track(track_name, config):
    start_time = time.time()
    logger.info(f"==================================================")
    logger.info(f"STARTING TRACK: {track_name.upper()}")
    logger.info(f"==================================================")
    
    # 1. Staging checks & authentic data verification
    if not os.path.exists(config['incident_csv']):
        raise FileNotFoundError(
            f"Source incident CSV not found at '{config['incident_csv']}'. "
            f"Please provide authentic historical crime incident records with timestamp, latitude, and longitude."
        )
        
    # 2. Ingest and Sanitise Crime logs
    logger.info(f"Ingesting incidents from {config['incident_csv']}...")
    incidents_df = pd.read_csv(config['incident_csv'])
    initial_rows = len(incidents_df)
    
    # Clean coordinates
    incidents_df['latitude'] = pd.to_numeric(incidents_df['latitude'], errors='coerce')
    incidents_df['longitude'] = pd.to_numeric(incidents_df['longitude'], errors='coerce')
    incidents_df = incidents_df.dropna(subset=['latitude', 'longitude'])
    # Filter non-zero outlier coordinates
    incidents_df = incidents_df[(incidents_df['latitude'] != 0.0) & (incidents_df['longitude'] != 0.0)]
    
    # Standardise timestamps
    # Identify time column dynamically
    time_col = None
    for c in incidents_df.columns:
        if any(k in c.lower() for k in ['date', 'time', 'timestamp']):
            time_col = c
            break
            
    if time_col is None:
        logger.error("Could not find a valid date/time column in incident logs.")
        return
        
    logger.info(f"Parsing timestamp values from column '{time_col}'...")
    incidents_df['parsed_time'] = pd.to_datetime(incidents_df[time_col], errors='coerce')
    incidents_df = incidents_df.dropna(subset=['parsed_time'])
    
    incidents_df['timestamp'] = incidents_df['parsed_time'].dt.strftime('%Y-%m-%d %H:%M:%S')
    incidents_df['date_key'] = incidents_df['parsed_time'].dt.strftime('%Y-%m-%d')
    incidents_df['hour_key'] = incidents_df['parsed_time'].dt.hour
    
    sanitized_rows = len(incidents_df)
    logger.info(f"Sanitization Complete: dropped {initial_rows - sanitized_rows} invalid rows ({sanitized_rows} rows remaining).")
    
    # 3. H3 Indexing (v4 API latlng_to_cell)
    logger.info("Computing H3 Index values at Resolution 7 and 8...")
    incidents_df['h3_res7'] = incidents_df.apply(
        lambda r: h3.latlng_to_cell(r['latitude'], r['longitude'], 7), axis=1
    )
    incidents_df['h3_res8'] = incidents_df.apply(
        lambda r: h3.latlng_to_cell(r['latitude'], r['longitude'], 8), axis=1
    )
    
    # 4. Load Census shapefiles and join with ACS CSV matrices
    global global_tracts, global_bgs
    
    # Download/cache shapefiles
    tracts_gdf = get_census_boundaries(config['cache_dir'], config['state_fips'], config['county_fips'], "tract")
    bgs_gdf = get_census_boundaries(config['cache_dir'], config['state_fips'], config['county_fips'], "bg")
    
    # Load socioeconomic CSV data
    tract_csv = pd.read_csv(config['socioeconomic_tract_csv'])
    bg_csv = pd.read_csv(config['socioeconomic_bg_csv'])
    
    # Zero-pad CSV FIPS parts to match TIGER GEOID format
    tract_csv['geoid_key'] = (
        tract_csv['state'].astype(str).str.zfill(2) + 
        tract_csv['county'].astype(str).str.zfill(3) + 
        tract_csv['tract'].astype(str).str.zfill(6)
    )
    
    bg_csv['geoid_key'] = (
        bg_csv['state'].astype(str).str.zfill(2) + 
        bg_csv['county'].astype(str).str.zfill(3) + 
        bg_csv['tract'].astype(str).str.zfill(6) + 
        bg_csv['block group'].astype(str)
    )
    
    # Renaming mapping
    rename_dict = {
        'median_income': 'Median Household Income',
        'vacant_housing_units': 'Housing Vacancy Ratio',
        'households_below_poverty': 'Poverty Level Ratio'
    }
    
    tract_csv = tract_csv.rename(columns=rename_dict)
    bg_csv = bg_csv.rename(columns=rename_dict)
    
    # Merge geometries with CSV socioeconomic descriptors
    global_tracts = tracts_gdf.merge(
        tract_csv[['geoid_key', 'Median Household Income', 'Housing Vacancy Ratio', 'Poverty Level Ratio']],
        left_on="GEOID", right_on="geoid_key", how="left"
    )
    
    global_bgs = bgs_gdf.merge(
        bg_csv[['geoid_key', 'Median Household Income', 'Housing Vacancy Ratio', 'Poverty Level Ratio']],
        left_on="GEOID", right_on="geoid_key", how="left"
    )
    
    # Ensure CRSs are standard WGS84
    if global_tracts.crs != "EPSG:4326":
        global_tracts = global_tracts.to_crs("EPSG:4326")
    if global_bgs.crs != "EPSG:4326":
        global_bgs = global_bgs.to_crs("EPSG:4326")
        
    # 5. Ingest transit stops and construct spatial indexing
    global global_kdtree, global_stops_df, global_local_crs
    global_local_crs = config['local_crs']
    
    stops_list = []
    for stops_path in config['transit_stops_txt']:
        if os.path.exists(stops_path):
            st = pd.read_csv(stops_path)
            # Remove quotes from column names and values
            st.columns = [c.replace('"', '').strip() for c in st.columns]
            st['stop_id'] = st['stop_id'].astype(str).str.replace('"', '').str.strip()
            stops_list.append(st[['stop_id', 'stop_lat', 'stop_lon']])
            
    if not stops_list:
        logger.error(f"No transit stops.txt files found in paths: {config['transit_stops_txt']}")
        return
        
    global_stops_df = pd.concat(stops_list, ignore_index=True)
    
    # Project transit stops to local SPCS or UTM zone before building KDTree to prevent Mercator scaling errors
    stops_gdf = gpd.GeoDataFrame(
        global_stops_df,
        geometry=gpd.points_from_xy(global_stops_df['stop_lon'], global_stops_df['stop_lat']),
        crs="EPSG:4326"
    )
    stops_gdf_projected = stops_gdf.to_crs(global_local_crs)
    stops_coords = np.column_stack((stops_gdf_projected.geometry.x, stops_gdf_projected.geometry.y))
    global_kdtree = KDTree(stops_coords)
    
    # 6. Execute spatial profiling chunks in parallel using ProcessPoolExecutor
    logger.info("Initializing multi-core processing pool across 24 Xeon processors...")
    cores = min(os.cpu_count(), 24)
    chunks = np.array_split(incidents_df, cores * 2)
    
    processed_chunks = []
    with ProcessPoolExecutor(max_workers=cores) as executor:
        futures = {executor.submit(parallel_spatial_worker, chunk): i for i, chunk in enumerate(chunks)}
        for fut in as_completed(futures):
            chunk_idx = futures[fut]
            try:
                res_df = fut.result()
                processed_chunks.append(res_df)
                logger.info(f"Processed chunk {chunk_idx + 1}/{len(chunks)} complete.")
            except Exception as e:
                logger.error(f"Error processing chunk {chunk_idx}: {e}")
                
    incidents_fused = pd.concat(processed_chunks, ignore_index=True)
    
    # Merge demographic control values back into final incidents matrix using joined tract/block group IDs
    # Map tract values
    tract_dict = global_tracts.set_index('GEOID')[['Median Household Income', 'Housing Vacancy Ratio', 'Poverty Level Ratio']].to_dict('index')
    bg_dict = global_bgs.set_index('GEOID')[['Median Household Income', 'Housing Vacancy Ratio', 'Poverty Level Ratio']].to_dict('index')
    
    incidents_fused['tract_median_income'] = incidents_fused['tract_id'].map(lambda x: tract_dict.get(x, {}).get('Median Household Income'))
    incidents_fused['tract_vacancy_ratio'] = incidents_fused['tract_id'].map(lambda x: tract_dict.get(x, {}).get('Housing Vacancy Ratio'))
    incidents_fused['tract_poverty_ratio'] = incidents_fused['tract_id'].map(lambda x: tract_dict.get(x, {}).get('Poverty Level Ratio'))
    
    incidents_fused['bg_median_income'] = incidents_fused['block_group_id'].map(lambda x: bg_dict.get(x, {}).get('Median Household Income'))
    incidents_fused['bg_vacancy_ratio'] = incidents_fused['block_group_id'].map(lambda x: bg_dict.get(x, {}).get('Housing Vacancy Ratio'))
    incidents_fused['bg_poverty_ratio'] = incidents_fused['block_group_id'].map(lambda x: bg_dict.get(x, {}).get('Poverty Level Ratio'))
    
    # 7. Ingest and Interpolate Weather vectors
    logger.info(f"Ingesting NOAA weather logs from {config['weather_csv']}...")
    weather_df = pd.read_csv(config['weather_csv'])
    
    # Standardize types and clean weather attributes
    weather_df['parsed_time'] = pd.to_datetime(weather_df['DATE'], errors='coerce')
    weather_df = weather_df.dropna(subset=['parsed_time'])
    
    weather_df['temperature_celsius'] = weather_df['HourlyDryBulbTemperature'].apply(clean_numeric)
    # Convert F to C: (F - 32) * 5/9
    weather_df['temperature_celsius'] = weather_df['temperature_celsius'].apply(lambda x: (x - 32) * 5.0 / 9.0 if x is not None else None)
    
    weather_df['precipitation_depth_mm'] = weather_df['HourlyPrecipitation'].apply(clean_precip)
    weather_df['barometric_pressure'] = weather_df['HourlyStationPressure'].apply(clean_numeric)
    weather_df['wind_speed_kmh'] = weather_df['HourlyWindSpeed'].apply(clean_numeric)
    # Convert mph to kmh: mph * 1.60934
    weather_df['wind_speed_kmh'] = weather_df['wind_speed_kmh'].apply(lambda x: x * 1.60934 if x is not None else None)
    
    weather_df['date_key'] = weather_df['parsed_time'].dt.strftime('%Y-%m-%d')
    weather_df['hour_key'] = weather_df['parsed_time'].dt.hour
    
    # Group by date and hour (calculating hourly means)
    hourly_weather = weather_df.groupby(['date_key', 'hour_key']).agg({
        'temperature_celsius': 'mean',
        'precipitation_depth_mm': 'mean',
        'barometric_pressure': 'mean',
        'wind_speed_kmh': 'mean'
    }).reset_index()
    
    # Generate full hourly range grid to guarantee continuous timeline coverage
    min_dt = weather_df['parsed_time'].min()
    max_dt = weather_df['parsed_time'].max()
    full_range = pd.date_range(start=min_dt.floor('H'), end=max_dt.ceil('H'), freq='h')
    
    grid_df = pd.DataFrame({'datetime': full_range})
    grid_df['date_key'] = grid_df['datetime'].dt.strftime('%Y-%m-%d')
    grid_df['hour_key'] = grid_df['datetime'].dt.hour
    
    hourly_weather = pd.merge(grid_df, hourly_weather, on=['date_key', 'hour_key'], how='left')
    
    # Clean anomalies and fill gaps via forward-fill and backward-fill
    weather_cols = ['temperature_celsius', 'precipitation_depth_mm', 'barometric_pressure', 'wind_speed_kmh']
    hourly_weather[weather_cols] = hourly_weather[weather_cols].ffill().bfill()
    
    # Join weather with incident matrix
    logger.info("Fusing weather log dimensions onto incident records...")
    incidents_final = pd.merge(
        incidents_fused,
        hourly_weather[['date_key', 'hour_key'] + weather_cols],
        on=['date_key', 'hour_key'],
        how='left'
    )
    
    # Clean up intermediate keys
    incidents_final = incidents_final.drop(columns=['parsed_time', 'date_key', 'hour_key'])
    
    # 8. Save output fused matrix to compressed Parquet format
    logger.info(f"Saving final fused parquet layout to {config['output_parquet']}...")
    os.makedirs(os.path.dirname(config['output_parquet']), exist_ok=True)
    incidents_final.to_parquet(config['output_parquet'], compression='snappy', index=False)
    
    elapsed_time = time.time() - start_time
    logger.info(f"SUCCESS: Finished {track_name.upper()} in {elapsed_time:.2f} seconds.")
    logger.info(f"Total out-of-bounds incidents: {incidents_final['out_of_bounds'].sum()}")
    logger.info(f"Output Matrix Shape: {incidents_final.shape}")

def main():
    # Staging paths and county FIPS configuration
    chicago_config = {
        'incident_csv': str(DATA_DIR / 'chicago_crimes.csv'),
        'weather_csv': str(EXTERNAL_DATASET_DIR / 'chicago_weather_2020_2026.csv'),
        'socioeconomic_tract_csv': str(EXTERNAL_DATASET_DIR / 'cook_county_tracts_socioeconomic.csv'),
        'socioeconomic_bg_csv': str(EXTERNAL_DATASET_DIR / 'cook_county_block_groups_socioeconomic.csv'),
        'transit_stops_txt': [str(EXTERNAL_DATASET_DIR / 'cta_gtfs' / 'stops.txt')],
        'output_parquet': str(PROCESSED_DIR / 'chicago_fused_matrix.parquet'),
        'state_fips': '17',
        'county_fips': '031',
        'local_crs': 'EPSG:3435',  # Illinois State Plane East (accurate meters)
        'cache_dir': str(EXTERNAL_DATASET_DIR / 'spatial_cache'),
    }
    
    sf_config = {
        'incident_csv': str(DATA_DIR / 'sf_crimes.csv'),
        'weather_csv': str(EXTERNAL_DATASET_DIR / 'sf_weather_2020_2026.csv'),
        'socioeconomic_tract_csv': str(EXTERNAL_DATASET_DIR / 'sf_county_tracts_socioeconomic.csv'),
        'socioeconomic_bg_csv': str(EXTERNAL_DATASET_DIR / 'sf_county_block_groups_socioeconomic.csv'),
        'transit_stops_txt': [
            str(EXTERNAL_DATASET_DIR / 'sfmta_gtfs' / 'stops.txt'),
            str(EXTERNAL_DATASET_DIR / 'bart_gtfs' / 'stops.txt')
        ],
        'output_parquet': str(PROCESSED_DIR / 'sf_fused_matrix.parquet'),
        'state_fips': '06',
        'county_fips': '075',
        'local_crs': 'EPSG:2227',  # California State Plane Zone 3 (accurate meters)
        'cache_dir': str(EXTERNAL_DATASET_DIR / 'spatial_cache'),
    }
    
    # Process both metropolitan tracks
    process_track("chicago", chicago_config)
    process_track("san_francisco", sf_config)

if __name__ == "__main__":
    main()
