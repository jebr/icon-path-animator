import math

from PIL import Image, ImageDraw

# === Configuratie ===
OUTPUT_FILENAME = "netwerk_verkeer.gif"
WIDTH = 600
HEIGHT = 100
DURATION_SECONDS = 30
PACKET_INTERVAL_SECONDS = 2
FPS = 15  # Frames per seconde (hoger is vloeiender, maar groter bestand)

# Kleuren voor de multi-color lijn
LINE_COLORS = [
    (255, 0, 0, 255),   # Rood
    (255, 165, 0, 255), # Oranje
    (255, 255, 0, 255), # Geel
    (0, 255, 0, 255),   # Groen
    (0, 0, 255, 255),   # Blauw
    (75, 0, 130, 255),  # Indigo
    (238, 130, 238, 255) # Violet
]
PACKET_COLOR = (255, 255, 255, 255) # Wit pakketje

# === Berekeningen ===
TOTAL_FRAMES = DURATION_SECONDS * FPS
FRAME_DURATION_MS = int(1000 / FPS)
PACKET_INTERVAL_FRAMES = PACKET_INTERVAL_SECONDS * FPS

# Lijn instellingen
START_X, END_X = 50, WIDTH - 50
Y_POS = HEIGHT // 2
DOT_SIZE = 4
DOT_SPACING = 10 # Ruimte tussen stippen

frames = []

print(f"Genereren van {TOTAL_FRAMES} frames... Een moment geduld.")

for frame_num in range(TOTAL_FRAMES):
    # 1. Maak een nieuwe transparante afbeelding (RGBA, met alpha 0)
    img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # --- A. Teken de bewegende multi-color stippellijn ---
    # De offset zorgt voor het bewegende effect ("marching ants")
    offset = (frame_num * 2) % (DOT_SIZE + DOT_SPACING)
    
    current_x = START_X - offset
    color_index = 0
    
    while current_x < END_X:
        # Alleen tekenen als de stip binnen de marges valt
        if current_x >= START_X:
            # Kies de kleur op basis van de positie in de lijst
            color = LINE_COLORS[color_index % len(LINE_COLORS)]
            # Teken een stip (klein cirkeltje)
            draw.ellipse(
                [current_x, Y_POS - DOT_SIZE//2, current_x + DOT_SIZE, Y_POS + DOT_SIZE//2],
                fill=color
            )
        
        current_x += DOT_SIZE + DOT_SPACING
        color_index += 1

    # --- B. Teken de data pakketjes ---
    # We berekenen hoeveel pakketjes er tot nu toe gestart zouden moeten zijn
    packets_started = frame_num // PACKET_INTERVAL_FRAMES + 1
    
    # Een pakketje doet er ook 2 seconden over om de overkant te bereiken
    travel_time_frames = PACKET_INTERVAL_FRAMES 

    for i in range(packets_started):
        # Frame waarop dit specifieke pakketje (i) begon
        start_frame_for_this_packet = i * PACKET_INTERVAL_FRAMES
        
        # Hoeveel frames is dit pakketje al onderweg?
        frames_traveled = frame_num - start_frame_for_this_packet
        
        # Als het pakketje nog onderweg is (progressie tussen 0.0 en 1.0)
        if 0 <= frames_traveled <= travel_time_frames:
            progress = frames_traveled / travel_time_frames
            
            # Bereken huidige X positie
            packet_x = START_X + (END_X - START_X) * progress
            
            # Teken het pakketje (een vierkantje)
            packet_size = 12
            draw.rectangle(
                [packet_x - packet_size//2, Y_POS - packet_size//2, 
                 packet_x + packet_size//2, Y_POS + packet_size//2],
                fill=PACKET_COLOR,
                outline=(0,0,0,255) # Zwart randje voor contrast
            )

    frames.append(img)

print("Frames gegenereerd. Bezig met opslaan als GIF...")

# Sla de frames op als een geanimeerde GIF
# disposal=2 is belangrijk voor transparantie (wist het vorige frame)
frames[0].save(
    OUTPUT_FILENAME,
    save_all=True,
    append_images=frames[1:],
    optimize=False,
    duration=FRAME_DURATION_MS,
    loop=0, # 0 betekent oneindig loopen
    disposal=2, 
    transparency=0
)

print(f"Klaar! Bestand opgeslagen als: {OUTPUT_FILENAME}")