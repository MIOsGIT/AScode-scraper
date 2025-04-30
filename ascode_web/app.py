from flask import Flask, request, render_template, session, Response, jsonify
from downloader import login as ascode_login, download_user_codes_with_log  # ✅ 함수명 수정

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
    data = request.get_json()  # ✅ JSON 데이터를 먼저 밖에서 가져오기
    user_id = data.get("user_id")
    sess = user_sessions.get(user_id)

    def generate_logs():
        if not sess:
            yield "❌ 로그인 세션 없음\n"
            return

        from downloader import download_user_codes_with_log
        for log_msg in download_user_codes_with_log(sess, user_id):
            yield log_msg + "\n"

    return Response(generate_logs(), mimetype="text/plain")



if __name__ == "__main__":
    app.run(debug=True)
