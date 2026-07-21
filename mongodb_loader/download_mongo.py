import os
import requests
import zipfile
import shutil

def download_and_extract():
    url = "https://fastdl.mongodb.org/windows/mongodb-windows-x86_64-7.0.12.zip"
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    dest_dir = os.path.join(base_dir, "mongodb-portable")
    zip_path = os.path.join(base_dir, "mongodb.zip")
    
    print("Creating destination directories...")
    os.makedirs(dest_dir, exist_ok=True)
    os.makedirs(os.path.join(dest_dir, "data"), exist_ok=True)
    os.makedirs(os.path.join(dest_dir, "log"), exist_ok=True)
    
    print(f"Downloading MongoDB from {url}...")
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, stream=True)
    
    if response.status_code != 200:
        print(f"Error: Server returned status code {response.status_code}")
        return
        
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024 * 1024 # 1 Megabyte
    written = 0
    
    with open(zip_path, 'wb') as f:
        for data in response.iter_content(block_size):
            f.write(data)
            written += len(data)
            if total_size > 0:
                pct = (written / total_size) * 100
                print(f"Downloaded: {written} / {total_size} bytes ({pct:.1f}%)")
            else:
                print(f"Downloaded: {written} bytes")
                
    print("Download completed. Extracting archive...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(dest_dir)
        
    print("Re-organizing files...")
    # Find the nested extracted directory
    extracted_dirs = [d for d in os.listdir(dest_dir) if os.path.isdir(os.path.join(dest_dir, d)) and "mongodb-win32" in d]
    if extracted_dirs:
        nested_dir = os.path.join(dest_dir, extracted_dirs[0])
        # Move all contents of nested_dir to dest_dir
        for item in os.listdir(nested_dir):
            src = os.path.join(nested_dir, item)
            dst = os.path.join(dest_dir, item)
            if os.path.exists(dst):
                if os.path.isdir(dst):
                    shutil.rmtree(dst)
                else:
                    os.remove(dst)
            shutil.move(src, dst)
        shutil.rmtree(nested_dir)
        print("Moved nested directory files to portable root.")
        
    # Clean up zip file
    if os.path.exists(zip_path):
        os.remove(zip_path)
        
    print("MongoDB portable version is ready in:", dest_dir)

if __name__ == "__main__":
    download_and_extract()
