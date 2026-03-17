
import os
import sys
import shutil
import zipfile
import requests

# Setup paths
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_PUBLIC_DIR = os.path.join(os.path.dirname(BACKEND_DIR), 'frontend', 'public')
ASSETS_DIR = os.path.join(FRONTEND_PUBLIC_DIR, 'brand-assets')
LOGO_ZIP_PATH = os.path.join(ASSETS_DIR, 'logo-pack.zip')
API_URL = "https://carre-sport-production.up.railway.app/api/v1/settings/store/public"

# Ensure assets dir exists
os.makedirs(ASSETS_DIR, exist_ok=True)

def fetch_and_zip_logo():
    print(f"Fetching public store settings from {API_URL}...")
    
    try:
        r = requests.get(API_URL, timeout=10)
        if r.status_code != 200:
            print(f"Failed to fetch settings: {r.status_code}")
            return
            
        settings = r.json()
        logo_url_suffix = settings.get('store_logo_url')
        
        if not logo_url_suffix:
            print("No store_logo_url found in public settings.")
            return
            
        print(f"Found logo URL suffix: {logo_url_suffix}")
        
        # Construct full URL logic from imageUrl.ts
        # If it starts with http, use it. If not, append to production base.
        if logo_url_suffix.startswith('http'):
             logo_url = logo_url_suffix
        else:
             # Ensure leading slash
             if not logo_url_suffix.startswith('/'):
                 logo_url_suffix = '/' + logo_url_suffix
             logo_url = f"https://carre-sport-production.up.railway.app{logo_url_suffix}"
             
        print(f"Full Logo URL: {logo_url}")
        
        local_logo_filename = "official-logo.png"
        
        # Download
        r_img = requests.get(logo_url, stream=True, timeout=10)
        if r_img.status_code == 200:
            with open(local_logo_filename, 'wb') as f:
                r_img.raw.decode_content = True
                shutil.copyfileobj(r_img.raw, f)
            print("Successfully downloaded logo.")
            
            # Zip it
            print(f"Creating zip at {LOGO_ZIP_PATH}")
            with zipfile.ZipFile(LOGO_ZIP_PATH, 'w') as zipf:
                zipf.write(local_logo_filename, arcname="carre-sports-logo.png")
            
            # Clean up
            os.remove(local_logo_filename)
            print("Done!")
        else:
            print(f"Failed to download image: {r_img.status_code}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_and_zip_logo()
