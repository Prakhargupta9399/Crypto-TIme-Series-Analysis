import subprocess
import sys
import time
import os

def main():
    print("--- CryptoTime Analytics Launcher ---")
    
    # 1. Setup Data
    print("🔄 Step 1: Checking data setup...")
    try:
        # Run setup script synchronously
        subprocess.check_call([sys.executable, "setup_data.py"])
        print("✅ Data setup complete.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Data setup failed: {e}")
        return

    # 2. Start Backend (FastAPI)
    print("🚀 Step 2: Starting Backend API...")
    # We use a list of arguments here to handle spaces in file paths correctly
    backend_cmd = [sys.executable, "main.py"]
    backend_process = subprocess.Popen(backend_cmd)
    
    # Give the backend a few seconds to initialize
    print("⏳ Waiting for Backend to initialize (5 seconds)...")
    time.sleep(5)

    # 3. Start Frontend (Streamlit)
    print("🖥️  Step 3: Launching Frontend Dashboard...")
    # CRITICAL: Use the specific 'streamlit' command, not 'python app.py'
    # Using sys.executable -m streamlit ensures it uses the correct python environment
    frontend_cmd = [sys.executable, "-m", "streamlit", "run", "app.py"]
    
    # This will run streamlit and take over this terminal window
    try:
        subprocess.call(frontend_cmd)
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        backend_process.terminate()
        print("👋 Goodbye!")

if __name__ == "__main__":
    main()