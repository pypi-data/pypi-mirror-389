from pchime.local_data_instances.fresh_installation_conditions.create_storage_blob_directory import create_storage_blob_folder
import os 
from pathlib import Path
import pandas as pd

def load_csv_file(args) -> None:
    csv_path = Path(args.csv)
    storage_path = create_storage_blob_folder()
    if storage_path is None:
        raise RuntimeError("Failed to locate storage path")
    out_dir = Path(storage_path) / args.project
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / (csv_path.stem + ".parquet")
    try:
        df = pd.read_csv(csv_path)
        df.to_parquet(out_path, index=False, compression="snappy")
        print(f"Saved parquet into storage blob: {out_path}")

    except Exception as e:
        raise RuntimeError(f"Conversion failed: {e}")
    

