import pygame
import random
import time
import math

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
CELL_SIZE = 20
GRID_WIDTH = WIDTH // (2 * CELL_SIZE)
GRID_HEIGHT = HEIGHT // CELL_SIZE
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Maze Generator")


class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.walls = {'top': True, 'right': True, 'bottom': True, 'left': True}
        self.visited = False
        self.parent = None


def create_grid():
    return [[Cell(x, y) for y in range(GRID_HEIGHT)] for x in range(GRID_WIDTH)]


def create_default_maze(grid):
    # Connect cells in each row
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH - 1):
            grid[x][y].walls['right'] = False
            grid[x + 1][y].walls['left'] = False

    # Connect cells in the rightmost column
    for y in range(GRID_HEIGHT - 1):
        grid[GRID_WIDTH - 1][y].walls['bottom'] = False
        grid[GRID_WIDTH - 1][y + 1].walls['top'] = False

    # Set up the root-connected tree
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if x > 0:
                grid[x][y].parent = grid[x - 1][y]
            elif y > 0:
                grid[x][y].parent = grid[x][y - 1]


def draw_tree(grid, root):
    def draw_arrow(start, end):
        pygame.draw.line(screen, GREEN, start, end, 2)
        angle = math.atan2(end[1] - start[1], end[0] - start[0])
        arrow_size = 7
        pygame.draw.polygon(screen, GREEN, [
            (end[0] - arrow_size * math.cos(angle - math.pi / 6),
             end[1] - arrow_size * math.sin(angle - math.pi / 6)),
            (end[0], end[1]),
            (end[0] - arrow_size * math.cos(angle + math.pi / 6),
             end[1] - arrow_size * math.sin(angle + math.pi / 6))
        ])

    def draw_node_and_children(node):
        x, y = node.x * CELL_SIZE + CELL_SIZE // 2, node.y * CELL_SIZE + CELL_SIZE // 2
        if node == root:
            pygame.draw.circle(screen, RED, (x, y), 5)
        else:
            pygame.draw.circle(screen, BLUE, (x, y), 3)

        if node.parent:
            parent_x = node.parent.x * CELL_SIZE + CELL_SIZE // 2
            parent_y = node.parent.y * CELL_SIZE + CELL_SIZE // 2
            draw_arrow((x, y), (parent_x, parent_y))  # Arrow points from node to its parent

        for child in [cell for row in grid for cell in row if cell.parent == node]:
            draw_node_and_children(child)

    draw_node_and_children(root)

    # Highlight the root node
    root_x = root.x * CELL_SIZE + CELL_SIZE // 2
    root_y = root.y * CELL_SIZE + CELL_SIZE // 2
    pygame.draw.circle(screen, RED, (root_x, root_y), 5)


def draw_maze(grid, offset=0):
    for x in range(GRID_WIDTH):
        for y in range(GRID_HEIGHT):
            cell = grid[x][y]
            x_pos = x * CELL_SIZE + offset
            y_pos = y * CELL_SIZE
            if cell.walls['top']:
                pygame.draw.line(screen, WHITE, (x_pos, y_pos), (x_pos + CELL_SIZE, y_pos))
            if cell.walls['right']:
                pygame.draw.line(screen, WHITE, (x_pos + CELL_SIZE, y_pos), (x_pos + CELL_SIZE, y_pos + CELL_SIZE))
            if cell.walls['bottom']:
                pygame.draw.line(screen, WHITE, (x_pos, y_pos + CELL_SIZE), (x_pos + CELL_SIZE, y_pos + CELL_SIZE))
            if cell.walls['left']:
                pygame.draw.line(screen, WHITE, (x_pos, y_pos), (x_pos, y_pos + CELL_SIZE))


def get_neighbors(grid, cell):
    neighbors = []
    x, y = cell.x, cell.y
    if x > 0:
        neighbors.append(('left', grid[x - 1][y]))
    if x < GRID_WIDTH - 1:
        neighbors.append(('right', grid[x + 1][y]))
    if y > 0:
        neighbors.append(('top', grid[x][y - 1]))
    if y < GRID_HEIGHT - 1:
        neighbors.append(('bottom', grid[x][y + 1]))
    return neighbors


def remove_wall(current, next, direction):
    if direction == 'left':
        current.walls['left'] = False
        next.walls['right'] = False
    elif direction == 'right':
        current.walls['right'] = False
        next.walls['left'] = False
    elif direction == 'top':
        current.walls['top'] = False
        next.walls['bottom'] = False
    elif direction == 'bottom':
        current.walls['bottom'] = False
        next.walls['top'] = False


def generate_maze(grid):
    current = grid[0][0]
    current.visited = True
    path = [current]

    while True:
        unvisited_neighbors = [(d, n) for d, n in get_neighbors(grid, current) if not n.visited]
        if unvisited_neighbors:
            direction, next_cell = random.choice(unvisited_neighbors)
            remove_wall(current, next_cell, direction)
            next_cell.visited = True
            path.append(next_cell)
            current = next_cell
            yield direction, current, False  # Moving forward
        elif len(path) > 1:
            path.pop()
            prev = path[-1]
            for d, n in get_neighbors(grid, prev):
                if n == current:
                    yield d, prev, True  # Backtracking
                    break
            current = prev
        else:
            break


def opposite_direction(direction):
    opposites = {'left': 'right', 'right': 'left', 'top': 'bottom', 'bottom': 'top'}
    return opposites[direction]


def root_shift(grid, current_root, direction):
    for d, neighbor in get_neighbors(grid, current_root):
        if d == direction:
            # Update parent relationships
            old_parent = current_root.parent
            if old_parent:
                old_parent.parent = current_root
            neighbor.parent = None
            current_root.parent = neighbor

            return neighbor
    return current_root  # If no valid shift, return the current root


# Create initial maze and root-connected tree
original_grid = create_grid()
create_default_maze(original_grid)
root = original_grid[0][0]

# Create new grid for DFS generation
new_grid = create_grid()
dfs_generator = generate_maze(new_grid)

running = True
clock = pygame.time.Clock()
auto_iterate = False
last_auto_time = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                running = False
            elif event.key == pygame.K_SPACE:
                try:
                    direction, current, is_backtracking = next(dfs_generator)
                    if is_backtracking:
                        direction = opposite_direction(direction)
                    root = root_shift(original_grid, root, direction)
                except StopIteration:
                    print("Maze generation complete")
            elif event.key == pygame.K_m:
                auto_iterate = not auto_iterate
                print("Auto-iterate:", "ON" if auto_iterate else "OFF")

    if auto_iterate and time.time() - last_auto_time > 0.1:  # 10 FPS
        try:
            direction, current, is_backtracking = next(dfs_generator)
            if is_backtracking:
                direction = opposite_direction(direction)
            root = root_shift(original_grid, root, direction)
            last_auto_time = time.time()
        except StopIteration:
            print("Maze generation complete")
            auto_iterate = False

    screen.fill(BLACK)

    # Draw root-connected tree (left side)
    draw_tree(original_grid, root)

    # Draw new maze being generated (right side)
    draw_maze(new_grid, WIDTH // 2)
    if 'current' in locals():
        pygame.draw.rect(screen, GREEN,
                         (current.x * CELL_SIZE + WIDTH // 2, current.y * CELL_SIZE, CELL_SIZE, CELL_SIZE), 2)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
