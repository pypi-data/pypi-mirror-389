import os

def setup_environment():
    print("📦 Setting up environment...\n")
    os.system("pip install -U yt-dlp spotdl")
    os.makedirs("Music", exist_ok=True)
    os.makedirs("Videos", exist_ok=True)
    print("✅ Environment setup complete!\n")

def auto_update():
    print("🔄 Checking & updating yt-dlp and spotdl...\n")
    os.system("pip install -U yt-dlp spotdl >nul 2>&1")
    print("✅ Update complete.\n")

def download_spotify():
    url = input("🎵 Enter Spotify song or playlist URL: ").strip()
    if url:
        print("⬇️ Downloading to Music folder...\n")
        os.system(f'spotdl "{url}" --output "Music/%(title)s.%(ext)s"')
        print("✅ Spotify download finished.\n")
    else:
        print("❌ No URL entered.\n")

def download_youtube():
    url = input("🎬 Enter YouTube video or playlist URL: ").strip()
    if url:
        print("⬇️ Downloading to Videos folder...\n")
        os.system(f'yt-dlp -f "bestvideo+bestaudio/best" -o "Videos/%(title)s.%(ext)s" "{url}"')
        print("✅ YouTube download finished.\n")
    else:
        print("❌ No URL entered.\n")

def main():
    print("🚀 Initializing Anshul Downloader...")
    auto_update()
    os.makedirs("Music", exist_ok=True)
    os.makedirs("Videos", exist_ok=True)

    while True:
        print("------------------------------------")
        print("🎧 Anshul Downloader (Auto Setup + Update)")
        print("------------------------------------")
        print("1. Download from Spotify (Music)")
        print("2. Download from YouTube (Video)")
        print("3. Setup / Repair Environment")
        print("4. Exit")
        print("------------------------------------")

        choice = input("Select option (1-4): ").strip()
        print("")

        if choice == "1":
            download_spotify()
        elif choice == "2":
            download_youtube()
        elif choice == "3":
            setup_environment()
        elif choice == "4":
            print("👋 Exiting... Created by Anshul Dubey ❤️")
            break
        else:
            print("❌ Invalid choice, please try again.\n")

if __name__ == "__main__":
    main()