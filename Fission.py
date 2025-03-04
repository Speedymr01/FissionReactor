import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 500, 500
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
GREY = (128, 128, 128)
BLACK = (10, 10, 10)
RED = (255, 0, 0)
DARK_GREY = (10, 10, 10)
PASTEL_ORANGE = (255, 182, 77)
FPS = 60
CONTROL_ROD_WIDTH = 10
CONTROL_ROD_HEIGHT = HEIGHT
CONTROL_ROD_SPEED = 2

# Create the screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Nuclear Fission Simulation")

# Define random_start variable
random_start = True  # Set this to False for fully U-235

# Define U-235 atoms in a 10x20 grid
grid_rows, grid_cols = 10, 10
margin_x, margin_y = 30, 30
space_x = (WIDTH - 2 * margin_x) // (grid_cols - 1)
space_y = (HEIGHT - 2 * margin_y) // (grid_rows - 1)
u235_atoms = [(margin_x + j * space_x, margin_y + i * space_y, random.random() < 0.04 if random_start else True) for i in range(grid_rows) for j in range(grid_cols)]

# Define Xenon atoms
xenon_atoms = []

# Define control rods
# Define control rods
# Placing a control rod in the middle of two columns
# Define control rods
control_rods = []
for j in range(1, grid_cols):
    if j % 2 == 0:
        middle_x = margin_x + (j - 1) * space_x + space_x // 2
        control_rods.append((middle_x, HEIGHT // 2 - CONTROL_ROD_HEIGHT // 2))


# Define neutrons
neutrons = [(random.randint(50, WIDTH-50), random.randint(50, HEIGHT-50), random.randint(-3, 3), random.randint(-3, 3)) for _ in range(10)]

# Load the font
font = pygame.font.SysFont(None, 48)

# Function to draw entities with antialiasing
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
    # Draw the neutron count
    neutron_count_text = font.render(f"Neutrons: {len(neutrons)}", True, BLACK)
    screen.blit(neutron_count_text, (10, 10))
    pygame.display.flip()

# Function to move neutrons
# Function to move neutrons
def move_neutrons():
    global neutrons, u235_atoms, xenon_atoms
    new_neutrons = []
    original_neutrons = neutrons[:]
    for i in range(len(original_neutrons) - 1, -1, -1):
        neutron = original_neutrons[i]
        neutron = (neutron[0] + neutron[2], neutron[1] + neutron[3], neutron[2], neutron[3])
        # Bounce neutrons off the window edges
        if neutron[0] < 0 or neutron[0] > WIDTH:
            neutron = (neutron[0], neutron[1], -neutron[2], neutron[3])
        if neutron[1] < 0 or neutron[1] > HEIGHT:
            neutron = (neutron[0], neutron[1], neutron[2], -neutron[3])
        original_neutrons[i] = neutron

        # Check for collisions with U-235 atoms
        for j in range(len(u235_atoms)):
            if u235_atoms[j][2]:
                dist = math.hypot(neutron[0] - u235_atoms[j][0], neutron[1] - u235_atoms[j][1])
                if dist < 15:
                    u235_atoms[j] = (u235_atoms[j][0], u235_atoms[j][1], False)
                    if random.random() < 0.066: #6.6% chance to produce a Xenon atom
                        xenon_atoms.append((u235_atoms[j][0], u235_atoms[j][1], 0))
                    for _ in range(3):
                        angle = random.uniform(0, 2 * math.pi)
                        new_neutrons.append((u235_atoms[j][0], u235_atoms[j][1], 3 * math.cos(angle), 3 * math.sin(angle)))

        # Check for collisions with control rods
        for rod in control_rods:
            if rod[0] < neutron[0] < rod[0] + CONTROL_ROD_WIDTH and rod[1] < neutron[1] < rod[1] + CONTROL_ROD_HEIGHT:
                original_neutrons.pop(i)
                break

        # Check for collisions with Xenon atoms
        for k in range(len(xenon_atoms) - 1, -1, -1):
            # Ensure neutron has moved away from the Xenon atom before checking for absorption
            if k < len(xenon_atoms) and math.hypot(neutron[0] - xenon_atoms[k][0], neutron[1] - xenon_atoms[k][1]) >= 15:
                if xenon_atoms[k][2] < 2 and math.hypot(neutron[0] - xenon_atoms[k][0], neutron[1] - xenon_atoms[k][1]) < 15:
                    xenon_atoms[k] = (xenon_atoms[k][0], xenon_atoms[k][1], xenon_atoms[k][2] + 1)
                    original_neutrons.pop(i)
                    break

    neutrons = original_neutrons + new_neutrons


# Function to regenerate uranium and emit neutrons randomly
def regenerate_and_emit():
    if random.random() < 0.15:  # 15% chance to regenerate a uranium atom
        i, j = random.randint(0, grid_rows-1), random.randint(0, grid_cols-1)
        u235_atoms[i * grid_cols + j] = (u235_atoms[i * grid_cols + j][0], u235_atoms[i * grid_cols + j][1], True)
    if random.random() < 0.05:  # 5% chance to emit a neutron
        i = random.randint(0, grid_rows * grid_cols - 1)
        if not u235_atoms[i][2]:
            angle = random.uniform(0, 2 * math.pi)
            neutrons.append((u235_atoms[i][0], u235_atoms[i][1], 3 * math.cos(angle), 3 * math.sin(angle)))

# Function to move control rods
def move_control_rods(keys):
    global control_rods
    for i in range(len(control_rods)):
        if keys[pygame.K_UP]:
            control_rods[i] = (control_rods[i][0], max(-CONTROL_ROD_HEIGHT + 10, control_rods[i][1] - CONTROL_ROD_SPEED))
        if keys[pygame.K_DOWN]:
            control_rods[i] = (control_rods[i][0], min(HEIGHT - 10, control_rods[i][1] + CONTROL_ROD_SPEED))

# Main loop
running = True
clock = pygame.time.Clock()
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    keys = pygame.key.get_pressed()
    move_control_rods(keys)
    move_neutrons()
    regenerate_and_emit()
    draw_entities()
    clock.tick(FPS)
pygame.quit()
