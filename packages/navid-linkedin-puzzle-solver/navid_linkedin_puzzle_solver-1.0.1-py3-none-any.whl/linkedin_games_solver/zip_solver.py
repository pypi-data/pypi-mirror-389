from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
import math
from collections import deque
import time

DOWN = 1
RIGHT = 2
LEFT = 3
UP = 4


class ZipSolver:
    game_url = "https://www.linkedin.com/games/zip/"

    def __init__(self, driver):
        self.driver = driver
        self.in_iframe = False  # Track if we're working inside an iframe
        self.board, self.walls = self.get_board_and_walls()
        self.print_board()

    def get_board_and_walls(self):
        print("⏳ Setting up board...")
        
        # When logged in, there's no iframe - board is directly accessible
        self.driver.switch_to.default_content()
        self.in_iframe = False
        
        # Wait for page to be ready and game to load
        print("⏳ Waiting for page to load...")
        WebDriverWait(self.driver, 30).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
        time.sleep(2)  # Give extra time for React/JS to render
        
        # Find game cells using data-testid (logged in, no iframe)
        print("⏳ Looking for game cells...")
        cells = WebDriverWait(self.driver, 30).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-testid*='cell']"))
        )
        print(f"✅ Found {len(cells)} cells")

        # Filter cells - try to get cells by data-testid pattern (cell-0, cell-1, etc.)
        grid_size_guess = int(math.sqrt(len(cells)))
        expected_cell_count = grid_size_guess ** 2
        
        filtered_cells = []
        for i in range(expected_cell_count):
            try:
                cell = self.driver.find_element(By.CSS_SELECTOR, f"[data-testid='cell-{i}']")
                filtered_cells.append(cell)
            except:
                break
        
        if len(filtered_cells) == expected_cell_count:
            cells = filtered_cells
        else:
            perfect_square = int(math.sqrt(len(cells))) ** 2
            if perfect_square != len(cells):
                print(f"⚠️ Using first {perfect_square} of {len(cells)} cells.")
                cells = cells[:perfect_square]
        
        grid_size = int(math.sqrt(len(cells)))
        print(f"📊 Grid size: {grid_size}x{grid_size} ({len(cells)} cells)")
        
        board = [[0 for _ in range(grid_size)] for _ in range(grid_size)]
        walls = set()

        # Extract cell values
        for idx, cell in enumerate(cells):
            row = idx // grid_size
            col = idx % grid_size
            cell_value = self.get_cell_value_if_int(cell)
            if cell_value:
                board[row][col] = cell_value

        # Detect walls by checking inner divs' ::after pseudo-elements
        print("\n🔍 Detecting walls from ::after pseudo-elements...")
        
        # Helper function to parse border widths
        def parse_border(border_str):
            if isinstance(border_str, str) and 'px' in border_str:
                try:
                    return float(border_str.replace('px', '').strip())
                except:
                    return 0
            return 0
        
        # JavaScript to get ::after pseudo-element styles
        after_style_script = """
        var elem = arguments[0];
        var styles = window.getComputedStyle(elem, '::after');
        return {
            borderTopWidth: styles.borderTopWidth,
            borderRightWidth: styles.borderRightWidth,
            borderBottomWidth: styles.borderBottomWidth,
            borderLeftWidth: styles.borderLeftWidth
        };
        """
        
        # Check each cell's inner divs for walls
        for idx, cell in enumerate(cells):
            row = idx // grid_size
            col = idx % grid_size
            
            # Find all inner divs (some cells may have multiple inner divs)
            inner_divs = cell.find_elements(By.CSS_SELECTOR, "div")
            
            for inner_div in inner_divs:
                try:
                    # Get ::after pseudo-element border widths
                    after_info = self.driver.execute_script(after_style_script, inner_div)
                    
                    border_right = parse_border(after_info.get('borderRightWidth', '0px'))
                    border_bottom = parse_border(after_info.get('borderBottomWidth', '0px'))
                    border_left = parse_border(after_info.get('borderLeftWidth', '0px'))
                    border_top = parse_border(after_info.get('borderTopWidth', '0px'))
                    
                    # Walls are indicated by 12px borders (or any border > 5px to be safe)
                    wall_threshold = 5.0
                    
                    # Right wall: border on right side of inner div
                    if border_right >= wall_threshold and col < grid_size - 1:
                        walls.add((row, col, row, col + 1))
                    
                    # Bottom wall: border on bottom side of inner div
                    if border_bottom >= wall_threshold and row < grid_size - 1:
                        walls.add((row, col, row + 1, col))
                    
                    # Left wall: border on left side means the cell to the left has a right wall
                    if border_left >= wall_threshold and col > 0:
                        walls.add((row, col - 1, row, col))
                    
                    # Top wall: border on top side means the cell above has a bottom wall
                    if border_top >= wall_threshold and row > 0:
                        walls.add((row - 1, col, row, col))
                        
                except Exception as e:
                    continue
        
        print(f"📊 Total walls detected: {len(walls)}")
        if walls:
            print(f"  Sample walls: {list(walls)[:10]}")
        
        return board, walls

    def get_cell_value_if_int(self, cell):
        # Try multiple ways to find the number in the cell
        # First, try direct text from cell
        try:
            text = cell.text.strip()
            if text.isdigit():
                return int(text)
        except:
            pass
        
        # Try finding content element with various selectors
        content_selectors = [
            ".trail-cell-content",
            "[class*='cell-content']",
            "[class*='content']",
            "span",
            "div",
        ]
        
        for selector in content_selectors:
            try:
                inner_div = cell.find_element(By.CSS_SELECTOR, selector)
                text = inner_div.text.strip()
                if text.isdigit():
                    return int(text)
            except (NoSuchElementException, Exception):
                continue

        return None

    def solve_game(self):
        board, walls = self.board, self.walls
        rows, cols = len(board), len(board[0])

        # Build wall set for fast lookups
        wall_set = set((x1, y1, x2, y2) for x1, y1, x2, y2 in walls)        

        # Find positions of numbers 1, 2, 3, ...
        numbered_positions = {}
        max_num = 0
        for x in range(rows):
            for y in range(cols):
                if board[x][y] > 0:
                    numbered_positions[board[x][y]] = (x, y)
                    max_num = max(max_num, board[x][y])

        # Movement directions
        DIRS = [(-1,0), (1,0), (0,-1), (0,1)]

        # BFS to find all paths from start to end, avoiding visited and walls
        def bfs_all_paths(start, end, visited):
            queue = deque()
            queue.append((start, [start]))
            all_paths = []

            while queue:
                (x, y), path = queue.popleft()

                if (x, y) == end:
                    all_paths.append(path)
                    continue

                for dx, dy in DIRS:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < rows and 0 <= ny < cols: # on the board
                        # no overlaps from previous paths or this path, no walls,
                        # not hitting a number (other than the one we want to hit)
                        if (nx, ny) not in visited \
                            and (nx, ny) not in path \
                            and not self.is_blocked(wall_set, x, y, nx, ny) \
                            and (self.board[nx][ny] == 0 or (nx, ny) == end):
                            queue.append(((nx, ny), path + [(nx, ny)]))

            return all_paths

        # Backtracking to build the full path from 1 → 2 → 3 → ...
        def backtrack(current_num, visited, path_so_far):
            if current_num == max_num:
                # Check if all cells are visited
                if len(visited) == rows * cols:
                    return path_so_far
                return None

            start = numbered_positions[current_num]
            end = numbered_positions[current_num + 1]

            paths = bfs_all_paths(start, end, visited.copy())

            for path in paths:
                new_visited = visited.union(path)
                full_path = path_so_far + path[1:]  # skip duplicate start
                result = backtrack(current_num + 1, new_visited, full_path)
                if result:
                    return result

            return None

        # Start from the position of 1
        start_pos = numbered_positions[1]
        visited = set([start_pos])
        self.path = backtrack(1, visited, [start_pos])

    def is_blocked(self, wall_set, x1, y1, x2, y2):
        return (x1, y1, x2, y2) in wall_set or (x2, y2, x1, y1) in wall_set
    
    def print_solved_game(self):
        print("-" * 60)
        if self.path is None:
            print("⚠️  COULD NOT SOLVE GAME")
            print("This might be due to incorrect wall detection.")
            print("-" * 60)
            print()
            self.print_board([])
        else:
            print("GAME SOLVED")
            print("-" * 60)
            print()
            self.print_board(self.path)

    def print_board(self, path=[]):
        # Define arrow symbols for directions
        arrows = {(0, 1): " → ", (1, 0): " ↓ ", (0, -1): " ← ", (-1, 0): " ↑ "}
        board = self.board

        display = [
            [" " + str(i) + " " if i > 0 else "  " for i in row] for row in board
        ]

        wall_set = set(self.walls)

        rows, cols = len(board), len(board[0])

        for i in range(len(path)):
            x, y = path[i]
            if board[x][y]:
                continue
            elif i + 1 < len(path):
                x2, y2 = path[i + 1]
                dx, dy = x2 - x, y2 - y
                display[x][y] = arrows.get((dx, dy), " ? ")
            else:
                display[x][y] = " • "

        # Print the board with walls
        for x in range(rows):

            # Print the current row and vertical walls
            line = ""
            for y in range(cols):
                if y > 0:
                    if (
                        x,
                        y - 1,
                        x,
                        y,
                    ) in wall_set:  # Check wall between (x,y-1) and (x,y)
                        line += "┃"
                    else:
                        line += " "
                line += f"{display[x][y]}"
            print(line)

            if x < rows:
                line = ""
                for y in range(cols):
                    if (
                        x,
                        y,
                        x + 1,
                        y,
                    ) in wall_set:
                        line += " ━━━"
                    else:
                        line += "    "
                print(line)

    def add_solved_board_to_site(self, timeout=0):
        if self.path is None:
            print("⚠️  Cannot add solution - no path found")
            return
            
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
        
        direction_keys = {
            (0, 1): Keys.ARROW_RIGHT,
            (0, -1): Keys.ARROW_LEFT,
            (1, 0): Keys.ARROW_DOWN,
            (-1, 0): Keys.ARROW_UP
        }

        body = self.driver.find_element("tag name", "body")
        for i in range(1, len(self.path)):
            x1, y1 = self.path[i - 1]
            x2, y2 = self.path[i]
            dx, dy = x2 - x1, y2 - y1
            key = direction_keys.get((dx, dy))

            if not key:
                raise ValueError(f"Invalid move from {self.path[i - 1]} to {self.path[i]}")

            body.send_keys(key)