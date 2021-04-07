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
        context['chips'] = [r.randint(15, 30)]  # диапазон камней, одна куча
        context['max_chips_out'] = r.randint(3, 5)  # максимальное колво забираемых камней
        return generate_response(req, 'Одна, так одна. Вам объяснить правила?')

    elif (answer == 'две' or answer == 'две кучки') and context['kuchki'] == 0 and context['mode'] == 'игра': #формируем игру на две кучки
        context['kuchki'] = 2
        context['chips'] = [r.randint(10, 20), r.randint(10, 20)]  # диапазон камней, две кучи
        return generate_response(req, 'Две, так две. Вам объяснить правила?')

    elif (answer == 'да' or answer == 'объясни') and context['mode'] == 'игра' and context['kuchki'] != 0:
        #объясняем правила для 1 и 2 куч, Алиса делает первый ход
        kuchki = context['kuchki']
        if kuchki == 1:
            chips = context['chips']
            chips_out = context['max_chips_out']
            motion = generate_motion(1, chips, chips_out=chips_out, first_motion=True)
            rest = context['chips'][0] - motion[1]
            print(context['chips'][0], motion[1], rest)
            rules = f'Объясняю: всего {chips[0]} камней в куче. Мы по очереди берём 1-{chips_out} камней.' \
                f'Выиграет тот, кто заберёт последний. Давайте я начну. Беру {motion[1]}. Осталось {rest}.' \
                f'Теперь ваш ход. Сколько камней вы забираете?'
            context['chips'][0] -= motion[1]
            return generate_response(req, rules)
        elif kuchki == 2:
            chips = context['chips']
            motion = generate_motion(2, chips, first_motion=True)
            rules = f'Объясняю: всего две кучи, в первой {chips[0]} камней, во второй - {chips[1]}.' \
                    f'Мы по очереди берём из любой кучи любое количество камней. ' \
                    f'Выиграет тот, кто заберёт последний камень. '
            if motion[0] == 1:
                context['chips'][0] -= motion[1]
            else:
                context['chips'][1] -= motion[1]
            rules += f'Давайте я начну. Беру {motion[1]} из {motion[0]}-ой кучи. ' \
                     f'Осталось {chips[0]} в первой и {chips[1]} во второй. ' \
                     f'Теперь ваш ход. Назовите кучу, затем количество забираемых камней.'
            return generate_response(req, rules)

    elif (answer == 'нет' or answer == 'не нужно') and context['mode'] == 'игра' and context['kuchki'] != 0:
        #Алиса делает первый ход
        kuchki = context['kuchki']
        if kuchki == 1:
            chips = context['chips']
            chips_out = context['max_chips_out']
            motion = generate_motion(1, chips, chips_out=chips_out, first_motion=True)
            text = f'Хорошо, тогда я начну. Всего {chips[0]}. '
            context['chips'][0] -= motion[1]
            text += f'Беру {motion[1]}. Осталось {chips[0]}. Теперь ваш ход.'
            return generate_response(req, text)
        elif kuchki == 2:
            chips = context['chips']
            motion = generate_motion(2, chips, first_motion=True)
            text = f'Хорошо, тогда я начну. В первой {chips[0]} камней, во второй {chips[1]}.'
            if motion[0] == 1:
                context['chips'][0] -= motion[1]
            else:
                context['chips'][1] -= motion[1]
            text += f'Беру {motion[1]} из {motion[0]}-ой кучи. ' \
                    f'Осталось {chips[0]} в первой, и {chips[1]} - во второй. Теперь ваш ход.'
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


def generate_motion(kuchki, chips, chips_out=0, first_motion=False):   #генерирует ход Алисы
    if kuchki == 1:       #ход в игре с одной кучкой
        kuchka = 1        #выбираем из какой кучки брать камни
        chips = chips[0]
        if first_motion:           #первым ходом создаём выигрышную позицию для игрока в игре с одной кучкой
            ost = chips % (chips_out + 1)
            if ost == 0:
                motion = r.randint(1, chips_out)
            elif ost > 1:
                motion = r.randint(1, ost - 1)
            else:
                motion = r.randint(2, chips_out)

        elif chips > chips_out:        #пытаемся привести игрока в проигрышную позицию
            ost = chips % (chips_out + 1)
            if ost == 0:
                motion = r.randint(1, chips_out)
            else:
                motion = ost

        elif chips <= chips_out:    #берём последние
            motion = chips

    elif kuchki == 2:     #ходы при игре с двумя кучками
        difference = abs(chips[0] - chips[1])
        if difference == 0:
            kuchka = r.randint(1, 2)
            motion = r.randint(1, chips[kuchka - 1])
        if first_motion:                                #можно подправить чутка, вылетала ошибка
            if difference == 1:
                if chips[0] < chips[1]:
                    kuchka = 1
                    motion = r.randint(1, chips[0])
                else:
                    kuchka = 2
                    motion = r.randint(1, chips[1])
            else:
                if chips[0] > chips[1]:
                    kuchka = 1
                else:
                    kuchka = 2
                motion = r.randint(1, difference - 1)
        else:
            if chips[0] > chips[1]:
                kuchka = 1
            else:
                kuchka = 2
            motion = difference

    return (kuchka, motion)


if __name__ == '__main__':
    app.run('0.0.0.0', 8080)
