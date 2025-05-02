from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from downloader import login as ascode_login, download_user_codes_with_log
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")
user_sessions = {}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/login")
async def login(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    password = data.get("password")

    sess = ascode_login(user_id, password)
    if sess:
        user_sessions[user_id] = sess
        return JSONResponse({"success": True})
    return JSONResponse({"success": False})

# 백그라운드 태스크 등록용 딕셔너리
background_tasks = {}

@app.post("/download")
async def download(request: Request, background_tasks_param: BackgroundTasks):
    data = await request.json()
    user_id = data["user_id"]
    sess = user_sessions.get(user_id)
    
    if not sess:
        return {"success": False, "message": "세션 없음"}

    def run_download():
        logs = []
        for log in download_user_codes_with_log(sess, user_id):
            logs.append(log)
        background_tasks[user_id] = {
            "status": "done",
            "logs": logs
        }

    background_tasks[user_id] = {"status": "running"}
    background_tasks_param.add_task(run_download)

    return {"success": True, "message": "백그라운드 다운로드 시작"}


@app.get("/get_zip")
async def get_zip(path: str):
    if path and os.path.exists(path):
        return FileResponse(path, filename=os.path.basename(path), media_type="application/zip")
    return JSONResponse({"error": "❌ 파일이 존재하지 않습니다."}, status_code=404)
