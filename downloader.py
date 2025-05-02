import os
import time
import requests
from bs4 import BeautifulSoup
import zipfile

base_url = "http://ascode.org"
SAVE_ROOT = "./downloaded_codes"
DOWNLOAD_DELAY = 0.3


def login(username, password):
    login_url = f"{base_url}/login.php"
    session = requests.Session()

    login_page_url = f"{base_url}/loginpage.php"
    session.get(login_page_url)

    login_data = {
        "user_id": username,
        "password": password
    }

    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': login_page_url,
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    }

    resp = session.post(login_url, data=login_data, headers=headers, allow_redirects=True)
    if check_login_status(session):
        print(f"✅ {username}님으로 성공적으로 로그인되었습니다.")
        return session
    else:
        print("❌ 로그인에 실패했습니다. 사용자 ID와 비밀번호를 확인하세요.")
        return None


def check_login_status(session):
    try:
        check_url = f"{base_url}/template/ascode/profile.php?138760013"
        resp = session.get(check_url)
        soup = BeautifulSoup(resp.text, 'html.parser')
        return soup.find('a', string='Logout') is not None
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
        return top, None
    return None, None


def zip_user_codes(user_id):
    user_folder = os.path.join(SAVE_ROOT, user_id)
    if not os.path.exists(user_folder):
        return None
    zip_filename = os.path.join(SAVE_ROOT, f"{user_id}_codes.zip")
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(user_folder):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), user_folder))
    return zip_filename


def count_files_in_user_folder(user_id):
    base_folder = os.path.join(SAVE_ROOT, user_id)
    return sum(len(files) for _, _, files in os.walk(base_folder))


def download_user_codes_with_log(session, user_id):
    os.makedirs(SAVE_ROOT, exist_ok=True)

    # 1. 전체 제출 runid 수집
    all_runids = []
    top = None
    prev_top = None
    while True:
        url = f"{base_url}/status.php?user_id={user_id}&jresult=4"
        if top:
            url += f"&top={top}"
        try:
            resp = session.get(url)
            soup = BeautifulSoup(resp.text, 'html.parser')
        except Exception as e:
            yield f"❌ 페이지 로딩 실패: {e}"
            return
        table = soup.find('table')
        if not table:
            yield "⚠️ 제출 테이블을 찾을 수 없습니다."
            return
        headers = [th.get_text(strip=True).lower() for th in table.find('tr').find_all('th')]
        try:
            runid_idx = headers.index('runid')
        except ValueError:
            yield "⚠️ 테이블 헤더 파싱 실패"
            return
        rows = table.find_all('tr')[1:]
        for row in rows:
            runid = row.find_all('td')[runid_idx].text.strip()
            all_runids.append(runid)
        prev_top = top
        top, _ = get_next_page_top(soup)
        if not top or top == prev_top:
            break

    unique_runids = list(dict.fromkeys(all_runids))
    total_submissions = len(unique_runids)
    yield f"📦 총 제출 수 확인됨: {total_submissions}개"

    # 2. 다운로드
    downloaded_runids = set()
    downloaded_problems = set()
    top = None
    prev_top = None
    completed = 0
    while True:
        url = f"{base_url}/status.php?user_id={user_id}&jresult=4"
        if top:
            url += f"&top={top}"
        try:
            resp = session.get(url)
            soup = BeautifulSoup(resp.text, 'html.parser')
        except Exception as e:
            yield f"❌ 페이지 로딩 실패: {e}"
            break
        table = soup.find('table')
        if not table:
            break
        headers = [th.get_text(strip=True).lower() for th in table.find('tr').find_all('th')]
        try:
            runid_idx = headers.index('runid')
            problem_idx = headers.index('problem')
            lang_idx = headers.index('language')
        except ValueError:
            break
        rows = table.find_all('tr')[1:]
        if not rows:
            break

        for row in rows:
            cols = row.find_all('td')
            runid = cols[runid_idx].text.strip()
            problem_id = cols[problem_idx].text.strip()
            language = cols[lang_idx].text.strip()

            if runid in downloaded_runids:
                continue
            downloaded_runids.add(runid)
            downloaded_problems.add(problem_id)
            completed += 1
            percent = (completed / total_submissions) * 100

            try:
                source_url = f"{base_url}/showsource.php?id={runid}"
                code_resp = session.get(source_url)
                code_soup = BeautifulSoup(code_resp.text, 'html.parser')
                code = code_soup.find('pre') or code_soup.find('textarea')
            except Exception as e:
                yield f"❌ {problem_id}번 소스 코드 요청 실패: {e}"
                continue

            if code and code.text.strip():
                extension = get_file_extension(language)
                folder = os.path.join(SAVE_ROOT, user_id, problem_id)
                os.makedirs(folder, exist_ok=True)
                file_path = os.path.join(folder, f"solution_{runid}{extension}")
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(code.text)
                    yield f"✅ {problem_id}번 코드 다운로드 완료 [{completed}/{total_submissions}] ({percent:.1f}%)"
                except Exception as e:
                    yield f"❌ {problem_id}번 저장 실패: {e} [{completed}/{total_submissions}] ({percent:.1f}%)"
            else:
                yield f"❌ {problem_id}번 코드 없음 [{completed}/{total_submissions}] ({percent:.1f}%)"

            time.sleep(DOWNLOAD_DELAY)

        prev_top = top
        top, _ = get_next_page_top(soup)
        if not top or top == prev_top:
            break

    problem_count = len(downloaded_problems)
    yield f"📊 문제 수: {problem_count}개, 제출 수: {total_submissions}개"
    true_count = count_files_in_user_folder(user_id)
    yield f"🎉 총 {true_count}개 코드 다운로드 완료!"

    zip_path = zip_user_codes(user_id)
    if zip_path:
        yield f"ZIP_READY:{os.path.abspath(zip_path)}"
    else:
        yield "❌ ZIP 파일 생성에 실패했습니다."

def get_submission_list(session, user_id):
    submissions = []
    top = None
    prev_top = None

    while True:
        url = f"{base_url}/status.php?user_id={user_id}&jresult=4"
        if top:
            url += f"&top={top}"

        resp = session.get(url)
        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find('table')
        if not table:
            break

        headers = [th.get_text(strip=True).lower() for th in table.find('tr').find_all('th')]
        try:
            runid_idx = headers.index('runid')
            problem_idx = headers.index('problem')
            lang_idx = headers.index('language')
        except ValueError:
            break

        rows = table.find_all('tr')[1:]
        for row in rows:
            cols = row.find_all('td')
            runid = cols[runid_idx].text.strip()
            problem_id = cols[problem_idx].text.strip()
            language = cols[lang_idx].text.strip()
            submissions.append({
                "runid": runid,
                "problem_id": problem_id,
                "language": language
            })

        prev_top = top
        top, _ = get_next_page_top(soup)
        if not top or top == prev_top:
            break

    return submissions



def download_selected_runids(session, user_id, runids):
    os.makedirs(SAVE_ROOT, exist_ok=True)
    downloaded_problems = set()
    total = len(runids)

    for idx, runid in enumerate(runids, 1):
        percent = (idx / total) * 100
        source_url = f"{base_url}/showsource.php?id={runid}"
        code_resp = session.get(source_url)
        code_soup = BeautifulSoup(code_resp.text, 'html.parser')
        code = code_soup.find('pre') or code_soup.find('textarea')

        # 문제 ID와 언어 추출 시도
        problem_id = f"problem_{runid}"
        language = "txt"
        try:
            status_url = f"{base_url}/status.php?user_id={user_id}&jresult=4"
            resp = session.get(status_url)
            soup = BeautifulSoup(resp.text, 'html.parser')
            row = soup.find(string=runid)
            if row:
                tr = row.find_parent("tr")
                tds = tr.find_all("td")
                problem_id = tds[2].text.strip()
                language = tds[4].text.strip()
        except:
            pass

        downloaded_problems.add(problem_id)

        if code and code.text.strip():
            extension = get_file_extension(language)
            folder = os.path.join(SAVE_ROOT, user_id, problem_id)
            os.makedirs(folder, exist_ok=True)
            file_path = os.path.join(folder, f"solution_{runid}{extension}")
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(code.text)
                yield f"✅ {problem_id}번 코드 다운로드 완료 [{idx}/{total}] ({percent:.1f}%)"
            except Exception as e:
                yield f"❌ {problem_id} 저장 실패: {e} [{idx}/{total}] ({percent:.1f}%)"
        else:
            yield f"❌ {runid} 코드 없음 [{idx}/{total}] ({percent:.1f}%)"

        time.sleep(DOWNLOAD_DELAY)

    yield f"📊 선택한 문제 수: {len(downloaded_problems)}개, 제출 수: {total}개"
    zip_path = zip_user_codes(user_id)
    if zip_path:
        yield f"ZIP_READY:{os.path.abspath(zip_path)}"
    else:
        yield "❌ ZIP 파일 생성에 실패했습니다."

