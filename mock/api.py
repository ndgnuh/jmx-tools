import random
from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException, Form
from fastapi.security import HTTPBearer
from faker import Faker

faker = Faker()
app = FastAPI()
bearer = HTTPBearer()


@app.get("/items")
def get_item():
    n = random.randint(10, 20)
    results = []
    for i in range(n):
        result = dict(
            id=i,
            name=faker.name()
        )
        results.append(result)
    return results


@app.get("/item/{id}")
def get_item_i(id: int):
    return dict(id=id, name=faker.name())


def validate(authorization=Depends(bearer)):
    if authorization.credentials == "123":
        return True

    raise HTTPException(status_code=403, detail="Unauthorized")


@app.post("/item/new", dependencies=[Depends(validate)])
def mk_item(id: Annotated[int, Form()], name: Annotated[str, Form()]):
    return dict(id=id, name=name)


@app.post("/auth", dependencies=[Depends(validate)])
def auth_stuff():
    return True
