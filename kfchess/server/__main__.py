import asyncio

from kfchess.server.server import serve

if __name__ == "__main__":
    asyncio.run(serve())
