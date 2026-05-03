# ClipVault - Windows Clipboard Manager

A lightweight, privacy-first clipboard history manager for Windows. Free forever for core features.

## Features

- **Clipboard History**: Automatically saves text you copy (last 50 items free, unlimited with Pro)
- **Instant Search**: Type to filter your clipboard history
- **Pin & Favorite**: Keep important clips at the top
- **System Tray**: Runs quietly in the background
- **Privacy-First**: All data stored locally in SQLite. No cloud, no telemetry.

## Installation

```bash
pip install -r requirements.txt
python main.py
```

## Requirements

- Python 3.8+
- Windows 10/11
- pyperclip, pywin32

## Pricing

| Feature | Free | Pro (¥29 lifetime) |
|---------|------|---------------------|
| Clipboard history | 50 items | Unlimited |
| Search | Yes | Yes |
| Pin items | Yes | Yes |
| Export history | No | Yes |
| Custom categories | No | Yes |

## Tech Stack

Python + tkinter + SQLite + pywin32. Zero external services.

## License

MIT
