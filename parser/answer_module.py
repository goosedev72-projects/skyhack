"""
Module for extracting answers from Skysmart tasks.
"""

import asyncio
import base64
import re

from bs4 import BeautifulSoup
from sky_api.skysmart_api import SkysmartAPIClient


def remove_extra_newlines(text: str) -> str:
    """
    Убираем лишные символы newline.

    Даешь:
        text (str): текст

    Получаешь:
        str: Текст без newline-ов
    """
    return re.sub(r'\n+', '\n', text.strip())


class SkyAnswers:
    """
    Получаем и парсим ответы

    Атрибуты:
        task_hash (str): Хэш задания
    """

    def __init__(self, task_hash: str):
        """
        Инициализация

        Передаешь:
            task_hash (str): Хэш задания
        """
        self.task_hash = task_hash

    async def get_answers(self):
        """
        Собираем все связанное с хешем

        Получаешь:
            list: Твои ответы для перепроверки, не списывай 😡
        """
        answers_list = []
        client = SkysmartAPIClient()

        try:
            tasks_uuids = await client.get_room(self.task_hash)

            # Собираем урожай
            tasks_html_coroutines = [client.get_task_html(uuid) for uuid in tasks_uuids]
            tasks_html_list = await asyncio.gather(*tasks_html_coroutines, return_exceptions=True)

            for idx, task_html in enumerate(tasks_html_list):
                if isinstance(task_html, Exception):
                    print(f"🥲 Не парсится HTML для задания с UUID {tasks_uuids[idx]}: {task_html}")
                    continue
                soup = BeautifulSoup(task_html, 'html.parser')
                task_answer = self._get_task_answer(soup, idx + 1)
                answers_list.append(task_answer)
        except Exception as e:
            print(f"🥲 Получение ответов свалилось с ошибкой {e}")
        finally:
            await client.close()

        return answers_list

    async def get_room_info(self):
        """
        Получаем информацию о комнате с хешем задания

        Получаем:
            dict: JSON с информацией
        """
        client = SkysmartAPIClient()
        try:
            room_info = await client.get_room_info(self.task_hash)
            return room_info
        except Exception as e:
            print(f"🥲 Считывание комнаты свалилось с ошибкой {e}")
            return None
        finally:
            await client.close()

    @staticmethod
    def _extract_task_question(soup):
        """
        Вытаскиваем сам вопрос

        Передаешь:
            soup (BeautifulSoup): Красивый супчик 4

        Получаешь:
            str: Сам вопрос
        """
        instruction = soup.find("vim-instruction")
        return instruction.text.strip() if instruction else ""

    @staticmethod
    def _extract_task_full_question(soup):
        """
        Полный текст задания

        Args:
            soup (BeautifulSoup): Супчик

        Returns:
            str: Полное задание
        """
        elements_to_exclude = [
            'vim-instruction', 'vim-groups', 'vim-test-item',
            'vim-order-sentence-verify-item', 'vim-input-answers',
            'vim-select-item', 'vim-test-image-item', 'math-input-answer',
            'vim-dnd-text-drop', 'vim-dnd-group-drag', 'vim-groups-row',
            'vim-strike-out-item', 'vim-dnd-image-set-drag',
            'vim-dnd-image-drag', 'edu-open-answer'
        ]
        for element in soup.find_all(elements_to_exclude):
            element.decompose()
        return remove_extra_newlines(soup.get_text())

    def _get_task_answer(self, soup, task_number):
        """
        Парсим супчик

        Передаешь:
            soup (BeautifulSoup): Задание из супчика
            task_number (int): Номер задания

        Получаешь:
            dict: Все решение и само задание
        """
        answers = []

        # Много правильных вариантов
        for item in soup.find_all('vim-test-item', attrs={'correct': 'true'}):
            answers.append(item.get_text())

        # Порядок в мыслях
        for item in soup.find_all('vim-order-sentence-verify-item'):
            answers.append(item.get_text())

        # Ввод
        for input_answer in soup.find_all('vim-input-answers'):
            input_item = input_answer.find('vim-input-item')
            if input_item:
                answers.append(input_item.get_text())

        # Выбираем
        for select_item in soup.find_all('vim-select-item', attrs={'correct': 'true'}):
            answers.append(select_item.get_text())

        # Тестируем изображения
        for image_item in soup.find_all('vim-test-image-item', attrs={'correct': 'true'}):
            answers.append(f"{image_item.get_text()} - верно")

        # Математика 🥵
        for math_answer in soup.find_all('math-input-answer'):
            answers.append(math_answer.get_text())

        # Перетяни текст
        for drop in soup.find_all('vim-dnd-text-drop'):
            drag_ids = drop.get('drag-ids', '').split(',')
            for drag_id in drag_ids:
                drag = soup.find('vim-dnd-text-drag', attrs={'answer-id': drag_id})
                if drag:
                    answers.append(drag.get_text())

        # Перетяни группы
        for drag_group in soup.find_all('vim-dnd-group-drag'):
            answer_id = drag_group.get('answer-id')
            for group_item in soup.find_all('vim-dnd-group-item'):
                drag_ids = group_item.get('drag-ids', '').split(',')
                if answer_id in drag_ids:
                    answers.append(f"{group_item.get_text()} - {drag_group.get_text()}")

        # Ряды групп
        for group_row in soup.find_all('vim-groups-row'):
            for group_item in group_row.find_all('vim-groups-item'):
                encoded_text = group_item.get('text')
                if encoded_text:
                    try:
                        decoded_text = base64.b64decode(encoded_text).decode('utf-8')
                        answers.append(decoded_text)
                    except Exception as e:
                        print(f"🥲 Декодер Base64 свалился с ошибкой {e}")

        # СТРАЙК! 🎳
        for striked_item in soup.find_all('vim-strike-out-item', attrs={'striked': 'true'}):
            answers.append(striked_item.get_text())

        # Перетяни картинки
        for image_drag in soup.find_all('vim-dnd-image-set-drag'):
            answer_id = image_drag.get('answer-id')
            for image_drop in soup.find_all('vim-dnd-image-set-drop'):
                drag_ids = image_drop.get('drag-ids', '').split(',')
                if answer_id in drag_ids:
                    answers.append(f"{image_drop.get('image')} - {image_drag.get_text()}")

        # Перетяни изображения
        for image_drag in soup.find_all('vim-dnd-image-drag'):
            answer_id = image_drag.get('answer-id')
            for image_drop in soup.find_all('vim-dnd-image-drop'):
                drag_ids = image_drop.get('drag-ids', '').split(',')
                if answer_id in drag_ids:
                    answers.append(f"{image_drop.get_text()} - {image_drag.get_text()}")

        # Самое сложное
        if soup.find('edu-open-answer', attrs={'id': 'OA1'}):
            answers.append('🥲 Нужно загрузить файл, самостоятельно')

        return {
            'question': self._extract_task_question(soup),
            'full_question': self._extract_task_full_question(soup),
            'answers': answers,
            'task_number': task_number,
        }
