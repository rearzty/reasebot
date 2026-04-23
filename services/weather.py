import aiohttp
from config import settings


async def get_weather(city: str) -> dict | None:
    params = {
        'appid': settings.weather_api_key,
        'q': city,
        'units': 'metric',
        'lang': 'ru'
    }
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.openweathermap.org/data/2.5/weather", params=params) as response:
            if response.status == 200:
                return await response.json()
            return None
