#!/usr/bin/env python3
"""
fetch_image.py — Zebronics Soundbar Finder
Fetches the main product image URL from Amazon, Flipkart, or Zebronics.

Usage:
    python fetch_image.py <url>
    python fetch_image.py <product_id>     (looks up in products.json)
    python fetch_image.py --all            (fills all missing images in products.json)

Examples:
    python fetch_image.py https://www.amazon.in/dp/B0GDVL68HW
    python fetch_image.py https://shop.zebronics.com/products/zeb-juke-bar-9580c
    python fetch_image.py jukebar_9580c
    python fetch_image.py --all
"""

import sys
import json
import re
import urllib.request
import urllib.parse
from pathlib import Path

PRODUCTS_FILE = Path(__file__).parent / 'products.json'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-IN,en;q=0.9',
}


def fetch(url, timeout=10):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode('utf-8', errors='replace')
    except Exception as e:
        return None


def extract_image_amazon(html, asin):
    """Extract main product image from Amazon product page."""
    # Method 1: JSON data in page (most reliable)
    m = re.search(r'"large"\s*:\s*"(https://m\.media-amazon\.com/images/I/[^"]+)"', html)
    if m:
        return m.group(1).split('._')[0] + '._SL600_.jpg'

    # Method 2: data-old-hires attribute
    m = re.search(r'data-old-hires="(https://[^"]+)"', html)
    if m:
        return m.group(1)

    # Method 3: landingImageUrl
    m = re.search(r'"landingImageUrl"\s*:\s*"(https://[^"]+)"', html)
    if m:
        url = m.group(1).replace('\\u0026', '&')
        return url.split('._')[0] + '._SL600_.jpg'

    # Method 4: og:image
    m = re.search(r'property="og:image"\s+content="([^"]+)"', html)
    if m:
        return m.group(1)

    # Method 5: standard Amazon CDN image pattern
    m = re.search(r'(https://m\.media-amazon\.com/images/I/[A-Za-z0-9%+]+)\.', html)
    if m:
        return m.group(1) + '._SL600_.jpg'

    return None


def extract_image_flipkart(html):
    """Extract main product image from Flipkart product page."""
    # Method 1: og:image
    m = re.search(r'property="og:image"\s+content="([^"]+)"', html)
    if m:
        return m.group(1)

    # Method 2: JSON-LD
    m = re.search(r'"image"\s*:\s*"(https://[^"]+rukmini[^"]+)"', html)
    if m:
        return m.group(1)

    # Method 3: src in img tags with rukmini CDN
    m = re.search(r'src="(https://rukminim[^"]+)"', html)
    if m:
        url = m.group(1)
        # Get the larger version
        url = re.sub(r'/\d+/\d+/', '/600/600/', url)
        return url

    return None


def extract_image_zebronics(html, url):
    """Extract main product image from Zebronics shop page."""
    # Method 1: shop.zebronics.com CDN pattern
    m = re.search(
        r'(https://shop\.zebronics\.com/cdn/shop/(?:files|products)/[^"\'?\s]+\.(?:jpg|jpeg|png|webp))',
        html
    )
    if m:
        img = m.group(1)
        # Ensure we get a good size
        if '?v=' in img:
            img = img.split('?v=')[0]
        return img + '?width=600'

    # Method 2: og:image
    m = re.search(r'property="og:image"\s+content="([^"]+)"', html)
    if m:
        return m.group(1)

    return None


def get_image_url(url):
    """Given a product URL, return the main image URL."""
    url = url.strip()
    if not url.startswith('http'):
        url = 'https://' + url

    print(f'  Fetching: {url}')
    html = fetch(url)

    if not html:
        print('  ❌ Could not fetch page')
        return None

    if 'amazon.in' in url or 'amazon.com' in url:
        asin_m = re.search(r'/dp/([A-Z0-9]{10})', url)
        asin = asin_m.group(1) if asin_m else None
        img = extract_image_amazon(html, asin)

    elif 'flipkart.com' in url:
        img = extract_image_flipkart(html)

    elif 'zebronics.com' in url or 'shop.zebronics.com' in url:
        img = extract_image_zebronics(html, url)

    else:
        # Try og:image as generic fallback
        m = re.search(r'property="og:image"\s+content="([^"]+)"', html)
        img = m.group(1) if m else None

    return img


def lookup_by_id(product_id):
    """Look up a product by id and return its buy URLs."""
    if not PRODUCTS_FILE.exists():
        return None
    with open(PRODUCTS_FILE) as f:
        products = json.load(f)
    for p in products:
        if p['id'] == product_id:
            return p
    return None


def update_product_image(product_id, img_url):
    """Update the img field for a product in products.json."""
    if not PRODUCTS_FILE.exists():
        print('❌ products.json not found')
        return
    with open(PRODUCTS_FILE) as f:
        products = json.load(f)
    updated = False
    for p in products:
        if p['id'] == product_id:
            p['img'] = img_url
            updated = True
            break
    if updated:
        with open(PRODUCTS_FILE, 'w') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
        print(f'  ✅ Updated products.json: {product_id} → {img_url[:60]}...')
    else:
        print(f'  ❌ Product {product_id} not found in products.json')


def run_all():
    """Fill all missing images in products.json."""
    if not PRODUCTS_FILE.exists():
        print('❌ products.json not found')
        return

    with open(PRODUCTS_FILE) as f:
        products = json.load(f)

    missing = [p for p in products if not p.get('img')]
    print(f'Found {len(missing)} products with missing images:\n')

    for p in missing:
        print(f"{'─'*50}")
        print(f"  Product: {p['name']} ({p['id']})")

        # Try Zebronics shop first (most reliable)
        img = None
        if p.get('zeb'):
            print(f"  Trying: {p['zeb']}")
            img = get_image_url(p['zeb'])

        # Try Amazon if Zebronics failed
        if not img and p.get('amz'):
            print(f"  Trying: {p['amz']}")
            img = get_image_url(p['amz'])

        # Try Flipkart if Amazon failed
        if not img and p.get('fk'):
            print(f"  Trying: {p['fk']}")
            img = get_image_url(p['fk'])

        if img:
            print(f"  ✅ Found: {img[:80]}")
            update_product_image(p['id'], img)
        else:
            print(f"  ⚠️  No image found — add manually to products.json")

        print()

    print('Done. Run: git add products.json && git commit -m "Add product images" && git push')


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    arg = sys.argv[1]

    # --all mode: fill all missing images
    if arg == '--all':
        run_all()
        return

    # Check if it looks like a product id (no slashes, no dots)
    if '/' not in arg and '.' not in arg:
        product = lookup_by_id(arg)
        if not product:
            print(f'❌ Product "{arg}" not found in products.json')
            sys.exit(1)

        print(f'\nProduct: {product["name"]} ({product["id"]})')
        print(f'Current image: {product.get("img") or "(none)"}')
        print()

        # Try each platform
        for label, url_key in [('Zebronics', 'zeb'), ('Amazon', 'amz'), ('Flipkart', 'fk')]:
            url = product.get(url_key)
            if not url:
                continue
            print(f'Trying {label}...')
            img = get_image_url(url)
            if img:
                print(f'\n✅ Image found:\n   {img}')
                answer = input('\nUpdate products.json with this URL? [y/n]: ').strip().lower()
                if answer == 'y':
                    update_product_image(arg, img)
                    print('\nNow run:')
                    print('  git add products.json')
                    print('  git commit -m "Add image for ' + product["name"] + '"')
                    print('  git push origin main')
                return

        print('❌ No image found on any platform. Add manually to products.json:')
        print(f'   Find the product on shop.zebronics.com or amazon.in')
        print(f'   Right-click the main image → Copy Image Address')
        print(f'   Paste it as the "img" value for "{arg}" in products.json')

    else:
        # It's a URL
        print(f'\nFetching image from: {arg}')
        img = get_image_url(arg)

        if img:
            print(f'\n✅ Image URL:\n   {img}')
            print('\nTo add to products.json:')
            print('  Open products.json → find your product → paste as the "img" value')
        else:
            print('\n❌ Could not extract image URL.')
            print('   Try: right-click the product image on the website → Copy Image Address')


if __name__ == '__main__':
    main()
