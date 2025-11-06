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
from pathlib import Path
from spotipy.oauth2 import SpotifyClientCredentials
from mpv import MPV
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.progress_bar import ProgressBar
from rich.prompt import Prompt, Confirm

console = Console()

# Configuration management
CONFIG_FILE = Path.home() / ".headless_music_config.json"

def load_config():
    """Load configuration from file or return defaults."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load config: {e}[/yellow]")
    return {}

def save_config(config):
    """Save configuration to file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        console.print(f"[red]Error saving config: {e}[/red]")
        return False

def setup_wizard():
    """Interactive setup wizard for first-time users."""
    console.clear()
    console.print("=" * 60, style="cyan")
    console.print("🎵 Welcome to Headless Music Setup!", style="bold cyan", justify="center")
    console.print("=" * 60, style="cyan")
    console.print()

    config = load_config()

    # Spotify credentials
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

    # Playlist source
    console.print("🎧 [bold]Playlist Source[/bold]")
    console.print()

    source_choice = Prompt.ask(
        "   Choose your playlist source",
        choices=["spotify", "youtube"],
        default=config.get('PLAYLIST_SOURCE', 'youtube')
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

    # Save configuration
    new_config = {
        'SPOTIFY_CLIENT_ID': spotify_id,
        'SPOTIFY_CLIENT_SECRET': spotify_secret,
        'PLAYLIST_SOURCE': source_choice,
        'PLAYLIST_URL': playlist_url
    }

    if save_config(new_config):
        console.print("✓ Configuration saved!", style="bold green")
        console.print(f"   Config location: {CONFIG_FILE}", style="dim")
    else:
        console.print("⚠️  Could not save configuration. You'll need to re-enter it next time.", style="yellow")

    console.print()
    if Confirm.ask("Start Headless Music now?", default=True):
        return new_config
    else:
        console.print("👋 Run this script again when you're ready!", style="cyan")
        sys.exit(0)

def validate_config(config):
    """Validate that required configuration exists."""
    required = ['SPOTIFY_CLIENT_ID', 'SPOTIFY_CLIENT_SECRET', 'PLAYLIST_SOURCE', 'PLAYLIST_URL']
    missing = [key for key in required if not config.get(key)]

    if missing:
        console.print(f"[red]Missing configuration: {', '.join(missing)}[/red]")
        return False
    return True

# Global variables
command_queue = queue.Queue()
master_playlist = []
current_index = 0
player = MPV(ytdl=True, video=False, keep_open=False)
layout = Layout()
is_running = True
sp_client = None
config = {}

def format_time(seconds):
    if seconds is None or seconds < 0:
        return "--:--"
    m, s = divmod(int(seconds), 60)
    return f"{m:02}:{s:02}"

def get_youtube_playlist_titles(url):
    ydl_opts = {'quiet': True, 'extract_flat': True, 'no_warnings': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        return [(e['title'], e.get('uploader', 'Unknown'), "YouTube") for e in info['entries'] if e]
    except Exception as e:
        console.print(f"[red]Error fetching YouTube playlist: {e}[/red]")
        return []

def get_spotify_playlist_tracks(sp, playlist_url):
    """Fetch tracks from a Spotify playlist."""
    try:
        # Extract playlist ID from URL or URI
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
                    results.append((
                        track['name'],
                        track['artists'][0]['name'],
                        "Spotify"
                    ))

            if not response['next']:
                break
            offset += 100

        return results
    except Exception as e:
        console.print(f"[red]Error fetching Spotify playlist: {e}[/red]")
        return []

def spotify_setup():
    """Initializes and returns a Spotipy client."""
    global sp_client, config
    if sp_client is None:
        sp_client = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            client_id=config['SPOTIFY_CLIENT_ID'],
            client_secret=config['SPOTIFY_CLIENT_SECRET']
        ))
    return sp_client

def get_spotify_tracks_by_search(sp, titles_artists, limit=20):
    results = []
    seen_ids = set()

    sample_size = min(len(titles_artists), 10)
    sampled = random.sample(titles_artists, sample_size)

    for title, artist, _ in sampled:
        try:
            artist_results = sp.search(q=f"artist:{artist}", type="artist", limit=1)
            if artist_results['artists']['items']:
                artist_id = artist_results['artists']['items'][0]['id']
                top_tracks = sp.artist_top_tracks(artist_id)
                for track in top_tracks['tracks'][:3]:
                    track_id = track['id']
                    if track_id not in seen_ids:
                        results.append((track['name'], track['artists'][0]['name'], track_id))
                        seen_ids.add(track_id)
                        if len(results) >= limit:
                            return results
        except Exception:
            continue

        try:
            track_results = sp.search(q=f"{title} {artist}", type="track", limit=3)
            for track in track_results['tracks']['items']:
                track_id = track['id']
                if track_id not in seen_ids:
                    results.append((track['name'], track['artists'][0]['name'], track_id))
                    seen_ids.add(track_id)
                    if len(results) >= limit:
                        return results
        except Exception:
            continue

    return results

def spotify_recommendations_with_fallback(sp, titles_artists, limit=20):
    results = []
    seen_ids = set()

    sample_size = min(len(titles_artists), 5)
    sampled = random.sample(titles_artists, sample_size)

    for title, artist, _ in sampled:
        try:
            search_results = sp.search(q=f"{title} {artist}", type="track", limit=1)
            if search_results['tracks']['items']:
                seed_id = search_results['tracks']['items'][0]['id']
                try:
                    recs = sp.recommendations(seed_tracks=[seed_id], limit=5)
                    for track in recs['tracks']:
                        track_id = track['id']
                        if track_id not in seen_ids:
                            results.append((track['name'], track['artists'][0]['name'], track_id))
                            seen_ids.add(track_id)
                except Exception:
                    pass
        except Exception:
            continue

    if len(results) < limit:
        for title, artist, _ in sampled:
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
                                results.append((track['name'], track['artists'][0]['name'], track_id))
                                seen_ids.add(track_id)
                                if len(results) >= limit:
                                    return results
            except Exception:
                continue

    if len(results) < limit // 2:
        search_results = get_spotify_tracks_by_search(sp, titles_artists, limit - len(results))
        for track in search_results:
            if track[2] not in seen_ids:
                results.append(track)
                seen_ids.add(track[2])

    return results

def fetch_more_youtube_tracks():
    if not master_playlist:
        return []

    results = []
    sample = random.sample(master_playlist, min(3, len(master_playlist)))
    ydl_opts = {'quiet': True, 'extract_flat': True, 'no_warnings': True}

    for title, artist, _ in sample:
        try:
            search_query = f"{artist} {title} audio"
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                search_results = ydl.extract_info(f"ytsearch5:{search_query}", download=False)
                if search_results and 'entries' in search_results:
                    for entry in search_results['entries']:
                        if entry:
                            results.append((
                                entry.get('title', 'Unknown'),
                                entry.get('uploader', 'Unknown'),
                                "YouTube"
                            ))
        except Exception:
            continue

    return results

# --- TUI Panels ---

def create_now_playing_panel(title, artist, source):
    source_color = "red" if source == "YouTube" else "green"
    display_title = title[:60] + "..." if len(title) > 60 else title
    display_artist = artist[:40] + "..." if len(artist) > 40 else artist

    display_text = Text.from_markup(f"""
🎵 Now Playing:
   » [bold]{display_title}[/bold]
     [dim]{display_artist}[/dim]

🔁 Source: [{source_color}]{source}[/{source_color}]
""")
    return Panel(display_text, title="🎛️ Headless Music", border_style="green", padding=(1, 2))

def create_next_up_panel():
    text = ""
    end_idx = min(current_index + 4, len(master_playlist))
    for i, (title, artist, source) in enumerate(master_playlist[current_index + 1 : end_idx]):
        display_title = title[:50] + "..." if len(title) > 50 else title
        text += f"  {i+1}. {display_title} – {artist[:30]}\n"
    if not text:
        text = "  [dim]Fetching more tracks...[/dim]"
    return Panel(Text.from_markup(text), title="▶ Next Up", border_style="dim")

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
    except Exception:
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
    layout.split_column(
        Layout(name="now_playing", size=8),
        Layout(name="progress", size=1),
        Layout(name="next_up", size=8),
        Layout(name="footer", size=3)
    )
    return layout

# --- Playback & Input Logic ---

def play_track(index):
    global current_index
    if index < 0 or index >= len(master_playlist):
        return

    current_index = index
    (title, artist, source) = master_playlist[current_index]

    layout["now_playing"].update(create_now_playing_panel(title, artist, source))
    layout["next_up"].update(create_next_up_panel())

    try:
        query = f"{title} {artist} audio"
        player.play(f"ytdl://ytsearch1:{query}")
        player.pause = False
    except Exception as e:
        console.print(f"[red]Error playing track: {e}[/red]")
        command_queue.put("next")

def check_and_refresh_queue():
    global master_playlist

    if len(master_playlist) - current_index < 5:
        seed_tracks = master_playlist[max(0, current_index - 10) : current_index + 1]
        sp = spotify_setup()
        new_tracks = spotify_recommendations_with_fallback(sp, seed_tracks, limit=15)

        if len(new_tracks) < 5:
            yt_tracks = fetch_more_youtube_tracks()
            new_tracks.extend(yt_tracks[:10])

        if new_tracks:
            master_playlist.extend(new_tracks)
            layout["next_up"].update(create_next_up_panel())
        else:
            master_playlist.extend(master_playlist[:20])

@player.property_observer('idle-active')
def handle_song_end(_name, value):
    if value and is_running:
        command_queue.put("next")

def input_thread():
    global is_running
    while is_running:
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

def main():
    global master_playlist, current_index, layout, is_running, config

    # Load or setup configuration
    config = load_config()

    if not validate_config(config):
        config = setup_wizard()

    console.print("🎵 Initializing Headless Music...", style="bold cyan")
    console.print(f"📡 Fetching {config['PLAYLIST_SOURCE'].title()} playlist...", style="bold green")

    # Fetch initial playlist based on source
    if config['PLAYLIST_SOURCE'] == 'spotify':
        sp = spotify_setup()
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

    sp = spotify_setup()
    additional_tracks = spotify_recommendations_with_fallback(sp, playlist_tracks, limit=30)

    if additional_tracks:
        console.print(f"✓ Added {len(additional_tracks)} additional tracks", style="green")
    else:
        console.print("[yellow]⚠️  Could not fetch additional tracks, using playlist only[/yellow]")

    master_playlist = playlist_tracks + additional_tracks
    current_index = 0
    layout = create_layout()

    try:
        import tty
        old_settings = tty.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())
    except:
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
                    console.print("\n[yellow]Please restart Headless Music to apply new settings.[/yellow]")
                    break
                elif cmd == "quit":
                    break

                try:
                    layout["progress"].update(create_progress_panel())
                    layout["footer"].update(create_controls_panel())
                except Exception:
                    pass

    except KeyboardInterrupt:
        is_running = False
    finally:
        is_running = False
        try:
            if old_settings:
                import termios
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        except:
            pass

        try:
            player.quit()
        except:
            pass

        console.clear()
        console.print("\n👋 Headless Music stopped. Goodbye!\n", style="bold yellow")

if __name__ == "__main__":
    main()