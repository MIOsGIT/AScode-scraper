<h1 align="center">📦 AScode-scraper</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Python-FF69B4?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Flask-EA7CAA?style=for-the-badge&logo=flask&logoColor=white" alt="Flask" />
  <img src="https://img.shields.io/badge/Render-D85D93?style=for-the-badge&logo=render&logoColor=white" alt="Render" />
</p>

<p align="center">
  <b>AScode 온라인 저지에 제출한 내 정답 코드를 ZIP으로 백업하는 웹 도구</b><br />
  <sub>학과 온라인 저지의 풀이를 GitHub 등에 쉽게 보관하기 위해 만든 개인 프로젝트</sub>
</p>

<p align="center">
  <a href="https://ascode-scraper.onrender.com">웹 다운로더 열기 ↗</a>
</p>

---

<h2 align="center">✨ 주요 기능</h2>

| 구분 | 기능 |
| :--- | :--- |
| 제출 내역 조회 | 로그인 세션을 유지하며 내 제출 목록 조회 |
| 정답 코드 선별 | 채점 결과가 Accepted(AC)인 제출만 다운로드 |
| 파일 정리 | 제출 번호와 언어별 확장자로 파일 저장 (`solution_123456.cpp`, `solution_123457.py`) |
| ZIP 다운로드 | 저장한 코드 파일을 ZIP으로 묶어 한 번에 다운로드 |

<p align="center">
  <b>로그인 → 제출 목록 조회 → 정답 코드 선별 → 언어별 파일 저장 → ZIP 다운로드</b>
</p>

---

<h2 align="center">⚙️ 구현 및 배포</h2>

- HTTP 세션으로 로그인 상태를 유지하며 제출 목록을 조회하고, 채점 결과가 Accepted(AC)인 코드만 수집
- 제출 번호와 언어별 확장자로 파일명을 구성하고, Flask에서 코드 파일을 ZIP으로 묶어 다운로드 제공
- Render에 배포한 뒤, 코드 수집에 시간이 걸리는 요청이 중간에 끊기는 문제를 줄이기 위해 Gunicorn 타임아웃을 600초로 조정

---

<h2 align="center">🛠️ 사용 기술</h2>

| 구분 | 기술 |
| :--- | :--- |
| 언어 | Python |
| 웹 프레임워크 | Flask |
| 운영 및 배포 | Gunicorn, Render |

---

<h2 align="center">🚀 로컬 실행</h2>

저장소 루트에서 아래 명령을 실행한 뒤 브라우저에서 `http://127.0.0.1:5000`에 접속합니다.

```bash
python -m pip install -r requirements.txt
python -m flask --app app run
```
