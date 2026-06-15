from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import lead, triage, dispatch, arrival, report

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="口腔连锁分诊派单系统",
    description="统一电话咨询、线上预约、到店首访前预分诊，减少约错医生/约错院区/到店再改的情况",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(lead.router, prefix="/api/v1")
app.include_router(triage.router, prefix="/api/v1")
app.include_router(dispatch.router, prefix="/api/v1")
app.include_router(arrival.router, prefix="/api/v1")
app.include_router(report.router, prefix="/api/v1")


@app.get("/", tags=["系统"])
def root():
    return {
        "service": "口腔连锁分诊派单系统",
        "version": "1.0.0",
        "modules": ["线索入口", "分诊规则", "派单中心", "到店确认", "运营复盘"],
    }


@app.get("/health", tags=["系统"])
def health():
    return {"status": "ok"}
