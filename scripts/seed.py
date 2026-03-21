"""Seed the database with well-known San Diego restaurants.

Idempotent — skips places that already exist by normalized name.
Run: python -m scripts.seed
"""

import asyncio

import asyncpg

from tastebud.config import get_settings
from tastebud.services.normalizer import normalize_city, normalize_name

SEED_PLACES = [
    # (name, city, neighborhood, cuisine_tags)
    ("Sab E Lee", "San Diego", "North Park", ["thai"]),
    ("Supannee House", "San Diego", "Kearny Mesa", ["thai"]),
    ("Tajima Ramen", "San Diego", "Hillcrest", ["japanese", "ramen"]),
    ("Underbelly", "San Diego", "Little Italy", ["japanese", "ramen"]),
    ("Tacos El Gordo", "San Diego", "Chula Vista", ["mexican", "tacos"]),
    ("Lolita's Mexican Food", "San Diego", "Kearny Mesa", ["mexican"]),
    ("Vallarta Express", "San Diego", "Barrio Logan", ["mexican", "tacos"]),
    ("Convoy Tofu House", "San Diego", "Kearny Mesa", ["korean"]),
    ("Friend's House", "San Diego", "Kearny Mesa", ["korean", "bbq"]),
    ("Dumpling Inn", "San Diego", "Kearny Mesa", ["chinese", "dumplings"]),
    ("Din Tai Fung", "San Diego", "UTC", ["chinese", "dumplings"]),
    ("Crack Shack", "San Diego", "Little Italy", ["american", "chicken"]),
    ("Hodad's", "San Diego", "Ocean Beach", ["american", "burgers"]),
    ("Rocky's Crown Pub", "San Diego", "Pacific Beach", ["american", "burgers"]),
    ("Phil's BBQ", "San Diego", "Point Loma", ["bbq"]),
    ("Bali Hai", "San Diego", "Point Loma", ["tiki", "seafood"]),
    ("Ironside Fish & Oyster", "San Diego", "Little Italy", ["seafood"]),
    ("Juniper & Ivy", "San Diego", "Little Italy", ["american", "fine dining"]),
    ("Addison", "San Diego", "Del Mar", ["french", "fine dining"]),
    ("Cucina Urbana", "San Diego", "Bankers Hill", ["italian"]),
    ("Bencotto", "San Diego", "Little Italy", ["italian", "pasta"]),
    ("Extraordinary Desserts", "San Diego", "Bankers Hill", ["dessert", "cafe"]),
    ("Better Buzz Coffee", "San Diego", "Pacific Beach", ["coffee"]),
    ("Bird Rock Coffee Roasters", "San Diego", "La Jolla", ["coffee"]),
    ("Cross Street Chicken and Beer", "San Diego", "Kearny Mesa", ["korean", "chicken"]),
    ("Pho Hoa", "San Diego", "City Heights", ["vietnamese", "pho"]),
    ("Shabu Shabu House", "San Diego", "Kearny Mesa", ["japanese", "hot pot"]),
    ("The Taco Stand", "San Diego", "La Jolla", ["mexican", "tacos"]),
    ("Werewolf", "San Diego", "Gaslamp", ["american", "brunch"]),
    ("Morning Glory", "San Diego", "Little Italy", ["american", "brunch"]),
    ("Herb & Wood", "San Diego", "Little Italy", ["american", "mediterranean"]),
    ("Civico 1845", "San Diego", "Little Italy", ["italian"]),
    ("Puesto", "San Diego", "La Jolla", ["mexican", "tacos"]),
    ("Akinori Sushi", "San Diego", "Kearny Mesa", ["japanese", "sushi"]),
    ("Sushi Ota", "San Diego", "Pacific Beach", ["japanese", "sushi"]),
    ("Oscar's Mexican Seafood", "San Diego", "Hillcrest", ["mexican", "seafood"]),
    ("Lucha Libre Taco Shop", "San Diego", "Mission Hills", ["mexican", "tacos"]),
    ("Mike's Taco Club", "San Diego", "Ocean Beach", ["mexican", "tacos"]),
    ("OB Noodle House", "San Diego", "Ocean Beach", ["asian", "noodles"]),
    ("Mama's Bakery", "San Diego", "Normal Heights", ["lebanese", "bakery"]),
]


async def seed() -> None:
    """Insert seed places, skipping duplicates."""
    conn = await asyncpg.connect(dsn=get_settings().database_url)

    inserted = 0
    skipped = 0

    for name, city, neighborhood, tags in SEED_PLACES:
        normalized = normalize_name(name)
        city_norm = normalize_city(city)

        exists = await conn.fetchval(
            "SELECT 1 FROM places WHERE name_normalized = $1 AND city = $2",
            normalized,
            city_norm,
        )

        if exists:
            skipped += 1
            continue

        await conn.execute(
            """
            INSERT INTO places (canonical_name, name_normalized, city, neighborhood, cuisine_tags)
            VALUES ($1, $2, $3, $4, $5)
            """,
            name,
            normalized,
            city_norm,
            neighborhood,
            tags,
        )
        inserted += 1

    await conn.close()
    print(f"Seed complete: {inserted} inserted, {skipped} skipped (already exist)")


if __name__ == "__main__":
    asyncio.run(seed())
