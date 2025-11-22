from PIL import Image, ImageDraw
import sys
import os

# === Configuratie ===
OUTPUT_FILENAME = "netwerk_tandwiel.gif"
GEAR_FILENAME = "gear.png" # Zorg dat dit bestand in dezelfde map staat!
WIDTH = 600
HEIGHT = 100
DURATION_SECONDS = 30
PACKET_INTERVAL_SECONDS = 2
FPS = 15
GEAR_SIZE = (24, 24) # De grootte waarnaar het tandwiel wordt geschaald

# Kleuren
TRANSPARENT = (0, 0, 0, 0)
DARK_BLUE = (0, 0, 139, 255) # Donkerblauw voor de lijn

# === Voorbereiding ===
# Controleer of het tandwiel plaatje bestaat en laad het
if not os.path.exists(GEAR_FILENAME):
    print(f"FOUT: Het bestand '{GEAR_FILENAME}' ontbreekt!")
    print("Plaats een PNG bestand van een tandwiel met transparante achtergrond")
    print("in dezelfde map als dit script en noem het 'gear.png'.")
    sys.exit(1)

try:
    # Laad de gear image en converteer naar RGBA voor transparantie ondersteuning
    gear_source = Image.open(GEAR_FILENAME).convert("RGBA")
    # Schaal het tandwiel naar een mooi formaat voor de lijn
    gear_img = gear_source.resize(GEAR_SIZE, Image.Resampling.LANCZOS)
    gear_w, gear_h = gear_img.size
    print(f"Tandwiel geladen en geschaald naar {gear_w}x{gear_h} pixels.")
except Exception as e:
    print(f"FOUT bij het laden van het plaatje: {e}")
    sys.exit(1)


# === Berekeningen ===
TOTAL_FRAMES = DURATION_SECONDS * FPS
FRAME_DURATION_MS = int(1000 / FPS)
PACKET_INTERVAL_FRAMES = PACKET_INTERVAL_SECONDS * FPS

# Lijn instellingen
START_X, END_X = 50, WIDTH - 50
Y_POS = HEIGHT // 2
DOT_SIZE = 4
DOT_SPACING = 10

frames = []

print(f"Genereren van {TOTAL_FRAMES} frames met donkerblauwe lijn en tandwielen...")

for frame_num in range(TOTAL_FRAMES):
    # 1. Maak een nieuwe transparante afbeelding
    img = Image.new('RGBA', (WIDTH, HEIGHT), TRANSPARENT)
    draw = ImageDraw.Draw(img)

    # --- A. Teken de bewegende donkerblauwe stippellijn ---
    offset = (frame_num * 2) % (DOT_SIZE + DOT_SPACING)
    current_x = START_X - offset
    
    while current_x < END_X:
        if current_x >= START_X:
            # Teken de stip nu altijd in donkerblauw
            draw.ellipse(
                [current_x, Y_POS - DOT_SIZE//2, current_x + DOT_SIZE, Y_POS + DOT_SIZE//2],
                fill=DARK_BLUE
            )
        current_x += DOT_SIZE + DOT_SPACING

    # --- B. Teken de tandwielen (plaatjes plakken) ---
    packets_started = frame_num // PACKET_INTERVAL_FRAMES + 1
    travel_time_frames = PACKET_INTERVAL_FRAMES 

    for i in range(packets_started):
        start_frame_for_this_packet = i * PACKET_INTERVAL_FRAMES
        frames_traveled = frame_num - start_frame_for_this_packet
        
        if 0 <= frames_traveled <= travel_time_frames:
            progress = frames_traveled / travel_time_frames
            
            # Bereken het middenpunt waar het tandwiel moet komen
            packet_center_x = START_X + (END_X - START_X) * progress
            packet_center_y = Y_POS
            
            # Bereken de linkerbovenhoek voor het plakken van het plaatje
            # zodat het midden van het plaatje op de lijn ligt
            paste_x = int(packet_center_x - gear_w // 2)
            paste_y = int(packet_center_y - gear_h // 2)
            
            # Plak het tandwiel plaatje op het huidige frame.
            # Het derde argument (gear_img) wordt gebruikt als 'mask' 
            # om de transparantie van de PNG te behouden.
            img.paste(gear_img, (paste_x, paste_y), gear_img)

    frames.append(img)

print("Frames gegenereerd. Bezig met opslaan als GIF (dit kan even duren)...")

# Sla de frames op als een geanimeerde GIF
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