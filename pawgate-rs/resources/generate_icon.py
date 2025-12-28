#!/usr/bin/env python3
"""
Generate colorblind-friendly icon for PawGate.

Uses high-contrast blue (#1565C0) and orange (#FF6D00) which are
distinguishable by most color vision deficiency types:
- Protanopia (red-blind)
- Deuteranopia (green-blind)
- Tritanopia (blue-blind)

Run this script to generate pawgate.ico in the resources folder.
Requires: pip install pillow
"""

from PIL import Image, ImageDraw
import os

def draw_paw(draw, size, bg_color, fg_color):
    """Draw a paw print icon."""
    center = size // 2

    # Draw circular background
    margin = 2
    draw.ellipse([margin, margin, size - margin, size - margin], fill=bg_color)

    # Scale factor for different icon sizes
    scale = size / 64.0

    # Main pad (center-bottom, oval shape)
    main_x = center
    main_y = center + int(8 * scale)
    main_rx = int(12 * scale)
    main_ry = int(10 * scale)
    draw.ellipse([
        main_x - main_rx, main_y - main_ry,
        main_x + main_rx, main_y + main_ry
    ], fill=fg_color)

    # Toe pads (top, smaller circles)
    toe_positions = [
        (center - int(12 * scale), center - int(8 * scale)),   # Left toe
        (center, center - int(14 * scale)),                     # Middle toe
        (center + int(12 * scale), center - int(8 * scale)),   # Right toe
    ]
    toe_radius = int(6 * scale)

    for tx, ty in toe_positions:
        draw.ellipse([
            tx - toe_radius, ty - toe_radius,
            tx + toe_radius, ty + toe_radius
        ], fill=fg_color)

def create_icon():
    """Create multi-resolution ICO file."""
    # Colorblind-friendly colors
    # Deep blue background - visible to all color vision types
    bg_color = (0x15, 0x65, 0xC0)  # #1565C0
    # Bright orange foreground - high contrast with blue
    fg_color = (0xFF, 0x6D, 0x00)  # #FF6D00

    # Standard ICO sizes
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = []

    for size in sizes:
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw_paw(draw, size, bg_color, fg_color)
        images.append(img)

    # Save as ICO
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ico_path = os.path.join(script_dir, 'pawgate.ico')

    # Save with all sizes
    images[0].save(
        ico_path,
        format='ICO',
        sizes=[(s, s) for s in sizes],
        append_images=images[1:]
    )

    print(f"Icon saved to: {ico_path}")

    # Also save a PNG for reference
    png_path = os.path.join(script_dir, 'pawgate.png')
    images[-1].save(png_path, format='PNG')
    print(f"PNG saved to: {png_path}")

if __name__ == '__main__':
    create_icon()
