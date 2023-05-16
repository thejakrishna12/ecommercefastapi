from fastapi.exceptions import HTTPException
from passlib.context import CryptContext
import jwt
from dotenv import dotenv_values
from models import User
from fastapi import status

config_credentials=dotenv_values(".env")
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def get_hashed_password(password):
    return pwd_context.hash(password)

async def very_token(token: str):
    # try:
    #"67c5e0911a91328960faaa61cb05333d30ed15f6"
        #payload=jwt.decode(token, "config_credential['SECRET']", algorithms=['HS256'])
        payload=jwt.decode(token, "67c5e0911a91328960faaa61cb05333d30ed15f6", algorithms=['HS256'])
        print(payload)
        user = await User.get(id = payload.get("id"))
        print(user)
    # except:
        # raise HTTPException(
        #     status_code = status.HTTP_401_UNAUTHORIZED,
        #     detail = "Invalid token",
        #     headers={"WWW.Authenticate":"Bearer"}

        # )
        return user
async def verify_password(plain_password,hashed_password):
      return pwd_context.verify(plain_password, hashed_password)
async def authenticate_user(username, password):
      user = await User.get(username = username)

      if user and verify_password(password, user.password):
            return user
      return False
async def token_generator(username:str, password: str):
      user = await authenticate_user(username, password)

      if not user:
            raise HTTPException(
                  status_code=status.HTTP_401_UNAUTHORIZED,
                  detail="Invalid username or password",
                  headers={"WWW.Authenticate":"Bearer"}
            )
      token_data  = {
            "id" : user.id,
            "username":user.username
      }

      token = jwt.encode(token_data, config_credentials['SECRET'])
      return token