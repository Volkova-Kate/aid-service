import core.schemas as schemas
from agents.bureau_agents import generate_writer_agent
from core.auth import User, get_available_user
from core.databases import get_relevant_bureau, get_session
from core.llm import embeddings, llm
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/report")

writer_llm = generate_writer_agent(llm)


@router.post("/", response_model=schemas.BureausResponse)  # Изменить response_model
async def report(
    input_data: schemas.BureauInput,
    user: User = Depends(get_available_user),
    db: AsyncSession = Depends(get_session),
):
    bureaus = await get_relevant_bureau(input_data.tags, res_count=5)  # Изменить на 5
    
    # Получаем описания для всех 5 бюро
    results = []
    for bureau in bureaus:
        resp = await writer_llm.ainvoke({"input": input_data.input, "bureaus": [bureau]})
        result = {
            "name": bureau["name"],
            "description": resp["description"],
            "cite": bureau["cite"],
            "add_info": {
                "year": bureau["year"],
                "country": bureau["country"],
                "projects": bureau["projects"],
            },
        }
        results.append(result)

    user.available_requests -= 1
    await db.commit()

    return {"bureaus": results}
