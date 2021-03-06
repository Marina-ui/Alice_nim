from flask import Flask, request
import json
import random as r
from data import db_session
from data.users import User


app = Flask(__name__)


storage = {}


@app.route('/', methods=['POST'])
def main():
    req = request.json
    user_id = req["session"]["user_id"]
    db_sess = db_session.create_session()

    if req["session"]["new"]:
        storage[user_id] = {'victories': 0, 'defeats': 0, 'mode': 'new'}   # можно будет подвести итог всем играм
        user = User()

        for i in db_sess.query(User).all():
            if i.username == user_id:
                storage[user_id]['victories'] = i.wins
                storage[user_id]['defeats'] = i.defs
                break
            else:
                user.username = user_id
                wins, defs = storage[user_id]['victories'], storage[user_id]['defeats']
                user.wins, user.defs = wins, defs
                db_sess.add(user)
                db_sess.commit()

        return gen_but_resp(req, 'Пожалуйста, выберите режим из списка: Обучение, Игра с Алисой.',
                            'Обучение', 'Игра с Алисой')

    context = storage[user_id]
    answer = req["request"]["original_utterance"].lower()
    answer_list = req["request"]["nlu"]["tokens"]

    wins, defs = context['victories'], context['defeats']
    user = db_sess.query(User).filter(User.username == user_id).first()
    user.wins, user.defs = wins, defs
    db_sess.commit()

    answ_let_to_num = {'ноль': 0, 'один': 1, 'два': 2, 'три': 3, 'четыре': 4, 'пять': 5,
                       'шесть': 6, 'семь': 7, 'восемь': 8, 'девять': 9, 'десять': 10,
                       'одиннадцать': 11, 'двенадцать': 12, 'тринадцать': 13, 'четырнадцать': 14,
                       'пятнадцать': 15, 'шестнадцать': 16, 'семнадцать': 17, 'восемнадцать': 18,
                       'девятнадцать': 19,
                       'двадцать': 20, 'двадцать один': 21, 'двадцать два': 22, 'двадцать три': 23,
                       'двадцать четыре': 24, 'двадцать пять': 25}
    phrase_list = ['я', 'беру', 'взял', 'забираю', 'взяла', 'камни', 'камней', 'камням', 'камнями', 'камнях',
                   'камня',
                   'камень', 'куча', 'кучи', 'кучка', 'кучки', 'из', 'возьму']
    greedy_sayings = [f'Жадность - хороший завтрак, но плохой ужин (по Вольтеру). ',
                      f'Подарите ему весь мир, и он потребует еще оберточную бумагу (Жюльен де Фалкенарё). ',
                      f'Жажда наживы не создала еще ни одного художника, но погубила многих. (У. Олстон). ',
                      f'Не тот жаден, у кого мало, а тот, кто хочет большего. ',
                      f'Жадность заключается в желании иметь более, чем необходимо (Аврелий Августин). ',
                      f'Жадность - не сон, подождет (Бузина М.). ',
                      f'Жадный король сам играет свою свиту (Теткоракс). ']
    facts_about_nim = ['Китайская игра ним упоминалась европейцами ещё в XVI веке. ',
                       'Имя «ним» было дано игре американским математиком Чарльзом Бутоном. ',
                       'Чарльз Бутон описал в 1901 году выигрышную стратегию для игры. ',
                       'Есть несколько вариантов происхождения названия игры: первое - от '
                       'немецкого глагола nehmen или от староанглийского глагола Nim, имеющих значение «брать»'
                       ' и второе - от английского глагола Win. ',
                       'Эта игра служит метафорой происходящего в фильме «В прошлом году в Мариенбаде». '
                       'Кстати, советую посмотреть. ',
                       'Не у всех получается обыграть наш мега-компьютер, '
                       'даже некоторые создатели этого навыка испытывают проблемы в игре! ']
    bye_phr_l = ['До новых встреч!', 'Пришло время прощаться. До скорого!', 'На сегодня все. До свидания!', '']

    if context['mode'] != 'new':
        answer_list = list(filter(lambda word: word not in phrase_list, answer_list))

    if answer not in {'обучение', 'игра с алисой', 'игра'} and context['mode'] == 'new':
        return gen_but_resp(req, 'Необходимо выбрать режим из списка.', 'Обучение', 'Игра с Алисой')

    if answer == 'обучение' and context['mode'] == 'new' or \
            answer == 'Алиса, включи обучение' and context['mode'] == 'игра' and context['game_finished']:          #*
        # запускается сценарий обучения
        context['mode'] = 'обучение'
        context['kuchki'] = 0
        context['onek_tng_finished'] = False
        context['twok_tng_finished'] = False
        context['tng_finished'] = False
        context['ask_for_learn'] = False
        context['ask_for_play'] = False
        context['patience'] = 3
        context['efforts'] = 1
        context['first_motion'] = False
        context['first_learn_game'] = True
        context['no_learn_game'] = False
        return gen_but_resp(req, 'Выберите количество кучек для обучения: одна или две.', fbut='Одна', sbut='Две')

    elif answer in ['игра с алисой', 'игра'] and context['mode'] == 'new':
        # создаём контекст игры, запрашиваем кол-во кучек
        context['mode'] = 'игра'
        context['kuchki'] = 0
        context['winner'] = None
        context['game_finished'] = False
        context['first_motion'] = False
        context['first_game'] = True
        context['ask_for_learn'] = False
        context['ask_for_play'] = False
        context['ask_for_fact'] = False
        context['no_learn_game'] = True
        return gen_but_resp(req, 'Всегда рада с вами поиграть. Выберите количество кучек: одна или две',
                            fbut='Одна', sbut='Две')

    elif answer in ['одна', '1'] and context['kuchki'] == 0 and context['mode'] in ['игра', 'обучение']:
        # формируем игру на одну кучку
        # записываем в контекст оставшиеся параметры, озвучиваем правила
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
                return gen_but_resp(req, 'Одна, так одна. Вам объяснить правила?', fbut='Да', sbut='Нет')
            text = f'Всего {chips[0]}. Берём от 1 до {chips_out}. '
            context['chips'][0] -= motion[1]
            text += f'Беру {motion[1]}. Осталось {chips[0]}. Ходите.'
        elif context['mode'] == 'обучение':
            stones = declination(chips[0], 'камень')
            text = f'Правила в игре с одной кучкой просты: задаётся начальное количество камней в куче. ' \
                   f'Вы можете брать некоторое m количество этих камней. Выигрывает тот, кто забирает последний. ' \
                   f'Чтобы выиграть в такой игре, вам нужно брать столько камней, ' \
                   f'чтобы их оставшееся количество перед последним ходом было на 1 больше максимального. ' \
                   f'Давайте потренируемся. ' \
                   f'В нашей куче {chips[0]} {stones}. Можно брать от 1 до {chips_out} камней. '
            context['chips'][0] -= motion[1]
            text += f'Я возьму {motion[1]}, и останется {chips[0]}. Теперь сделайте свой ход.'
        context['first_motion'] = True
        return generate_response(req, text)

    elif answer in ['две', '2'] and context['kuchki'] == 0 and context['mode'] in ['игра', 'обучение']:
        # формируем игру на две кучки
        context['kuchki'] = 2
        context['chips'] = [r.randint(10, 20), r.randint(10, 20)]  # диапазон камней, две кучи
        chips = context['chips']
        motion = generate_motion(2, chips, first_motion=True)
        if context['mode'] == 'игра':
            if context['first_game']:
                return gen_but_resp(req, 'Две, так две. Вам объяснить правила?', fbut='Да', sbut='Нет')
            text = f'В первой {chips[0]} камней, во второй {chips[1]}. '
            context['chips'][motion[0] - 1] -= motion[1]
            text += f'Беру {motion[1]} из {motion[0]}-ой кучи. ' \
                    f'Осталось {chips[0]} и {chips[1]}. Ходите.'
        elif context['mode'] == 'обучение':
            stones = declination(chips[0], 'камень')
            if context['onek_tng_finished']:
                text = f'Правила в игре с двумя кучками ещё проще, чем с одной: '
            else:
                text = f'Правила в игре с двумя кучами предельно просты: '
            text += f'задаётся начальное количество камней в двух кучах. ' \
                    f'Вы можете брать любое количество камней из любой одной кучи. ' \
                    f'Выигрывает тот, кто забирает последние. ' \
                    f'Чтобы выиграть в такой игре, вам нужно всегда оставлять камни в обеих кучах, ' \
                    f'иначе я сразу выиграю. Давайте потренируемся. ' \
                    f'В нашей первой куче {chips[0]} {stones}, а во второй {chips[1]}. '
            context['chips'][motion[0] - 1] -= motion[1]
            text += f'Беру {motion[1]} из {motion[0]}-ой. Остаётся {chips[0]} и {chips[1]} камней. ' \
                    f'Сделайте свой ход: скажите, сколько камней вы берёте и из какой кучки.'
        context['first_motion'] = True
        return generate_response(req, text)

    elif context['mode'] == 'игра' and not context['game_finished'] and context['first_motion'] and \
            answer in ['алиса, какой счёт', 'какой счёт', 'счёт', 'скажи счёт', 'алиса, скажи счёт',
                       'алиса, скажи, какой счёт', 'скажи, какой счёт']:
        wins, defs = context['victories'], context['defeats']
        if wins == defs == 0:
            score = f'Пока что наш счёт {wins}:{defs}. '
        elif wins == defs:
            score = f'Наш счёт {wins}:{defs} в ничью. '
        elif wins > defs:
            score = f'Наш счёт {wins}:{defs} в вашу пользу. '
        else:
            score = f'Наш счёт {wins}:{defs} в мою пользу. '
        score += f'Сделайте свой ход.'
        return generate_response(req, score)

    elif ((context['mode'] == 'игра' and not context['game_finished'] or
          context['mode'] == 'обучение' and not context['tng_finished']) and context['first_motion'] and \
            answer in ['алиса, расскажи интересный факт про ним', 'интересный факт про ним',
                       'расскажи интересный факт про ним', 'скажи интересный факт',
                       'расскажи что-нибудь иннтересное про ним', 'расскажи что-нибудь интересное',
                       'алиса, расскажи интересный факт', 'интересный факт']) or \
            context['mode'] == 'игра' and not context['game_finished'] and context['first_motion'] and \
            context['ask_for_fact'] and answer in ['да', 'давай', 'расскажи']:
        fact = r.choice(facts_about_nim)
        context['ask_for_fact'] = False
        fact += f'Давайте продолжим игру, сделайте свой ход.'
        return generate_response(req, fact)

    elif (answer in ['да', 'объясни'] and context['mode'] == 'игра' and context['kuchki'] != 0 and
            context['first_game'] and not context['game_finished']) or \
            (answer in ['алиса, объясни правила', 'объясни правила', 'правила'] and
             context['kuchki'] != 0 and not context['game_finished']):
        # объясняем правила для 1 и 2 куч, Алиса делает первый ход
        kuchki = context['kuchki']
        if kuchki == 1:
            chips = context['chips']
            chips_out = context['max_chips_out']
            motion = generate_motion(1, chips, chips_out=chips_out, first_motion=True)
            stones = declination(chips[0], 'камень')
            rules = f'Объясняю: в куче {chips[0]} {stones}. Мы по очереди берём от 1 до {chips_out} камней. ' \
                    f'Вам нужно назвать количество забираемых камней. Выиграет тот, кто заберёт последний. '
            if answer in ['алиса, объясни правила', 'объясни правила', 'правила']:
                rules += f'Сейчас ваш ход.'
            else:
                context['chips'][0] -= motion[1]
                rules += f'Давайте я начну. Беру {motion[1]}. Осталось {chips[0]}. ' \
                    f'Теперь ваш ход. Сколько камней вы забираете?'
                context['first_motion'] = True
            return generate_response(req, rules)
        elif kuchki == 2:
            chips = context['chips']
            motion = generate_motion(2, chips, first_motion=True)
            stones = declination(chips[0], 'камень')
            rules = f'Объясняю: всего две кучи, в первой {chips[0]} {stones}, во второй - {chips[1]}. ' \
                    f'Мы по очереди берём из любой кучи любое количество камней. ' \
                    f'Выиграет тот, кто заберёт последний камень. '
            if answer in ['алиса, объясни правила', 'объясни правила', 'правила']:
                rules += f'Сейчас ваш ход.'
            else:
                context['chips'][motion[0] - 1] -= motion[1]
                rules += f'Давайте я начну. Беру {motion[1]} из {motion[0]}-ой кучи. ' \
                         f'Осталось {chips[0]} в первой и {chips[1]} во второй. ' \
                         f'Теперь ваш ход. Назовите количество камней и из какой кучи вы их берёте.'
                context['first_motion'] = True
            return generate_response(req, rules)

    elif (answer in ['нет', 'не нужно'] and context['mode'] == 'игра' and context['kuchki'] != 0 and
          context['first_game'] and not context['game_finished']):
        # Алиса делает первый ход
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
            stones = declination(chips[0], 'камень')
            text = f'Хорошо, тогда я начну. В первой {chips[0]} {stones}, во второй {chips[1]}. '
            context['chips'][motion[0] - 1] -= motion[1]
            context['first_motion'] = True
            text += f'Беру {motion[1]} из {motion[0]}-ой кучи. ' \
                    f'Осталось {chips[0]} в первой, и {chips[1]} - во второй. Теперь ваш ход.'
            return generate_response(req, text)

    elif (answer and context['mode'] == 'игра' and context['first_motion'] and not context['game_finished'] or
          context['mode'] == 'обучение' and context['first_motion']) and \
            (len(answer_list) == 2 and (answer_list[0].lower() in ['последние', 'все', 'всё', 'последний'] or
                                        answer_list[0].lower() in answ_let_to_num.keys() or answer_list[0].isdigit() or
                                        answer_list[1].lower() in ['последние', 'все', 'всё', 'последний'] or
                                        answer_list[1].lower() in answ_let_to_num.keys() or
                                        answer_list[1].isdigit() and int(answer_list[1]) in answ_let_to_num.values())
             or len(answer_list) == 1 and
             (answer_list[0].lower() in ['последние', 'все', 'всё', 'последний'] or
              answer_list[0].lower() in answ_let_to_num.keys() or
             answer_list[0].isdigit())):
        # обрабатываем ход игрока
        kuchki = context['kuchki']
        chips = context['chips']

        if kuchki == 1 and len(answer_list) > 1:
            return generate_response(req, 'Назовите количество забираемых камней.')
        elif kuchki == 2 and len(answer_list) < 2 and \
                (answer_list[0].lower() in ['последние', 'все', 'всё', 'последний'] and
                 chips[0] != 0 and chips[1] != 0 or
                 answer_list[0].lower() not in ['последние', 'все', 'всё', 'последний'] and
                 'перв' not in answer and 'втор' not in answer and '1' not in answer and '2' not in answer):
            return generate_response(req, 'Вы не назвали номер кучки. '
                                          'Назовите ещё раз количество камней и номер кучи.')
        elif kuchki == 2 and len(answer_list) < 2 and \
                (answer_list[0] in ['первая', 'первой', 'вторая', 'второй', '1', '2']):
            return generate_response(req, 'Вы не назвали количество камней. '
                                          'Назовите ещё раз количество камней и номер кучи.')
        elif kuchki == 2 and len(answer_list) == 2 and ('перв' not in answer and 'втор' not in answer and
                                                        '1' not in answer and '2' not in answer):
            return generate_response(req, 'Вы неверно назвали номер кучки: '
                                          'вы можете брать камни только из первой или второй кучки. '
                                          'Назовите ещё раз количество камней и номер кучи.')
        elif kuchki == 1 and len(answer_list) == 1:
            chips_out = context['max_chips_out']
            user_motion = answer_list[0].lower()

            if user_motion in answ_let_to_num.keys():
                user_motion = answ_let_to_num.get(user_motion)
            elif user_motion.isdigit():
                user_motion = int(user_motion)

            if user_motion in ['последние', 'все', 'всё', 'последний'] and chips[0] > chips_out or \
                    str(user_motion).isdigit() and user_motion > chips_out:
                text = r.choice(greedy_sayings)
                stones = declination(chips_out, 'камень')
                text += f'Вы можете взять максимум {chips_out} {stones}.'
                return generate_response(req, text)
            elif user_motion in ['последние', 'все', 'всё', 'последний']:
                user_motion = chips[0]
            elif user_motion == 0:
                return generate_response(req, f'Извините, но вы не можете не брать камней или брать 0 камней. '
                                              f'Возможный ход от 1 до {chips_out}.')
            context['chips'][0] -= user_motion
            if chips[0] <= 0 and context['mode'] == 'обучение':
                # картинка с сертификатом
                context['onek_tng_finished'] = True
                context['tng_finished'] = True
                image_id = ''
                if chips[0] == 0:
                    text = f'Отлично! '                                              # SERTIFICAT
                else:
                    text = f'Отлично! ' #*
                if context['twok_tng_finished'] and context['first_learn_game']:
                    # предлагает сертификат о прохождение одной кучки и предлагает сыграть с ней,
                    # если у игрока уже есть сертификат об обучении с двумя кучками
                    image_id = '213044/e1236b63401abe28dd46'
                    efforts = context['efforts']
                    attempts = declination(efforts, 'попытка')
                    if efforts == 1:
                        ushlo = 'ушла'
                    else:
                        ushlo = 'ушло'
                    text += f'Вы завершили обучение с одной и двумя кучами. ' \
                            f'У вас {ushlo} на это суммарно {efforts} {attempts}. ' \
                            f'Не хотите теперь обыграть меня?'
                    context['ask_for_play'] = True
                if not context['twok_tng_finished'] and context['first_learn_game']:
                    # предлагает сертификат о прохождении одной кучкой и предлагает пройти обучение с двумя
                    image_id = '213044/e1236b63401abe28dd46'
                    efforts = context['efforts']
                    attempts = declination(efforts, 'попытка')
                    if efforts == 1:
                        ushlo = 'ушла'
                    else:
                        ushlo = 'ушло'
                    text += f'Вы завершили обучение с одной кучей. ' \
                            f'У вас {ushlo} на это всего лишь {efforts} {attempts}. ' \
                            f'Не хотите теперь пройти обучение с двумя?'
                    context['ask_for_learn'] = True
                elif context['twok_tng_finished'] and not context['first_learn_game']:
                    text += f'Вы снова успешно прошли обучение. Не хотите теперь сыграть? '
                    context['ask_for_play'] = True
                elif not context['twok_tng_finished'] and not context['first_learn_game']:
                    text += f'Как говориться, повторенье - мать ученья. ' \
                            f'Не хотите теперь пройти обучение с двумя кучами? '
                    context['ask_for_learn'] = True
                context['first_learn_game'] = False
                return generate_image_response(req, text, image_id=image_id)
            elif chips[0] <= 0 and context['mode'] == 'игра':
                context['winner'] = 'user'
                context['game_finished'] = True
                context['victories'] += 1
                if chips[0] == 0:
                    if not context['no_learn_game'] and context['onek_tng_finished']:
                        result = f'Надо же, вы победили! Где вы научились так играть? Сыграем ещё?'
                    else:
                        result = f'Ну вот, вы не оставили мне камней, вы победили. Не хотите сыграть ещё?'
                else:
                    result = f'Сделаю вид, что вы взяли {chips[0] + user_motion}. ' \
                             f'Поздравляю, вы победили. Не хотите сыграть ещё? '
                context['ask_for_play'] = True
                return gen_but_resp(req, result, fbut='Новая игра', sbut='Обучение', thbut='Выход', audio_id='W')
            elif context['mode'] == 'обучение' and chips[0] % (chips_out + 1) != 0:
                # Алиса в режиме обучения ругает пользователя за неправильный ход, убавляются очки терпения
                context['patience'] -= 1
                if context['patience'] == 0:
                    # если терпения не осталось, Алиса начинает обучение сначала,
                    # счётчик попыток пройти обучение увеличивается
                    # инициализируется новое обучение и Алиса делает ход
                    context['patience'] = 3
                    context['efforts'] += 1
                    context['chips'] = [r.randint(15, 20)]  # диапазон камней, одна куча, обучение
                    context['max_chips_out'] = r.randint(3, 5)  # максимальное кол-во забираемых камней
                    chips = context['chips']
                    chips_out = context['max_chips_out']
                    motion = generate_motion(1, chips, chips_out=chips_out, first_motion=True)
                    stones = declination(chips[0], 'камень')
                    text = f'Давайте начнём сначала: чтобы выиграть в игре с одной кучкой, ' \
                           f'вам нужно брать столько камней, чтобы их оставшееся количество делилось на m + 1. ' \
                           f'В нашей куче {chips[0]} {stones}. Можно брать от 1 до {chips_out} камней. '
                    context['chips'][0] -= motion[1]
                    text += f'Я сделаю так, чтобы вы смогли выиграть, и возьму {motion[1]}. Останется {chips[0]}. ' \
                            f'Теперь ваш ход: сколько вы забираете? '
                    return generate_response(req, text)
                elif context['patience'] == 2:
                    text = f'Вы должны привести кучу в такое состояние,' \
                           f' чтобы оно делилось на максимальное количество забираемых камней + 1. ' \
                           f' Попробуйте сходить еще раз.'
                elif context['patience'] == 1:
                    stones = declination(user_motion, 'камень')
                    text = f'Если вы возьмёте {user_motion} {stones}, ' \
                           f'то в куче останется {chips[0]} - число, некратное {chips_out + 1}. Попробуйте ещё раз.'
                context['chips'][0] += user_motion
                return generate_response(req, text)
            else:
                Alice_motion = generate_motion(1, chips, chips_out=chips_out)
                if context['mode'] == 'обучение':
                    # Алиса в режиме обучения хвалит игрока за правильный ответ
                    result = f'Так держать. '
                elif context['mode'] == 'игра':
                    result = f''        #*
                if chips[0] in range(2, 5):
                    result += f'Осталось {chips[0]} камня. '
                elif chips[0] == 1:
                    result += f'Остался 1 камень. '
                else:
                    result += f'Осталось {chips[0]} камней. '
                context['chips'][0] -= Alice_motion[1]
                if context['chips'][0] == 0:
                    context['winner'] = 'Alice'
                    context['game_finished'] = True
                    context['defeats'] += 1
                    if Alice_motion[1] == 1:
                        result += f'Я беру последний. И снова я победила! Не хотите выбрать режим обучения?'
                        audio_id = 'L'
                        context['ask_for_learn'] = True
                    else:
                        result += f'Я беру последние. И снова я победила! Не хотите выбрать режим обучения?'
                        audio_id = 'L'
                        context['ask_for_learn'] = True
                    return gen_but_resp(req, result, fbut='Обучение', sbut='Игра', thbut='Выход', audio_id=audio_id)
                else:
                    result += f'Я беру {Alice_motion[1]}. Остаётся {chips[0]}.'
                    audio_id = ''
                return generate_response(req, result, audio_id)
        elif kuchki == 2 and len(answer_list) == 2 or answer in ['все', 'всё', 'последние', 'последний']:
            if len(answer_list) == 1:
                user_motion = answer_list[0].lower()
                kuchka = r.randint(1, 2)
            elif ('первая' in answer or 'первой' in answer) and \
                    (answer_list[0].lower() == '1' or answer_list[1].lower() == '1'):
                if answer_list[0].lower() == '1':
                    kuchka = answer_list[0].lower()
                    user_motion = answer_list[1].lower()
                else:
                    user_motion = answer_list[0].lower()
                    kuchka = answer_list[1].lower()
            elif ('вторая' in answer or 'второй' in answer) and \
                    (answer_list[0].lower() == '2' or answer_list[1].lower() == '2'):
                if answer_list[0].lower() == '2':
                    kuchka = answer_list[0].lower()
                    user_motion = answer_list[1].lower()
                else:
                    user_motion = answer_list[0].lower()
                    kuchka = answer_list[1].lower()
            elif (answer_list[0].lower().isdigit() or
                    answer_list[0].lower() in ['все', 'всё', 'последние', 'последний'] or
                    answer_list[0].lower() in answ_let_to_num.keys()):
                user_motion = answer_list[0].lower()
                kuchka = answer_list[1].lower()
            else:
                kuchka = answer_list[0].lower()
                user_motion = answer_list[1].lower()

            if kuchka in ['первая', 'первой', '1']:
                kuchka = 1
            else:
                kuchka = 2

            if user_motion in ['все', 'всё', 'последние', 'последний'] and (chips[0] == 0 or chips[1] == 0):
                if context['mode'] == 'игра':
                    context['winner'] = 'user'
                    context['game_finished'] = True
                    context['victories'] += 1
                    if not context['no_learn_game'] and context['twok_tng_finished']:
                        result = f'Вот это победа! Интересно, кто научил вас так играть? Сыграем ещё?'
                    else:
                        result = f'Забирайте, вам нужнее. Поздравляю с победой. ' \
                                 f'Не хотите сыграть ещё?'
                    context['ask_for_play'] = True
                    return gen_but_resp(req, result, fbut='Новая игра', sbut='Обучение', thbut='Выход', audio_id='W')
                elif context['mode'] == 'обучение':
                    context['twok_tng_finished'] = True
                    context['tng_finished'] = True
                    image_id = ''
                    if chips[0] == 0:
                        text = f'Отлично! '                                        # SERTIFICAT
                    else:
                        text = f'Отлично! '
                    if context['onek_tng_finished'] and context['first_learn_game']:
                        # предлагает сертификат о прохождение c двумя кучками и предлагает сыграть с ней,
                        # если у игрока уже есть сертификат об обучении с одной кучкой
                        image_id = '213044/452fd48f51f73c0c767c'
                        efforts = context['efforts']
                        attempts = declination(efforts, 'попытка')
                        if efforts == 1:
                            ushlo = 'ушла'
                        else:
                            ushlo = 'ушло'
                        text += f'Вы завершили обучение с одной и двумя кучами. ' \
                                f'У вас {ushlo} на это суммарно {efforts} {attempts}. ' \
                                f'Не хотите теперь обыграть меня?'
                        context['ask_for_play'] = True
                    if not context['onek_tng_finished'] and context['first_learn_game']:
                        # предлагает сертификат о прохождении с двумя кучками и предлагает пройти обучение с одной
                        image_id = '213044/452fd48f51f73c0c767c'
                        efforts = context['efforts']
                        attempts = declination(efforts, 'попытка')
                        if efforts == 1:
                            ushlo = 'ушла'
                        else:
                            ushlo = 'ушло'
                        text += f'Вы завершили обучение с двумя кучами. ' \
                                f'У вас {ushlo} на это всего лишь {efforts} {attempts}. ' \
                                f'Не хотите теперь пройти обучение с одной?'
                        context['ask_for_learn'] = True
                    elif context['onek_tng_finished'] and not context['first_learn_game']:
                        text += f'Вы снова успешно прошли обучение. Не хотите теперь сыграть? '
                        context['ask_for_play'] = True
                    elif not context['onek_tng_finished'] and not context['first_learn_game']:
                        text += f'Как говориться, повторенье - мать ученья. ' \
                                f'Не хотите теперь пройти обучение с одной кучей? '
                        context['ask_for_learn'] = True
                    context['first_learn_game'] = False
                    return generate_image_response(req, text, image_id=image_id)
            elif user_motion in ['все', 'всё', 'последние', 'последний']:
                # обрабатываем ответ "беру все из *номер кучи*"
                user_motion = chips[kuchka - 1]
            elif user_motion.isdigit():
                user_motion = int(user_motion)
            else:
                user_motion = answ_let_to_num.get(user_motion)
            if user_motion > chips[kuchka - 1]:
                text = r.choice(greedy_sayings)
                stones = declination(chips[kuchka - 1], 'камень')
                if chips[0] != 0 and chips[1] != 0:
                    text += f'Вы можете взять максимум {chips[0]} {stones} из первой кучки или ' \
                            f'{chips[1]} из второй. '
                elif chips[0] == 0:
                    text = f'Не нужно мне поддаваться, заберите оставшиеся камни из второй кучи. '
                else:
                    text = f'Не нужно мне поддаваться, заберите оставшиеся камни из первой кучи. '
                return generate_response(req, text)
            elif user_motion == 0:
                return generate_response(req, f'Извините, но вы не можете не брать камней или брать 0 камней. '
                                              f'Возможный ход - от 1 до {chips[0]} в первой куче '
                                              f'и от 1 до {chips[1]} во второй. ')
            context['chips'][kuchka - 1] -= user_motion
            if chips[0] == 0 and chips[1] == 0:
                if context['mode'] == 'игра':
                    context['winner'] = 'user'
                    context['game_finished'] = True
                    context['victories'] += 1
                    if not context['no_learn_game'] and context['twok_tng_finished']:
                        result = f'Ученик превзошёл мастера! Сыграем ещё?'
                    else:
                        result = f'Ну вот, вы не оставили мне камней, вы победили. Сыграем ещё одну? '
                    context['ask_for_play'] = True
                    return gen_but_resp(req, result, fbut='Новая игра', sbut='Обучение', thbut='Выход', audio_id='W')
                elif context['mode'] == 'обучение':
                    context['twok_tng_finished'] = True
                    context['tng_finished'] = True
                    image_id = ''
                    if chips[0] == 0:
                        text = f'Отлично! '                 # SERTIFICAT
                    else:
                        text = f'Отлично! '
                    if context['onek_tng_finished'] and context['first_learn_game']:
                        # предлагает сертификат о прохождение с двумя кучками и предлагает сыграть с ней,
                        # если у игрока уже есть сертификат об обучении с одной кучкой
                        image_id = '213044/452fd48f51f73c0c767c'
                        efforts = context['efforts']
                        attempts = declination(efforts, 'попытка')
                        if efforts == 1:
                            ushlo = 'ушла'
                        else:
                            ushlo = 'ушло'
                        text += f'Вы завершили обучение с одной и двумя кучами. ' \
                                f'У вас {ushlo} на это суммарно {efforts} {attempts}. ' \
                                f'Не хотите теперь обыграть меня?'
                        context['ask_for_play'] = True
                    if not context['onek_tng_finished'] and context['first_learn_game']:
                        # предлагает сертификат о прохождении с двумя кучками и предлагает пройти обучение с одной
                        image_id = '213044/452fd48f51f73c0c767c'
                        efforts = context['efforts']
                        attempts = declination(efforts, 'попытка')
                        if efforts == 1:
                            ushlo = 'ушла'
                        else:
                            ushlo = 'ушло'
                        text += f'Вы завершили обучение с двумя кучами. ' \
                                f'У вас {ushlo} на это всего лишь {efforts} {attempts}. ' \
                                f'Не хотите теперь пройти обучение с одной?'
                        context['ask_for_learn'] = True
                    elif context['onek_tng_finished'] and not context['first_learn_game']:
                        text += f'Вы снова успешно прошли обучение. Не хотите теперь сыграть? '
                        context['ask_for_play'] = True
                    elif not context['onek_tng_finished'] and not context['first_learn_game']:
                        text += f'Как говориться, повторенье - мать ученья. ' \
                                f'Не хотите теперь пройти обучение с одной кучей? '
                        context['ask_for_learn'] = True
                    context['first_learn_game'] = False
                    return generate_image_response(req, text, image_id)
            elif context['mode'] == 'обучение' and chips[0] != chips[1]:
                # Алиса ругает игрока за неправильный ход
                context['patience'] -= 1
                if context['patience'] == 0:
                    # если терпения не осталось, Алиса начинает обучение сначала,
                    # счётчик попыток пройти обучение увеличивается
                    # инициализация нового обучения и первый ход Алисы
                    context['efforts'] += 1
                    context['patience'] = 3
                    context['chips'] = [r.randint(10, 20), r.randint(10, 20)]  # диапазон камней, две кучи
                    chips = context['chips']
                    motion = generate_motion(2, chips, first_motion=True)
                    stones = declination(chips[0], 'камень')
                    text = f'Давайте начнём сначала: чтобы выиграть в игре с двумя кучами, ' \
                           f'вам нужно брать столько камней, чтобы их оставшееся количество в обоих кучах ' \
                           f'было одинаково. В нашей первой куче {chips[0]} {stones}, а во второй {chips[1]}. '
                    context['chips'][motion[0] - 1] -= motion[1]
                    stones = declination(chips[1], 'камень')
                    text += f'Беру {motion[1]} из {motion[0]}-ой. Остаётся {chips[0]} и {chips[1]} {stones}. ' \
                            f'Сделайте свой ход: назовите количество камней и номер кучки.'
                    return generate_response(req, text)
                elif context['patience'] == 2:
                    text = f'После такого хода Алиса оставит в любой из куч 1 камень, что не позволит Вам выиграть. ' \
                           f'Попробуйте сходить еще раз.'
                elif context['patience'] == 1:
                    text = f'Так и быть, вот главный секрет: сделайте количество камней в кучах одинаковым. ' \
                           f'Только никому не рассказывайте!'
                context['chips'][kuchka - 1] += user_motion
                return generate_response(req, text)
            Alice_motion = generate_motion(2, chips)
            if context['mode'] == 'обучение':
                text = f'Продолжайте в том же духе! '
            elif context['mode'] == 'игра':
                text = f''
            text += f'Осталось {chips[0]} в первой и {chips[1]} во второй. '
            ask = r.randint(1, 10)
            if ask == 5:
                text += f'Хотите расскажу что-то интересное?'
            context['chips'][Alice_motion[0] - 1] -= Alice_motion[1]
            if chips[0] == chips[1] == 0:
                context['winner'] = 'Alice'
                context['game_finished'] = True
                context['ask_for_learn'] = True
                context['defeats'] += 1
                text += f'Я забираю последние. И снова я победила! Не хотите выбрать режим обучения?'
                audio_id = 'L'
                return gen_but_resp(req, text, fbut='Обучение', sbut='Игра', thbut='Выход', audio_id=audio_id)
            else:
                text += f'Беру {Alice_motion[1]} из {Alice_motion[0]}-ой. Остаётся {chips[0]} и {chips[1]}.'
                audio_id = ''
            return generate_response(req, text, audio_id)

    elif context['mode'] == 'игра' and context['game_finished'] and (context['winner'] == 'user' or
                                                                     context['ask_for_play'] or
                                                                     answer in ['игра', 'новая игра', 'выход']) or \
            context['mode'] == 'обучение' and context['tng_finished'] and (context['ask_for_play'] or
                                                                           answer in ['игра', 'новая игра', 'выход']):
        if answer in ['да', 'хочу', 'давай сыграем', 'давай', 'новая игра', 'игра']:
            # сценарий перезапуска игры после победы в игре с алисой
            context['mode'] = 'игра'
            context['kuchki'] = 0
            context['winner'] = None
            context['game_finished'] = False
            context['first_motion'] = False
            context['first_game'] = False
            context['ask_for_play'] = False
            return gen_but_resp(req, 'На сколько куч играем?', fbut='Одна', sbut='Две')
        elif answer in ['нет', 'не хочу', 'нет, спасибо', 'давай в другой раз', 'выход']:
            # выход из сессии
            if answer == 'выход':
                result = f'Спасибо за игру! '
            else:
                result = f'Отлично, я тоже не очень хотела. '
            bye = r.choice(bye_phr_l)
            wins, defs = context['victories'], context['defeats']
            if wins > defs:
                result += f'Счёт в нашем противостоянии {wins}:{defs} в вашу пользу. {bye}'
            elif context['victories'] < context['defeats']:
                result += f'Счёт в нашем противостоянии {wins}:{defs} в мою пользу. {bye}'
            else:
                result += f'Счёт в нашем противостоянии {wins}:{defs}. Победила дружба. {bye}'
            return generate_response(req, result, end_session=True)
        else:
            return generate_response(req, 'Неправильный формат ответа. Пожалуйста, повторите.')

    elif context['mode'] == 'игра' and context['game_finished'] and (context['winner'] == 'Alice' or
                                                                     answer in ['обучение', 'игра', 'новая игра',
                                                                                'выход']) or \
            context['mode'] == 'обучение' and context['tng_finished'] and (context['ask_for_learn'] or
                                                                           answer in ['обучение', 'игра',
                                                                                      'новая игра', 'выход']):
        if answer in ['да', 'хочу', 'включи', 'давай', 'обучение']:
            # сценарий перехода к обучению после проигрыша в игре с алисой/запуска обучения с другим числом кучек
            if context['mode'] == 'игра':
                context['mode'] = 'обучение'
                context['winner'] = None
                context['game_finished'] = False
                context['first_motion'] = False
                context['ask_for_learn'] = False
                if context['no_learn_game']:
                    context['first_learn_game'] = True
                    context['onek_tng_finished'] = False
                    context['twok_tng_finished'] = False
                    context['no_learn_game'] = False
                    context['efforts'] = 1
                else:
                    context['first_learn_game'] = False
                if context['kuchki'] == 1:
                    text = f'Тогда включаю режим обучения для одной кучки. '
                elif context['kuchki'] == 2:
                    text = f'Тогда включаю режим обучения для двух кучек. '
            elif context['mode'] == 'обучение':
                context['first_learn_game'] = False
                if context['kuchki'] == 1:
                    context['kuchki'] = 2
                    text = f'Тогда включаю режим обучения для двух кучек. '
                elif context['kuchki'] == 2:
                    context['kuchki'] = 1
                    text = f'Тогда включаю режим обучения для одной кучки. '
            context['tng_finished'] = False
            context['patience'] = 3
            context['efforts'] = 1
            context['ask_for_learn'] = False
            if context['kuchki'] == 1:
                context['chips'] = [r.randint(15, 20)]  # диапазон камней, одна куча, обучение
                context['max_chips_out'] = r.randint(3, 5)  # максимальное кол-во забираемых камней
                chips = context['chips']
                chips_out = context['max_chips_out']
                motion = generate_motion(1, chips, chips_out=chips_out, first_motion=True)
                stones = declination(chips[0], 'камень')
                text += f'Правила в игре с одной кучкой просты: задаётся начальное количество камней в куче. ' \
                        f'Вы можете брать некоторое m количество этих камней. ' \
                        f'Выигрывает тот, кто забирает последний. ' \
                        f'Чтобы выиграть в такой игре, вам нужно брать столько камней, ' \
                        f'чтобы их оставшееся количество перед последним ходом было на 1 больше максимального. ' \
                        f'Давайте потренируемся. ' \
                        f'В нашей куче {chips[0]} {stones}. Можно брать от 1 до {chips_out} камней. '
                context['chips'][0] -= motion[1]
                text += f'Я возьму {motion[1]}, и останется {chips[0]}. Теперь сделайте свой ход.'
            elif context['kuchki'] == 2:
                context['chips'] = [r.randint(10, 20), r.randint(10, 20)]  # диапазон камней, две кучи
                chips = context['chips']
                motion = generate_motion(2, chips, first_motion=True)
                stones = declination(chips[0], 'камень')
                text += f'Правила в игре с двумя кучками ещё проще, чем с одной: ' \
                        f'задаётся начальное количество камней в двух кучах. ' \
                        f'Вы можете брать любое количество камней из любой одной кучи. ' \
                        f'Выигрывает тот, кто забирает последние. ' \
                        f'Чтобы выиграть в такой игре, вам нужно всегда оставлять камни в обеих кучах, ' \
                        f'иначе Алиса сразу выиграет. Давайте потренируемся. ' \
                        f'В нашей первой куче {chips[0]} {stones}, а во второй {chips[1]}. '
                context['chips'][motion[0] - 1] -= motion[1]
                text += f'Беру {motion[1]} из {motion[0]}-ой. Остаётся {chips[0]} и {chips[1]} камней. ' \
                        f'Сделайте свой ход: скажите номер кучки и количество камней.'
            context['first_motion'] = True
            return generate_response(req, text)

        elif context['mode'] == 'обучение' and answer in ['нет', 'не хочу']:
            # сценарий, при котором игрок откаался от второго обучения, алиса спрашивает, хочет ли он поиграть
            context['ask_for_learn'] = False
            context['ask_for_play'] = True
            return generate_response(req, 'Может тогда сыграем?')
        elif context['mode'] == 'игра' and answer in ['нет', 'не хочу']:
            # сценарий, при котором игрок отказался от обучения после проигрыша,
            # алиса спрашивает, хочет ли он сыграть еще раз
            context['ask_for_learn'] = False
            context['ask_for_play'] = True
            return generate_response(req, 'Хотите взять реванш?')
        elif answer in ['нет, запусти новую игру', 'давай сыграем ещё раз', 'хочу реванш', 'реванш', 'новая игра',
                        'запусти новую игру', 'новая игра', 'игра']:
            # сценарий переапуска игры после проигрыша в игре с алисой
            context['mode'] = 'игра'
            context['kuchki'] = 0
            context['winner'] = None
            context['game_finished'] = False
            context['first_motion'] = False
            context['first_game'] = False
            context['ask_for_learn'] = False
            return gen_but_resp(req, 'На сколько куч играем?', fbut='Одна', sbut='Две')
        elif answer in ['выход', 'спасибо за игру', 'на сегодня все', 'давай закончим']:
            # выход из сессии
            result = f'Было приятно с вами поиграть. '
            bye = r.choice(bye_phr_l)
            wins, defs = context['victories'], context['defeats']
            if wins > defs:
                result += f'Счёт в нашем противостоянии {wins}:{defs} в вашу пользу. {bye}'
            elif context['victories'] < context['defeats']:
                result += f'Счёт в нашем противостоянии {wins}:{defs} в мою пользу. {bye}'
            else:
                result += f'Счёт в нашем противостоянии {wins}:{defs}. Победила дружба. До новых встреч! {bye}'
            return generate_response(req, result, end_session=True)
        else:
            return generate_response(req, 'Неправильный формат ответа. Пожалуйста, повторите.')

    else:
        return generate_response(req, 'Неправильный формат ответа. Пожалуйста, повторите.')


def generate_response(req, text, audio_id='', end_session=False):
    if audio_id == 'W':
        res = {
            "version": req["version"],
            "session": req["session"],
            "response": {
                "end_session": end_session,
                "text": text,
                "tts": '<speaker audio="alice-sounds-game-win-1.opus"> ого! вы не оставили мне камней, '
                       'вы победили. Не хотите сыграть ещё?'
            }
        }

    elif audio_id == 'L':
        res = {
            "version": req["version"],
            "session": req["session"],
            "response": {
                "end_session": end_session,
                "text": text,
                "tts": 'Я забираю последние. <speaker audio="alice-sounds-game-loss-2.opus"> '
                       'И снова я победила! Не хотите выбрать режим обучения?'
            }
        }

    else:
        res = {
            "version": req["version"],
            "session": req["session"],
            "response": {
                "end_session": end_session,
                "text": text
            },
            "session_state": {
                "value": 10
            }
        }
    return json.dumps(res, indent=2)


def generate_image_response(req, text, image_id='', end_session=False):
    if image_id != '':
        res = {
            "version": req["version"],
            "session": req["session"],
            "response": {
                "end_session": end_session,
                "text": '',
                "tts": 'Поздравляем с завершением обучения!',
                'card': {
                    'type': 'BigImage',
                    'image_id': image_id,
                    'title': text
                }
            }
        }

    return json.dumps(res, indent=2)


def gen_but_resp(req, text, fbut, sbut, thbut='', audio_id='', end_session=False):
    if audio_id == 'W' and not thbut:
        res = {
            "version": req["version"],
            "session": req["session"],
            "response": {
                "end_session": end_session,
                "text": text,
                "tts": '<speaker audio="alice-sounds-game-win-1.opus"> ого! вы не оставили мне камней, '
                       'вы победили. Не хотите сыграть ещё?',
                "buttons": [
                    {
                        "title": fbut,
                        "hide": True
                    },
                    {
                        "title": sbut,
                        "hide": True
                    },
                ],
            },

        }
    elif audio_id == 'L' and not thbut:
        res = {
            "version": req["version"],
            "session": req["session"],
            "response": {
                "end_session": end_session,
                "text": text,
                "tts": 'Я забираю последние. <speaker audio="alice-sounds-game-loss-2.opus"> '
                       'И снова я победила! Не хотите выбрать режим обучения?',
                "buttons": [
                    {
                        "title": fbut,
                        "hide": True
                    },
                    {
                        "title": sbut,
                        "hide": True
                    },
                ],
            },

        }
    elif audio_id == 'L':
        res = {
            "version": req["version"],
            "session": req["session"],
            "response": {
                "end_session": end_session,
                "text": text,
                "tts": 'Я забираю последние. <speaker audio="alice-sounds-game-loss-2.opus"> '
                       'И снова я победила! Не хотите выбрать режим обучения?',
                "buttons": [
                    {
                        "title": fbut,
                        "hide": True
                    },
                    {
                        "title": sbut,
                        "hide": True
                    },
                    {
                        "title": thbut,
                        "hide": True
                    },
                ],
            },

        }
    elif audio_id == 'W':
        res = {
            "version": req["version"],
            "session": req["session"],
            "response": {
                "end_session": end_session,
                "text": text,
                "tts": '<speaker audio="alice-sounds-game-win-1.opus"> ого! вы не оставили мне камней, '
                       'вы победили. Не хотите сыграть ещё?',
                "buttons": [
                    {
                        "title": fbut,
                        "hide": True
                    },
                    {
                        "title": sbut,
                        "hide": True
                    },
                    {
                        "title": thbut,
                        "hide": True
                    },
                ],
            },

        }
    else:
        res = {
            "version": req["version"],
            "session": req["session"],
            "response": {
                "end_session": end_session,
                "text": text,
                "buttons": [
                    {
                        "title": fbut,
                        "hide": True
                    },
                    {
                        "title": sbut,
                        "hide": True
                    },
                ],
            },

        }
    return json.dumps(res, indent=2)


def generate_motion(kuchki, chips, chips_out=0, first_motion=False):   # генерирует ход Алисы
    if kuchki == 1:       # ход в игре с одной кучкой
        kuchka = 1        # выбираем из какой кучки брать камни
        chips = chips[0]
        if first_motion:           # первым ходом создаём выигрышную позицию для игрока в игре с одной кучкой
            ost = chips % (chips_out + 1)
            if ost == 0:
                motion = r.randint(1, chips_out)
            elif ost > 1:
                motion = r.randint(1, ost - 1)
            else:
                motion = r.randint(2, chips_out)

        elif chips > chips_out:        # пытаемся привести игрока в проигрышную позицию
            ost = chips % (chips_out + 1)
            if ost == 0:
                motion = r.randint(1, chips_out)
            else:
                motion = ost

        elif chips <= chips_out:    # берём последние
            motion = chips

    elif kuchki == 2:     # ходы при игре с двумя кучками
        difference = abs(chips[0] - chips[1])
        if not difference:
            kuchka = r.randint(1, 2)
            motion = r.randint(1, chips[kuchka - 1])
        elif first_motion:                                # нужно подправить чутка, вылетала ошибка
            if difference == 1:
                if chips[0] < chips[1]:
                    kuchka = 1
                    motion = r.randint(1, chips[0] - 1)
                else:
                    kuchka = 2
                    motion = r.randint(1, chips[1] - 1)
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


def declination(amount, word):
    if word == 'камень' or word == 'попытка':
        if amount == 1 or amount == 21:
            if word == 'камень':
                return 'камень'
            elif word == 'попытка':
                return 'попытка'
        elif (amount) in [2, 3, 4, 22, 23, 24]:
            if word == 'камень':
                return 'камня'
            elif word == 'попытка':
                return 'попытки'
        else:
            if word == 'камень':
                return 'камней'
            elif word == 'попытка':
                return 'попыток'


if __name__ == '__main__':
    db_session.global_init("db/users.db")
    app.run('0.0.0.0', 8080)
