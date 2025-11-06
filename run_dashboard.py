"""
Run Trading Dashboard
"""
import subprocess
import sys
import os

def main():
    """Run Streamlit dashboard"""
    print("="*60)
    print("Starting Trading Dashboard...")
    print("="*60)
    print("\nDashboard will open in your browser")
    print("Press Ctrl+C to stop\n")
    
    # Run streamlit
    subprocess.run([sys.executable, "-m", "streamlit", "run", "dashboard_app.py"])


if __name__ == "__main__":
    main()


