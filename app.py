import os
import sys
import subprocess
import time
import socket
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_env():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    while True:
        env_path = os.path.join(current_dir, ".env")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        os.environ[k.strip()] = v.strip()
            break
        parent = os.path.dirname(current_dir)
        if parent == current_dir:
            break
        current_dir = parent

load_env()

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def run_all():
    print("=" * 60)
    print("LAUNCHING WORKFORCEX PLATFORM SUITE")
    print("=" * 60)
    
    processes = []
    
    # 1. Database Connection & Seeding Check
    print("\n[Database] Connecting to MongoDB...")
    mongo_uri = os.environ.get("MONGO_URI")
    connected = False
    
    try:
        import pymongo
        client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client["WorkForceX"]
        prof_count = db["professionals"].count_documents({})
        job_count = db["jobs"].count_documents({})
        print(f"[Database] Connected to MongoDB Atlas successfully! ({prof_count} professionals, {job_count} jobs found).")
        connected = True
        
        if prof_count == 0 or job_count == 0:
            print("[Database] Collections are empty. Running dataset loader...")
            seeder_script = os.path.join(BASE_DIR, "mongodb_loader", "load_datasets.py")
            subprocess.run([sys.executable, seeder_script], check=True)
            print("[Database] Seeding completed.")
    except Exception as e:
        print(f"[Database] Could not connect to primary MONGO_URI: {e}")
        
    if not connected:
        if not is_port_open(27017):
            print("\n[Database] Starting local portable MongoDB server...")
            mongo_path = os.path.join(BASE_DIR, "mongodb-portable", "bin", "mongod.exe")
            db_path = os.path.join(BASE_DIR, "mongodb-portable", "data")
            log_path = os.path.join(BASE_DIR, "mongodb-portable", "log", "mongo.log")
            
            os.makedirs(db_path, exist_ok=True)
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            
            cmd = [
                mongo_path,
                "--dbpath", db_path,
                "--logpath", log_path,
                "--port", "27017",
                "--bind_ip", "127.0.0.1"
            ]
            
            try:
                mongo_proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                processes.append(("MongoDB", mongo_proc))
                print("[Database] Portable MongoDB process started in background.")
                time.sleep(2)
            except Exception as e:
                print(f"[Database] Error starting local MongoDB: {e}")
        else:
            print("[Database] Local MongoDB is already running on port 27017.")

        # Ensure environment variable points to local MongoDB for child processes
        local_uri = "mongodb://127.0.0.1:27017"
        os.environ["MONGO_URI"] = local_uri
        try:
            import pymongo
            client = pymongo.MongoClient(local_uri, serverSelectionTimeoutMS=3000)
            db = client["WorkForceX"]
            prof_count = db["professionals"].count_documents({})
            job_count = db["jobs"].count_documents({})
            print(f"[Database] Connected to local MongoDB ({prof_count} professionals, {job_count} jobs found).")
            if prof_count == 0 or job_count == 0:
                print("[Database] Collections are empty. Running dataset loader...")
                seeder_script = os.path.join(BASE_DIR, "mongodb_loader", "load_datasets.py")
                subprocess.run([sys.executable, seeder_script], env=os.environ, check=True)
                print("[Database] Seeding completed.")
        except Exception as e:
            print(f"[Database] Notice on local MongoDB check: {e}")

    # 2. Start Flask Backend API
    print("\n[Backend] Starting Flask REST API server on port 5000...")
    backend_script = os.path.join(BASE_DIR, "backend", "app.py")
    try:
        backend_proc = subprocess.Popen([sys.executable, "-u", backend_script], env=os.environ)
        processes.append(("Flask Backend", backend_proc))
    except Exception as e:
        print(f"[Backend] Failed to start Flask: {e}")
        sys.exit(1)
        
    time.sleep(2)

    # 3. Start Streamlit Frontend Web App
    print("\n[Frontend] Starting Streamlit interface on port 8501...")
    frontend_script = os.path.join(BASE_DIR, "frontend", "streamlit_app.py")
    try:
        frontend_proc = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", frontend_script, 
            "--server.port", "8501",
            "--server.headless", "true"
        ], env=os.environ)
        processes.append(("Streamlit Frontend", frontend_proc))
    except Exception as e:
        print(f"[Frontend] Failed to start Streamlit: {e}")
        backend_proc.terminate()
        sys.exit(1)
        
    time.sleep(2)
    
    # 4. Open Web Browser
    print("\n[System] Opening application inside browser...")
    try:
        webbrowser.open("http://localhost:8501")
    except Exception as e:
        print(f"[System] Failed to open browser: {e}. Access at http://localhost:8501")
    
    print("\n" + "=" * 60)
    print("WORKFORCEX IS FULLY ONLINE & READY TO USE!")
    print("Go to http://localhost:8501 in your browser.")
    print("Press Ctrl+C in this terminal window to stop all services.")
    print("=" * 60 + "\n")
    
    # Keep main thread alive and monitor processes
    try:
        while True:
            for name, proc in processes:
                if proc.poll() is not None:
                    print(f"\nWARNING: {name} process exited unexpectedly with code {proc.poll()}.")
                    raise KeyboardInterrupt
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n[System] Stopping all services...")
        for name, proc in processes:
            print(f"[System] Terminating {name}...")
            try:
                proc.terminate()
                proc.wait()
            except Exception:
                pass
        print("[System] All services shut down successfully. Goodbye!")

if __name__ == "__main__":
    run_all()
