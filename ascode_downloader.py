import os
import time
import requests
from bs4 import BeautifulSoup

# === 1. 복사한 쿠키 입력 ===
cookies = {
    "PHPSESSID": "jo6g6ori6d1jmpd6meovv2n9f5",
    "lastlang": "undefined"
}

# === 2. 기본 설정 ===
save_root = "./ascode_solutions"
base_url = "http://ascode.org"
status_url = f"{base_url}/status.php"
username = "20243100"  # 본인 사용자 ID

# === 3. 세션 생성 및 헤더/쿠키 적용 ===
session = requests.Session()
session.cookies.update(cookies)
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
    'Referer': 'http://ascode.org/modifypage.php',
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
})

# === 4. 로그인 상태 확인 ===
def check_login_status():
    try:
        check_url = "http://ascode.org/template/ascode/profile.php?138760013"
        resp = session.get(check_url)
        with open('debug_profile.html', 'w', encoding='utf-8') as f:
            f.write(resp.text)
        soup = BeautifulSoup(resp.text, 'html.parser')
        logout_link = soup.find('a', string='Logout')
        return logout_link is not None
    except Exception as e:
        print("로그인 상태 확인 중 오류:", e)
        return False

# === 5. 제출 기록 페이지 가져오기 ===
def fetch_user_submissions(user_id, top=None, prevtop=None, result="4"):
    # URL에 'top'과 'prevtop'을 포함하여 페이지를 요청
    url = f"{status_url}?user_id={user_id}&jresult={result}"
    if top:
        url += f"&top={top}"
    if prevtop:
        url += f"&prevtop={prevtop}"
    
    try:
        resp = session.get(url)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        print(f"제출 기록 가져오기 실패: {e}")
        return None

# === 6. 제출 코드 저장 ===
def save_code_from_page(user_id, top=None, prevtop=None):
    page_html = fetch_user_submissions(user_id, top, prevtop, result="4")  # AC만 가져오기
    if not page_html:
        return False

    soup = BeautifulSoup(page_html, 'html.parser')
    table = soup.find('table')
    if not table:
        print("제출 기록 테이블을 찾을 수 없습니다.")
        return False

    headers = [th.get_text(strip=True).lower() for th in table.find('tr').find_all('th')]
    try:
        runid_idx = headers.index('runid')
        problem_idx = headers.index('problem')
        lang_idx = headers.index('language')
    except ValueError as e:
        print(f"필요한 열을 찾을 수 없습니다: {e}")
        print(f"발견된 헤더: {headers}")
        return False

    submissions = []
    for row in table.find_all('tr')[1:]:
        cols = row.find_all('td')
        if len(cols) <= max(runid_idx, problem_idx, lang_idx):
            continue
        runid = cols[runid_idx].get_text(strip=True)
        problem_id = cols[problem_idx].get_text(strip=True)
        language_cell = cols[lang_idx]
        language_text = language_cell.get_text(strip=True)

        # Edit 링크 찾기
        edit_link = None
        for a_tag in language_cell.find_all('a'):
            if 'edit' in a_tag.get_text().lower():
                edit_link = a_tag.get('href')
                break
        if not edit_link:
            edit_link = f"showsource.php?id={runid}"
        if edit_link.startswith('/'):
            edit_link = f"{base_url}{edit_link}"
        elif not edit_link.startswith('http'):
            edit_link = f"{base_url}/{edit_link}"

        if '/' in language_text:
            language = language_text.split('/')[0]
        else:
            language = language_text.replace('Edit', '').strip()

        submissions.append((runid, problem_id, language, edit_link))

    for idx, (runid, problem_id, language, source_link) in enumerate(submissions):
        print(f"[{idx+1}/{len(submissions)}] RunID {runid}, 문제 {problem_id}, 언어 {language} 처리 중...")
        try:
            resp = session.get(source_link)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[{problem_id}] 코드 요청 실패: {e}")
            continue

        soup = BeautifulSoup(resp.text, 'html.parser')
        code_element = soup.find('pre') or soup.find('textarea')
        if code_element:
            code_text = code_element.get_text()
            extension = get_file_extension(language)
            problem_folder = os.path.join(save_root, problem_id)
            os.makedirs(problem_folder, exist_ok=True)
            file_path = os.path.join(problem_folder, f"solution_{runid}{extension}")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code_text)
            print(f"[{problem_id}] 코드(RunID: {runid}) 저장 완료: {file_path}")
        else:
            print(f"[{problem_id}] 코드를 찾을 수 없습니다.")
        time.sleep(1)
    return True

# === 7. 파일 확장자 매칭 ===
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

# === 8. 페이지 내비게이션 처리 ===
def get_next_page_top(soup):
    next_page_link = soup.find('a', string='Next Page')
    if next_page_link:
        # 'Next Page' 링크에서 top과 prevtop 추출
        next_url = next_page_link.get('href')
        top = next_url.split('top=')[1].split('&')[0]
        prevtop = next_url.split('prevtop=')[1] if 'prevtop' in next_url else None
        return top, prevtop
    return None, None

# === 9. 메인 ===
def main():
    if not os.path.exists(save_root):
        os.makedirs(save_root)
    if not check_login_status():
        print("❌ 쿠키가 올바르지 않거나 만료되었습니다. 브라우저에서 쿠키를 새로 복사하세요.")
        return
    print(f"✅ AScode.org에 로그인된 상태입니다. 사용자: {username}")
    page = 1
    max_pages = 20
    top = None
    prevtop = None

    while page <= max_pages:
        print(f"====== 페이지 {page} 처리 시작 ======")
        if not save_code_from_page(username, top, prevtop):
            print(f"페이지 {page}에서 처리 중단 - 더 이상 페이지가 없거나 오류 발생")
            break

        page_html = fetch_user_submissions(username, top, prevtop)
        if page_html:
            soup = BeautifulSoup(page_html, 'html.parser')
            # 페이지의 'Next Page' 링크를 찾아 top과 prevtop을 추출
            top, prevtop = get_next_page_top(soup)
            if top:
                page += 1
                continue
        break
    print("🎉 모든 코드 다운로드 작업이 완료되었습니다!")
    print(f"다운로드된 코드는 {save_root} 폴더에 저장되었습니다.")

if __name__ == "__main__":
    main()