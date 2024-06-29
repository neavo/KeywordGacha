import asyncio
from extractor import CharacterNameExtractor


async def main():
    extractor = await CharacterNameExtractor.create()
    await extractor.process()


if __name__ == "__main__":
    asyncio.run(main())