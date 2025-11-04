## Navid LinkedIn Puzzle Solver

Automate solving LinkedIn mini games (Queens, Tango, Zip) using Selenium with a simple, cross‑platform CLI. Solve most puzzles in ~3 seconds and climb the leaderboard 😉

## Legal/Usage Notice
This project was created by me as a personal challenge.
It is not affiliated with LinkedIn.
Always use it responsibly and strictly in accordance with LinkedIn’s Terms of Service.


### Features
- **Games**: Queens, Tango, Zip
- **CLI**: Number-based menu (no special keys required)
- **Auto browser setup**: Uses Selenium + webdriver-manager; reuses a local Chrome profile to stay logged in
- **Human-like timing**: Adds small delays to avoid suspiciously instant solves
  - Tip: Even with timing, typical end-to-end runs are ~3s on modern machines

## Quick Start

### Install from PyPI
```bash
pip install navid-linkedin-puzzle-solver
```

### Run the CLI
```bash
navid-linkedin-puzzle-solver
```

1) Select "Login" to open Chrome and sign in to LinkedIn (once). Close the tab or return to the terminal when done.
2) Select a game (Queens, Tango, Zip). The solver will read the current board, solve it, and submit the solution automatically.

### Requirements
- Google Chrome installed
- Internet access to `linkedin.com`
- Python 3.9+

## How It Works
- The CLI launches Chrome via Selenium.
- It navigates to the chosen game URL, detects the board, computes a solution, and inputs the moves.
- A minimal delay is applied for realism (particularly for Queens).

## Command Reference

### Start the solver
```bash
navid-linkedin-puzzle-solver
```

### Menu options
- **Login**: Opens `https://www.linkedin.com` in a real Chrome window so you can sign in.
- **Queens / Tango / Zip**: Solves the currently displayed daily puzzle instance.
- **Exit**: Quits the program.

## Troubleshooting

- **Chrome not opening / driver errors**
  - Ensure Google Chrome is installed and up to date.
  - The package uses Selenium Manager or `webdriver-manager` to fetch a compatible driver automatically.

- **Page opens but board not detected**
  - Wait a moment; React content may still be rendering.
  - Make sure you are actually on the game page (e.g., Queens).
  - If you are not logged in, choose "Login" first.

- **Clicks not applied / iframe issues**
  - Some game pages load inside an iframe when logged out. The solver handles both cases, but if you see inconsistent behavior, sign in first via "Login".

- **Slow or blocked solving**
  - Network conditions and LinkedIn UI changes can affect scraping. Try again later or after refreshing the page.

## Development

### Run from source
```bash
python -m pip install --upgrade build
python -m pip install -e .
navid-linkedin-puzzle-solver
```

### Project layout
- `linkedin_games_solver/cli.py`: CLI entry point and menu
- `linkedin_games_solver/solver.py`: Backward-compatible wrapper
- `linkedin_games_solver/web_scraper.py`: Chrome driver initialization and utilities
- `linkedin_games_solver/*_solver.py`: Individual game solvers (Queens, Tango, Zip)


## License
MIT

