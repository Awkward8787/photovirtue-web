<p align="center">
  <img src="docs/banner.png" alt="PhotoVirtue" width="100%">
</p>

# PhotoVirtue

**Telegram bot and browser photo editor with Bitcoin one-time payments for 1-year access.**

[![License: All Rights Reserved](https://img.shields.io/badge/license-all%20rights%20reserved-lightgrey)](#license)
![Python](https://img.shields.io/badge/Python-3776AB&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688&logo=fastapi&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-26A5E4&logo=telegram&logoColor=white)

Original IP by Anthony Jones. Python stack: Telegram bot (`telegram_bot.py`), FastAPI web editor (`web_editor.py`), and a Tkinter desktop editor (`photo_virtue.py`).

## Features

- Telegram bot entry for paid access
- Browser photo editor (FastAPI + Pillow)
- Desktop Tkinter editor with layers/filters concepts
- Bitcoin one-time payment model described in project docs ($19/year access)

## Tech stack

- Python 3
- python-telegram-bot / FastAPI / uvicorn
- Pillow
- Tkinter (desktop editor)

## How to run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

See `AGENTS.md` for development rules. Bot and editor entrypoints are `telegram_bot.py` and `web_editor.py`.

## Status

Public. Early codebase. Payment and deploy wiring are not finished in-repo.

## License

All rights reserved. Original IP by Anthony Jones.

## Download

Source archives are published on the [Releases page](https://github.com/Awkward8787/photovirtue-web/releases); the latest release carries `photovirtue-web-v0.1.0.zip`.

### Install & run
```bash
unzip photovirtue-web-v0.1.0.zip
cd photovirtue-web
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python telegram_bot.py   # Telegram bot (long polling)
python web_editor.py     # browser photo editor (uvicorn on http://localhost:8000)
```
See `AGENTS.md` for development rules.
