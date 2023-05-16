from fastapi import FastAPI, Request, HTTPException,status ,Depends
from starlette.requests import Request
from starlette.responses import HTMLResponse
from tortoise import models
from tortoise.contrib.fastapi import register_tortoise
from models import*
from authentication import (get_hashed_password, very_token)

# Authentication
from authentication import*
from fastapi.security import (OAuth2PasswordBearer,OAuth2PasswordRequestForm)



#signals
from tortoise.signals import post_save
from typing import List,Optional,Type
from tortoise import BaseDBAsyncClient
from maill import send_email
#response classes
from fastapi.responses import HTMLResponse
# templates
from fastapi.templating import Jinja2Templates
# images
from fastapi import File, UploadFile
import secrets
from fastapi.staticfiles import StaticFiles
from PIL import Image
app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

# static file setup config
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post('/token')
async def generate_token(request_form: OAuth2PasswordRequestForm=Depends()):
    token = await token_generator(request_form.username,request_form.password)
    return {"access_token" : token, "token_type": "bearer"}



async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, config_credentials["SECRET"], algorithms=['HS256'])
        user = await User.get(id = payload.get("id"))
    except:
        raise HTTPException(
                  status_code=status.HTTP_401_UNAUTHORIZED,
                  detail="Invalid username or password",
                  headers={"WWW.Authenticate":"Bearer"}
            )
    return await user

@app.post("/user/me")
async def user_login(user: user_pydanticIn = Depends(get_current_user)):
    business = await Business.get(owner = user)

    return {
        "status": "ok",
        "data": {
            "username" : user.username,
            "email" : user.email,
            "verified" : user.is_verified,
            "joined_data" : user.join_date.strftime("%b %d %y" )
        }
    }
@post_save(User)
async def create_business(
    sender : "Type[User]",
    instance : User,
    created:bool,
    using_db: "Optional[BaseDBAsyncClient]",
    update_fields:List[str]
)-> None:
    
    if created:
        business_obj = await Business.create(
            business_name = instance.username, owner = instance
        )

        await business_pydantic.from_tortoise_orm(business_obj)
        # send the email
        await send_email([instance.email], instance)

@app.post("/registration")
async def user_registrations(user: user_pydanticIn):
    user_info = user.dict(exclude_unset=True)
    user_info["password"] = get_hashed_password(user_info["password"])
    user_obj = await User.create(**user_info)
    new_user = await user_pydantic.from_tortoise_orm(user_obj)
    return{
        "status": "ok",
        "data" : f"Hello{new_user.username}thanks for choosing our service. please check the email inbox and click on te link to confirm your registration"
    }
templates= Jinja2Templates(directory="templates")
@app.get('/verification', response_class=HTMLResponse)
async def email_verification(request:Request, token:str):
    user = await very_token(token)

    if user and not user.is_verified:
        user.is_verified = True
        await user.save()
        return templates.TemplateResponse("verification.html", {"request":request, "username":user.username})



    raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid token or expired token",
            headers={"WWW.Authenticate":"Bearer"} )


@app.get("/")
def index():
    return {"message":"Hello world"}


@app.post("uploadfile/profile")
async def create_upload_file(file: UploadFile = File(...),
                                user: user_pydantic = Depends(get_current_user)):
    
    FILEPATH = "./static/images"
    filename = file.filename
    # test.png
    extension = filename.split(".")
    if extension not in ["png","jpg"]:
        return {"status":"error", "detail":"File extension not allowed"}
    

    # ucycj343.png
    token_name = secrets.token_hex(10)+"."+extension
    generate_name = FILEPATH + token_name
register_tortoise(
    app,
    db_url="sqlite://database.sqlite3",
    modules={"models":["models"]},
    generate_schemas=True,
    add_exception_handlers=True

)
