from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from downloader import login as ascode_login, download_user_codes_with_log
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")
user_sessions = {}
download_status = {}  # user_id -> {status: "running"|"done", logs: [...], zip_path: str}

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

@app.post("/download")
async def download(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    user_id = data.get("user_id")
    sess = user_sessions.get(user_id)

    if not sess:
        return JSONResponse({"success": False, "message": "세션이 없습니다."})

    download_status[user_id] = {"status": "running", "logs": [], "zip_path": None}

    def run_download():
        logs = []
        zip_path = None
        for log in download_user_codes_with_log(sess, user_id):
            logs.append(log)
            if log.startswith("ZIP_READY:"):
                zip_path = log.split("ZIP_READY:")[1].strip()
        download_status[user_id] = {"status": "done", "logs": logs, "zip_path": zip_path}

    background_tasks.add_task(run_download)
    return JSONResponse({"success": True, "message": "다운로드가 백그라운드에서 시작되었습니다."})

@app.get("/status")
async def status(user_id: str):
    return download_status.get(user_id, {"status": "not_started"})

@app.get("/get_zip")
async def get_zip(path: str):
    if path and os.path.exists(path):
        return FileResponse(path, filename=os.path.basename(path), media_type="application/zip")
    return JSONResponse({"error": "❌ 파일이 존재하지 않습니다."}, status_code=404)
