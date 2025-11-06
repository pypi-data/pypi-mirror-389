import yt_dlp
import spotipy
import time
import random
import threading
import queue
import sys
import select
import os
import json
import argparse
import logging
import requests
import io
from pathlib import Path
from PIL import Image
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.cache_handler import CacheFileHandler
from mpv import MPV
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.progress_bar import ProgressBar
from rich.prompt import Prompt, Confirm

console = Console()

# --- Configuration & Logging Setup ---

cache_path = os.path.join(os.path.expanduser("~"), ".cache_headless_music")
cache_handler = CacheFileHandler(cache_path=cache_path)

CONFIG_FILE = Path.home() / ".headless_music_config.json"
LOG_FILE = Path.home() / ".headless_music.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- Config & Setup ---

def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.warning(f"Could not load config: {e}")
            console.print(f"[yellow]Warning: Could not load config: {e}[/yellow]")
    return {}

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        logging.error(f"Error saving config: {e}")
        console.print(f"[red]Error saving config: {e}[/red]")
        return False

def setup_wizard():
    console.clear()
    console.print("=" * 60, style="cyan")
    console.print("🎵 Welcome to headless_music Setup!", style="bold cyan", justify="center")
    console.print("=" * 60, style="cyan")
    console.print()

    config = load_config()

    console.print("📱 [bold]Spotify API Credentials[/bold]")
    console.print("   Get these from: https://developer.spotify.com/dashboard", style="dim")
    console.print()

    spotify_id = Prompt.ask(
        "   Spotify Client ID",
        default=config.get('SPOTIFY_CLIENT_ID', '')
    )
    spotify_secret = Prompt.ask(
        "   Spotify Client Secret",
        default=config.get('SPOTIFY_CLIENT_SECRET', ''),
        password=True
    )

    console.print()
    console.print("🎧 [bold]Playlist Source[/bold]")
    console.print()

    source_choice = Prompt.ask(
        "   Choose your playlist source",
        choices=["spotify", "youtube"],
        default=config.get('PLAYLIST_SOURCE', 'spotify')
    )

    console.print()

    if source_choice == "spotify":
        console.print("   Enter your Spotify playlist URL or URI", style="dim")
        console.print("   Example: https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M", style="dim")
        playlist_url = Prompt.ask("   Spotify Playlist URL/URI")
    else:
        console.print("   Enter your YouTube playlist URL", style="dim")
        console.print("   Example: https://www.youtube.com/playlist?list=...", style="dim")
        playlist_url = Prompt.ask("   YouTube Playlist URL")

    console.print()

    new_config = {
        'SPOTIFY_CLIENT_ID': spotify_id,
        'SPOTIFY_CLIENT_SECRET': spotify_secret,
        'PLAYLIST_SOURCE': source_choice,
        'PLAYLIST_URL': playlist_url
    }

    if save_config(new_config):
        console.print("✓ Configuration saved!", style="bold green")
        console.print(f"   Config location: {CONFIG_FILE}", style="dim")
        console.print(f"   Log location: {LOG_FILE}", style="dim")
    else:
        console.print("⚠️  Could not save configuration. You'll need to re-enter it next time.", style="yellow")

    console.print()
    if Confirm.ask("Start headless_music now?", default=True):
        return new_config
    else:
        console.print("👋 Run this script again when you're ready!", style="cyan")
        sys.exit(0)

def validate_config(config):
    required = ['SPOTIFY_CLIENT_ID', 'SPOTIFY_CLIENT_SECRET', 'PLAYLIST_SOURCE', 'PLAYLIST_URL']
    missing = [key for key in required if not config.get(key)]

    if missing:
        console.print(f"[red]Missing configuration: {', '.join(missing)}[/red]")
        return False
    return True

# --- Globals ---

command_queue = queue.Queue()
master_playlist = []
current_index = 0
player = MPV(ytdl=True, video=False, keep_open=False)
layout = Layout()
is_running = True
sp_client = None
config = {}
current_ascii_art = None

# --- Helper Functions ---

def format_time(seconds):
    if seconds is None or seconds < 0:
        return "--:--"
    m, s = divmod(int(seconds), 60)
    return f"{m:02}:{s:02}"

# --- Data Fetching Functions ---

def get_youtube_playlist_titles(url):
    ydl_opts = {'quiet': True, 'extract_flat': True, 'no_warnings': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        # Store (title, artist, source, image_url)
        return [(e['title'], e.get('uploader', 'Unknown'), "YouTube", None) for e in info['entries'] if e]
    except Exception as e:
        logging.error(f"Error fetching YouTube playlist: {e}")
        return []

def get_spotify_playlist_tracks(sp, playlist_url):
    try:
        if 'spotify.com' in playlist_url:
            playlist_id = playlist_url.split('playlist/')[-1].split('?')[0]
        elif 'spotify:playlist:' in playlist_url:
            playlist_id = playlist_url.split('spotify:playlist:')[-1]
        else:
            playlist_id = playlist_url

        results = []
        offset = 0

        while True:
            response = sp.playlist_tracks(playlist_id, offset=offset, limit=100)
            for item in response['items']:
                if item['track']:
                    track = item['track']
                    # Get the smallest image URL (better for terminal rendering)
                    image_url = track['album']['images'][-1]['url'] if track['album']['images'] else None
                    results.append((
                        track['name'],
                        track['artists'][0]['name'],
                        "Spotify",
                        image_url
                    ))

            if not response['next']:
                break
            offset += 100

        logging.info(f"Fetched {len(results)} tracks from Spotify playlist")
        return results
    except Exception as e:
        logging.error(f"Error fetching Spotify playlist: {e}")
        return []

def spotify_setup():
    global sp_client, config
    if sp_client is None:
        try:
            sp_client = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
                client_id=config['SPOTIFY_CLIENT_ID'],
                client_secret=config['SPOTIFY_CLIENT_SECRET']
            ))
            logging.info("Spotify client initialized successfully")
        except Exception as e:
            logging.error(f"Failed to setup Spotify client: {e}")
            return None
    return sp_client

def get_spotify_tracks_by_search(sp, titles_artists, limit=20):
    """Returns (name, artist, image_url, track_id)"""
    results = []
    seen_ids = set()

    sample_size = min(len(titles_artists), 10)
    sampled = random.sample(titles_artists, sample_size)

    for title, artist, _, _ in sampled:
        try:
            artist_results = sp.search(q=f"artist:{artist}", type="artist", limit=1)
            if artist_results['artists']['items']:
                artist_id = artist_results['artists']['items'][0]['id']
                top_tracks = sp.artist_top_tracks(artist_id)
                for track in top_tracks['tracks'][:3]:
                    track_id = track['id']
                    if track_id not in seen_ids:
                        image_url = track['album']['images'][-1]['url'] if track['album']['images'] else None
                        results.append((track['name'], track['artists'][0]['name'], image_url, track_id))
                        seen_ids.add(track_id)
                        if len(results) >= limit: return results
        except Exception as e:
            logging.warning(f"Error in Spotify artist search: {e}")
            continue

        try:
            track_results = sp.search(q=f"{title} {artist}", type="track", limit=3)
            for track in track_results['tracks']['items']:
                track_id = track['id']
                if track_id not in seen_ids:
                    image_url = track['album']['images'][-1]['url'] if track['album']['images'] else None
                    results.append((track['name'], track['artists'][0]['name'], image_url, track_id))
                    seen_ids.add(track_id)
                    if len(results) >= limit: return results
        except Exception as e:
            logging.warning(f"Error in Spotify track search: {e}")
            continue

    return results

def spotify_recommendations_with_fallback(sp, titles_artists, limit=20):
    """Returns (name, artist, source, image_url)"""
    if not sp: return []
    results = []
    seen_ids = set()

    sample_size = min(len(titles_artists), 5)
    sampled = random.sample(titles_artists, sample_size)

    for title, artist, _, _ in sampled:
        try:
            search_results = sp.search(q=f"{title} {artist}", type="track", limit=1)
            if search_results['tracks']['items']:
                seed_id = search_results['tracks']['items'][0]['id']
                try:
                    recs = sp.recommendations(seed_tracks=[seed_id], limit=5)
                    for track in recs['tracks']:
                        track_id = track['id']
                        if track_id not in seen_ids:
                            image_url = track['album']['images'][-1]['url'] if track['album']['images'] else None
                            results.append((track['name'], track['artists'][0]['name'], "Spotify", image_url))
                            seen_ids.add(track_id)
                except Exception as e:
                    logging.warning(f"Error getting Spotify recommendations: {e}")
                    pass
        except Exception as e:
            logging.warning(f"Error searching for seed track: {e}")
            continue

    if len(results) < limit:
        for title, artist, _, _ in sampled:
            try:
                artist_results = sp.search(q=f"artist:{artist}", type="artist", limit=1)
                if artist_results['artists']['items']:
                    artist_id = artist_results['artists']['items'][0]['id']
                    related = sp.artist_related_artists(artist_id)
                    for rel_artist in related['artists'][:3]:
                        top_tracks = sp.artist_top_tracks(rel_artist['id'])
                        for track in top_tracks['tracks'][:2]:
                            track_id = track['id']
                            if track_id not in seen_ids:
                                image_url = track['album']['images'][-1]['url'] if track['album']['images'] else None
                                results.append((track['name'], track['artists'][0]['name'], "Spotify", image_url))
                                seen_ids.add(track_id)
                                if len(results) >= limit: return results
            except Exception as e:
                logging.warning(f"Error getting related artist tracks: {e}")
                continue

    if len(results) < limit // 2:
        search_results = get_spotify_tracks_by_search(sp, titles_artists, limit - len(results))
        for name, artist, image_url, track_id in search_results:
            if track_id not in seen_ids:
                results.append((name, artist, "Spotify", image_url))
                seen_ids.add(track_id)

    logging.info(f"Generated {len(results)} recommended tracks")
    return results

def fetch_more_youtube_tracks():
    if not master_playlist: return []

    results = []
    sample = random.sample(master_playlist, min(3, len(master_playlist)))
    ydl_opts = {'quiet': True, 'extract_flat': False, 'no_warnings': True}

    for title, artist, _, _ in sample:
        try:
            search_query = f"{artist} {title} audio"
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                search_results = ydl.extract_info(f"ytsearch5:{search_query}", download=False)
                if search_results and 'entries' in search_results:
                    for entry in search_results['entries']:
                        if entry:
                            image_url = entry.get('thumbnail')
                            results.append((
                                entry.get('title', 'Unknown'),
                                entry.get('uploader', 'Unknown'),
                                "YouTube",
                                image_url
                            ))
        except Exception as e:
            logging.warning(f"Error fetching more YouTube tracks: {e}")
            continue

    return results

# --- ASCII Art Generation ---

def generate_ascii_art(image_url, height):
    """Generate ASCII art from image URL using colored blocks."""
    try:
        # Limit dimensions to prevent issues
        height = max(1, min(height, 30))
        width = height * 2

        logging.info(f"Generating ASCII art: {image_url} (size: {width}x{height})")

        response = requests.get(image_url, timeout=5)
        response.raise_for_status()

        with Image.open(io.BytesIO(response.content)) as img:
            # Resize image to desired ASCII dimensions
            img = img.resize((width, height), Image.Resampling.LANCZOS)
            img = img.convert("RGB")

            ascii_lines = []
            for y in range(height):
                line = ""
                for x in range(width):
                    r, g, b = img.getpixel((x, y))
                    # Use block character with matching foreground and background
                    line += f"[rgb({r},{g},{b}) on rgb({r},{g},{b})]▀[/]"

                ascii_lines.append(line)

            logging.info(f"ASCII art generated successfully ({len(ascii_lines)} lines)")
            return Text.from_markup("\n".join(ascii_lines), justify="center")

    except Exception as e:
        logging.warning(f"Failed to generate ASCII art for {image_url}: {e}")
        return None

def get_placeholder_art(height=8):
    """Returns the static placeholder art, scaled to height."""
    base_art = [
        "╔══════════════╗",
        "║              ║",
        "║    [bold]🎵[/bold]        ║",
        "║              ║",
        "║   [dim]headless[/dim]   ║",
        "║   [dim]_music[/dim]    ║",
        "║              ║",
        "╚══════════════╝",
    ]
    base_height = len(base_art)

    scaled_art_lines = []

    if height <= 0:
        return Text("")

    if height < base_height:
        start_index = (base_height - height) // 2
        for i in range(height):
            scaled_art_lines.append(f"  [green]{base_art[start_index + i]}[/green]")
    else:
        top_padding = (height - base_height) // 2
        bottom_padding = height - base_height - top_padding

        scaled_art_lines.extend([""] * top_padding)
        for line in base_art:
            scaled_art_lines.append(f"  [green]{line}[/green]")
        scaled_art_lines.extend([""] * bottom_padding)

    return Text.from_markup("\n".join(scaled_art_lines), justify="center")

# --- UI Panel Creation ---

def create_ascii_art_panel(image_url, height):
    """Creates the panel, trying to generate art, falling back to placeholder."""
    global current_ascii_art

    if image_url:
        try:
            art = generate_ascii_art(image_url, height)
            if art:
                current_ascii_art = Panel(art, border_style="dim", padding=(0, 0))
                return current_ascii_art
        except Exception as e:
            logging.warning(f"Failed to create ASCII art panel: {e}")

    # Fallback to placeholder
    current_ascii_art = Panel(get_placeholder_art(height), border_style="dim")
    return current_ascii_art

def create_now_playing_panel(title, artist, source):
    source_color = "red" if source == "YouTube" else "green"
    display_title = title[:60] + "..." if len(title) > 60 else title
    display_artist = artist[:40] + "..." if len(artist) > 40 else artist

    display_text = Text.from_markup(f"""
[bold]{display_title}[/bold]
[dim]{display_artist}[/dim]
Source: [{source_color}]{source}[/{source_color}]
""")
    return Panel(display_text, title="Now Playing", padding=(0, 2, 0, 2), border_style="dim")

def create_queue_panel():
    lines = []

    if 0 <= current_index < len(master_playlist):
        title, artist, _, _ = master_playlist[current_index]
        display_title = title[:30] + "..." if len(title) > 30 else title
        lines.append(Text.from_markup(f"[bold green] > {display_title}[/bold green]"))
        lines.append(Text.from_markup(f"   [dim]{artist[:30]}[/dim]"))
        lines.append(Text.from_markup("---"))

    end_idx = min(current_index + 11, len(master_playlist))

    if end_idx == current_index + 1 and len(master_playlist) > 0:
         lines.append(Text.from_markup("  [dim]Fetching more tracks...[/dim]"))

    for i in range(current_index + 1, end_idx):
        title, artist, _, _ = master_playlist[i]
        display_title = title[:30] + "..." if len(title) > 30 else title
        lines.append(Text.from_markup(f"   {i - current_index}. {display_title}"))
        lines.append(Text.from_markup(f"      [dim]{artist[:30]}[/dim]"))

    if not lines:
        return Panel(Text("  [dim]Loading queue...[/dim]"), title="Queue", border_style="dim", padding=(1,1))

    return Panel(Text("\n").join(lines), title="Queue", border_style="dim", padding=(1,1))

def create_progress_panel():
    try:
        time_pos = player.time_pos if player.time_pos else 0
        duration = player.duration if player.duration else 0
        percent = (time_pos / duration * 100) if duration and time_pos else 0

        bar = ProgressBar(total=100, completed=percent, width=None, complete_style="green", pulse=duration == 0)
        time_display = Text(f"{format_time(time_pos)} / {format_time(duration)}", justify="right")
        icon = "⏸" if player.pause else "▶"

        prog_layout = Layout()
        prog_layout.split_row(
            Layout(Text(f" {icon} "), name="icon", size=3),
            Layout(bar, name="bar"),
            Layout(time_display, name="time", size=15)
        )
        return prog_layout
    except Exception as e:
        logging.warning(f"Error creating progress panel: {e}")
        return Layout(Text(""))

def create_controls_panel():
    return Panel(
        Text.from_markup(
            "[bold cyan]n[/bold cyan] next  •  [bold cyan]p[/bold cyan] prev  •  [bold cyan]space[/bold cyan] pause/play  •  [bold cyan]q[/bold cyan] quit  •  [bold cyan]c[/bold cyan] config",
            justify="center"
        ),
        border_style="dim"
    )

def create_layout():
    """Creates the Spotify-esque layout."""
    layout.split_row(
        Layout(name="sidebar", size=40),
        Layout(name="main", ratio=1)
    )

    layout["main"].split_column(
        Layout(name="art", ratio=1),
        Layout(name="now_playing", size=5),
        Layout(name="progress", size=1),
        Layout(name="footer", size=3)
    )

    return layout

# --- Playback & Input Logic ---

def play_track(index):
    global current_index
    if index < 0 or index >= len(master_playlist):
        if index >= len(master_playlist) and len(master_playlist) > 0:
           index = 0
        else:
            return

    current_index = index
    (title, artist, source, image_url) = master_playlist[current_index]

    # Calculate available height for art dynamically
    # Account for: now_playing (5) + progress (1) + footer (3) + panel borders (2)
    available_height = max(1, console.height - 11)

    logging.info(f"Playing track: {title} by {artist}")
    logging.info(f"Console height: {console.height}, Art height: {available_height}")
    logging.info(f"Image URL: {image_url}")

    # Update all relevant UI panels
    layout["art"].update(create_ascii_art_panel(image_url, available_height))
    layout["now_playing"].update(create_now_playing_panel(title, artist, source))
    layout["sidebar"].update(create_queue_panel())

    try:
        query = f"{title} {artist} audio"
        player.play(f"ytdl://ytsearch1:{query}")
        player.pause = False
    except Exception as e:
        logging.error(f"Error playing track: {e}")
        command_queue.put("next")

def check_and_refresh_queue():
    global master_playlist

    if len(master_playlist) - current_index < 5:
        seed_tracks = master_playlist[max(0, current_index - 10) : current_index + 1]
        sp = spotify_setup()
        if not sp:
            logging.error("Spotify client not available for refreshing queue.")
            return

        new_tracks = spotify_recommendations_with_fallback(sp, seed_tracks, limit=15)

        if len(new_tracks) < 5:
            yt_tracks = fetch_more_youtube_tracks()
            new_tracks.extend(yt_tracks[:10])

        if new_tracks:
            master_playlist.extend(new_tracks)
            layout["sidebar"].update(create_queue_panel())
            logging.info(f"Queue refreshed with {len(new_tracks)} new tracks")
        else:
            master_playlist.extend(master_playlist[:20])
            logging.info("Queue refreshed by looping playlist")

@player.property_observer('idle-active')
def handle_song_end(_name, value):
    if value and is_running:
        command_queue.put("next")

def input_thread():
    global is_running
    while is_running:
        try:
            if sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
                char = sys.stdin.read(1)
                if char == 'n':
                    command_queue.put("next")
                elif char == 'p':
                    command_queue.put("prev")
                elif char == ' ':
                    command_queue.put("pause")
                elif char == 'q':
                    command_queue.put("quit")
                    is_running = False
                elif char == 'c':
                    command_queue.put("config")
        except Exception as e:
            logging.error(f"Error in input thread: {e}")
            is_running = False

# --- Main ---

def main():
    global master_playlist, current_index, layout, is_running, config, current_ascii_art

    logging.info("=" * 60)
    logging.info("headless_music starting")
    logging.info("=" * 60)

    config = load_config()

    if not validate_config(config):
        config = setup_wizard()

    console.print("🎵 Initialising headless_music...", style="bold cyan")
    console.print(f"📡 Fetching {config['PLAYLIST_SOURCE'].title()} playlist...", style="bold green")

    sp = spotify_setup()
    if config['PLAYLIST_SOURCE'] == 'spotify':
        if not sp:
            console.print("[red]Failed to initialize Spotify client. Check credentials. Exiting.[/red]")
            return
        playlist_tracks = get_spotify_playlist_tracks(sp, config['PLAYLIST_URL'])
        if not playlist_tracks:
            console.print("[red]Failed to fetch Spotify playlist. Exiting.[/red]")
            return
    else:  # youtube
        playlist_tracks = get_youtube_playlist_titles(config['PLAYLIST_URL'])
        if not playlist_tracks:
            console.print("[red]Failed to fetch YouTube playlist. Exiting.[/red]")
            return

    console.print(f"✓ Found {len(playlist_tracks)} tracks from {config['PLAYLIST_SOURCE'].title()}", style="green")
    console.print("🎧 Fetching additional tracks...", style="bold green")

    if not sp:
        console.print("[yellow]⚠️  Spotify client not available, cannot fetch additional tracks.[/yellow]")
        additional_tracks = []
    else:
        additional_tracks = spotify_recommendations_with_fallback(sp, playlist_tracks, limit=30)
        if additional_tracks:
            console.print(f"✓ Added {len(additional_tracks)} additional tracks", style="green")
        else:
            console.print("[yellow]⚠️  Could not fetch additional tracks, using playlist only[/yellow]")

    master_playlist = playlist_tracks + additional_tracks
    if not master_playlist:
        console.print("[red]No tracks found. Exiting.[/red]")
        return

    current_index = 0
    layout = create_layout()
    current_ascii_art = Panel(get_placeholder_art(), border_style="dim")

    try:
        import tty
        old_settings = tty.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())
    except Exception:
        logging.warning("Could not set TTY to cbreak mode. Input may not work.")
        old_settings = None

    input_handler = threading.Thread(target=input_thread, daemon=True)
    input_handler.start()

    console.print("\n✨ Starting playback...\n", style="bold magenta")
    time.sleep(1)

    try:
        with Live(layout, console=console, screen=True, refresh_per_second=4) as live:
            play_track(current_index)

            while is_running:
                try:
                    cmd = command_queue.get(timeout=0.25)
                except queue.Empty:
                    cmd = None

                if cmd == "next":
                    check_and_refresh_queue()
                    play_track(current_index + 1)
                elif cmd == "prev":
                    play_track(max(0, current_index - 1))
                elif cmd == "pause":
                    player.pause = not player.pause
                elif cmd == "config":
                    is_running = False
                    player.pause = True
                    live.stop()
                    console.clear()
                    setup_wizard()
                    console.print("\n[yellow]Please restart headless_music to apply new settings.[/yellow]")
                    break
                elif cmd == "quit":
                    break

                try:
                    layout["progress"].update(create_progress_panel())
                    layout["footer"].update(create_controls_panel())
                except Exception as e:
                    logging.warning(f"Error updating UI panel: {e}")

    except KeyboardInterrupt:
        is_running = False
    finally:
        is_running = False
        try:
            if old_settings:
                import termios
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        except Exception:
            logging.warning("Error restoring terminal settings.")

        try:
            player.quit()
        except Exception:
            logging.warning("Error quitting MPV.")

        console.clear()
        console.print("\nheadless_music stopped. goodbye! 👋 \n", style="bold yellow")
        logging.info("headless_music stopped")

if __name__ == "__main__":
    main()