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

@app.post("/download")
async def download(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    sess = user_sessions.get(user_id)

    async def stream_logs():
        if not sess:
            yield "❌ 로그인 세션 없음\n"
            return
        for log_msg in download_user_codes_with_log(sess, user_id):
            yield log_msg + "\n"

    return StreamingResponse(stream_logs(), media_type="text/plain")

@app.get("/get_zip")
async def get_zip(path: str):
    if path and os.path.exists(path):
        return FileResponse(path, filename=os.path.basename(path), media_type="application/zip")
    return JSONResponse({"error": "❌ 파일이 존재하지 않습니다."}, status_code=404)
