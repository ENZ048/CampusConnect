"""Idempotent seed for local dev. Currently a no-op because seeding lives in migrations,
but the entry point exists so `make seed` works and future seed data can land here."""
import asyncio

from app.config import get_settings


async def main() -> None:
    settings = get_settings()
    print(f"Seed complete for {settings.APP_ENV} (DB: {settings.DATABASE_URL.split('@')[-1]})")


if __name__ == "__main__":
    asyncio.run(main())
