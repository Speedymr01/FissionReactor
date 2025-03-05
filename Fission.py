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
    neutron_count_text = font.render(f"Neutrons: {len(neutrons)}", True, BLACK)
    screen.blit(neutron_count_text, (10, 10))
    pygame.display.flip()

def move_neutrons():
    global neutrons, u235_atoms, xenon_atoms
    new_neutrons = []
    original_neutrons = neutrons[:]
    current_time = time.time()

    for i in range(len(original_neutrons) - 1, -1, -1):
        neutron = original_neutrons[i]
        neutron = (neutron[0] + neutron[2], neutron[1] + neutron[3], neutron[2], neutron[3], neutron[4])

        if neutron[0] < 0 or neutron[0] > WIDTH:
            neutron = (neutron[0], neutron[1], -neutron[2], neutron[3], neutron[4])
        if neutron[1] < 0 or neutron[1] > HEIGHT:
            neutron = (neutron[0], neutron[1], neutron[2], -neutron[3], neutron[4])

        original_neutrons[i] = neutron

        # Check if the neutron has passed the grace period
        if current_time - neutron[4] >= neutron_grace_period:
            for j in range(len(u235_atoms)):
                if u235_atoms[j][2]:
                    dist = math.hypot(neutron[0] - u235_atoms[j][0], neutron[1] - u235_atoms[j][1])
                    if dist < 15:
                        u235_atoms[j] = (u235_atoms[j][0], u235_atoms[j][1], False)
                        if random.random() < 0.066:
                            xenon_atoms.append((u235_atoms[j][0], u235_atoms[j][1], 0))
                        for _ in range(3):
                            angle = random.uniform(0, 2 * math.pi)
                            new_neutrons.append((u235_atoms[j][0], u235_atoms[j][1], 3 * math.cos(angle), 3 * math.sin(angle), time.time()))

            for rod in control_rods:
                if rod[0] < neutron[0] < rod[0] + CONTROL_ROD_WIDTH and rod[1] < neutron[1] < rod[1] + CONTROL_ROD_HEIGHT:
                    original_neutrons.pop(i)
                    break

            for k in range(len(xenon_atoms) - 1, -1, -1):
                if k < len(xenon_atoms) and math.hypot(neutron[0] - xenon_atoms[k][0], neutron[1] - xenon_atoms[k][1]) < 15:
                    xenon_atoms[k] = (xenon_atoms[k][0], xenon_atoms[k][1], xenon_atoms[k][2] + 1)
                    original_neutrons.pop(i)
                    break

    neutrons = original_neutrons + new_neutrons

    for k in range(len(xenon_atoms) - 1, -1, -1):
        if xenon_atoms[k][2] >= 2:
            u235_atoms.append((xenon_atoms[k][0], xenon_atoms[k][1], False))
            xenon_atoms.pop(k)

def regenerate_and_emit():
    if random.random() < 0.15:
        i, j = random.randint(0, grid_rows-1), random.randint(0, grid_cols-1)
        u235_atoms[i * grid_cols + j] = (u235_atoms[i * grid_cols + j][0], u235_atoms[i * grid_cols + j][1], True)
    if random.random() < 0.05:
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

def toggle_control_mode(keys):
    global auto_control
    if keys[pygame.K_m]:  # Press 'M' to toggle control mode
        auto_control = not auto_control

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
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    keys = pygame.key.get_pressed()
    toggle_control_mode(keys)
    move_control_rods(keys)
    move_neutrons()
    regenerate_and_emit()
    draw_entities()
    clock.tick(FPS)
    neutron_counts.append(len(neutrons))
    rod_position_percentage = max(0, min(100, 100 * (control_rods[0][1] / HEIGHT)))
    control_rod_percentages.append(rod_position_percentage)

pygame.quit()
save_results_to_csv(neutron_counts, control_rod_percentages)
