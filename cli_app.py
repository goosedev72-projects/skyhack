import argparse
from parser.answer_module import SkyAnswers
import asyncio

def main():
    parser = argparse.ArgumentParser(description='SkyHack')
    parser.add_argument('room_name', type=str, help='📘 Название комнаты')
    args = parser.parse_args()

    async def fetch_answers(room_name):
        answers_module = SkyAnswers(room_name)
        answers = await answers_module.get_answers()
        for solution in answers:
            print(f"❓ Задание #{solution['task_number']} - {solution['question']}")
            for answer in solution['answers']:
                print(f'💡 Ответ: {answer}')
            print('')

    asyncio.run(fetch_answers(args.room_name))

if __name__ == '__main__':
    main()