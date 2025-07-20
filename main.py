import functools
import os
import json
from typing import Tuple
from datetime import datetime

import ytmusicapi
from ytmusicapi import YTMusic, setup_oauth

version = "1.0"
config_filename = "config.json"


def prompt_yes_no(message: str, default_yes: bool = True) -> bool:
    while True:
        sel = input(message + (" [Y/n] " if default_yes else " [y/N] "))
        if not sel:
            return default_yes
        elif sel in "yY":
            return True
        elif sel in "nN":
            return False


def write_backup(data: list | dict, type: str) -> bool:
    try:
        backup_date = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        with open(f"{type}_backup_{backup_date}.json", "w") as backup_file:
            json.dump(data, backup_file)
    except Exception as e:
        print(f"Failed to save backup, {str(e)}!")
        return False
    else:
        print("Backup saved succesfully!")
        return True


def clean_search_term(text: str) -> str:
    """Remove special characters and normalize text for better search results."""
    # Characters that could affect search efficiency
    chars_to_remove = ['&', '(', ')', '[', ']', '{', '}', '"', "'", ',', '/', '\\', '-', '+', '=', '*']
    cleaned = text
    for char in chars_to_remove:
        cleaned = cleaned.replace(char, ' ')
    # Remove extra whitespace and normalize
    cleaned = ' '.join(cleaned.split())
    return cleaned


def find_best_match(ytm: YTMusic, title: str, artists: list[str], duration_ms: int = None) -> str | None:
    """
    Find the best matching song in YouTube Music.
    Returns the videoId of the best match, or None if no good match is found.
    """
    # Clean the search terms
    clean_title = clean_search_term(title)
    clean_artists = [clean_search_term(artist) for artist in artists]
    search_query = f"{clean_title} {' '.join(clean_artists)}"
    
    try:
        # Search for the song
        results = ytm.search(search_query, filter="songs", limit=5)
        if not results:
            return None
            
        # Filter and score results
        best_match = None
        best_score = -1
        
        for result in results:
            # Skip if not a song
            if result.get('resultType') != 'song' or result.get('category') != 'Songs':
                continue
                
            # Basic score based on title and artist match
            score = 0
            result_title = clean_search_term(result.get('title', ''))
            result_artists = [clean_search_term(artist.get('name', '')) for artist in result.get('artists', [])]
            
            # Title similarity (using lower case for better matching)
            if clean_title.lower() == result_title.lower():
                score += 3
            elif clean_title.lower() in result_title.lower() or result_title.lower() in clean_title.lower():
                score += 1
                
            # Artist similarity
            for artist in clean_artists:
                for result_artist in result_artists:
                    if artist.lower() == result_artist.lower():
                        score += 2
                    elif artist.lower() in result_artist.lower() or result_artist.lower() in artist.lower():
                        score += 1
                        
            # Prefer higher quality versions
            if 'isAvailable' in result and result['isAvailable']:
                score += 1
                
            # Update best match if this result has a higher score
            if score > best_score:
                best_score = score
                best_match = result.get('videoId')
                
        return best_match if best_score >= 2 else None  # Require minimum score for match
        
    except Exception as e:
        print(f"Error searching for {title}: {str(e)}")
        return None


def copy_likes(ytm: Tuple[YTMusic, YTMusic]):
    try:
        print("\nGetting liked songs from source account...")
        liked_songs = ytm[0].get_liked_songs(limit=None)
        if not liked_songs or 'tracks' not in liked_songs:
            print("No liked songs found in source account")
            return

        liked_songs['tracks'] = list(reversed(liked_songs['tracks']))
            
        total = len(liked_songs['tracks'])
        print(f"Found {total} liked songs")
        
        success = 0
        skipped = 0
        failed = 0
        
        for i, track in enumerate(liked_songs['tracks'], 1):
            try:
                title = track.get('title', '')
                artists = [artist.get('name', '') for artist in track.get('artists', [])]
                duration = track.get('duration_seconds', 0) * 1000  # Convert to ms
                
                print(f"\n[{i}/{total}] Processing: {title} by {', '.join(artists)}")
                
                # Find the best matching song in destination account
                best_match_id = find_best_match(ytm[1], title, artists, duration)
                
                if best_match_id:
                    try:
                        ytm[1].rate_song(best_match_id, rating='LIKE')
                        success += 1
                        print(f"✓ Successfully liked the song")
                    except Exception as e:
                        print(f"✗ Failed to like the song: {str(e)}")
                        failed += 1
                else:
                    print("✗ Could not find a good match for this song")
                    skipped += 1
                    
            except Exception as e:
                print(f"✗ Error processing track: {str(e)}")
                failed += 1
                
        print(f"\nFinished copying likes:")
        print(f"Success: {success}")
        print(f"Skipped: {skipped}")
        print(f"Failed: {failed}")
        
    except Exception as e:
        print(f"Failed to copy likes: {str(e)}")


def copy_playlist(
    ytm: Tuple[YTMusic, YTMusic], playlist_id: str, playlist_name: str = ""
):
    print(f"Loading playlist: {playlist_name} - [{playlist_id}]...")
    playlist_data = ytm[0].get_playlist(playlist_id, limit=5000)
    if not playlist_data:
        print("Failed to load playlist!")
        return

    song_ids = functools.reduce(
        lambda l, i: l + [i["videoId"]], playlist_data["tracks"], []
    )

    print("Creating playlist... ", end="", flush=True)
    try:
        dest_playlist_id = ytm[1].create_playlist(
            playlist_data["title"],
            playlist_data["description"] if playlist_data["description"] else "",
            playlist_data["privacy"],
            song_ids,
        )
        # dest_playlist_id = "TEST_IS_WORKING"
        if type(dest_playlist_id) == str:
            print(
                f"\rPlaylist created successfully! URL: https://music.youtube.com/playlist?list={dest_playlist_id}"
            )
        else:
            print("\nFailed to create new playlist!")
    except Exception as e:
        print("\nFailed to create new playlist,", e)


def parse_number_ids(selection: str):
    result = []
    id_tokens = selection.split()

    for token in id_tokens:
        try:
            if "-" in token:
                start, end = map(int, token.split("-"))
                result.extend(range(start, end + 1))
            else:
                result.append(int(token))
        except ValueError:
            print(
                f"Error: Invalid format for token '{token}'. Please use a valid format."
            )
            return None
    return result


def menu_copy_playlists(ytm: Tuple[YTMusic, YTMusic]):
    print("Loading playlists from source account...", end="", flush=True)
    source_playlists = ytm[0].get_library_playlists(100)
    print("\rSelect playlists:" + " " * 30)

    all_playlists = []
    count = 0

    for playlist in source_playlists:
        # Exclude "Episodes for later" and "Liked songs" playlists
        if playlist["playlistId"] not in ("LM", "SE"):
            all_playlists += [playlist]
            count += 1
            print(
                f"{count}: {playlist['title']}"
                + (f" - {playlist['count']} songs" if "count" in playlist else "")
                + f" - [{playlist['playlistId']}]"
            )

    print("A: All playlists")
    print("C: Cancel")

    while True:
        sel = input(
            "Selection (enter playlist numbers, 'A' for all, or 'C' to cancel): "
        )
        sel_playlists = []

        if sel.lower() == "c":
            print("Operation cancelled!")
            return
        elif sel.lower() == "a":
            sel_playlists = all_playlists
        else:
            sel_ids = parse_number_ids(sel)
            if not sel_ids or not all(1 <= i <= count for i in sel_ids):
                print("Invalid selection. Please enter valid playlist numbers.")
                continue
            for i in sel_ids:
                sel_playlists += [all_playlists[i - 1]]

        for p in sel_playlists:
            try:
                copy_playlist(ytm, p["playlistId"], p["title"])
            except Exception as e:
                print(f"Error copying playlist '{p['title']}': {e}")
                # Handle the error appropriately, e.g., log it or prompt the user
        return


def copy_albums(ytm: Tuple[YTMusic, YTMusic]):
    print("Loading saved albums from source account...", end="", flush=True)
    albums_source = ytm[0].get_library_albums(limit=5000)
    # List of playlistId of all albums from library
    albums_source_ids = functools.reduce(
        lambda l, i: l + [i["playlistId"]], albums_source, []
    )

    print("\rLoading saved albums from destination account...", end="", flush=True)
    albums_dest = ytm[1].get_library_albums(limit=5000)
    # List of playlistId of all albums from library
    albums_dest_ids = functools.reduce(
        lambda l, i: l + [i["playlistId"]], albums_dest, []
    )

    print("\r" + " " * 50 + "\r", end="", flush=True)

    albums_to_save = list(set(albums_source_ids) - set(albums_dest_ids))

    if len(albums_to_save) < len(albums_source_ids):
        print(
            f"Skipping {len(albums_source_ids) - len(albums_to_save)} out of "
            f"{len(albums_source_ids)} albums saved!"
        )

    if len(albums_to_save) == 0:
        print("No albums left to transfer over!")
        return

    if not prompt_yes_no(
        f"Add {len(albums_to_save)} albums to destination account's library?"
    ):
        print("Operation cancelled!")
        return

    try:
        for index, album_playlist_id in enumerate(albums_to_save):
            print(
                f"\rAdding albums to likes... {index + 1}/{len(albums_to_save)}",
                end="",
                flush=True,
            )
            ytm[1].rate_playlist(album_playlist_id, "LIKE")
    except Exception as e:
        print("\nFailed to add albums,", e)
    else:
        print("\nTransferred all saved albums successfully!")


def remove_albums(ytm: YTMusic):
    print("\rLoading saved albums from selected account...", end="", flush=True)
    albums_data = ytm.get_library_albums(limit=5000)
    # List of playlistId and browseId of all albums from library
    albums_ids = functools.reduce(
        lambda l, i: l + [{"playlistId": i["playlistId"], "browseId": i["browseId"]}],
        albums_data,
        [],
    )

    print("\r" + " " * 50 + "\r", end="", flush=True)

    if len(albums_ids) == 0:
        print("No albums left to remove!")
        return

    print("Removed album IDs will be saved to a JSON file for safety.")
    if not prompt_yes_no(
        f"Remove {len(albums_ids)} albums from the selected account's library?"
    ):
        print("Operation cancelled!")
        return

    if not write_backup(albums_ids, "removed_albums"):
        print("Aborting operation!")
        return

    try:
        for index, album in enumerate(albums_ids):
            print(
                f"\rRemoving albums from library... {index + 1}/{len(albums_ids)}",
                end="",
                flush=True,
            )
            ytm.rate_playlist(album["playlistId"], "INDIFFERENT")
    except Exception as e:
        print("\nFailed to remove albums,", e)
    else:
        print("\nRemoved all saved albums successfully!")


def remove_likes(ytm: YTMusic):
    print("Loading liked songs from selected account...", end="", flush=True)
    liked_data = ytm.get_playlist("LM", limit=5000)
    liked_ids = functools.reduce(
        lambda l, i: l + [{"videoId": i["videoId"]}], liked_data["tracks"], []
    )

    print("\r" + " " * 50 + "\r", end="", flush=True)

    if len(liked_ids) == 0:
        print("No liked songs left to remove!")
        return

    print("Removed liked song IDs will be saved to a JSON file for safety.")
    if not prompt_yes_no(
        f"Remove {len(liked_ids)} songs from the selected account's likes?"
    ):
        print("Operation cancelled!")
        return

    if not write_backup(liked_ids, "removed_likes"):
        print("Aborting operation!")
        return

    try:
        for index, song in enumerate(liked_ids):
            print(
                f"\rRemoving songs from likes... {index + 1}/{len(liked_ids)}",
                end="",
                flush=True,
            )
            ytm.rate_song(song["videoId"], "INDIFFERENT")
    except Exception as e:
        print("\nFailed to remove songs from likes,", e)
    else:
        print("\nRemoved all liked songs successfully!")


def removal_tools(ytm: Tuple[YTMusic, YTMusic]):
    selected_ytm = ytm[0]
    while True:
        sel = input("Select an account [0=source / 1=destination]: ")
        if sel == "0" or sel == "1":
            selected_ytm = ytm[int(sel)]
            break
        else:
            print("Invalid input!")

    while True:
        print("\nWARNING: These operations are permanent and cannot be undone.")
        print("Removal tools:")
        print("  1. Remove liked songs")
        print("  2. Remove saved albums")
        print("  0. Back")
        sel = input("Your selection: ")
        match sel:
            case "0":
                return
            case "1":
                remove_likes(selected_ytm)
            case "2":
                remove_albums(selected_ytm)
            case _:
                print("Invalid selection:", sel)


def menu_main(ytm: Tuple[YTMusic, YTMusic]):
    while True:
        print("\nMain menu:")
        print("Copy tools:")
        print("  1. Copy playlists")
        print("  2. Copy likes")
        print("  3. Copy albums")
        print("Other tools:")
        print("  4. Removal tools")
        print("  0. Exit")
        sel = input("Your selection: ")
        match sel:
            case "0":
                return
            case "1":
                menu_copy_playlists(ytm)
            case "2":
                copy_likes(ytm)
            case "3":
                copy_albums(ytm)
            case "4":
                removal_tools(ytm)
            case _:
                print("Invalid option:", sel)



def check_auth_files() -> Tuple[str, str]:
    """Check which authentication files exist and return the method to use."""
    # Check for OAuth files
    source_oauth = "source_oauth.json"
    dest_oauth = "dest_oauth.json"
    if os.path.exists(source_oauth) and os.path.exists(dest_oauth):
        return "oauth", (source_oauth, dest_oauth)
    
    # Check for header files
    source_headers = "source_headers.json"
    dest_headers = "dest_headers.json"
    if os.path.exists(source_headers) and os.path.exists(dest_headers):
        return "headers", (source_headers, dest_headers)
    
    return "none", ("", "")




def do_auth() -> Tuple[YTMusic, YTMusic] | None:
    try:
        # Check which authentication method to use
        auth_method, (source_file, dest_file) = check_auth_files()
        
        if auth_method == "none":
            print("\nNo authentication files found!")
            print("\nTo use OAuth authentication (recommended):")
            print("1. Run: python setup_oauth.py client_secrets.json source_oauth.json")
            print("2. Run: python setup_oauth.py client_secrets.json dest_oauth.json")
            print("\nOr to use browser headers:")
            print("1. Run: python setup_headers.py source_headers.json")
            print("2. Run: python setup_headers.py dest_headers.json")
            return None
            
        print(f"Using {auth_method} authentication...")
        
        print("Initializing source account...")
        try:
            source_ytm = YTMusic(source_file)
            # Test with a simple search query first
            test_search = source_ytm.search("test", filter="songs", limit=1)
            if not test_search:
                raise Exception("Could not perform search")
            print("Source account initialized and tested successfully")
        except Exception as e:
            print(f"Failed to initialize source account: {str(e)}")
            return None
        
        print("Initializing destination account...")
        try:
            dest_ytm = YTMusic(dest_file)
            # Test with a simple search query first
            test_search = dest_ytm.search("test", filter="songs", limit=1)
            if not test_search:
                raise Exception("Could not perform search")
            print("Destination account initialized and tested successfully")
        except Exception as e:
            print(f"Failed to initialize destination account: {str(e)}")
            return None
        
        # Now test more specific functionality
        try:
            print("Testing source account liked songs access...")
            source_test = source_ytm.get_playlist("LM", limit=1)
            if source_test is None:
                raise Exception("Could not access library")
                
            print("Testing destination account liked songs access...")
            dest_test = dest_ytm.get_playlist("LM", limit=1)
            if dest_test is None:
                raise Exception("Could not access library")
                
            print("All authentication tests successful!")
            return (source_ytm, dest_ytm)
        except Exception as e:
            print(f"Failed to verify full access: {str(e)}")
            if auth_method == "oauth":
                print("\nPlease try setting up OAuth authentication again:")
                print("1. Run: python setup_oauth.py client_secrets.json source_oauth.json")
                print("2. Run: python setup_oauth.py client_secrets.json dest_oauth.json")
            else:
                print("\nPlease try updating your browser headers:")
                print("1. Run: python setup_headers.py source_headers.json")
                print("2. Run: python setup_headers.py dest_headers.json")
            return None
            
    except Exception as e:
        print(f"Authentication failed: {str(e)}")
        return None


def main():
    print(f"YTMigrate, version {version}\n")

    ytm = do_auth()
    if ytm:
        menu_main(ytm)


if __name__ == "__main__":
    main()
