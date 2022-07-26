import re
from io import BytesIO

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.types import CallbackQuery, InputMediaAudio, MediaGroup, Message, ContentTypes, InputFile

from app.config import Config, pay
from app.filters.admin import IsAdminFilter
from app.keyboards.inline.post import admin_cb, music_kb, price_cb, admin_kb
from app.keyboards.inline.tracks import tracks_kb, edit_track, track_cb, back_track_cb, back_menu_cb, set_title, \
    set_price

from app.services.repos import PostRepo, TrackRepo, Track, Post
from app.states.admin import AdminSG

PRICE_REGEX = re.compile(
    r'^\d{1,4}$'
)


async def public_in_channel(call: CallbackQuery, callback_data: dict,
                            post_db: PostRepo, track_db: TrackRepo, config: Config):
    post_id = int(callback_data.get('post_id'))
    post = await post_db.get_post_by_post_id(post_id)
    tracks = await track_db.get_tracks_by_post_id(post_id)
    text = await _resolve_post_text(post, tracks)
    send_msg = await call.bot.send_photo(
        chat_id=config.misc.post_channel_chat_id, caption=text, photo=post.photo_id,
        reply_markup=await music_kb(post_id, tracks)
    )
    media = await _media(tracks)
    if media:
        await call.bot.send_media_group(
            chat_id=config.misc.post_channel_chat_id, media=media)
    else:
        media = await _exclusiv_media(tracks)
        await call.bot.send_media_group(
            chat_id=config.misc.sub_channel_chat_id, media=media
        )
    await call.message.delete_reply_markup()
    await call.message.answer(f'<a href="{send_msg.url}">Пост</a> розміщено')


async def edit_tracks(call: CallbackQuery, callback_data: dict, track_db: TrackRepo, state: FSMContext):
    post_id = int(callback_data.get('post_id'))
    tracks = await track_db.get_tracks_by_post_id(post_id)
    call = await call.message.edit_reply_markup(reply_markup=tracks_kb(tracks, post_id))
    await state.update_data(lst_msg_id=call.message_id, post_id=post_id)
    await AdminSG.Track.set()


async def edit_chosen_track(call: CallbackQuery, callback_data: dict, track_db: TrackRepo, state: FSMContext):
    track_id = int(callback_data.get('track_id'))
    track = await track_db.get_tracks_by_track_id(track_id)
    await call.message.edit_reply_markup(edit_track(track))
    await state.update_data(track_id=track_id)
    await AdminSG.Edit.set()


async def edit_track_title(call: CallbackQuery, callback_data: dict, track_db: TrackRepo):
    track_id = int(callback_data.get('track_id'))
    track = await track_db.get_tracks_by_track_id(track_id)
    await call.message.answer(
        f'Введіть нову назву треку у форматі назва треку - виконавець\n\n<pre>{track.title}</pre>'
    )
    await AdminSG.Title.set()


async def save_track_title(msg: Message, track_db: TrackRepo, post_db: PostRepo, state: FSMContext):
    data = await state.get_data()
    track_id = int(data.get('track_id'))
    lst_msg_id = data.get('lst_msg_id')
    post_id = data.get('post_id')

    await track_db.update_track(track_id, title=msg.text)

    tracks = await track_db.get_tracks_by_post_id(post_id)
    track = await track_db.get_tracks_by_track_id(track_id)
    post = await post_db.get_post_by_post_id(post_id)

    await msg.bot.delete_message(chat_id=msg.from_user.id, message_id=lst_msg_id)
    last_msg = await msg.bot.send_photo(
        chat_id=msg.from_user.id, caption=await _resolve_post_text(post, tracks), photo=post.photo_id,
        reply_markup=edit_track(track)
    )
    save_to_io = BytesIO()
    await msg.bot.download_file_by_id(file_id=track.file_id, destination=save_to_io)
    title, performer = msg.text.split(' - ')
    if performer is None:
        performer = 'Unknown'
    msg = await msg.bot.send_media_group(
        chat_id=msg.from_user.id, media=[InputMediaAudio(save_to_io, title=performer, performer=title)]
    )
    await track_db.update_track(track_id, file_id=msg[0].audio.file_id)
    await state.update_data(lst_msg_id=last_msg.message_id)
    await AdminSG.Edit.set()


async def edit_track_price(call: CallbackQuery):
    await call.message.answer(
        f'Введіть нову ціну за трек'
    )
    await AdminSG.Price.set()


async def save_track_price(msg: Message, track_db: TrackRepo, post_db: PostRepo, state: FSMContext):
    data = await state.get_data()
    track_id = int(data.get('track_id'))
    lst_msg_id = data.get('lst_msg_id')
    post_id = data.get('post_id')
    new_price = msg.text

    await track_db.update_track(track_id, price=int(new_price))

    tracks = await track_db.get_tracks_by_post_id(post_id)
    track = await track_db.get_tracks_by_track_id(track_id)
    post = await post_db.get_post_by_post_id(post_id)

    await msg.bot.delete_message(chat_id=msg.from_user.id, message_id=lst_msg_id)
    last_msg = await msg.bot.send_photo(
        chat_id=msg.from_user.id, caption=await _resolve_post_text(post, tracks), photo=post.photo_id,
        reply_markup=edit_track(track)
    )
    await state.update_data(lst_msg_id=last_msg.message_id)
    await AdminSG.Edit.set()


async def _back_to_menu(call: CallbackQuery, callback_data: dict, track_db: TrackRepo):
    post_id = int(callback_data.get('post_id'))
    tracks = await track_db.get_tracks_by_post_id(post_id)
    prices = list(set([track.price for track in tracks]))
    is_free = (0 in prices and len(prices) == 1)
    await call.message.edit_reply_markup(admin_kb(post_id=post_id, is_free=is_free))


async def change_settings(msg: Message):
    data = pay().data
    await msg.bot.send_document(chat_id=msg.from_user.id, document=InputFile('app/handlers/data/details.json', 'settings.json'))
    await msg.answer('Надішліть файл у форматі <b>.json</b> із встановленими налаштуваннями\n\n'
                     f'Поточні параметри:\n<code>{data}</code>')
    await AdminSG.Settings.set()


async def save_settings(msg: Message, state: FSMContext):
    settings = await msg.document.download(destination='app/handlers/data/details.json')
    data = pay().data
    await msg.answer(f'Параметри встановленні успішно:\n<code>{data}</code>')
    await state.finish()


def setup(dp: Dispatcher):
    dp.register_callback_query_handler(public_in_channel, admin_cb.filter(), state='*')
    dp.register_callback_query_handler(edit_tracks, price_cb.filter(), state='*')
    dp.register_callback_query_handler(edit_chosen_track, track_cb.filter(), state=AdminSG.Track)
    dp.register_callback_query_handler(edit_track_title, set_title.filter(), state=AdminSG.Edit)
    dp.register_callback_query_handler(edit_track_price, set_price.filter(), state=AdminSG.Edit)

    dp.register_message_handler(save_track_price, state=AdminSG.Price, regexp=PRICE_REGEX)
    dp.register_message_handler(save_track_title, state=AdminSG.Title)

    dp.register_callback_query_handler(edit_tracks, back_track_cb.filter(), state=AdminSG.Edit)
    dp.register_callback_query_handler(_back_to_menu, back_menu_cb.filter(), state=AdminSG.Track)

    dp.register_message_handler(change_settings, Command('admin'), IsAdminFilter(), state='*')
    dp.register_message_handler(save_settings, state=AdminSG.Settings, content_types=ContentTypes.DOCUMENT)



async def _resolve_post_text(post: Post, tracks: list[Track]) -> str:
    tracks_str = ''
    for track in tracks:
        if track.price == 0:
            tracks_str += f'🎵 {track.title}\n'
        else:
            tracks_str += f'⭐️<b>Платний трек</b>: {track.title}\n'
    return (
        f'Рік випуску: {post.year}\n'
        f'Тип: #{post.type}\n\n' + tracks_str
    )


async def _exclusiv_media(tracks: list[Track]) -> MediaGroup | bool:
    media = []
    for track in tracks:
        if track.price > 0:
            media.append(InputMediaAudio(track.file_id))
    return MediaGroup(media)


async def _media(tracks: list[Track]) -> MediaGroup | bool:
    media = []
    for track in tracks:
        if track.price == 0:
            media.append(InputMediaAudio(track.file_id))
    if media:
        return MediaGroup(media)
    else:
        return False



