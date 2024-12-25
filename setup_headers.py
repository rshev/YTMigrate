#!/usr/bin/env python3
import sys
import subprocess
from ytmusicapi import setup

def get_clipboard_content():
    """Get content from clipboard using pbpaste on macOS."""
    if sys.platform == "darwin":  # macOS
        try:
            return subprocess.check_output(['pbpaste']).decode('utf-8')
        except (subprocess.SubprocessError, FileNotFoundError):
            return None
    return None

def main():
    if len(sys.argv) != 2:
        print("Usage: python setup_headers.py <output_file>")
        print("Example: python setup_headers.py source_headers.json")
        sys.exit(1)

    output_file = sys.argv[1]
    
    print("\nPlease follow these steps:")
    print("1. Open YouTube Music in your browser")
    print("2. Press F12 to open Developer Tools")
    print("3. Go to Network tab")
    print("4. Click on any request to music.youtube.com")
    print("5. Right-click the request -> Copy -> Copy request headers")
    
    print("\nOn macOS, headers will be automatically read from clipboard.")
    print("On other systems, you'll be prompted to paste them.")
    
    input("\nPress Enter when you have copied the headers...")
    
    # Try to get headers from clipboard first
    headers_raw = get_clipboard_content()
    
    try:
        # Use ytmusicapi.setup to create the headers file
        setup(filepath=output_file, headers_raw=headers_raw)
        print(f"\nHeaders successfully saved to {output_file}")
    except Exception as e:
        print(f"\nError setting up headers: {str(e)}")
        print("Please make sure you copied the correct headers format from the browser.")
        sys.exit(1)

if __name__ == "__main__":
    main()
