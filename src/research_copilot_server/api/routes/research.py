from fastapi import APIRouter,Depends,status
from sqlalchemy.orm import Session
from research_copilot_server.config.db import get_db
from research_copilot_server.schema.research import UserQueryBody,UserQueryResponse

router = APIRouter()

@router.post("/",status_code=status.HTTP_201_CREATED,response_model=UserQueryResponse)
def register_user_query(user_query:UserQueryBody,db:Session=Depends(get_db)):
    print(user_query)


    return {"id":1,"query":user_query.query,"status":"created"}


