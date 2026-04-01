import logging
import google.generativeai as genai
from config import VALID_TAGS

logger = logging.getLogger(__name__)


def build_prompt(title: str, content: str) -> str:
    tags_str = ", ".join(VALID_TAGS)
    return f"""당신은 AI 코딩 도구 전문 분석가입니다.
다음 기술 뉴스를 분석해주세요.

## 판단 기준
- 중요도 점수(1~10): 단순 버그픽스/마이너 패치는 1~3, 새 기능/성능 개선은 4~6, 아키텍처 변화/전략적 의미/업계 영향이 큰 내용은 7~10
- "그래서 뭐?" 테스트: AI 코딩 도구를 쓰는 개발자에게 실질적으로 왜 중요한지 근거를 제시하세요

## 입력
제목: {title}
내용: {content[:3000]}

## 출력 형식 (정확히 지켜주세요)
중요도: (1~10 숫자만)
근거: (이 소식이 왜 중요한지, 실무에 어떤 영향이 있는지 1~2줄)
요약: (한국어 핵심 요약 2~3줄)
태그: (다음 중 선택: {tags_str})"""


def parse_response(text: str) -> dict:
    lines = text.strip().split("\n")
    result = {"importance": 0, "reason": "", "summary": "", "tags": "기타"}
    summary_parts = []

    for line in lines:
        if line.startswith("중요도:"):
            try:
                result["importance"] = int(line.replace("중요도:", "").strip())
            except ValueError:
                result["importance"] = 5
        elif line.startswith("근거:"):
            result["reason"] = line.replace("근거:", "").strip()
        elif line.startswith("태그:"):
            raw_tags = line.replace("태그:", "").strip()
            valid = [t.strip() for t in raw_tags.split(",") if t.strip() in VALID_TAGS]
            result["tags"] = ", ".join(valid) if valid else "기타"
        elif line.startswith("요약:"):
            summary_parts.append(line.replace("요약:", "").strip())
        else:
            summary_parts.append(line.strip())

    result["summary"] = "\n".join(p for p in summary_parts if p)
    return result


def summarize(title: str, content: str, api_key: str = "") -> dict | None:
    if not api_key:
        logger.info("No Gemini API key, skipping summarization")
        return None

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = build_prompt(title, content)
        response = model.generate_content(prompt)
        return parse_response(response.text)
    except Exception as e:
        logger.error("Gemini API error: %s", e)
        return None
