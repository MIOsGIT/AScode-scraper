import os
import time
import requests
from bs4 import BeautifulSoup

base_url = "http://ascode.org"
SAVE_ROOT = "./downloaded_codes"

def login(username, password):
    login_url = f"{base_url}/login.php"
    session = requests.Session()
    
    # 로그인 페이지에서 폼 정보 가져오기
    login_page_url = f"{base_url}/loginpage.php"
    resp = session.get(login_page_url)
    
    # 로그인 요청
    login_data = {
        "user_id": username,
        "password": password
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        'Referer': login_page_url,
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    # 리디렉션을 자동으로 처리하도록 allow_redirects=True 추가
    resp = session.post(login_url, data=login_data, headers=headers, allow_redirects=True)
    
    # 로그인 성공 여부 확인
    if check_login_status(session):
        print(f"✅ {username}님으로 성공적으로 로그인되었습니다.")
        return session
    else:
        print("❌ 로그인에 실패했습니다. 사용자 ID와 비밀번호를 확인하세요.")
        return None

# 로그인 상태 확인 함수 추가
def check_login_status(session):
    try:
        check_url = f"{base_url}/template/ascode/profile.php?138760013"
        resp = session.get(check_url)
        soup = BeautifulSoup(resp.text, 'html.parser')
        logout_link = soup.find('a', string='Logout')
        return logout_link is not None
    except Exception as e:
        print("로그인 상태 확인 중 오류:", e)
        return False

def get_file_extension(language):
    language = language.lower()
    if "c++" in language or "cpp" in language:
        return ".cpp"
    elif "c" in language and "c++" not in language:
        return ".c"
    elif "java" in language:
        return ".java"
    elif "python" in language or "py" in language:
        return ".py"
    elif "javascript" in language or "js" in language:
        return ".js"
    else:
        return ".txt"

def get_next_page_top(soup):
    next_page_link = soup.find('a', string='Next Page')
    if next_page_link:
        next_url = next_page_link.get('href')
        top = next_url.split('top=')[1].split('&')[0]
        prevtop = next_url.split('prevtop=')[1] if 'prevtop' in next_url else None
        return top, prevtop
    return None, None

def download_user_codes_with_log(session, user_id):
    if not os.path.exists(SAVE_ROOT):
        os.makedirs(SAVE_ROOT)

    downloaded = 0
    top = None

    while True:
        url = f"{base_url}/status.php?user_id={user_id}&jresult=4"
        if top:
            url += f"&top={top}"

        resp = session.get(url)
        soup = BeautifulSoup(resp.text, 'html.parser')

        table = soup.find('table')
        if not table:
            yield "⚠️ 제출 테이블을 찾을 수 없습니다."
            break

        headers = [th.get_text(strip=True).lower() for th in table.find('tr').find_all('th')]
        try:
            runid_idx = headers.index('runid')
            problem_idx = headers.index('problem')
            lang_idx = headers.index('language')
        except ValueError:
            yield "⚠️ 테이블 헤더 파싱 실패"
            break

        rows = table.find_all('tr')[1:]
        if not rows:
            break

        for row in rows:
            cols = row.find_all('td')
            runid = cols[runid_idx].text.strip()
            problem_id = cols[problem_idx].text.strip()
            language = cols[lang_idx].text.strip()

            source_url = f"{base_url}/showsource.php?id={runid}"
            code_resp = session.get(source_url)
            code_soup = BeautifulSoup(code_resp.text, 'html.parser')
            code = code_soup.find('pre') or code_soup.find('textarea')

            if code:
                extension = get_file_extension(language)
                folder = os.path.join(SAVE_ROOT, problem_id)
                os.makedirs(folder, exist_ok=True)
                with open(os.path.join(folder, f"solution_{runid}{extension}"), "w", encoding="utf-8") as f:
                    f.write(code.text)
                downloaded += 1
                yield f"✅ {problem_id}번 코드 다운로드 완료"
            else:
                yield f"❌ {problem_id}번 코드 다운로드 실패"

            time.sleep(0.5)

        top, _ = get_next_page_top(soup)
        if not top:
            break

    yield f"🎉 총 {downloaded}개 코드 다운로드 완료!"