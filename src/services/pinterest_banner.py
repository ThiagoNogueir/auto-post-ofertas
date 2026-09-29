"""
Pinterest Banner Generator
Generates clean, high-converting, professional Pinterest Pins (1000x1500 px, 2:3 aspect ratio)
for deals without AI artifacts, using PIL (Pillow).
"""

import os
import io
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def get_font(size: int, bold: bool = True):
    """Load system font with cross-platform fallback"""
    font_names = [
        "segoeuib.ttf" if bold else "segoeui.ttf",
        "arialbd.ttf" if bold else "arial.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "LiberationSans-Bold.ttf" if bold else "LiberationSans-Regular.ttf"
    ]
    
    # Check Windows Fonts
    win_dir = os.environ.get("WINDIR", "C:\\Windows")
    for name in font_names:
        p = os.path.join(win_dir, "Fonts", name)
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
                
    # Check Linux standard fonts
    linux_paths = [
        "/usr/share/fonts/truetype/dejavu/",
        "/usr/share/fonts/truetype/liberation/",
        "/usr/share/fonts/truetype/freefont/"
    ]
    for lp in linux_paths:
        for name in font_names:
            p = os.path.join(lp, name)
            if os.path.exists(p):
                try:
                    return ImageFont.truetype(p, size)
                except Exception:
                    pass

    return ImageFont.load_default()


def create_pinterest_pin(
    title: str,
    price: float,
    old_price: float = None,
    image_url: str = None,
    category: str = "Achadinhos",
    store: str = "Mercado Livre",
    coupon_code: str = None,
    output_path: str = None
) -> Image.Image:
    """
    Generates a 1000x1500 high-converting Pinterest Pin graphic.
    """
    WIDTH, HEIGHT = 1000, 1500
    
    # 1. Base Canvas (Subtle luxury gradient: Soft Off-White / Cream)
    base = Image.new("RGBA", (WIDTH, HEIGHT), (248, 249, 251, 255))
    draw = ImageDraw.Draw(base)
    
    # Gradient background
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(255 * (1 - ratio) + 242 * ratio)
        g = int(255 * (1 - ratio) + 245 * ratio)
        b = int(255 * (1 - ratio) + 248 * ratio)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b, 255))

    # 2. Top Header (Store Badge + Category Tag)
    # Store branding colors
    store_lower = store.lower()
    if "shopee" in store_lower:
        brand_color = (238, 77, 45, 255) # Shopee Orange
        store_display = "SHOPEE OFERTAS"
    else:
        brand_color = (255, 180, 0, 255) # ML Yellow/Gold
        store_display = "MERCADO LIVRE"
    
    # Header bar
    header_font = get_font(26, bold=True)
    cat_font = get_font(24, bold=True)
    
    # Top Tag
    tag_text = f"ACHADINHO EM OFERTA  •  {category.upper()}"
    tag_bbox = draw.textbbox((0, 0), tag_text, font=cat_font)
    tag_w = tag_bbox[2] - tag_bbox[0]
    tag_x = (WIDTH - tag_w) // 2
    
    # Pill background for top tag
    pill_pad_x = 24
    pill_pad_y = 12
    draw.rounded_rectangle(
        [(tag_x - pill_pad_x, 45 - pill_pad_y), (tag_x + tag_w + pill_pad_x, 45 + 32 + pill_pad_y)],
        radius=25,
        fill=(235, 40, 40, 240)
    )
    draw.text((tag_x, 47), tag_text, fill=(255, 255, 255, 255), font=cat_font)

    # 3. Product Container Card with Soft Shadow
    card_x0, card_y0 = 60, 130
    card_x1, card_y1 = WIDTH - 60, 890
    card_radius = 36
    
    # Drop shadow
    shadow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.rounded_rectangle(
        [(card_x0 - 4, card_y0 + 10), (card_x1 + 4, card_y1 + 18)],
        radius=card_radius + 4,
        fill=(0, 0, 0, 35)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(14))
    base = Image.alpha_composite(base, shadow)
    draw = ImageDraw.Draw(base)
    
    # Main White Card
    draw.rounded_rectangle([(card_x0, card_y0), (card_x1, card_y1)], radius=card_radius, fill=(255, 255, 255, 255))
    draw.rounded_rectangle([(card_x0, card_y0), (card_x1, card_y1)], radius=card_radius, outline=(225, 230, 238, 255), width=2)

    # 4. Insert & Scale Real Product Image
    if image_url:
        try:
            resp = requests.get(image_url, timeout=10)
            if resp.status_code == 200:
                p_img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
                
                # Fit inside card area (max 720 x 700)
                max_w, max_h = 720, 680
                p_img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
                
                # Center product inside card
                px = card_x0 + (card_x1 - card_x0 - p_img.width) // 2
                py = card_y0 + (card_y1 - card_y0 - p_img.height) // 2
                
                # Composite
                base.alpha_composite(p_img, (px, py))
        except Exception as e:
            pass

    # 5. Discount Floating Badge (% OFF)
    discount_pct = 0
    if old_price and old_price > price:
        discount_pct = int(round(((old_price - price) / old_price) * 100))
    
    if discount_pct >= 5:
        badge_text = f"-{discount_pct}%"
        sub_badge = "OFF"
        b_font = get_font(46, bold=True)
        s_font = get_font(24, bold=True)
        
        bx0, by0 = card_x0 + 30, card_y0 + 30
        bx1, by1 = bx0 + 150, by0 + 85
        
        # Badge Shadow
        draw.rounded_rectangle([(bx0 + 2, by0 + 4), (bx1 + 2, by1 + 4)], radius=20, fill=(0, 0, 0, 40))
        # Badge Body (Gradient red/coral)
        draw.rounded_rectangle([(bx0, by0), (bx1, by1)], radius=20, fill=(235, 35, 45, 255))
        
        draw.text((bx0 + 16, by0 + 10), badge_text, fill=(255, 255, 255, 255), font=b_font)
        draw.text((bx0 + 95, by0 + 46), sub_badge, fill=(255, 240, 240, 255), font=s_font)

    # 6. Store Badge inside Card (Top-right)
    store_font = get_font(22, bold=True)
    sb_bbox = draw.textbbox((0, 0), store_display, font=store_font)
    sb_w = sb_bbox[2] - sb_bbox[0]
    sb_x1 = card_x1 - 30
    sb_x0 = sb_x1 - sb_w - 24
    draw.rounded_rectangle([(sb_x0, card_y0 + 30), (sb_x1, card_y0 + 72)], radius=16, fill=(245, 247, 250, 255), outline=(215, 220, 230, 255), width=1)
    draw.text((sb_x0 + 12, card_y0 + 39), store_display, fill=(60, 64, 75, 255), font=store_font)

    # 7. Bottom Section (Product Title, Prices, Trust Badges, CTA)
    title_font = get_font(38, bold=True)
    
    # Word wrap title to 2 lines
    words = title.split()
    lines = []
    curr_line = ""
    for w in words:
        test_line = f"{curr_line} {w}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=title_font)
        if bbox[2] - bbox[0] < WIDTH - 140:
            curr_line = test_line
        else:
            lines.append(curr_line)
            curr_line = w
            if len(lines) == 2:
                break
    if curr_line and len(lines) < 2:
        lines.append(curr_line)
    elif len(lines) == 2 and curr_line:
        lines[1] = lines[1] + "..."
        
    ty = 925
    for l in lines:
        draw.text((70, ty), l, fill=(25, 28, 36, 255), font=title_font)
        ty += 52

    # 8. Price Display Area
    py = max(ty + 15, 1050)
    
    # Old Price
    if old_price and old_price > price:
        old_font = get_font(30, bold=False)
        old_text = f"De: R$ {old_price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        draw.text((70, py), old_text, fill=(130, 138, 150, 255), font=old_font)
        
        # Strikethrough line
        old_bbox = draw.textbbox((70, py), old_text, font=old_font)
        draw.line([(old_bbox[0], py + 18), (old_bbox[2], py + 18)], fill=(220, 50, 50, 255), width=3)
        py += 44

    # Promo Price (Huge & Impactful)
    price_label_font = get_font(32, bold=True)
    price_val_font = get_font(68, bold=True)
    
    draw.text((70, py + 22), "Por:", fill=(25, 28, 36, 255), font=price_label_font)
    
    price_text = f"R$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    draw.text((145, py), price_text, fill=(0, 150, 64, 255), font=price_val_font)
    
    # Extra Tag (e.g. Cupom or Frete Gratis)
    tag_y = py + 95
    trust_font = get_font(22, bold=True)
    
    # Pill 1: Frete Grátis
    draw.rounded_rectangle([(70, tag_y), (250, tag_y + 44)], radius=12, fill=(235, 248, 240, 255), outline=(180, 230, 195, 255), width=1)
    draw.text((95, tag_y + 9), "FRETE GRÁTIS", fill=(0, 135, 60, 255), font=trust_font)
    
    # Pill 2: Cupom if available
    if coupon_code:
        c_text = f"CUPOM: {coupon_code}"
        c_bbox = draw.textbbox((0, 0), c_text, font=trust_font)
        cw = c_bbox[2] - c_bbox[0]
        draw.rounded_rectangle([(265, tag_y), (265 + cw + 28, tag_y + 44)], radius=12, fill=(255, 248, 225, 255), outline=(245, 215, 120, 255), width=1)
        draw.text((279, tag_y + 9), c_text, fill=(180, 110, 0, 255), font=trust_font)

    # 9. Big CTA Button at the Bottom
    btn_x0, btn_y0 = 70, HEIGHT - 170
    btn_x1, btn_y1 = WIDTH - 70, HEIGHT - 75
    btn_radius = 45
    
    # Button shadow
    b_shadow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    bsdraw = ImageDraw.Draw(b_shadow)
    bsdraw.rounded_rectangle([(btn_x0, btn_y0 + 6), (btn_x1, btn_y1 + 10)], radius=btn_radius, fill=(230, 0, 35, 70))
    b_shadow = b_shadow.filter(ImageFilter.GaussianBlur(10))
    base = Image.alpha_composite(base, b_shadow)
    draw = ImageDraw.Draw(base)
    
    # Vibrant CTA Button (Pinterest Red / Coral #E60023)
    draw.rounded_rectangle([(btn_x0, btn_y0), (btn_x1, btn_y1)], radius=btn_radius, fill=(230, 0, 35, 255))
    
    cta_font = get_font(36, bold=True)
    cta_text = "VER OFERTA NO SITE  >"
    cbbox = draw.textbbox((0, 0), cta_text, font=cta_font)
    cw = cbbox[2] - cbbox[0]
    cx = (WIDTH - cw) // 2
    draw.text((cx, btn_y0 + 26), cta_text, fill=(255, 255, 255, 255), font=cta_font)

    # Save if requested
    if output_path:
        base.save(output_path, "PNG", quality=95)
        
    return base
