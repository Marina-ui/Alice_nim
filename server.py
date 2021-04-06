from flask import Flask, request
import json
import random as r


app = Flask(__name__)


storage = {}


@app.route('/', methods=['POST'])
def main():
    req = request.json
    user_id = req["session"]["user_id"]

    if req["session"]["new"]:
        storage[user_id] = {'victories': 0, 'defeats': 0, 'mode': 'new'}   #можно будет подвести итог всем играм
        return generate_response(req, "Пожалуйста, выберите режим из списка: Обучение, Игра с Алисой.")

    context = storage[user_id]
    answer = req["request"]["original_utterance"].lower()

    if answer not in {'обучение', 'игра с алисой'} and context['mode'] == 'new':
        return generate_response(req, "Необходимо выбрать режим из списка.")

    if answer == 'обучение' and context['mode'] == 'new':
        #запускается сценарий обучения
        pass
    elif answer == 'игра с алисой' and context['mode'] == 'new':
        #создаём контекст игры, запрашиваем кол-во кучек
        context['mode'] = 'игра'
        context['kuchki'] = 0
        return generate_response(req, 'Всегда рада с вами поиграть. Выберите количество кучек: одна или две')

    elif (answer == 'одна' or answer == 'одна кучка') and context['kuchki'] == 0 and context['mode'] == 'игра': #формируем игру на одну кучку
        #записываем в контекст оставшиеся параметры, овучиваем правила
        context['kuchki'] = 1
        chips = r.randint(20, 30)       #диапазон камней
        chips_out = r.randint(3, 5)     #максимальное колво забираемых камней
        context['chips'] = chips
        context['max_chips_out'] = chips_out
        rules = f'Отлично. Вот правило: всего {chips} фишек в куче. Мы по очереди берём 1-{chips_out} фишек.' \
                f'Выиграет тот, кто заберёт последнюю. Формат вашего ответа: Забираю n фишек. Давайте, я начну.'   #тут будет логика с функцией generate_motion
        return generate_response(req, rules)

    elif (answer == 'две' or answer == 'две кучки') and context['kuchki'] == 0 and context['mode'] == 'игра': #формируем игру на две кучки
        pass

    #...

    else:
        return generate_response(req, 'Неправильный формат ответа. Пожалуйста, повторите.')


    #return generate_response(req, result, end_session=True)


def generate_response(req, text, end_session=False):
    res = {
        "version": req["version"],
        "session": req["session"],
        "response": {
            "end_session": end_session,
            "text": text
        }
    }
    return json.dumps(res, indent=2)


def generate_motion(kuchki, chips, chips_out, first=False):   #генерирует ход Алисы
    pass


if __name__ == '__main__':
    app.run('0.0.0.0', 8080)
