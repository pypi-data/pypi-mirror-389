from typing import List
from .web_scraper import WebScraper
from .tango_solver import TangoSolver
from .queens_solver import QueensSolver
from .zip_solver import ZipSolver
import time
import random


GAMES = {
    "Tango": TangoSolver,
    "Queens": QueensSolver,
    "Zip": ZipSolver,
}


def _prompt_menu(options: List[str]) -> str:
    print("\n=== LinkedIn Games Solver ===")
    for idx, opt in enumerate(options, start=1):
        print(f"  {idx}. {opt}")
    while True:
        choice = input("Select an option by number: ").strip()
        if choice.isdigit():
            i = int(choice) - 1
            if 0 <= i < len(options):
                return options[i]
        print("Invalid choice. Try again.")


def run_once(selection: str) -> None:
    if selection == "Login":
        web = WebScraper("https://www.linkedin.com")
        try:
            input("\nBrowser opened for login. Log in, then press Enter to return to menu...")
        finally:
            web.quit_driver()
        return

    game_cls = GAMES.get(selection)
    if not game_cls:
        print("Invalid game selected. Exiting...")
        raise SystemExit(1)

    start_time = time.time()
    game_url = game_cls.game_url
    web = WebScraper(game_url)
    try:
        driver = web.get_driver()
        solver = game_cls(driver)

        found_board_time = time.time()
        print(f"Took {found_board_time - start_time} to find board data")

        solver.solve_game()

        solved_game_time = time.time()
        solve_duration = solved_game_time - found_board_time
        print(f"Took {solve_duration} to solve game")

        solver.print_solved_game()

        delay = 0
        if selection == "Queens" and solve_duration < 2:
            min_delay = 2 - solve_duration
            max_delay = 5 - solve_duration
            delay = random.uniform(min_delay, max_delay)
            print(f"Queens solved too quickly ({solve_duration:.2f}s). Adding {delay:.2f}s delay")
            time.sleep(delay)
            timeout = 0
        else:
            total_time = time.time() - found_board_time
            if total_time < 1:
                timeout = 0.9 - total_time
                print(f"Waiting {timeout} seconds before adding solution")
            else:
                timeout = 0

        solver.add_solved_board_to_site(timeout=timeout)

        added_solution_time = time.time()
        print(f"Took {added_solution_time - solved_game_time} to add solution to site")
    finally:
        web.quit_driver()


def main() -> None:
    EXIT = "Exit"
    LOGIN = "Login"
    options = [LOGIN] + list(GAMES.keys()) + [EXIT]
    while True:
        selection = _prompt_menu(options)
        if selection == EXIT:
            print("Thanks for playing!")
            break
        run_once(selection)


if __name__ == "__main__":
    main()


