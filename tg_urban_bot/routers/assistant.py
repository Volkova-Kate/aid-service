from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.filters import StateFilter
from aiogram.types import Message
from core.async_requests import aioreq
from core.auth import registration, tg_auth_cred
from core.bot import bot
from core.utils import COMMAND_LIST

router = Router()


async def create_report(input_text: str, tags: list[str], user_id: int) -> str:
    return await aioreq.request_json(
        "/report",
        method="POST",
        json={"input": input_text, "tags": tags},
        auth=tg_auth_cred(user_id),
    )


async def assistant(message: Message) -> dict | str:
    resp = await aioreq._request(
        "/assistant",
        method="POST",
        json={"input": message.text},
        auth=tg_auth_cred(message.from_user.id),
    )
    if resp.status == 401:
        await registration(message.from_user.id)
        resp = await aioreq._request(
            "/assistant",
            method="POST",
            json={"input": message.text},
            auth=tg_auth_cred(message.from_user.id),
        )
    print(resp)
    if resp.status == 403:
        return "У Вас закончились запросы. Оформите новые...\nYou have run out of requests. Make new ones..."
    elif resp.status != 200:
        return "Запрос не корректный!\nThe request is incorrect!"

    result = await resp.json(encoding="utf-8")

    match result["agent_type"]:
        case "simple":
            return result["response"]
        case "urban":
            if corr := result["response"]["correction"]:
                return (
                    "\n".join(corr)
                    + "\n(Пожалуйста, напишите Ваш запрос заново с учетом ответов на эти вопросы.\nPlease, re-write your request based on the answers to the questions.)"
                )
            else:
                report = await create_report(
                    message.text,
                    [result["response"]["base_params"]["function"]]
                    + result["response"]["criteria"]["tags"],
                    user_id=message.from_user.id,
                )

                return f"""[{report["name"]}]({report["cite"]})

{report["description"]}

{report["add_info"]["year"]}, {report["add_info"]["country"]}
"""


@router.message(
    StateFilter(None), F.text.not_in(["/" + k for k in COMMAND_LIST.keys()])
)
async def any_message(message: Message):
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    await message.answer(await assistant(message), parse_mode="Markdown")
