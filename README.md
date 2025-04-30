# AScode-scraper

🎯 AScode 자동 코드 백업 스크립트
AScode 온라인 저지 사이트에서 로그인 쿠키를 기반으로 본인의 Accepted(AC) 코드만 자동으로 다운로드하고 정리해주는 Python 스크립트입니다.

📦 설치 방법
Python 3.x 설치
https://www.python.org/downloads/

필수 라이브러리 설치
터미널(명령 프롬프트)에서 아래 명령어를 실행하세요.
pip install requests beautifulsoup4

프로젝트 클론 (깃허브에서 내려받기)
Git이 설치되어 있다면 아래 명령어를 실행하세요.
git clone https://github.com/MIOsGIT/ascode-downloader.git

🔐 쿠키 복사 방법
크롬에서 http://ascode.org 로그인

F12 키를 눌러 개발자 도구 열기

상단 탭에서 "Application" 클릭

좌측 메뉴에서 "Cookies" > "http://ascode.org" 선택

PHPSESSID 값을 복사

▶️ 사용 방법
Click! 파일 실행 후

학번, 복사한 쿠키 입력

💾 저장 구조
각 문제별 폴더가 자동 생성됨 (./ascode_solutions/문제번호/)

Accepted 코드만 언어 확장자에 맞춰 저장됨
예: solution_123456.cpp, solution_123457.py 등

📌 주의사항
쿠키가 만료되면 다시 복사해서 붙여넣어야 함

🙋‍♀️ 만든 사람
MIO (MIOsGIT)
