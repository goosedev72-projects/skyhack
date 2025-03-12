import aiohttp
from user_agent import generate_user_agent
from utils import api_variables as api


class SkysmartAPIClient:
    """
    Клиент и методы для скайсамсы
    """

    def __init__(self):
        """
        Инициализация
        """
        self.session = aiohttp.ClientSession()
        self.token = ''
        self.user_agent = generate_user_agent()

    async def close(self):
        """
        Аиохттп закрывается 🔐
        """
        await self.session.close()

    async def _authenticate(self):
        """
        Входим в API и получаем JWT
        """
        headers = {
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'User-Agent': self.user_agent
        }
        async with self.session.post(api.url_auth2, headers=headers) as resp:
            if resp.status == 200:
                json_resp = await resp.json()
                self.token = json_resp["jwtToken"]
            else:
                raise Exception(f"😅 Не вошли со статусом {resp.status}")

    async def _get_headers(self):
        """
        Получаем заголовок с JWT

        Получаешь:
            dict: Заголовки с JWT
        """
        if not self.token:
            await self._authenticate()
        return {
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'User-Agent': self.user_agent,
            'Accept': 'application/json, text/plain, */*',
            'Authorization': f'Bearer {self.token}'
        }

    async def get_room(self, task_hash):
        """
        Получаем UUID задачек

        Передаешь:
            task_hash (str): Хэш задачки

        Получаешь:
            list: Список UUID-шек
        """
        payload = {"taskHash": task_hash}
        headers = await self._get_headers()
        async with self.session.post(api.url_room, headers=headers, json=payload) as resp:
            if resp.status == 200:
                json_resp = await resp.json()
                return json_resp['meta']['stepUuids']
            else:
                raise Exception(f"😅 Получение информации о комнате свалилось с ошибкой {resp.status}")

    async def get_meta(self, task_hash):
        """
        Получаем метаданные

        Передаешь:
            task_hash (str): ИД хеша

        Получаешь:
            tuple: заголовок?
        """
        payload = {"taskHash": task_hash}
        headers = await self._get_headers()
        async with self.session.post(api.url_room, headers=headers, json=payload) as resp:
            if resp.status == 200:
                json_resp = await resp.json()
                title = json_resp["title"]
                module_title = json_resp["meta"]["path"]["module"]["title"]
                return title, module_title
            else:
                raise Exception(f"😅 Получение метаданных свалилось с ошибкой {resp.status}")

    async def get_task_html(self, uuid):
        """
        Получаем HTML задачки по UUID

        Передаешь:
            uuid (str): UUID задачки

        Получаешь:
            str: HTML контент задачки
        """
        headers = await self._get_headers()
        async with self.session.get(f"{api.url_steps}{uuid}", headers=headers) as resp:
            if resp.status == 200:
                json_resp = await resp.json()
                return json_resp['content']
            else:
                raise Exception(f"😅 Получение HTML кодв задания свалилось с ошибкой {resp.status}")

    async def get_room_info(self, task_hash):
        """
        Получаем информацию о комнате

        Передаешь:
            task_hash (str): Идентификатор хеша

        Получаешь:
            dict: JSON с инфой
        """
        payload = {"taskHash": task_hash}
        headers = await self._get_headers()
        async with self.session.post(api.url_room_preview, headers=headers, json=payload) as resp:
            if resp.status == 200:
                json_resp = await resp.json()
                return json_resp
            else:
                raise Exception(f"😅 Получение информации о комнате свалилось с ошибкой {resp.status}")
