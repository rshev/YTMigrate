#!/usr/bin/env python3
import json
import sys
from ytmusicapi import setup_oauth, YTMusic

def load_client_secrets(file_path):
    """Load client ID and secret from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            secrets = json.load(f)
            web = secrets.get('web', secrets.get('installed', {}))
            return web.get('client_id'), web.get('client_secret')
    except Exception as e:
        print(f"Error loading client secrets: {str(e)}")
        return None, None

def main():
    if len(sys.argv) != 3:
        print("Usage: python setup_oauth.py <client_secrets_file> <output_file>")
        print("Example: python setup_oauth.py client_secrets.json source_oauth.json")
        sys.exit(1)

    secrets_file = sys.argv[1]
    output_file = sys.argv[2]
    
    print("\nSetting up OAuth authentication...")
    
    # Load client secrets
    client_id, client_secret = load_client_secrets(secrets_file)
    if not client_id or not client_secret:
        print("Error: Could not load client ID and secret from secrets file")
        print("Make sure your client_secrets.json file is properly formatted")
        print("You can download it from Google Cloud Console -> APIs & Services -> Credentials")
        sys.exit(1)
    
    try:
        print("\nStarting OAuth flow...")
        print("A browser window will open for you to sign in to your Google account.")
        print("Please make sure to:")
        print("1. Select your Google Account")
        print("2. Click 'Continue' when asked about access")
        print("3. Click 'Continue' again if warned about verification")
        print("\nIf the browser doesn't open automatically, check the terminal for the authorization URL.")
        
        # Setup OAuth with automatic browser opening and required scopes
        oauth_token = setup_oauth(
            client_id=client_id,
            client_secret=client_secret,
            filepath=output_file,
            open_browser=True
        )
        
        print(f"\nOAuth setup successful!")
        print(f"Credentials saved to {output_file}")
        
        # Test the credentials
        print("\nTesting the credentials...")
        try:
            ytm = YTMusic(auth=output_file)
            test = ytm.search("test", filter="songs", limit=1)
            if test:
                print("Credentials verified successfully!")
            else:
                print("Warning: Could not verify credentials with a test search")
        except Exception as e:
            print(f"Warning: Could not verify credentials: {str(e)}")
        
    except Exception as e:
        print(f"\nError during OAuth setup: {str(e)}")
        print("\nPlease make sure:")
        print("1. Your client_secrets.json is valid")
        print("2. You have a stable internet connection")
        print("3. The application is properly configured in Google Cloud Console")
        print("4. You have enabled the YouTube Data API v3 in Google Cloud Console")
        sys.exit(1)

if __name__ == "__main__":
    main()
