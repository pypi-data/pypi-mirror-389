from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import math
from collections import defaultdict
from enum import Enum
import time

class CellContents(Enum):
    EMPTY = 0
    QUEEN = 1
    X = 2

class QueenCell:
    def __init__(self, color: int, contents: CellContents = CellContents.EMPTY):
        self.color = color
        self.contents = contents
        self.starting_queen = False

    def set_starting_queen(self):
        self.starting_queen = True


class QueensSolver:
    game_url = "https://www.linkedin.com/games/queens/"

    def __init__(self, driver):
        self.driver = driver
        self.in_iframe = False  # Track if we're working inside an iframe
        self.cells, self.board = self.get_cells_and_regions()
        self.grid_size = len(self.board)

        self.x = set()
        self.print_board()
        self.regions = defaultdict(set)
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                if self.board[row][col].contents == CellContents.QUEEN:
                    self.mark_x_squares(row, col)
                    self.board[row][col].set_starting_queen()
                region_id = self.board[row][col].color
                self.regions[region_id].add((row, col))

    def get_cells_and_regions(self):
        print("⏳ Setting up board...")
        
        # First check if board is directly available (when logged in, no iframe)
        self.driver.switch_to.default_content()
        try:
            print("⏳ Checking for direct board access (logged in)...")
            WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.CLASS_NAME, "queens-board"))
            )
            self.in_iframe = False
            print("✅ Board found directly (logged in, no iframe).")
        except Exception:
            # Board not found directly, check for iframe (when not logged in)
            print("⏳ Looking for game iframe...")
            try:
                iframe = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "iframe"))
                )
                self.driver.switch_to.frame(iframe)
                self.in_iframe = True
                print("✅ Switched into iframe.")
                
                WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "launch-footer-start-button"))
                ).click()
                print("✅ Launch button clicked.")
                
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "queens-board"))
                )
                print("✅ Board found in iframe.")
            except Exception as e:
                raise Exception("Could not find queens-board or iframe")

        # Only check for dismiss button when in iframe (when not logged in)
        if self.in_iframe:
            try:
                dismiss = self.driver.find_element(
                    By.CSS_SELECTOR, '[aria-label="Dismiss"]'
                )
                dismiss.click()
            except:
                pass

        cells = self.driver.find_elements(By.CLASS_NAME, "queens-cell-with-border")

        grid_size = int(math.sqrt(len(cells)))
        region_map = [[0 for _ in range(grid_size)] for _ in range(grid_size)]

        for idx, cell in enumerate(cells):
            row = idx // grid_size
            col = idx % grid_size

            cell_class_names = cell.get_attribute("class").split()
            color_class = [
                class_name
                for class_name in cell_class_names
                if "cell-color-" in class_name
            ][0]
            color_number = int(color_class.replace("cell-color-", ""))

            new_queen_cell = None
            try:
                span = cell.find_element(By.TAG_NAME, "span")
                span_class = span.get_attribute("class")

                if "queen" in span_class:
                    new_queen_cell = QueenCell(color_number, CellContents.QUEEN)
                elif "cross" in span_class:
                    new_queen_cell = QueenCell(color_number, CellContents.X)
                else:
                    raise Exception

            except NoSuchElementException:
                new_queen_cell = QueenCell(color_number, CellContents.EMPTY)

            region_map[row][col] = new_queen_cell

        return cells, region_map

    def is_valid_placement(self, row, col):
        return not ((row, col) in self.x)

        # Must not be adjacent to another queen
        for r in range(max(0, row - 1), min(self.grid_size, row + 2)):
            for c in range(max(0, col - 1), min(self.grid_size, col + 2)):
                if self.board[r][c].contents == CellContents.QUEEN:
                    return False

        # Same row or column
        for r in range(len(self.board)):
            if self.board[r][col].contents == CellContents.QUEEN:
                return False

        for c in range(len(self.board)):
            if self.board[row][c].contents == CellContents.QUEEN:
                return False

        return True

    def mark_x_squares(self, row, col):
        x = set()
        cell_color = self.board[row][col].color
        for r in range(max(0, row - 1), min(self.grid_size, row + 2)):
            for c in range(max(0, col - 1), min(self.grid_size, col + 2)):
                if self.board[r][c].contents != CellContents.QUEEN:
                    x.add((r, c))

        # Same row or column
        for r in range(len(self.board)):
            for c in range(len(self.board)):
                if self.board[r][c].contents != CellContents.QUEEN:
                    if self.board[r][c].color == cell_color or r == row or c == col:
                        x.add((r, c))

        self.x = self.x.union(x)
        return x

    def solve_game(self):
        self.solve_region(0)

    def solve_region(self, color_index):
        if color_index == len(self.regions):
            return True  # All regions filled

        if self.has_queen(color_index):
            return self.solve_region(color_index + 1)

        for row, col in self.regions[color_index]:
            if self.is_valid_placement(row, col):
                self.board[row][col].contents = CellContents.QUEEN
                old_x = self.x
                self.mark_x_squares(row, col)
                if self.solve_region(color_index + 1):
                    return True
                self.board[row][col].contents = CellContents.EMPTY
                self.x = old_x

        return False

    def has_queen(self, color_index):
        for row, col in self.regions[color_index]:
            if self.board[row][col].contents == CellContents.QUEEN:
                return True

        return False

    def add_solved_board_to_site(self, timeout=0):
        if timeout:
            time.sleep(timeout)
        
        # Ensure we're in the correct context (iframe or default)
        if self.in_iframe:
            try:
                # Switch back to iframe if we're using one
                iframe = self.driver.find_element(By.CSS_SELECTOR, "iframe")
                self.driver.switch_to.frame(iframe)
            except:
                pass  # If iframe is gone, stay in default content
        else:
            self.driver.switch_to.default_content()
        
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                obj = self.board[row][col]
                if obj.contents == CellContents.QUEEN and not obj.starting_queen:
                    cell = self.cells[col + row * self.grid_size]
                    try:
                        cell.click()
                        cell.click()
                    except Exception as e:
                        print(f"Error clicking ({row}, {col}): {e}")

    def print_board(self):
        print("Queen placements:")
        for row in range(len(self.board)):
            row_str = ""
            for col in range(len(self.board)):
                cellContents = self.board[row][col].contents
                if (row, col) in self.x:
                    row_str += "x "
                elif cellContents == CellContents.QUEEN:
                    row_str += "Q "
                elif cellContents == CellContents.EMPTY:
                    row_str += ". "

            print(row_str)

        print("\n\n")
        print("Color map:")
        for row in self.board:
            print(" ".join(str(val.color) for val in row))

    def print_solved_game(self):
        print("-" * 60)
        print("GAME SOLVED")
        print("-" * 60)
        print()
        self.print_board()
