from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from downloader import login as ascode_login, download_user_codes_with_log, count_user_submissions
import os, time
from threading import Thread

app = FastAPI()
templates = Jinja2Templates(directory="templates")

user_sessions = {}
download_status = {}  # user_id -> dict(status, logs, zip_path, start_time, progress)

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

    total = count_user_submissions(sess, user_id)  # 총 제출 수 추정 함수
    download_status[user_id] = {
        "status": "running",
        "logs": [],
        "zip_path": None,
        "start_time": time.time(),
        "progress": {"current": 0, "total": total, "percent": 0.0}
    }

    def run_download():
        zip_path = None
        downloaded = 0
        total_count = total or 1

        for log in download_user_codes_with_log(sess, user_id):
            downloaded += 1 if log.startswith("✅") else 0

            progress_str = f"[{downloaded}/{total_count}] ({(downloaded/total_count)*100:.1f}%)"
            download_status[user_id]["progress"] = {
                "current": downloaded,
                "total": total_count,
                "percent": (downloaded / total_count) * 100
            }

            download_status[user_id]["logs"].append(f"{log}\n{progress_str}")

            if log.startswith("ZIP_READY:"):
                zip_path = log.split("ZIP_READY:")[1].strip()
                download_status[user_id]["zip_path"] = zip_path

        download_status[user_id]["status"] = "done"

        # ✅ ZIP 파일 삭제 예약 (1시간 뒤)
        if zip_path:
            def delete_zip_later(path, delay=3600):
                time.sleep(delay)
                if os.path.exists(path):
                    os.remove(path)
            Thread(target=delete_zip_later, args=(zip_path,), daemon=True).start()

    background_tasks.add_task(run_download)
    return JSONResponse({"success": True, "message": "다운로드가 백그라운드에서 시작되었습니다."})

@app.get("/status")
async def status(user_id: str):
    status_info = download_status.get(user_id)
    if not status_info:
        return {"status": "not_started"}

    elapsed = time.time() - status_info.get("start_time", time.time())
    progress = status_info.get("progress", {"current": 0, "total": 0, "percent": 0.0})
    eta = None

    if progress["percent"] > 0:
        total_estimated = elapsed / (progress["percent"] / 100)
        eta = int(total_estimated - elapsed)

    return {
        **status_info,
        "eta_seconds": eta
    }

@app.get("/get_zip")
async def get_zip(path: str):
    if path and os.path.exists(path):
        return FileResponse(path, filename=os.path.basename(path), media_type="application/zip")
    return JSONResponse({"error": "❌ 파일이 존재하지 않습니다."}, status_code=404)
