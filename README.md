# YTMigrate

A Python tool to migrate your YouTube Music data (liked songs, playlists) between different accounts.

## Setup

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)
- A Google Cloud Project with YouTube Data API v3 enabled (for OAuth authentication)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/raedkit/YTMigrate.git
cd YTMigrate
```

2. Create and activate a virtual environment:

```bash
# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
.\venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Authentication

YTMigrate supports two authentication methods:

### Method 1: OAuth Authentication (Recommended)

1. Set up OAuth credentials:

   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project or select an existing one
   - Enable the YouTube Data API v3
   - Go to Credentials -> Create Credentials -> OAuth Client ID
   - Choose "Desktop Application" as application type
   - Download the client secrets file and save it as `client_secrets.json` in the project directory

2. Set up authentication for both accounts:

```bash
# For source account
python setup_oauth.py client_secrets.json source_oauth.json

# For destination account
python setup_oauth.py client_secrets.json dest_oauth.json
```

### Method 2: Browser Headers Authentication

If OAuth setup is not possible, you can use browser headers:

1. Set up authentication for both accounts:

```bash
# For source account
python setup_headers.py source_headers.json

# For destination account
python setup_headers.py dest_headers.json
```

2. Follow the instructions to copy headers from your browser:
   - Open YouTube Music in your browser
   - Open Developer Tools (F12)
   - Go to Network tab
   - Click on any request to music.youtube.com
   - Right-click -> Copy -> Copy request headers
   - Paste when prompted (on macOS, headers will be automatically read from clipboard)

## Usage

After setting up authentication, run the main script:

```bash
python main.py
```

The script will:

1. Authenticate with both accounts
2. Load liked songs from the source account
3. Copy any songs that aren't already liked in the destination account

## Troubleshooting

### OAuth Issues

- Make sure the YouTube Data API v3 is enabled in your Google Cloud Project
- Verify that your OAuth consent screen is properly configured
- Check that you're using the correct Google accounts when authorizing

### Headers Issues

- Ensure you're copying the full headers from a recent request
- Try logging out and back in to YouTube Music before copying headers
- Make sure you're using different browsers/incognito mode for each account
- Read `ytmusicapi` headers authentication [documentation](https://ytmusicapi.readthedocs.io/en/stable/setup/browser.html)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
