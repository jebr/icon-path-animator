from PIL import Image, ImageDraw, ImageOps
import sys
import os
import colorsys
import math

# ==========================================
# ============ CONFIGURATIE ================
# ==========================================

# --- Vorm & Richting ---
PATH_SHAPE      = "ARC"             # Kies "STRAIGHT" (rechte lijn) of "ARC" (boogje)
DIRECTION       = "RTL"             # Kies "LTR" (Links-naar-Rechts) of "RTL" (Rechts-naar-Links)
AUTO_FLIP_ICON  = True              # Zet op True om het plaatje automatisch te spiegelen bij "RTL"

# --- Boog Instellingen ---
ARC_HEIGHT      = 80                # Hoe hoog de boog komt in pixels (alleen actief als PATH_SHAPE = "ARC")

# --- Bestanden ---
OUTPUT_FILENAME = "media/output/drawing-animatie.gif" # De naam van het resultaatbestand (moet .gif zijn)
ICON_FILENAME   = "media/drawing.png"       # De naam van je plaatje (zorg dat deze in dezelfde map staat)

# --- Afmetingen & Kwaliteit ---
WIDTH     = 600            # Totale breedte van de afbeelding
HEIGHT    = 200            # Totale hoogte (houd dit hoog genoeg zodat de boog erin past!)
ICON_SIZE = (24, 24)       # Formaat waarnaar het plaatje wordt geschaald (breedte, hoogte)
FPS       = 15             # Frames Per Seconde (snelheid/vloeiendheid van de animatie)

# --- Tijd & Frequentie ---
DURATION_SECONDS        = 30       # Totale duur van de animatie in seconden
PACKET_INTERVAL_SECONDS = 3        # Om de hoeveel seconden verschijnt een nieuw icoontje

# --- Lijn Uiterlijk ---
DOT_SIZE    = 4            # Dikte van de stippen in pixels
DOT_SPACING = 10           # Afstand (witruimte) tussen de stippen
LINE_Y_POS  = 180          # Verticale startpositie (zet laag, bijv 180, zodat de boog omhoog kan)

# --- Kleuren ---
# Formaat: (Rood, Groen, Blauw, Transparantie) | 0-255
LINE_COLOR       = (0, 0, 139, 255) # Vaste kleur van de lijn (wordt genegeerd bij regenboog)
USE_RAINBOW_LINE = False            # Zet op True voor regenboogkleuren, False voor vaste kleur
BACKGROUND_COLOR = (0, 0, 0, 0)     # Achtergrondkleur ((0, 0, 0, 0) is transparant)

# ==========================================
# ======= EINDE CONFIGURATIE ===============
# ==========================================

def get_rainbow_color(progress, total_length=1.0):
    """Genereert een kleur op basis van voortgang (0.0 tot 1.0)."""
    r, g, b = colorsys.hls_to_rgb(progress, 0.5, 1.0)
    return (int(r*255), int(g*255), int(b*255), 255)

def get_bezier_point(t, p0, p1, p2):
    """Berekent (x,y) op een kwadratische curve voor tijdstip t (0.0 tot 1.0)."""
    # Formule: (1-t)^2 * P0 + 2(1-t)t * P1 + t^2 * P2
    x = (1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0]
    y = (1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1]
    return (x, y)

# === Voorbereiding ===
if not os.path.exists(ICON_FILENAME):
    print(f"FOUT: Het bestand '{ICON_FILENAME}' is niet gevonden!")
    print("Controleer de naam in de configuratie.")
    sys.exit(1)

try:
    # Laad de image en converteer naar RGBA
    icon_source = Image.open(ICON_FILENAME).convert("RGBA")
    icon_img = icon_source.resize(ICON_SIZE, Image.Resampling.LANCZOS)
    
    # Spiegelen indien nodig
    if DIRECTION == "RTL" and AUTO_FLIP_ICON:
        icon_img = ImageOps.mirror(icon_img)
        print(f"Afbeelding geladen en gespiegeld (RTL modus).")
    else:
        print(f"Afbeelding geladen.")
        
    icon_w, icon_h = icon_img.size
except Exception as e:
    print(f"FOUT bij verwerken plaatje: {e}")
    sys.exit(1)

# === Berekeningen ===
TOTAL_FRAMES = DURATION_SECONDS * FPS
FRAME_DURATION_MS = int(1000 / FPS)
PACKET_INTERVAL_FRAMES = PACKET_INTERVAL_SECONDS * FPS

# Definieer de punten voor de route
MARGIN = 50
P0 = (MARGIN, LINE_Y_POS)          # Startpunt (Links)
P2 = (WIDTH - MARGIN, LINE_Y_POS)  # Eindpunt (Rechts)

# Het controlepunt P1 bepaalt de vorm
if PATH_SHAPE == "ARC":
    # P1 ligt in het midden, en 'ARC_HEIGHT' pixels omhoog (Y wordt kleiner)
    mid_x = (P0[0] + P2[0]) / 2
    mid_y = LINE_Y_POS - ARC_HEIGHT
    P1 = (mid_x, mid_y)
else:
    # Bij een rechte lijn ligt het punt precies tussenin op dezelfde hoogte
    mid_x = (P0[0] + P2[0]) / 2
    P1 = (mid_x, LINE_Y_POS)

# --- Pad voorberekenen (Look-up Table) ---
# Dit zorgt ervoor dat de stippels mooi gelijk verdeeld zijn, ook in de bocht.
path_points = []
TOTAL_DISTANCE = 0
STEPS = 500 # Hoe hoger, hoe nauwkeuriger de curve

prev_pos = P0
path_points.append({"pos": P0, "dist": 0, "t": 0})

for i in range(1, STEPS + 1):
    t = i / STEPS
    pos = get_bezier_point(t, P0, P1, P2)
    
    # Afstand berekenen (Pythagoras)
    dist_segment = math.sqrt((pos[0] - prev_pos[0])**2 + (pos[1] - prev_pos[1])**2)
    TOTAL_DISTANCE += dist_segment
    
    path_points.append({"pos": pos, "dist": TOTAL_DISTANCE, "t": t})
    prev_pos = pos

print(f"Genereren van {TOTAL_FRAMES} frames. Vorm: {PATH_SHAPE}, Richting: {DIRECTION}...")

frames = []

for frame_num in range(TOTAL_FRAMES):
    img = Image.new('RGBA', (WIDTH, HEIGHT), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(img)

    # --- A. Teken de Stippellijn ---
    pattern_len = DOT_SIZE + DOT_SPACING
    phase = (frame_num * 2) % pattern_len
    
    # Als we RTL gaan, draaien we de fase om zodat de lijn terug lijkt te lopen
    if DIRECTION == "RTL":
        phase = pattern_len - phase

    current_dist_target = phase
    
    # Loop door de look-up table om stippen op de juiste afstand te zetten
    last_idx = 0
    while current_dist_target < TOTAL_DISTANCE:
        for i in range(last_idx, len(path_points)):
            pt = path_points[i]
            if pt["dist"] >= current_dist_target:
                # Positie gevonden
                cx, cy = pt["pos"]
                
                if USE_RAINBOW_LINE:
                    fill_color = get_rainbow_color(pt["t"])
                else:
                    fill_color = LINE_COLOR

                draw.ellipse(
                    [cx - DOT_SIZE/2, cy - DOT_SIZE/2, cx + DOT_SIZE/2, cy + DOT_SIZE/2],
                    fill=fill_color
                )
                last_idx = i
                break
        current_dist_target += pattern_len

    # --- B. Teken de Icoontjes ---
    packets_started = frame_num // PACKET_INTERVAL_FRAMES + 1
    travel_time_frames = PACKET_INTERVAL_FRAMES 

    for i in range(packets_started):
        start_frame = i * PACKET_INTERVAL_FRAMES
        frames_traveled = frame_num - start_frame
        
        if 0 <= frames_traveled <= travel_time_frames:
            # Progressie van 0.0 tot 1.0
            raw_progress = frames_traveled / travel_time_frames
            
            # Pas richting toe
            if DIRECTION == "LTR":
                t = raw_progress
            else:
                t = 1.0 - raw_progress
            
            # Bereken positie op curve
            cur_x, cur_y = get_bezier_point(t, P0, P1, P2)
            
            paste_x = int(cur_x - icon_w // 2)
            paste_y = int(cur_y - icon_h // 2)
            
            img.paste(icon_img, (paste_x, paste_y), icon_img)

    frames.append(img)

# === Opslaan ===
print("Frames genereren voltooid. Opslaan als GIF...")

frames[0].save(
    OUTPUT_FILENAME,
    save_all=True,
    append_images=frames[1:],
    optimize=False,
    duration=FRAME_DURATION_MS,
    loop=0,
    disposal=2, 
    transparency=0
)

print(f"Klaar! Bestand opgeslagen als: {OUTPUT_FILENAME}")