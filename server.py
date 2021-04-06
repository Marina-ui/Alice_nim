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
        #записываем в контекст оставшиеся параметры, озвучиваем правила
        context['kuchki'] = 1
        context['chips'] = r.randint(15, 30)  # диапазон камней
        context['max_chips_out'] = r.randint(3, 5)  # максимальное колво забираемых камней
        return generate_response(req, 'Одна, так одна. Вам объяснить правила?')

    elif (answer == 'две' or answer == 'две кучки') and context['kuchki'] == 0 and context['mode'] == 'игра': #формируем игру на две кучки
        pass

    elif (answer == 'да' or answer == 'объясни') and context['mode'] == 'игра' and context['kuchki'] == 1:
        #объясняем правила, Алиса делает первый ход
        chips = context['chips']
        chips_out = context['max_chips_out']
        motion = generate_motion(1, chips, chips_out, first=True)
        context['chips'] -= motion[1]
        rules = f'Объясняю: всего {chips} фишек в куче. Мы по очереди берём 1-{chips_out} фишек.' \
                f'Выиграет тот, кто заберёт последнюю. Давайте, я начну. Беру {motion[0]}. Осталось {motion[1]}.' \
                f'Теперь ваш ход. Сколько фишек вы забираете?'
        return generate_response(req, rules)

    elif (answer == 'нет' or answer == 'не нужно') and context['mode'] == 'игра' and context['kuchki'] == 1:
        #Алиса делает первый ход
        chips = context['chips']
        chips_out = context['max_chips_out']
        motion = generate_motion(1, chips, chips_out, first=True)
        context['chips'] -= motion[1]
        text = f'Хорошо, тогда я начну. Беру {motion[0]}. Осталось {motion[1]}. Теперь ваш ход.'
        return generate_response(req, text)

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
    if kuchki == 1 and first:           #первым ходом создаём выигрышную позицию для игрока в игре с одной кучкой
        ost = chips % (chips_out + 1)
        if ost == 0:
            motion = r.randint(1, chips_out)
        elif ost > 1:
            motion = r.randint(1, ost - 1)
        else:
            motion = r.randint(2, chips_out)

    elif kuchki == 1 and chips > chips_out:        #пытаемся привести игрока в проигрышную позицию
        ost = chips % (chips_out + 1)
        if ost == 0:
            motion = r.randint(1, chips_out)
        else:
            motion = ost

    elif kuchki == 1 and chips < chips_out:    #берём последние
        motion = chips

    elif kuchki == 2:     #ходы при игре с двумя кучками
        pass

    chips -= motion
    return (motion, chips)


if __name__ == '__main__':
    app.run('0.0.0.0', 8080)
