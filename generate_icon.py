"""
Generate PawGate icon - clean, minimal paw print with lock indicator.
Optimized for system tray visibility (16x16 up to 256x256).
"""
from PIL import Image, ImageDraw
import math


def draw_paw_print(draw, cx, cy, size, color):
    """Draw a cat paw print centered at (cx, cy). BOLD version for visibility."""
    # Main pad (large oval at bottom) - BIGGER
    pad_w = size * 0.55
    pad_h = size * 0.42
    pad_y = cy + size * 0.12
    draw.ellipse(
        [cx - pad_w/2, pad_y - pad_h/2, cx + pad_w/2, pad_y + pad_h/2],
        fill=color
    )

    # Toe beans (4 circles above the main pad) - BIGGER and BOLDER
    toe_radius = size * 0.16
    toe_y_base = cy - size * 0.22
    toe_positions = [
        (cx - size * 0.26, toe_y_base + size * 0.06),   # Left outer
        (cx - size * 0.09, toe_y_base - size * 0.06),   # Left inner
        (cx + size * 0.09, toe_y_base - size * 0.06),   # Right inner
        (cx + size * 0.26, toe_y_base + size * 0.06),   # Right outer
    ]

    for tx, ty in toe_positions:
        draw.ellipse(
            [tx - toe_radius, ty - toe_radius, tx + toe_radius, ty + toe_radius],
            fill=color
        )


def draw_lock_badge(draw, cx, cy, size, bg_color, fg_color):
    """Draw a small lock icon."""
    # Lock body (rounded rectangle)
    body_w = size * 0.6
    body_h = size * 0.5
    body_top = cy + size * 0.1

    draw.rounded_rectangle(
        [cx - body_w/2, body_top, cx + body_w/2, body_top + body_h],
        radius=size * 0.08,
        fill=fg_color
    )

    # Lock shackle (arc at top)
    shackle_w = size * 0.35
    shackle_h = size * 0.35
    shackle_thickness = size * 0.12

    # Outer arc
    draw.arc(
        [cx - shackle_w/2, body_top - shackle_h, cx + shackle_w/2, body_top + shackle_h * 0.3],
        start=180, end=0,
        fill=fg_color,
        width=int(shackle_thickness)
    )

    # Keyhole (small circle + triangle)
    keyhole_y = body_top + body_h * 0.35
    keyhole_r = size * 0.08
    draw.ellipse(
        [cx - keyhole_r, keyhole_y - keyhole_r, cx + keyhole_r, keyhole_y + keyhole_r],
        fill=bg_color
    )
    # Keyhole slot
    draw.polygon(
        [(cx - keyhole_r * 0.6, keyhole_y),
         (cx + keyhole_r * 0.6, keyhole_y),
         (cx, keyhole_y + size * 0.15)],
        fill=bg_color
    )


def create_icon(size):
    """Create a single icon at the specified size."""
    # Use RGBA for transparency
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Colors - MORRIS THE CAT orange, high visibility
    paw_color = (255, 140, 50)     # Bright orange tabby - Morris the Cat
    lock_color = (0, 90, 180)      # Deep blue - high contrast against orange
    lock_bg = (255, 255, 255)      # White keyhole

    # Calculate positions - FILL MORE OF THE CANVAS
    center = size / 2
    paw_size = size * 0.95  # Bigger paw

    # Draw paw print (centered, fills the space)
    paw_cx = center
    paw_cy = center - size * 0.02
    draw_paw_print(draw, paw_cx, paw_cy, paw_size, paw_color)

    # Draw lock badge in bottom-right - BIGGER and BOLDER
    if size >= 32:
        lock_size = size * 0.45  # Bigger lock
        lock_cx = center + size * 0.30
        lock_cy = center + size * 0.28
        draw_lock_badge(draw, lock_cx, lock_cy, lock_size, lock_bg, lock_color)
    elif size >= 16:
        # For tiny sizes, bright blue dot - still visible
        dot_r = size * 0.18
        dot_cx = center + size * 0.28
        dot_cy = center + size * 0.28
        draw.ellipse(
            [dot_cx - dot_r, dot_cy - dot_r, dot_cx + dot_r, dot_cy + dot_r],
            fill=lock_color
        )

    return img


def main():
    # Standard Windows icon sizes - most important for system tray and taskbar
    sizes = [16, 32, 48, 256]

    # Generate all sizes
    images = []
    for s in sizes:
        img = create_icon(s)
        # Convert to proper format for ICO embedding
        images.append(img)

    # Save as ICO with proper multi-size embedding
    # The largest image saves, others are appended
    icon_path = 'resources/img/icon.ico'
    images[-1].save(
        icon_path,
        format='ICO',
        append_images=images[:-1],
        sizes=[(s, s) for s in sizes]
    )

    # Verify the ICO file
    import os
    ico_size = os.path.getsize(icon_path)
    print(f"Created icon.ico ({ico_size:,} bytes) with sizes: {sizes}")

    # Save 256px PNG for other uses (README, etc.)
    images[-1].save('resources/img/icon.png', format='PNG', optimize=True)
    png_size = os.path.getsize('resources/img/icon.png')
    print(f"Created icon.png (256x256, {png_size:,} bytes)")

    # Clean up preview file if it exists
    preview_path = 'resources/img/icon_preview.png'
    if os.path.exists(preview_path):
        os.remove(preview_path)


if __name__ == '__main__':
    main()
