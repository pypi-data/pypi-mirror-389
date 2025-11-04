from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from .web_scraper import WebScraper
import math
from collections import Counter
import threading
import time

class TangoSolver:
    game_url = "https://www.linkedin.com/games/tango/"
    game_icon_dict = {"Moon": 1, "Sun": 2}

    EMPTY = 0

    MOON = 1
    SUN = 2

    EQUAL = 3
    DIFFERENT = 4

    rules_dict = {"Equal": 3, "Cross": 4}

    symbol_map = {0: " ", 1: "X", 2: "O"}  # Empty  # Moon  # Sun

    edge_symbol_map = {0: " ", 3: "=", 4: "x"}

    def __init__(self, driver):
        self.driver = driver
        self.in_iframe = False  # Track if we're working inside an iframe
        cells = self.get_cells(driver)
        self.board, self.left_right_transitions, self.up_down_transitions = (
            self.get_detailed_board(cells)
        )
        self.starting_board = [[i for i in row] for row in self.board]
        print("Empty cells: ", self.empty_cell_count)
        print("Board: ", self.board)
        print("LR transitions: ", self.left_right_transitions)
        print("UP transitions ", self.up_down_transitions)

    def get_cells(self, driver):
        # First check if grid is directly available (when logged in, no iframe)
        driver.switch_to.default_content()
        try:
            print("⏳ Checking for direct grid access (logged in)...")
            grid = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.CLASS_NAME, "lotka-grid"))
            )
            self.in_iframe = False
            print("✅ Grid found directly (logged in, no iframe).")
        except Exception:
            # Grid not found directly, check for iframe (when not logged in)
            print("⏳ Looking for game iframe...")
            try:
                iframe = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "iframe[src*='/games/view/tango/']")
                    )
                )
                driver.switch_to.frame(iframe)
                self.in_iframe = True
                print("✅ Switched into iframe.")
                
                print("⏳ Waiting for launch button...")
                button = (
                    WebDriverWait(driver, 10)
                    .until(EC.element_to_be_clickable((By.ID, "launch-footer-start-button")))
                    .click()
                )
                print("✅ Launch button clicked.")
                
                print("⏳ Waiting for game grid...")
                grid = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "lotka-grid"))
                )
                print("✅ Grid found in iframe.")
            except Exception as e:
                WebScraper.print_error_output_screenshot(
                    driver, e, "Could not find game grid or iframe", "grid_error"
                )

        # Only check for dismiss button when in iframe (when not logged in)
        if self.in_iframe:
            try:
                print("Hitting x button to dismiss popup")
                dismiss_button = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, '[aria-label="Dismiss"]')
                    )
                )
                print("Dismiss button found")
                dismiss_button.click()
                print("Dismiss button clicked")
            except Exception as e:
                # Dismiss button might not exist, just continue
                pass

        self.cells = grid.find_elements(By.CLASS_NAME, "lotka-cell")
        return self.cells

    def get_detailed_board(self, cells):
        self.grid_size = int(math.sqrt(len(cells)))
        board = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        left_right_transitions = [
            [0 for _ in range(self.grid_size - 1)] for _ in range(self.grid_size)
        ]
        up_down_transitions = [
            [0 for _ in range(self.grid_size)] for _ in range(self.grid_size - 1)
        ]
        self.empty_cell_count = 0

        for idx, cell in enumerate(cells):
            row = idx // self.grid_size
            col = idx % self.grid_size

            try:
                svg = cell.find_element(By.TAG_NAME, "svg")
                label = svg.get_attribute("aria-label")

                board[row][col] = TangoSolver.game_icon_dict[label]
            except:
                self.empty_cell_count += 1

            try:
                edges = cell.find_elements(By.CLASS_NAME, "lotka-cell-edge")
                for edge in edges:
                    edge_label = edge.find_element(By.TAG_NAME, "svg").get_attribute(
                        "aria-label"
                    )

                    symbol_id = (
                        TangoSolver.rules_dict[edge_label]
                        if edge_label in TangoSolver.rules_dict
                        else 0
                    )
                    class_attr = edge.get_attribute("class")

                    if "lotka-cell-edge--right" in class_attr:
                        left_right_transitions[row][col] = symbol_id
                    elif "lotka-cell-edge--down" in class_attr:
                        up_down_transitions[row][col] = symbol_id
            except:
                pass  # No edges found — that's okay

        return (board, left_right_transitions, up_down_transitions)

    def solve_game(self, debug=False):
        for i in range(self.empty_cell_count):
            if debug:
                print("-" * 60)
                print("Iteration", i)
                self.print_board()
            self.add_new_icon()

    def add_new_icon(self):
        for row in range(self.grid_size):
            can_update, pos_in_row, value = self.find_cell_to_update(
                self.board[row], self.left_right_transitions[row]
            )
            if can_update:
                self.board[row][pos_in_row] = value
                return

        for col in range(self.grid_size):
            col_icons = [row[col] for row in self.board]
            col_transitions = [row[col] for row in self.up_down_transitions]

            can_update, pos_in_col, value = self.find_cell_to_update(
                col_icons, col_transitions
            )
            if can_update:
                self.board[pos_in_col][col] = value
                return

        print("Could not find anywhere to add an icon. Exiting...")
        time.sleep(1000)

    def find_cell_to_update(self, row, transitions):
        max_count = self.grid_size // 2

        # Rule 1: No more than two same symbols in a row
        for i in range(self.grid_size - 2):
            triple = row[i : i + 3]
            if triple.count(TangoSolver.MOON) == 2 and TangoSolver.EMPTY in triple:
                idx = i + triple.index(TangoSolver.EMPTY)
                return True, idx, TangoSolver.SUN
            elif triple.count(TangoSolver.SUN) == 2 and TangoSolver.EMPTY in triple:
                idx = i + triple.index(TangoSolver.EMPTY)
                return True, idx, TangoSolver.MOON

        # Rule 2: Fill based on transitions
        for i in range(self.grid_size - 1):
            a, b = row[i], row[i + 1]
            t = transitions[i]

            if t == TangoSolver.EQUAL:
                if a != TangoSolver.EMPTY and b == TangoSolver.EMPTY:
                    return True, i + 1, a
                elif b != TangoSolver.EMPTY and a == TangoSolver.EMPTY:
                    return True, i, b
            elif t == TangoSolver.DIFFERENT:
                if a != TangoSolver.EMPTY and b == TangoSolver.EMPTY:
                    icon_to_add = (
                        TangoSolver.SUN if a == TangoSolver.MOON else TangoSolver.MOON
                    )
                    return True, i + 1, icon_to_add
                elif b != TangoSolver.EMPTY and a == TangoSolver.EMPTY:
                    icon_to_add = (
                        TangoSolver.SUN if b == TangoSolver.MOON else TangoSolver.MOON
                    )
                    return True, i, icon_to_add

        # Rule 3: Fill in remaining if one symbol has maxed out
        counter = Counter(row)
        if counter[TangoSolver.MOON] == max_count:
            for i in range(self.grid_size):
                if row[i] == TangoSolver.EMPTY:
                    return True, i, TangoSolver.SUN
        elif counter[TangoSolver.SUN] == max_count:
            for i in range(self.grid_size):
                if row[i] == TangoSolver.EMPTY:
                    return True, i, TangoSolver.MOON

        # Rule 4: If there's a filled cell next to two '=' connected blanks, those blanks must be the opposite
        for i in range(len(row)):
            # Check left side: filled - blank - blank
            if (
                i <= len(row) - 3
                and row[i] in (TangoSolver.MOON, TangoSolver.SUN)
                and row[i + 1] == TangoSolver.EMPTY
                and row[i + 2] == TangoSolver.EMPTY
                and transitions[i + 1] == TangoSolver.EQUAL
            ):

                icon_to_add = (
                    TangoSolver.MOON if row[i] == TangoSolver.SUN else TangoSolver.SUN
                )
                return True, i + 1, icon_to_add

            # Check right side: blank - blank - filled
            if (
                i <= len(row) - 3
                and row[i] == TangoSolver.EMPTY
                and row[i + 1] == TangoSolver.EMPTY
                and row[i + 2] in (TangoSolver.SUN, TangoSolver.MOON)
                and transitions[i] == TangoSolver.EQUAL
            ):

                icon_to_add = (
                    TangoSolver.MOON
                    if row[i + 2] == TangoSolver.SUN
                    else TangoSolver.SUN
                )
                return True, i, icon_to_add

        # Rule 5: Minority outnumbered symbol at the edge must be pushed to the farthest cell
        if (
            row[:3].count(TangoSolver.EMPTY) == 0
            and row[3:6].count(TangoSolver.EMPTY) == 3
        ):
            a, b, c = row[0], row[1], row[2]
            if a == b and c != a:
                icon_to_add = c
                return True, len(row) - 1, icon_to_add

        if (
            row[3:].count(TangoSolver.EMPTY) == 0
            and row[:3].count(TangoSolver.EMPTY) == 3
        ):
            a, b, c = row[-3], row[-2], row[-1]
            if b == c and a != c:
                icon_to_add = a
                return True, 0, icon_to_add

        # Rule 6: Three symbols filled in on the edge and two x between the remaining three
        # Ex. XOX_x_x_ OR OXO_x_x_
        if (row[:3].count(TangoSolver.EMPTY) == 0
            and row[3:].count(TangoSolver.EMPTY == 3)
            and transitions[3] == TangoSolver.DIFFERENT
            and transitions[4] == TangoSolver.DIFFERENT):
            count_suns = row[:3].count(TangoSolver.SUN)
            count_moons = row[:3].count(TangoSolver.MOON)

            if (count_suns < count_moons):
                return True, 3, TangoSolver.SUN
            return True, 3, TangoSolver.MOON
        
        if (row[:3].count(TangoSolver.EMPTY) == 3
            and row[3:].count(TangoSolver.EMPTY == 0)
            and transitions[0] == TangoSolver.DIFFERENT
            and transitions[1] == TangoSolver.DIFFERENT):

            count_suns = row[3:].count(TangoSolver.SUN)
            count_moons = row[3:].count(TangoSolver.MOON)

            if (count_suns < count_moons):
                return True, 2, TangoSolver.SUN
            return True, 2, TangoSolver.MOON

        return False, 0, 0

    def add_solved_board_to_site(self, timeout=0):
        if timeout:
            time.sleep(timeout)
        
        # Ensure we're in the correct context (iframe or default)
        if self.in_iframe:
            try:
                # Switch back to iframe if we're using one
                iframe = self.driver.find_element(By.CSS_SELECTOR, "iframe[src*='/games/view/tango/']")
                self.driver.switch_to.frame(iframe)
            except:
                pass  # If iframe is gone, stay in default content
        else:
            self.driver.switch_to.default_content()
        
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                if self.starting_board[row][col] != TangoSolver.EMPTY:
                    continue

                cell_value = self.board[row][col]
                cell_object = self.cells[col + row * self.grid_size]

                try:
                    if cell_value == TangoSolver.SUN:
                        cell_object.click()
                    elif cell_value == TangoSolver.MOON:
                        cell_object.click()
                        cell_object.click()
                except Exception as e:
                    print(f"⚠️ Error clicking cell ({row}, {col}): {e}")

        return

        def click_cell(cell_object, clicks, row, col):
            try:
                for _ in range(clicks):
                    cell_object.click()
            except Exception as e:
                print(f"⚠️ Error clicking cell ({row}, {col}): {e}")

        threads = []

        for row in range(self.grid_size):
            for col in range(self.grid_size):
                if self.starting_board[row][col] != TangoSolver.EMPTY:
                    continue

                cell_value = self.board[row][col]
                cell_object = self.cells[col + row * self.grid_size]

                if cell_value == TangoSolver.MOON:
                    t = threading.Thread(
                        target=click_cell, args=(cell_object, 1, row, col)
                    )
                    threads.append(t)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all to complete
        for thread in threads:
            thread.join()

    def print_board(self, board=None):
        if not board:
            board = self.board
        grid_size = len(board)

        for row in range(grid_size):
            # Build the row of symbols
            row_str = ""
            for col in range(grid_size):
                cell_value = board[row][col]
                row_str += TangoSolver.symbol_map.get(cell_value, " ")

                # Add horizontal edge (to the right)
                if col < grid_size - 1:
                    edge = self.left_right_transitions[row][col]
                    row_str += TangoSolver.edge_symbol_map.get(edge, "|")
            print(row_str)

            # Build the row of vertical edges (below each cell)
            if row < grid_size - 1:
                edge_str = ""
                for col in range(grid_size):
                    edge = self.up_down_transitions[row][col]
                    edge_str += TangoSolver.edge_symbol_map.get(edge, "-")

                    # Space between verticals
                    if col < grid_size - 1:
                        edge_str += " "
                print(edge_str)

    def print_solved_game(self):
        print("-" * 60)
        print("GAME SOLVED")
        print("-" * 60)
        print()
        self.print_board()
