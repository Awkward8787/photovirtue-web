<p align="center">
  <img src="assets/banner.png" alt="PhotoVirtue" width="100%">
</p>

# PhotoVirtue

**Telegram bot and browser photo editor with Bitcoin one-time payments for 1-year access.**

[![License: All Rights Reserved](https://img.shields.io/badge/license-all%20rights%20reserved-lightgrey)](#license)
![Python](https://img.shields.io/badge/Python-3776AB&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688&logo=fastapi&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-26A5E4&logo=telegram&logoColor=white)

Original IP by Anthony Jones. Python stack: Telegram bot (`telegram_bot.py`), FastAPI web editor (`web_editor.py`), and a Tkinter desktop editor (`photo_virtue.py`).


## How it works

```mermaid
flowchart LR
  U[User] --> TG[Telegram bot]
  TG --> BTC[Bitcoin one-time payment]
  BTC --> Access[1-year access]
  Access --> Web[FastAPI web editor]
  Web --> Local[Local PIL filters]
  Web --> AC[ArtCraft / providers]
```

Python stack: `telegram_bot.py` for BTC-provisioned access, `web_editor.py` FastAPI editor with local PIL and optional ArtCraft providers.

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
