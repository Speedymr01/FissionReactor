import pygame
import random
import math
import time
import csv

pygame.init()

WIDTH, HEIGHT = 500, 500
WHITE, BLUE, GREY, BLACK = (255, 255, 255), (0, 0, 255), (128, 128, 128), (10, 10, 10)
RED, DARK_GREY, PASTEL_ORANGE = (255, 0, 0), (10, 10, 10), (255, 182, 77)
FPS = 60
CONTROL_ROD_WIDTH, CONTROL_ROD_HEIGHT, CONTROL_ROD_SPEED = 10, HEIGHT, 2
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Nuclear Fission Simulation")

random_start = False
auto_control = False  # Variable to track control mode
grid_rows, grid_cols = 10, 10
margin_x, margin_y = 30, 30
space_x = (WIDTH - 2 * margin_x) // (grid_cols - 1)
space_y = (HEIGHT - 2 * margin_y) // (grid_rows - 1)

u235_atoms = [(margin_x + j * space_x, margin_y + i * space_y, random.random() < 0.04 if random_start else True) for i in range(grid_rows) for j in range(grid_cols)]
xenon_atoms, control_rods = [], []
for j in range(1, grid_cols):
    if j % 2 == 0:
        middle_x = margin_x + (j - 1) * space_x + space_x // 2
        control_rods.append((middle_x, HEIGHT // 2 - CONTROL_ROD_HEIGHT // 2))

neutron_grace_period = 1
neutrons = [(random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50), random.randint(-3, 3), random.randint(-3, 3), time.time()) for _ in range(10)]
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

# Collision check function
def check_collision(entity1_pos, entity2_pos, mask1, mask2):
    offset = (int(entity2_pos[0] - entity1_pos[0]), int(entity2_pos[1] - entity1_pos[1]))
    return mask1.overlap(mask2, offset) is not None

def draw_entities():
    screen.fill(WHITE)
    for atom in u235_atoms:
        color = BLUE if atom[2] else GREY
        pygame.draw.circle(screen, color, (int(atom[0]), int(atom[1])), 7)
    for neutron in neutrons:
        pygame.draw.circle(screen, BLACK, (int(neutron[0]), int(neutron[1])), 3)
    for rod in control_rods:
        pygame.draw.rect(screen, DARK_GREY, (rod[0], rod[1], CONTROL_ROD_WIDTH, CONTROL_ROD_HEIGHT))
    for xenon in xenon_atoms:
        color = PASTEL_ORANGE if xenon[2] < 2 else GREY
        pygame.draw.circle(screen, color, (int(xenon[0]), int(xenon[1])), 7)

    # Display neutron count
    neutron_count_text = font.render(f"Neutrons: {len(neutrons)}", True, BLACK)
    screen.blit(neutron_count_text, (10, 10))

    # Display FPS
    fps = int(clock.get_fps())  # Get the current FPS
    fps_text = font.render(f"FPS: {fps}", True, BLACK)
    screen.blit(fps_text, (10, 50))

    pygame.display.flip()


def move_neutrons():
    global neutrons, u235_atoms, xenon_atoms
    new_neutrons = []
    original_neutrons = neutrons[:]
    current_time = time.time()

    for neutron in original_neutrons:
        # Update neutron position
        neutron = (neutron[0] + neutron[2], neutron[1] + neutron[3], neutron[2], neutron[3], neutron[4])
        if neutron[0] < 0 or neutron[0] > WIDTH:
            neutron = (neutron[0], neutron[1], -neutron[2], neutron[3], neutron[4])
        if neutron[1] < 0 or neutron[1] > HEIGHT:
            neutron = (neutron[0], neutron[1], neutron[2], -neutron[3], neutron[4])

        # Collision with U-235 atoms
        for i, atom in enumerate(u235_atoms):
            if atom[2] and check_collision(neutron[:2], atom[:2], neutron_mask, atom_mask):
                u235_atoms[i] = (atom[0], atom[1], False)
                if random.random() < 0.066:
                    xenon_atoms.append((atom[0], atom[1], 0))
                for _ in range(3):
                    angle = random.uniform(0, 2 * math.pi)
                    new_neutrons.append((atom[0], atom[1], 3 * math.cos(angle), 3 * math.sin(angle), time.time()))
                break

        # Collision with Xenon atoms
        for i, xenon in enumerate(xenon_atoms):
            if check_collision(neutron[:2], xenon[:2], neutron_mask, xenon_mask):
                xenon_atoms[i] = (xenon[0], xenon[1], xenon[2] + 1)
                break

        # Collision with control rods
        for rod in control_rods:
            rod_rect = pygame.Rect(rod[0], rod[1], CONTROL_ROD_WIDTH, CONTROL_ROD_HEIGHT)
            if rod_rect.collidepoint(neutron[:2]):
                break
        else:
            # If no collisions, keep neutron
            new_neutrons.append(neutron)

    neutrons = new_neutrons

def regenerate_and_emit():
    if random.random() < 0.10:
        i, j = random.randint(0, grid_rows - 1), random.randint(0, grid_cols - 1)
        u235_atoms[i * grid_cols + j] = (u235_atoms[i * grid_cols + j][0], u235_atoms[i * grid_cols + j][1], True)
    if random.random() < 0.01:
        i = random.randint(0, grid_rows * grid_cols - 1)
        if not u235_atoms[i][2]:
            angle = random.uniform(0, 2 * math.pi)
            neutrons.append((u235_atoms[i][0], u235_atoms[i][1], 3 * math.cos(angle), 3 * math.sin(angle), time.time()))

def move_control_rods(keys):
    global control_rods, auto_control
    if auto_control:
        total_neutrons = len(neutrons)
        for i in range(len(control_rods)):
            if total_neutrons > 50:
                if control_rods[i][1] + CONTROL_ROD_HEIGHT + CONTROL_ROD_SPEED <= HEIGHT:
                    control_rods[i] = (control_rods[i][0], control_rods[i][1] + CONTROL_ROD_SPEED)
            elif total_neutrons < 50:
                control_rods[i] = (control_rods[i][0], max(-CONTROL_ROD_HEIGHT + 10, control_rods[i][1] - CONTROL_ROD_SPEED))
    else:
        for i in range(len(control_rods)):
            if keys[pygame.K_UP]:
                control_rods[i] = (control_rods[i][0], max(-CONTROL_ROD_HEIGHT + 10, control_rods[i][1] - CONTROL_ROD_SPEED))
            if keys[pygame.K_DOWN]:
                if control_rods[i][1] + CONTROL_ROD_HEIGHT + CONTROL_ROD_SPEED <= HEIGHT:
                    control_rods[i] = (control_rods[i][0], control_rods[i][1] + CONTROL_ROD_SPEED)

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
    rod_position_percentage = max(0, min(100, 100 * (control_rods[0][1] / HEIGHT)))
    control_rod_percentages.append(rod_position_percentage)

    # Cap the frame rate
    clock.tick(FPS)


# Quit Pygame and save results to CSV
pygame.quit()
save_results_to_csv(neutron_counts, control_rod_percentages)
