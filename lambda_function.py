import json
import requests
from bs4 import BeautifulSoup

def get_summary_and_score(api_key, result_text):
    # 要約リクエストデータ
    request_body_summary = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "文章を簡潔に要約してください。"},
            {"role": "user", "content": result_text}
        ]
    }

    # スコアリクエストデータ
    request_body_score = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "文章について以下の基準で1~100点で、スコアが高いほど高リスクとしてください：被害範囲・被害程度・社会的影響・死傷者 • 被害金額の大きさ。なお返答は85などのように数字のみでお願いします。それ以外の応答はしないでください。"},
            {"role": "user", "content": result_text}
        ]
    }

    # APIリクエストを送信するURL
    api_url = "https://api.openai.com/v1/chat/completions"

    # 要約リクエストを送信
    response_summary = requests.post(api_url, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }, json=request_body_summary)

    # スコアリクエストを送信
    response_score = requests.post(api_url, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }, json=request_body_score)

    # 結果を解析
    summary = None
    score = None

    if response_summary.status_code == 200:
        summary = response_summary.json()['choices'][0]['message']['content']
    else:
        summary = "要約に失敗しました"

    if response_score.status_code == 200:
        score = response_score.json()['choices'][0]['message']['content']
    else:
        score = "スコア取得に失敗しました"

    return summary, score

def lambda_handler(event, content):
    # URLを取得
    url = event.get('url')
    if not url:
        return {
            'statusCode': 400,
            'body': json.dumps('URLを指定してください。')
        }

    # HTMLを取得して解析

    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # タイトルの取得
    title = soup.title.text.strip().replace(' | NHK |', '')

    # 日付の取得
    date = soup.find('time')
    date_text = date.text.strip() if date else '日付情報なし'

    # 必要なテキストを取得
    paragraphs = soup.find_all(['p', 'div'], class_='body-text')
    content = [p.text.strip() for p in paragraphs if p.text.strip() and 
               'ニュース一覧へ戻る' not in p.text and 'シェア' not in p.text]

    # フィルタされたテキストを1つに整形
    result_text = '\n'.join(content)
    openai_key="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"
    summary, score = get_summary_and_score(openai_key, result_text)
    # 結果を返す
    return {
        'statusCode': 200,
        'body': json.dumps({
            'title': title,
            'date': date_text,
            'content': result_text,
            'summary': summary,
            'score': score
        }, ensure_ascii=False)
    }