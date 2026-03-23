import zipfile
import os

def create_zip(csv_path: str, metadata_path: str, output_path: str):
    with zipfile.ZipFile(output_path, 'w') as zipf:
        zipf.write(csv_path, os.path.basename(csv_path))
        zipf.write(metadata_path, os.path.basename(metadata_path))

    return output_path