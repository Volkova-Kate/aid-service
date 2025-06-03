import json

from aiogram import Router
from aiogram.enums import ChatAction
from aiogram.types import Message
from aiohttp import FormData
from core.async_requests import aioreq
from core.auth import registration, status_checker, tg_auth_cred
from core.auth import registration, tg_auth_cred
from core.utils import COMMAND_LIST

router = Router()


async def create_report(text: str, tags: list[str], user_id: int) -> str:
    data = await aioreq.request_json(
        "/report/",
        "POST",
        json={"input": text, "tags": tags, "count": 5},  # Добавление параметра count
        auth=tg_auth_cred(user_id),
    )
    response = ""  # Инициализируем переменную для хранения ответа

    for bureau in data["bureaus"]:  # Предполагаем, что сервер возвращает список бюро
        response += f"""[{bureau["name"]}]({bureau["cite"]})\n\n{bureau["description"]}\n\n{bureau["add_info"]["year"]}, {bureau["add_info"]["country"]}\n\n"""

    return response



async def assistant(message: Message) -> str:
    user_id = message.from_user.id
    data = FormData() if message.photo else None

    if message.photo:
        photo_bytes = (await message.bot.download(message.photo[-1].file_id)).getvalue()
        data.add_field(
            "input_data",
            json.dumps({"input": message.text}),
            content_type="application/json",
        )
        data.add_field(
            "file", photo_bytes, filename="image.jpg", content_type="image/jpeg"
        )

    resp = await aioreq._request(
        "/assistant/visual" if message.photo else "/assistant/",
        method="POST",
        json=None if data else {"input": message.text},
        data=data,
        auth=tg_auth_cred(user_id),
    )

    if code_str := await status_checker(resp.status, user_id):
        return code_str

    result = await resp.json(encoding="utf-8")

    if result["agent_type"] == "support":
        return result["response"]
    elif result["agent_type"] == "urban":
        corr = result["response"]["correction"]
        return (
            "\n".join(corr) + "\n(Переформулируйте запрос\nReframe your request)"
            if corr
            else await create_report(
                message.text,
                [result["response"]["base_params"]["function"]] + result["response"]["base_params"]["tags"]
                + result["response"]["criteria"]["tags"],
                user_id,
            )
        )
    elif result["agent_type"] == "visual":
        if not result["response"]["is_design"]:
            return "На изображении нет архитектурного объекта!\nThere is no architectural object in the image!"
        return await create_report(
            f"{message.text}\nAbout building:\n{result['response']['description']}",
            result["response"]["tags"],
            user_id,
        )

    return "Я не могу ответить на данный вопрос..."


@router.message(lambda msg: msg.text not in ["/" + k for k in COMMAND_LIST.keys()])

async def any_message(message: Message):
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    response = await assistant(message)
    await message.answer(response, parse_mode="Markdown")
