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
    answ_let_to_num = {'один': 1, 'два': 2, 'три': 3, 'четыре': 4, 'пять': 5,
                       'шесть': 6, 'семь': 7, 'восемь': 8, 'девять': 9, 'десять': 10,
                       'одиннадцать': 11, 'двенадцать': 12, 'тринадцать': 13, 'четырнадцать': 14,
                       'пятнадцать': 15, 'шестнадцать': 16, 'семнадцать': 17, 'восемнадцать': 18, 'девятнадцать': 19,
                       'двадцать': 20}

    if answer not in {'обучение', 'игра с алисой'} and context['mode'] == 'new':
        return generate_response(req, "Необходимо выбрать режим из списка.")

    if answer == 'обучение' and context['mode'] == 'new' or \
            (answer == 'да' or answer == 'хочу') and context['mode'] == 'игра' and context['winner'] == 'Alice' or \
            answer == 'Алиса, включи обучение' and context['mode'] == 'игра' and context['game_finished']:
        #запускается сценарий обучения
        context['mode'] = 'обучение'
        context['kuchki'] = 0
        context['onek_tng_finished'] = False
        context['twok_tng_finished'] = False
        return generate_response(req, "Выберите количество кучек для обучения: одна или две.")

    elif answer == 'игра с алисой' and context['mode'] == 'new':
        #создаём контекст игры, запрашиваем кол-во кучек
        context['mode'] = 'игра'
        context['kuchki'] = 0
        context['winner'] = None
        context['game_finished'] = False
        context['first_motion'] = False
        context['first_game'] = True
        return generate_response(req, 'Всегда рада с вами поиграть. Выберите количество кучек: одна или две')

    elif (answer == 'одна' or answer == 'одна кучка') and context['kuchki'] == 0 and (context['mode'] == 'игра' or
            context['mode'] == 'обучение'):
        #формируем игру на одну кучку
        #записываем в контекст оставшиеся параметры, озвучиваем правила
        context['kuchki'] = 1
        if context['mode'] == 'игра':
            context['chips'] = [r.randint(15, 30)]  # диапазон камней, одна куча, игра
        elif context['mode'] == 'обучение':
            context['chips'] = [r.randint(15, 20)]  # диапазон камней, одна куча, обучение
        context['max_chips_out'] = r.randint(3, 5)  # максимальное кол-во забираемых камней
        chips = context['chips']
        chips_out = context['max_chips_out']
        motion = generate_motion(1, chips, chips_out=chips_out, first_motion=True)
        if context['mode'] == 'игра':
            if context['first_game']:
                return generate_response(req, 'Одна, так одна. Вам объяснить правила?')
            text = f'Всего {chips[0]}. Берём от 1 до {chips_out}. '
            context['chips'][0] -= motion[1]
            text += f'Беру {motion[1]}. Осталось {chips[0]}. Ходите.'
        elif context['mode'] == 'обучение':
            if context['onek_tng_finished']:
                #*
                pass
            text = f'Правила в игре с одной кучкой просты: задаётся начальное количество камней в куче. ' \
                   f'Вы можете брать некоторое m количество этих камней. Выигрывает тот, кто забирает последний. ' \
                   f'Чтобы выиграть в такой игре, вам нужно брать столько камней, ' \
                   f'чтобы их оставшееся количество делилось на m + 1. Давайте потренируемся. ' \
                   f'В нашей куче {chips[0]} камней. Можно брать 1-{chips_out} камней. '
            context['chips'][0] -= motion[1]
            text += f'Я возьму {motion[1]}, и останется {chips[0]}. Теперь сделайте свой ход.'
        context['first_motion'] = True
        return generate_response(req, text)

    elif (answer == 'две' or answer == 'две кучки') and context['kuchki'] == 0 and context['mode'] == 'игра' and not \
            context['game_finished']:    #формируем игру на две кучки
        context['kuchki'] = 2
        context['chips'] = [r.randint(10, 20), r.randint(10, 20)]  # диапазон камней, две кучи
        chips = context['chips']
        motion = generate_motion(2, chips, first_motion=True)
        if context['mode'] == 'игра':
            if context['first_game']:
                return generate_response(req, 'Две, так две. Вам объяснить правила?')
            text = f'В первой {chips[0]} камней, во второй {chips[1]}.'
            context['chips'][motion[0] - 1] -= motion[1]
            text += f'Беру {motion[1]} из {motion[0]}-ой кучи. ' \
                    f'Осталось {chips[0]} и {chips[1]}. Ходите.'
        elif context['mode'] == 'обучение':
            if context['twok_tng_finished']:
                #*
                pass
            text = f'Правила в игре с двумя кучками ещё проще, чем с одной: ' \
                   f'задаётся начальное количество камней в двух кучах. ' \
                   f'Вы можете брать любое количество камней из любой одной кучи. ' \
                   f'Выигрывает тот, кто забирает последние. ' \
                   f'Чтобы выиграть в такой игре, вам нужно брать столько камней, ' \
                   f'чтобы их оставшееся количество в обоих кучах было одинаково. Давайте потренируемся. ' \
                   f'В нашей первой куче {chips[0]} камней, а во второй {chips[1]}. '
            context['chips'][motion[0] - 1] -= motion[1]
            text += f'Беру {motion[1]} из {motion[0]}-ой. Остаётся {chips[0]} и {chips[1]} камней. ' \
                    f'Сделайте свой ход: сначала назовите количество камней, затем номер кучки.'
        context['first_motion'] = True
        return generate_response(req, text)

    elif ((answer == 'да' or answer == 'объясни') and context['mode'] == 'игра' and context['kuchki'] != 0 and
            context['first_game'] and not context['game_finished']) or \
            answer == 'Алиса, объясни правила' and context['kuchki'] != 0:    #*
        #объясняем правила для 1 и 2 куч, Алиса делает первый ход
        kuchki = context['kuchki']
        if kuchki == 1:
            chips = context['chips']
            chips_out = context['max_chips_out']
            motion = generate_motion(1, chips, chips_out=chips_out, first_motion=True)
            rules = f'Объясняю: всего {chips[0]} камней в куче. Мы по очереди берём 1-{chips_out} камней.' \
                    f'Вам нужно назвать только количество камней. Выиграет тот, кто заберёт последний.'
            if answer != 'Алиса, объясни правила':
                context['chips'][0] -= motion[1]
                context['first_motion'] = True
                rules += f'Давайте я начну. Беру {motion[1]}. Осталось {chips[0]}.' \
                    f'Теперь ваш ход. Сколько камней вы забираете?'
            return generate_response(req, rules)
        elif kuchki == 2:
            chips = context['chips']
            motion = generate_motion(2, chips, first_motion=True)
            rules = f'Объясняю: всего две кучи, в первой {chips[0]} камней, во второй - {chips[1]}.' \
                    f'Мы по очереди берём из любой кучи любое количество камней. ' \
                    f'Выиграет тот, кто заберёт последний камень. '
            if answer != 'Алиса, объясни правила':
                context['chips'][motion[0] - 1] -= motion[1]
                rules += f'Давайте я начну. Беру {motion[1]} из {motion[0]}-ой кучи. ' \
                         f'Осталось {chips[0]} в первой и {chips[1]} во второй. ' \
                         f'Теперь ваш ход. Назовите количество забираемых камней, затем номер кучи.'
                context['first_motion'] = True
            return generate_response(req, rules)

    elif ((answer == 'нет' or answer == 'не нужно') and context['mode'] == 'игра' and context['kuchki'] != 0 and
          context['first_game'] and not context['game_finished']):
        #Алиса делает первый ход
        kuchki = context['kuchki']
        if kuchki == 1:
            chips = context['chips']
            chips_out = context['max_chips_out']
            motion = generate_motion(1, chips, chips_out=chips_out, first_motion=True)
            text = f'Хорошо, тогда я начну. Всего {chips[0]}. Можно брать от 1 до {chips_out} камней. '
            context['chips'][0] -= motion[1]
            context['first_motion'] = True
            text += f'Беру {motion[1]}. Осталось {chips[0]}. Теперь ваш ход.'
            return generate_response(req, text)
        elif kuchki == 2:
            chips = context['chips']
            motion = generate_motion(2, chips, first_motion=True)
            text = f'Хорошо, тогда я начну. В первой {chips[0]} камней, во второй {chips[1]}.'
            context['chips'][motion[0] - 1] -= motion[1]
            context['first_motion'] = True
            text += f'Беру {motion[1]} из {motion[0]}-ой кучи. ' \
                    f'Осталось {chips[0]} в первой, и {chips[1]} - во второй. Теперь ваш ход.'
            return generate_response(req, text)

    elif answer and context['mode'] == 'игра' and context['first_motion'] and not context['game_finished'] and \
            ('забираю последн' in answer or 'беру последн' in answer or
             req["request"]["nlu"]["tokens"][0].lower() in answ_let_to_num.keys() or
             int(req["request"]["nlu"]["tokens"][0]) in answ_let_to_num.values()):
        #обрабатываем ход игрока
        user_motion = req["request"]["nlu"]["tokens"]
        kuchki = context['kuchki']
        chips = context['chips']
        if user_motion[0] in answ_let_to_num.keys():
            user_motion[0] = answ_let_to_num.get(user_motion[0])
        if len(user_motion) == 1 and kuchki > 1:
            return generate_response(req, 'Вы не назвали номер кучки. '
                                          'Назовите ещё раз количество камней, затем номер кучки.')
        elif len(user_motion) > 1 and kuchki == 1 and 'забираю последн' not in answer and 'беру последн' not in answer:        #*
            return generate_response(req, 'Назовите только количество камней.')
        elif kuchki == 1:              #*
            chips_out = context['max_chips_out']
            if ('забираю последн' in answer or 'беру последн' in answer) and chips[0] > chips_out or \
                    user_motion[0].isdigit() and int(user_motion[0]) > chips_out:
                text = f'Жадность - хороший завтрак, но плохой ужин (по Вольтеру). '
                if chips_out == 5:
                    text += f'Вы можете вять максимум {chips_out} камней.'
                else:
                    text += f'Вы можете вять максимум {chips_out} камня.'
                return generate_response(req, text)
            elif 'забираю последн' not in answer and 'беру последн' not in answer:  # *
                user_motion[0] = int(user_motion[0])
                context['chips'][0] -= user_motion[0]
            if chips[0] == 0 or 'забираю последн' in answer or 'беру последн' in answer:
                context['winner'] = 'user'
                context['game_finished'] = True
                context['victories'] += 1
                return generate_response(req, 'Ну вот, вы не оставили мне камней, вы победили. Не хотите сыграть ещё?')
            elif chips[0] < 0:
                context['winner'] = 'user'
                context['game_finished'] = True
                context['victories'] += 1
                return generate_response(req, f'Сделаю вид, что вы взяли {user_motion[0] + chips[0]}'
                                              f'Поздравляю, вы победили. Не хотите сыграть ещё?')
            else:
                Alice_motion = generate_motion(1, chips, chips_out=chips_out)
                if chips[0] in range(1, 5):
                    result = f'Осталось {chips[0]} камня. '
                else:
                    result = f'Осталось {chips[0]} камней. '
                context['chips'][0] -= Alice_motion[1]
                if context['chips'][0] == 0:
                    context['winner'] = 'Alice'
                    context['game_finished'] = True
                    context['defeats'] += 1
                    result += f'Я беру последние. И снова я победила! Не хотите выбрать режим обучения?'
                else:
                    result += f'Я беру {Alice_motion[1]}. Остаётся {chips[0]}.'
                return generate_response(req, result)
        elif kuchki == 2 and len(user_motion) == 2:      #*
            if 'забираю последн' in answer or 'беру последн' in answer:
                if chips[0] == 0 or chips[1] == 0:
                    context['winner'] = 'user'
                    context['game_finished'] = True
                    context['victories'] += 1
                    return generate_response(req,
                                             'Забирайте, вам нужнее. Поздравляю с победой. Не хотите сыграть ещё?')
            umotion, kuchka = int(user_motion[0]), user_motion[1]
            if kuchka == 'первая':
                kuchka = 1
            elif kuchka == 'вторая':
                kuchka = 2
            elif kuchka == '1' or kuchka == '2':
                kuchka = int(kuchka)
            else:
                return generate_response(req, 'Неправильный номер кучки')
            if umotion > chips[kuchka - 1]:
                text = f'Подарите ему весь мир, и он потребует еще оберточную бумагу (Жюльен де Фалкенарё). '
                if chips[kuchka - 1] in range(5, 20 + 1):
                    text += f'Вы можете вять максимум {chips[kuchka - 1]} камней.'
                elif chips[kuchka - 1] == 1:
                    text += f'Вы можете вять максимум {chips[kuchka - 1]} камень.'
                else:
                    text += f'Вы можете вять максимум {chips[kuchka - 1]} камня.'
                return generate_response(req, text)
            context['chips'][kuchka - 1] -= umotion
            if chips[0] == 0 and chips[1] == 0:
                context['winner'] = 'user'
                context['game_finished'] = True
                context['victories'] += 1
                return generate_response(req, 'Ну вот, вы не оставили мне камней, вы победили. Не хотите сыграть ещё?')
            Alice_motion = generate_motion(2, chips)
            text = f'Осталось {chips[0]} в первой и {chips[1]} во второй. '
            context['chips'][Alice_motion[0] - 1] -= Alice_motion[1]
            if chips[0] == chips[1] == 0:
                context['winner'] = 'Alice'
                context['game_finished'] = True
                context['defeats'] += 1
                text += f'Я забираю последние. И снова я победила! Не хотите выбрать режим обучения?'
            else:
                text += f'Беру {Alice_motion[1]} из {Alice_motion[0]}-ой. Остаётся {chips[0]} и {chips[1]}.'
            return generate_response(req, text)

    elif context['mode'] == 'игра' and context['game_finished'] and context['winner'] == 'user':
        if answer == 'да' or answer == 'хочу' or answer == 'давай сыграем' or answer == 'давай':
            context['mode'] = 'игра'
            context['kuchki'] = 0
            context['winner'] = None
            context['game_finished'] = False
            context['first_motion'] = False
            context['first_game'] = False
            return generate_response(req, 'На сколько куч играем?')
        else:
            result = f'Отлично, я тоже не очень хотела. '
            wins, defs = context['victories'], context['defeats']
            if wins > defs:
                result += f'Счёт на сегодня {wins}:{defs} в вашу пользу.'      #дополнить прощание
            elif context['victories'] < context['defeats']:
                result += f'Счёт на сегодня {wins}:{defs} в мою пользу.'
            else:
                result += f'Счёт на сегодня {wins}:{defs}. Победила дружба. '
            return generate_response(req, result, end_session=True)

    elif context['game_finished'] and context['winner'] == 'Alice' and context['mode'] == 'игра':
        if answer == 'да' or answer == 'хочу' or answer == 'включи' or answer == 'давай':
            context['mode'] = 'обучение'
            context['kuchki'] = 0
            context['winner'] = None
            context['game_finished'] = False
            context['first_motion'] = False
            return generate_response(req, "Так и быть, включаю режим обучения. "
                                          "Для начала выберите количество кучек: одна или две.")
        elif answer == 'нет, запусти новую игру' or answer == 'давай сыграем ещё раз' or answer == 'хочу реванш' or \
                answer == 'реванш':
            context['mode'] = 'игра'
            context['kuchki'] = 0
            context['winner'] = None
            context['game_finished'] = False
            context['first_motion'] = False
            context['first_game'] = False
            return generate_response(req, 'На сколько куч играем?')
        else:
            result = f'Было приятно с вами поиграть. '
            wins, defs = context['victories'], context['defeats']
            if wins > defs:
                result += f'Счёт на сегодня {wins}:{defs} в вашу пользу.'  # дополнить прощание
            elif context['victories'] < context['defeats']:
                result += f'Счёт на сегодня {wins}:{defs} в мою пользу.'
            else:
                result += f'Счёт на сегодня {wins}:{defs}. Победила дружба. '
            return generate_response(req, result, end_session=True)

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
        if not difference:
            kuchka = r.randint(1, 2)
            motion = r.randint(1, chips[kuchka - 1])
        elif first_motion:                                #нужно подправить чутка, вылетала ошибка
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
            if chips[0] == 0:
                kuchka = 2
            elif chips[1] == 0:
                kuchka = 1
            elif chips[0] > chips[1]:
                kuchka = 1
            else:
                kuchka = 2
            motion = difference

    return (kuchka, motion)


if __name__ == '__main__':
    app.run('0.0.0.0', 8080)
