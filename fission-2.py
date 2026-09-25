import pygame
import random
import math
import time
import csv

pygame.init()

WIDTH, HEIGHT = 800, 800

WHITE, BLUE, GREY, BLACK = (255, 255, 255), (0, 0, 255), (128, 128, 128), (10, 10, 10)
RED, DARK_GREY, PASTEL_ORANGE = (255, 0, 0), (10, 10, 10), (255, 182, 77)
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Nuclear Fission Simulation")

random_start = False
auto_control = False 
grid_rows, grid_cols = 20, 20

# Initialize lists before first layout update
u235_atoms = []
control_rods = []
xenon_atoms = {} # Changed to dictionary for O(1) lookup: {(i, j): absorption_count}


def update_layout():
    global WIDTH, HEIGHT, margin_x, margin_y, space_x, space_y, SIM_LEFT, SIM_TOP, SIM_RIGHT, SIM_BOTTOM, CONTROL_ROD_WIDTH, CONTROL_ROD_HEIGHT, CONTROL_ROD_SPEED, u235_atoms, control_rods, neutrons
    
    # Store old boundaries for scaling neutrons
    try:
        old_left, old_top = SIM_LEFT, SIM_TOP
        old_right, old_bottom = SIM_RIGHT, SIM_BOTTOM
        has_old_bounds = True
    except NameError:
        has_old_bounds = False
    
    margin_x, margin_y = WIDTH * 0.1, HEIGHT * 0.1
    space_x = (WIDTH - 2 * margin_x) // (grid_cols - 1) if grid_cols > 1 else 0
    space_y = (HEIGHT - 2 * margin_y) // (grid_rows - 1) if grid_rows > 1 else 0
    
    SIM_LEFT, SIM_TOP = margin_x - 20, margin_y - 20
    SIM_RIGHT, SIM_BOTTOM = WIDTH - margin_x + 20, HEIGHT - margin_y + 20
    
    CONTROL_ROD_WIDTH = WIDTH * 0.01
    CONTROL_ROD_HEIGHT = SIM_BOTTOM - SIM_TOP
    CONTROL_ROD_SPEED = 2
    
    # Update atom positions to scale
    new_u235 = []
    for i in range(grid_rows):
        for j in range(grid_cols):
            idx = i * grid_cols + j
            state = u235_atoms[idx][2] if idx < len(u235_atoms) else (random.random() < 0.04 if random_start else True)
            new_u235.append((margin_x + j * space_x, margin_y + i * space_y, state))
    u235_atoms = new_u235

    # Update control rods (every other rod is white)
    new_rods = []
    for j in range(1, grid_cols):
        if j % 2 == 0:
            middle_x = margin_x + (j - 1) * space_x + space_x // 2
            is_white = len(new_rods) % 2 == 1
            new_rods.append((middle_x, HEIGHT // 2 - CONTROL_ROD_HEIGHT, is_white))
    control_rods = new_rods

    # Scale neutrons relative to simulation boundaries
    if has_old_bounds:
        new_neutrons = []
        for n in neutrons:
            x_rel = (n[0] - old_left) / (old_right - old_left) if (old_right - old_left) != 0 else 0.5
            y_rel = (n[1] - old_top) / (old_bottom - old_top) if (old_bottom - old_top) != 0 else 0.5
            
            new_x = SIM_LEFT + x_rel * (SIM_RIGHT - SIM_LEFT)
            new_y = SIM_TOP + y_rel * (SIM_BOTTOM - SIM_TOP)
            new_neutrons.append((new_x, new_y, n[2], n[3], n[4], n[5]))
        neutrons = new_neutrons

update_layout()

neutron_grace_period = 1

def make_neutron(x, y, vx, vy, spawn_time=None):
    if spawn_time is None:
        spawn_time = time.time()
    is_white = random.random() < 0.5
    return (x, y, vx, vy, spawn_time, is_white)

neutrons = [make_neutron(random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50), random.randint(-3, 3), random.randint(-3, 3)) for _ in range(25)]
font = pygame.font.SysFont(None, 48)

# Create masks
neutron_surface = pygame.Surface((6, 6), pygame.SRCALPHA)
pygame.draw.circle(neutron_surface, BLACK, (3, 3), 3)
neutron_mask = pygame.mask.from_surface(neutron_surface)

atom_surface = pygame.Surface((14, 14), pygame.SRCALPHA)
pygame.draw.circle(atom_surface, BLUE, (7, 7), 7)
atom_mask = pygame.mask.from_surface(atom_surface)

xenon_surface = pygame.Surface((14, 14), pygame.SRCALPHA)
pygame.draw.circle(xenon_surface, PASTEL_ORANGE, (7, 7), 7)
xenon_mask = pygame.mask.from_surface(xenon_surface)

# Collision check function using distance squared for speed
def check_collision(pos1, pos2, radius1, radius2):
    dist_sq = (pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2
    return dist_sq < (radius1 + radius2)**2


def draw_entities():
    screen.fill(WHITE)

    # Draw the updated simulation boundary
    pygame.draw.rect(screen, BLACK, (SIM_LEFT, SIM_TOP, SIM_RIGHT - SIM_LEFT, SIM_BOTTOM - SIM_TOP), 3)

    for atom in u235_atoms:
        color = BLUE if atom[2] else GREY
        pygame.draw.circle(screen, color, (int(atom[0]), int(atom[1])), 7)
    for neutron in neutrons:
        pos = (int(neutron[0]), int(neutron[1]))
        if neutron[5]:
            pygame.draw.circle(screen, WHITE, pos, 3)
            pygame.draw.circle(screen, BLACK, pos, 3, 1)
        else:
            pygame.draw.circle(screen, BLACK, pos, 3)
    for rod in control_rods:
        rect = (rod[0], rod[1], CONTROL_ROD_WIDTH, CONTROL_ROD_HEIGHT)
        if rod[2]:
            pygame.draw.rect(screen, WHITE, rect)
            pygame.draw.rect(screen, BLACK, rect, 1)
        else:
            pygame.draw.rect(screen, DARK_GREY, rect)
    for pos, count in xenon_atoms.items():
        color = PASTEL_ORANGE if count < 2 else GREY
        pygame.draw.circle(screen, color, (int(pos[0]), int(pos[1])), 7)

    # Display neutron count
    neutron_count_text = font.render(f"Neutrons: {len(neutrons)}", True, BLACK)
    screen.blit(neutron_count_text, (10, 10))

    # Display FPS
    fps = int(clock.get_fps())
    fps_text = font.render(f"FPS: {fps}", True, BLACK)
    screen.blit(fps_text, (10, 50))

    pygame.display.flip()



def move_neutrons():
    global neutrons, u235_atoms, xenon_atoms
    new_neutrons = []
    current_time = time.time()

    for neutron in neutrons:
        # Update neutron position
        x, y, vx, vy, spawn_time, is_white = neutron
        x += vx / 2
        y += vy / 2

        # Check for collisions with updated simulation boundaries and clamp position
        if x < SIM_LEFT:
            x = SIM_LEFT
            vx = -vx
        elif x > SIM_RIGHT:
            x = SIM_RIGHT
            vx = -vx
            
        if y < SIM_TOP:
            y = SIM_TOP
            vy = -vy
        elif y > SIM_BOTTOM:
            y = SIM_BOTTOM
            vy = -vy

        # Collision logic for U-235
        collided = False
        for i, atom in enumerate(u235_atoms):
            if atom[2] and check_collision((x, y), atom[:2], 3, 7):
                u235_atoms[i] = (atom[0], atom[1], False)
                if random.random() < 0.066:
                    xenon_atoms[(atom[0], atom[1])] = 0
                for _ in range(3):
                    angle = random.uniform(0, 2 * math.pi)
                    new_neutrons.append(make_neutron(atom[0], atom[1], 3 * math.cos(angle), 3 * math.sin(angle), current_time))
                collided = True
                break

        if collided: continue

        # Collision logic for Xenon
        for pos in list(xenon_atoms.keys()):
            if check_collision((x, y), pos, 3, 7):
                xenon_atoms[pos] += 1
                if xenon_atoms[pos] >= 2:
                    # Convert back to U235 by finding nearest slot or adding to list
                    u235_atoms.append((pos[0], pos[1], True))
                    del xenon_atoms[pos]
                collided = True
                break
        
        if collided: continue

        # Collision logic for control rods: a neutron is only absorbed by a rod of its own colour
        for rod in control_rods:
            if rod[2] != is_white:
                continue
            if rod[0] <= x <= rod[0] + CONTROL_ROD_WIDTH and rod[1] <= y <= rod[1] + CONTROL_ROD_HEIGHT:
                collided = True
                break
        
        if not collided:
            new_neutrons.append((x, y, vx, vy, spawn_time, is_white))

    neutrons = new_neutrons




def regenerate_and_emit():
    if random.random() < 0.10:
        i, j = random.randint(0, grid_rows - 1), random.randint(0, grid_cols - 1)
        u235_atoms[i * grid_cols + j] = (u235_atoms[i * grid_cols + j][0], u235_atoms[i * grid_cols + j][1], True)
    if random.random() < 0.01:
        i = random.randint(0, grid_rows * grid_cols - 1)
        if not u235_atoms[i][2]:
            angle = random.uniform(0, 2 * math.pi)
            neutrons.append(make_neutron(u235_atoms[i][0], u235_atoms[i][1], 3 * math.cos(angle), 3 * math.sin(angle)))

def move_control_rods(keys):
    global control_rods, auto_control
    if auto_control:
        total_neutrons = len(neutrons)
        # PID-like approach: Targeted neutron count is 30
        target = 30
        error = total_neutrons - target
        
        # Adjust speed based on error magnitude for smoother convergence
        speed = CONTROL_ROD_SPEED if abs(error) < 20 else CONTROL_ROD_SPEED * 2
        
        for i in range(len(control_rods)):
            if error > 0: # Too many neutrons -> Lower rods (increase absorption)
                if control_rods[i][1] + CONTROL_ROD_HEIGHT + speed <= SIM_BOTTOM:
                    control_rods[i] = (control_rods[i][0], control_rods[i][1] + speed, control_rods[i][2])
            elif error < 0: # Too few neutrons -> Raise rods (decrease absorption)
                control_rods[i] = (control_rods[i][0], max(-CONTROL_ROD_HEIGHT + 10, control_rods[i][1] - speed), control_rods[i][2])
    else:
        for i in range(len(control_rods)):
            if keys[pygame.K_UP]:
                control_rods[i] = (control_rods[i][0], max(-CONTROL_ROD_HEIGHT + 10, control_rods[i][1] - CONTROL_ROD_SPEED), control_rods[i][2])
            if keys[pygame.K_DOWN]:
                if control_rods[i][1] + CONTROL_ROD_HEIGHT + CONTROL_ROD_SPEED <= SIM_BOTTOM:
                    control_rods[i] = (control_rods[i][0], control_rods[i][1] + CONTROL_ROD_SPEED, control_rods[i][2])

last_toggle_time = 0  # Initialize the last toggle time

def toggle_control_mode(keys):
    global auto_control, last_toggle_time
    current_time = time.time()
    if keys[pygame.K_m] and current_time - last_toggle_time > 1:  # Check for 1-second cooldown
        auto_control = not auto_control
        last_toggle_time = current_time  # Update the last toggle time

def save_results_to_csv(neutron_counts, control_rod_percentages, filename="results.csv"):
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Neutron Count", "Control Rod Percentage"])
        for count, percentage in zip(neutron_counts, control_rod_percentages):
            writer.writerow([count, percentage])

neutron_counts = []
control_rod_percentages = []
running = True
clock = pygame.time.Clock()

FPS = 60  # Initial FPS
max_FPS = 120  # Define a maximum FPS limit
min_FPS = 10   # Define a minimum FPS limit

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:  # Handle quit event
            running = False
        elif event.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = event.w, event.h
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            update_layout()

    keys = pygame.key.get_pressed()  # Capture pressed keys

    # Adjust FPS with Q and E keys
    if keys[pygame.K_q]:
        FPS = max(min_FPS, FPS - 1)  # Decrease FPS but do not go below the minimum
    if keys[pygame.K_e]:
        FPS = min(max_FPS, FPS + 1)  # Increase FPS but do not exceed the maximum

    # Toggle control mode
    toggle_control_mode(keys)

    # Move control rods based on the control mode
    move_control_rods(keys)

    # Update neutron positions and handle collisions
    move_neutrons()

    # Regenerate U-235 atoms and emit new neutrons
    regenerate_and_emit()

    # Redraw all entities (U-235 atoms, neutrons, Xenon, control rods)
    draw_entities()

    # Append data for saving results
    neutron_counts.append(len(neutrons))
    rod_bottom_y = control_rods[0][1] + CONTROL_ROD_HEIGHT
    rod_position_percentage = max(0, min(100, 100 * (rod_bottom_y - SIM_TOP) / (SIM_BOTTOM - SIM_TOP)))

    control_rod_percentages.append(rod_position_percentage)

    # Cap the frame rate
    clock.tick(FPS)


# Quit Pygame and save results to CSV
pygame.quit()
save_results_to_csv(neutron_counts, control_rod_percentages)
