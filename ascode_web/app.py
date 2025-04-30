import os
from flask import Flask, request, render_template, session, Response, jsonify, send_file
from downloader import login as ascode_login, download_user_codes_with_log

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

user_sessions = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user_id = data.get("user_id")
    password = data.get("password")

    sess = ascode_login(user_id, password)
    if sess:
        session["user_id"] = user_id
        user_sessions[user_id] = sess
        return jsonify(success=True)
    return jsonify(success=False)

@app.route("/download", methods=["POST"])
def download():
    data = request.get_json()
    user_id = data.get("user_id")
    sess = user_sessions.get(user_id)

    def generate_logs():
        if not sess:
            yield "❌ 로그인 세션 없음\n"
            return

        from downloader import download_user_codes_with_log
        for log_msg in download_user_codes_with_log(sess, user_id):
            yield log_msg + "\n"  # 실시간 로그 메시지 전달

    return Response(generate_logs(), mimetype="text/plain")

@app.route("/get_zip")
def get_zip():
    zip_path = request.args.get("path")
    if zip_path and os.path.exists(zip_path):
        return send_file(zip_path, as_attachment=True)
    return "❌ 파일이 존재하지 않습니다.", 404

if __name__ == "__main__":
    app.run(debug=True, threaded=True)  # threaded=True로 요청을 동시에 처리하도록 함
