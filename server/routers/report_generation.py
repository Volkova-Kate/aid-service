@router.post("/", response_model=schemas.BureauResponse)
async def report(
    input_data: schemas.BureauInput,
    user: User = Depends(get_available_user),
    db: AsyncSession = Depends(get_session),
):
    bureaus = await get_relevant_bureau(input_data.tags, res_count=5)  # Изменено с 3 на 5
    resp = await writer_llm.ainvoke({"input": input_data.input, "bureaus": bureaus})
    
    # Создаем список для всех бюро, включая лучшее
    result_bureaus = []
    
    # Добавляем лучшее бюро с подробным описанием
    best_bureau = [b for b in bureaus if b["name"] == resp["name"]][0]
    result_bureaus.append({
        "name": resp["name"],
        "description": resp["description"],
        "cite": best_bureau["cite"],
        "add_info": {
            "year": best_bureau["year"],
            "country": best_bureau["country"],
            "projects": best_bureau["projects"],
        },
        "is_best": True
    })
    
    # Добавляем остальные бюро с краткой информацией
    for bureau in bureaus:
        if bureau["name"] != resp["name"]:
            result_bureaus.append({
                "name": bureau["name"],
                "description": f"Альтернативное бюро для вашего проекта",
                "cite": bureau["cite"],
                "add_info": {
                    "year": bureau["year"],
                    "country": bureau["country"],
                    "projects": bureau["projects"],
                },
                "is_best": False
            })
    
    user.available_requests -= 1
    await db.commit()

    return {"bureaus": result_bureaus}

