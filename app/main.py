from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import router as auth_router
from app.admin import router as admin_router
from app.photos import router as photos_router
from app.events import router as events_router
from app.visitor_info import router as visitor_info_router
from app.notices import router as notices_router



app = FastAPI(
    title="Durga Puja Admin API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(photos_router)
app.include_router(events_router)
app.include_router(visitor_info_router)
app.include_router(notices_router)



@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "durga-puja-admin-api",
    }