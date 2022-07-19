import os
import re
from datetime import datetime
from io import BytesIO

from PIL import Image
from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import MediaGroupFilter
from aiogram.types import Message, ContentType, MediaGroup, InputMediaAudio, InputFile, CallbackQuery

from app.config import Config
from app.handlers.private.start import command_start
from app.keyboards.inline.post import admin_kb, exclusive_cb
from app.keyboards.reply.post import cancel_kb, type_kb, send_kb, confirm_kb
from app.services.repos import TrackRepo, PostRepo, UserRepo, SubscriptRepo
from app.states.post import PostSG


YEAR_REGEX = re.compile(
    r'^\d{4,4}$'
)


async def start_post(msg: Message, state: FSMContext):
    text = (
        'Щоб розмістити трек в спільноті, для початку надішліть нам '
        '<b>рік випуску</b> треку/альбому (наприклад 1960)'
    )
    await msg.answer(text)
    await state.update_data(tracks=[], exclusive=False)
    await PostSG.Year.set()


async def add_one_track(msg: Message, state: FSMContext, track_db: TrackRepo, group: bool = False):
    title = await _get_track_param(msg)
    bitrate = await _bitrate(msg)
    if not title:
        await msg.answer('Заборонений символ "_" у назві файлу')
    elif bitrate < 320:
        await msg.answer(f'Якість треку має бути більшою за 320 Kbps замість {bitrate} Kbps')
        return
    file_id = msg.audio.file_id
    extend = await _extend_new_track(title, file_id, state, track_db)
    if not extend:
        await msg.answer('Ви не можете завантажити більше 10 треків')
    if not group:
        await msg.answer('Трек успішно додано 👌', reply_markup=confirm_kb)


async def add_group_of_track(msg: Message, state: FSMContext, media: list[Message], track_db: TrackRepo):
    for m in media:
        await add_one_track(m, state, track_db, group=True)
    await msg.answer('Треки успішно додано 👌', reply_markup=confirm_kb)


async def add_and_check_photo(msg: Message, state: FSMContext, config: Config):
    check_photo = await _check_photo_size(msg)
    if check_photo:
        await resolve_photo_file_id(msg, state, config)
        text = (
            'Щоб розмістити трек в спільноті, для початку надішліть нам <b>файл(и)'
            'у форматі mp3</b> (до 10 файлів), та натисніть "✅ Готово"'
        )
        await msg.answer(text, reply_markup=cancel_kb)
        await PostSG.Audio.set()
    else:
        height, width = check_photo
        await msg.answer(f'Розміри фото мають бути 1000x1000 замість {height}x{width}')


async def add_year(msg: Message, state: FSMContext):
    year = int(msg.text)
    if year > datetime.now().year:
        return
    else:
        await state.update_data(year=str(year))
        await msg.answer('Оберіть один з варіантів', reply_markup=type_kb)
        await PostSG.Type.set()


async def add_new_type(msg: Message, state: FSMContext):
    group_type = msg.text
    types = ['Remix', 'Official Remix', 'Original Track',
             'Mashup', 'Mix', 'Live Mix', 'Acapella']
    if group_type in types:
        await state.update_data(type=group_type)
        text = (
            'Для продовження завантажте <b>обкладинку</b> для релізу\n(розмір картинки 1000x1000 пікселів)'
        )
        await msg.answer(text)
        await PostSG.Wrapper.set()


async def confirm_track(msg: Message, state: FSMContext):
    await msg.answer('Ваш пост готовий. Підтвердіть або скасуйте відправку', reply_markup=send_kb)
    await _send_preview_post(msg, state)
    await PostSG.Send.set()


async def send_to_moderator(msg: Message, state: FSMContext, config: Config,
                            post_db: PostRepo, track_db: TrackRepo, user_db: UserRepo, sub_db: SubscriptRepo):
    text, photo_id, media = await _construct_post(state)

    data = await state.get_data()
    photo_id = data['photo_id']
    year = data['year']
    group_type = data['type'].replace(' ', '_')
    track_ids = [int(track['track_id']) for track in data['tracks']]
    exclusive = data['exclusive']

    exclusive_text = ''
    if exclusive:
        exclusive_text = 'Користувач вибрав пост як <b>екслюзивний</b> ⭐️\n\n'

    text = f'Від [{msg.from_user.get_mention()}]\n\n' + exclusive_text + text

    price = 0
    if exclusive:
        price = 1

    post = await post_db.add(type=group_type, year=year, photo_id=photo_id)
    for track_id in track_ids:
        await track_db.update_track(track_id, post_id=post.post_id, price=price)

    is_free = False if exclusive else True
    reply_markup = admin_kb(post_id=post.post_id, is_free=is_free)
    for admin_id in config.bot.admin_ids:
        await msg.bot.send_photo(chat_id=admin_id, photo=photo_id, caption=text, reply_markup=reply_markup)
        await msg.bot.send_media_group(chat_id=admin_id, media=media)

    await msg.answer('Дякуємо,за співпрацю! Ваш трек на модерації')
    await state.finish()
    await command_start(msg, user_db, sub_db)


async def exclusive_post(call: CallbackQuery, state: FSMContext):
    await call.answer('Тепер ваш пост ексклюзивний')
    await call.message.delete_reply_markup()
    await state.update_data(exclusive=True)


def setup(dp: Dispatcher):
    dp.register_message_handler(start_post, text='Розмістити трек 🎵', state='*')
    dp.register_message_handler(add_year, regexp=YEAR_REGEX, state=PostSG.Year)
    dp.register_message_handler(add_new_type, state=PostSG.Type)
    dp.register_message_handler(
        add_and_check_photo, MediaGroupFilter(False), content_types=ContentType.PHOTO, state=PostSG.Wrapper
    )
    dp.register_message_handler(
        add_one_track, MediaGroupFilter(False), content_types=ContentType.AUDIO, state=PostSG.Audio
    )
    dp.register_message_handler(
        add_group_of_track, MediaGroupFilter(True), content_types=ContentType.AUDIO, state=PostSG.Audio
    )
    dp.register_message_handler(confirm_track, text='✅ Готово', state=PostSG.Audio)
    dp.register_callback_query_handler(exclusive_post, text='exclusive', state=PostSG.Send)
    dp.register_message_handler(send_to_moderator, text='Відправити ⤴️', state=PostSG.Send)


async def _get_track_param(msg: Message):
    title = msg.audio.title
    performer = msg.audio.performer
    file_name = msg.audio.file_name
    if title and performer:
        return f'{title} - {performer}'
    elif '_' in file_name:
        return False
    else:
        return file_name.replace('.mp3', '')


async def _extend_new_track(title: str, file_id: str, state: FSMContext, track_db: TrackRepo):
    data = await state.get_data()
    tracks = data['tracks']
    if not len(tracks) == 10:
        track = await track_db.add(title=title, file_id=file_id)
        tracks.append(dict(title=title, file_id=file_id, track_id=track.track_id))
        await state.update_data(tracks=tracks)
        return True
    return False


async def _check_photo_size(msg: Message):
    width = msg.photo[-1].width
    height = msg.photo[-1].height
    if width >= 500 and height >= 500:
        return True
    else:
        return height, width


async def _send_preview_post(msg: Message, state: FSMContext):
    text, photo_id, media = await _construct_post(state)
    await msg.bot.send_photo(chat_id=msg.from_user.id, caption=text, photo=photo_id, reply_markup=exclusive_cb)
    await msg.bot.send_media_group(chat_id=msg.from_user.id, media=media)


async def _construct_post(state: FSMContext):
    data = await state.get_data()
    tracks = data['tracks']
    photo_id = data['photo_id']
    year = data['year']
    group_type = data['type'].replace(' ', '_')

    track_ids = [track['file_id'] for track in tracks]
    track_titles = [track['title'] for track in tracks]

    tracks_str = ''
    num = 1
    for track in track_titles:
        tracks_str += f'{num}. {track}\n'
        num += 1

    text = (
            f'Рік випуску: {year}\n'
            f'Тип: #{group_type}\n\n' + tracks_str
    )
    return text, photo_id, await _media(track_ids)


async def _media(track_ids: list) -> MediaGroup:
    return MediaGroup([InputMediaAudio(track_id) for track_id in track_ids])


async def resolve_photo_file_id(msg: Message, state: FSMContext, config: Config):
    n = str(len(os.listdir('app/data')))

    input_path = BytesIO()
    output_path = 'app/data/output' + n + '.png'
    resize_logo = BytesIO()
    watermark_path = config.misc.logo

    # resize logo
    logo = Image.open(watermark_path)
    logo_width, logo_height = logo.size
    photo_width = msg.photo[-1].width
    photo_height = msg.photo[-1].height
    new_width = int(0.6*photo_width/1.4)
    new_height = int(new_width*logo_height/logo_width)
    logo = logo.resize((new_width, new_height), Image.ANTIALIAS)
    logo.save(resize_logo, 'PNG')

    position = (int(photo_width-new_width), int(0.8*photo_height))

    await msg.photo[-1].download(destination_file=input_path)
    watermark_with_transparency(input_path, output_path, resize_logo, position=position)
    msg = await msg.bot.send_photo(
        chat_id=config.misc.photo_channel_chat_id, photo=InputFile(output_path, filename='photo.png')
    )
    os.remove(output_path)
    await state.update_data(photo_id=msg.photo[-1].file_id)


def watermark_with_transparency(input_image_path, output_image_path,
                                watermark_image_path, position):
    base_image = Image.open(input_image_path)
    watermark = Image.open(watermark_image_path)
    width, height = base_image.size

    transparent = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    transparent.paste(base_image, (0, 0))
    transparent.paste(watermark, position, mask=watermark)
    transparent.save(output_image_path, 'PNG')


async def _bitrate(msg: Message):
    file_size = msg.audio.file_size*0.008
    return int(file_size/msg.audio.duration)
