from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from downloader import login as ascode_login, download_user_codes_with_log, get_submission_list, download_selected_runids
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

@app.get("/submissions")
async def submissions(user_id: str):
    sess = user_sessions.get(user_id)
    if not sess:
        return JSONResponse({"success": False, "message": "세션이 없습니다."})
    subs = get_submission_list(sess, user_id)
    return JSONResponse({"success": True, "submissions": subs})

@app.post("/download")
async def download(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    user_id = data.get("user_id")
    sess = user_sessions.get(user_id)

    if not sess:
        return JSONResponse({"success": False, "message": "세션이 없습니다."})

    download_status[user_id] = {
        "status": "running",
        "logs": [],
        "zip_path": None,
        "start_time": time.time(),
        "progress": {"current": 0, "total": 0, "percent": 0.0}
    }

    def run_download():
        zip_path = None
        for log in download_user_codes_with_log(sess, user_id):
            import re
            match = re.search(r"\[(\d+)/(\d+)]\s+\((\d+(?:\.\d+)?)%\)", log)
            if match:
                download_status[user_id]["progress"] = {
                    "current": int(match[1]),
                    "total": int(match[2]),
                    "percent": float(match[3])
                }
            if log.startswith("ZIP_READY:"):
                zip_path = log.split("ZIP_READY:")[1].strip()
                download_status[user_id]["zip_path"] = zip_path
            download_status[user_id]["logs"].append(log)

        download_status[user_id]["status"] = "done"
        if zip_path:
            def delete_zip_later(path, delay=3600):
                time.sleep(delay)
                if os.path.exists(path):
                    os.remove(path)
            Thread(target=delete_zip_later, args=(zip_path,), daemon=True).start()

    background_tasks.add_task(run_download)
    return JSONResponse({"success": True})

@app.post("/download_selected")
async def download_selected(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    user_id = data.get("user_id")
    runids = data.get("runids")
    sess = user_sessions.get(user_id)

    if not sess or not runids:
        return JSONResponse({"success": False, "message": "세션 또는 RunID 누락"})

    download_status[user_id] = {
        "status": "running",
        "logs": [],
        "zip_path": None,
        "start_time": time.time(),
        "progress": {"current": 0, "total": len(runids), "percent": 0.0}
    }

    def run_download():
        zip_path = None
        for log in download_selected_runids(sess, user_id, runids):
            import re
            match = re.search(r"\[(\d+)/(\d+)]\s+\((\d+(?:\.\d+)?)%\)", log)
            if match:
                download_status[user_id]["progress"] = {
                    "current": int(match[1]),
                    "total": int(match[2]),
                    "percent": float(match[3])
                }
            if log.startswith("ZIP_READY:"):
                zip_path = log.split("ZIP_READY:")[1].strip()
                download_status[user_id]["zip_path"] = zip_path
            download_status[user_id]["logs"].append(log)

        download_status[user_id]["status"] = "done"
        if zip_path:
            def delete_zip_later(path, delay=3600):
                time.sleep(delay)
                if os.path.exists(path):
                    os.remove(path)
            Thread(target=delete_zip_later, args=(zip_path,), daemon=True).start()

    background_tasks.add_task(run_download)
    return JSONResponse({"success": True})

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
