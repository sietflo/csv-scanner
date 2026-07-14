import argparse
import requests
from pathlib import Path
from pydantic import BaseModel
import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

llm = genai.Client(api_key=GEMINI_API_KEY)


def fetch_github_files(owner: str, repo: str, path="", branch="main"):
    """Рекурсивна функція, яка ходить по GitHub API замість локального диска"""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        print(f"Помилка GitHub API: {response.status_code} ({response.json().get('message')})")
        return {}
    repo_data = {}
    items = response.json()

    for item in items:
        # Ігноруємо службову папку .git
        if item["name"] == ".git":
            continue

        if item["type"] == "dir":
            print(f"Папка: {item['path']}")
            repo_data.update(fetch_github_files(owner, repo, item["path"], branch))
        else:
            print(f"Файл: {item['path']}")
            if item["download_url"] and not any(
                    item["name"].endswith(ext) for ext in ['.png', '.jpg', '.ico', '.zip', '.pdf']):
                file_response = requests.get(item["download_url"])
                if file_response.status_code == 200:
                    repo_data[item["path"]] = file_response.text
                else:
                    repo_data[item["path"]] = "[Не вдалося завантажити вміст]"
            else:
                repo_data[item["path"]] = "[Бінарний або пропущений файл]"
    return repo_data

def llm_report(repo_structure: dict):
    """Створює формат запиту до Gemini, визначає промпт та інструкції, та виконує запит"""
    print("\nНадсилаємо запит до Gemini для аналізу коду...")
    repo_content_string = json.dumps(repo_structure, ensure_ascii=False)
    prompt = f"""Проаналізуй структуру та вміст цього репозиторію.
     Визнач основні технології, сильні сторони,
      можливі проблеми та рекомендації щодо покращення:
      \n\n{repo_content_string}"""

    class RepoReview(BaseModel):
        summary: str
        tech: list[str]
        pros: list[str]
        cons: list[str]
        suggestions: list[str]

    response = llm.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=RepoReview,
            system_instruction="Ти — досвідчений Senior розробник. Твоє завдання — надати чіткий структурований аналіз коду українською мовою."
        ),
    )
    return response.text



def save_to_markdown(json_str: str, filename="review"):
    """Форматує отриманий JSON та зберігає його у файл .md"""
    try:
        folder_path = Path("output")
        folder_path.mkdir(parents=True, exist_ok=True)

        data = json.loads(json_str)
        md_path = folder_path / f'{filename}.md'
        json_path = folder_path / f'{filename}.json'

        with open(json_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=2)

        md_content = f"""
# Code Review Report
### 📝 Короткий огляд

        {data.get('summary', '')}

---
### Використані технології

        {'\n'.join([f'- {item}' for item in data.get('tech', [])])}

### ✅ Плюси (Pros)

        {'\n'.join([f'- {item}' for item in data.get('pros', [])])}

### ❌ Мінуси / Проблеми (Cons)

        {'\n'.join([f'- {item}' for item in data.get('cons', [])])}

 ### 💡 Рекомендації щодо покращення (Suggestions)

        {'\n'.join([f'- {item}' for item in data.get('suggestions', [])])}
        """
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"\nРезультат успішно збережено у файли:\n - {md_path} \n - {json_path}")
    except Exception as e:
        print(f"Помилка при збереженні: {e}")


def main():
    parser = argparse.ArgumentParser(description="Скіл для роботи з GitHub API")

    parser.add_argument("owner", type=str, help="Власник репозиторію (наприклад, 'sietflo')")
    parser.add_argument("repo", type=str, help="Назва репозиторію (наприклад, 'csv-scanner')")
    parser.add_argument("--branch", type=str, default="main", help="Назва гілки")
    parser.add_argument("--review", action="store_true", help="Запустити аналіз коду через Gemini та зберегти в .md")
    args = parser.parse_args()

    print(f"Підключаємось до GitHub API для репозиторію {args.owner}/{args.repo}...\n")
    repo_data = fetch_github_files(args.owner, args.repo, branch=args.branch)
    if args.review:
        if not repo_data:
            print("Немає даних для аналізу.")
            return

        json_review = llm_report(repo_data)
        save_to_markdown(json_review)


if __name__ == "__main__":
    main()