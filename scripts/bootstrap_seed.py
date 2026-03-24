import asyncio

from seed import seed


if __name__ == "__main__":
    asyncio.run(seed())
    print("Seed bootstrap complete")
