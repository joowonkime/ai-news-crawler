import json
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

DEBATES_DIR = os.path.join(os.path.dirname(__file__), "history_debates")
PROGRESS_FILE = os.path.join(os.path.dirname(__file__), "history_debate_progress.json")
COLLECTED_FILE = os.path.join(os.path.dirname(__file__), "history_collected.json")

FORUM_TAGS = {
    "Community - 의견/토론": "1489494643426070579",
    "Community - 프로젝트": "1489494678473801778",
    "Community - 제품/스타트업": "1489494700913197076",
    "Dev - 코딩 도구": "1489494730931961956",
    "Dev - Vibe Coding": "1489494755116187729",
    "Dev - 에이전트": "1489494779887620187",
    "Dev - MCP": "1489495357644869763",
    "Infra - 프레임워크": "1489495865977733200",
    "Infra - RAG/데이터": "1489553735817629766",
    "Infra - 배포/운영": "1489499384277237851",
    "Model - 모델 출시": "1489499406649524345",
    "Model - 벤치마크": "1489499428682469498",
    "Model - 추론/성능": "1489499453835444224",
    "Model - 오픈소스 모델": "1489499475880706228",
}

PROMPTS = {
    "researcher_r1": """당신은 AI/ML 기술 연구자입니다. 다음 Hacker News 기사를 기술적 관점에서 분석하세요.

기사: {title}
URL: {url}
HN Points: {points}
날짜: {date}

분석 지침:
- 이 기사의 기술적 핵심이 무엇인지 분석하세요
- 선행 기술 대비 어떤 차이/혁신이 있는지 설명하세요
- 주장에는 반드시 기술적 근거를 들어주세요. 추측이면 추측이라고 밝히세요
- 한국어로 작성하되, 기술 용어는 원문 유지
- 300자 이내로 간결하게""",

    "practitioner_r1": """당신은 현업 시니어 개발자입니다. 다음 Hacker News 기사를 실무 관점에서 분석하세요.

기사: {title}
URL: {url}
HN Points: {points}
날짜: {date}

분석 지침:
- 이 기술/도구/소식이 실무에 어떤 영향을 미치는지 분석하세요
- 구체적인 사용 시나리오를 들어주세요
- '좋다/나쁘다'가 아니라 '어떤 상황에서 어떻게 쓸 수 있다'로 답하세요
- 비용/성능/생산성 트레이드오프를 고려하세요
- 한국어로 작성, 300자 이내""",

    "devil_r1": """당신은 Devil's Advocate입니다. 다음 Hacker News 기사에 대해 의도적으로 반론을 제기하세요.

기사: {title}
URL: {url}
HN Points: {points}
날짜: {date}

분석 지침:
- 이 기사가 과대평가되었을 수 있는 이유를 제시하세요
- 숨겨진 비용, 리스크, 제한사항을 지적하세요
- 마케팅과 실제의 괴리가 있다면 지적하세요
- 단순 부정이 아니라 근거 있는 반론을 제시하세요
- 한국어로 작성, 300자 이내""",

    "researcher_r2": """당신은 AI/ML 기술 연구자입니다. Round 1의 토론 내용을 읽고 반응하세요.

기사: {title}

=== Round 1 토론 내용 ===
[Researcher] {r1_researcher}

[Practitioner] {r1_practitioner}

[Devil's Advocate] {r1_devil}
===

지침:
- Devil's Advocate의 반론에 대해 기술적으로 재반박하세요
- Practitioner의 실무 관점에서 놓친 기술적 맥락을 보완하세요
- 상대의 구체적 주장을 인용하며 응답하세요
- 한국어로 작성, 300자 이내""",

    "practitioner_r2": """당신은 현업 시니어 개발자입니다. Round 1의 토론 내용을 읽고 반응하세요.

기사: {title}

=== Round 1 토론 내용 ===
[Researcher] {r1_researcher}

[Practitioner] {r1_practitioner}

[Devil's Advocate] {r1_devil}
===

지침:
- Researcher의 기술 분석에 실무 현실을 보완하세요
- Devil's Advocate의 반론 중 타당한 것은 인정하고, 실무에서의 해결책을 제시하세요
- 상대의 구체적 주장을 인용하며 응답하세요
- 한국어로 작성, 300자 이내""",

    "devil_r2": """당신은 Devil's Advocate입니다. Round 1의 토론 내용을 읽고 추가 반론을 제기하세요.

기사: {title}

=== Round 1 토론 내용 ===
[Researcher] {r1_researcher}

[Practitioner] {r1_practitioner}

[Devil's Advocate] {r1_devil}
===

지침:
- Researcher와 Practitioner 양쪽의 약점을 추가로 지적하세요
- Round 1에서 제기한 반론에 대한 그들의 방어가 충분한지 평가하세요
- 새로운 각도의 비판을 추가하세요
- 한국어로 작성, 300자 이내""",

    "researcher_r3": """당신은 AI/ML 기술 연구자입니다. 2라운드의 토론을 모두 검토하고 최종 입장을 정리하세요.

기사: {title}

=== Round 1 ===
[Researcher] {r1_researcher}
[Practitioner] {r1_practitioner}
[Devil's Advocate] {r1_devil}

=== Round 2 ===
[Researcher] {r2_researcher}
[Practitioner] {r2_practitioner}
[Devil's Advocate] {r2_devil}
===

지침:
- 토론을 통해 수정한 부분을 명시하세요 ("DA 반론을 받아들여 X를 수정")
- 유지하는 입장과 그 이유를 밝히세요
- 다른 에이전트와의 합의/불합의를 명시하세요
- 한국어로 작성, 300자 이내""",

    "practitioner_r3": """당신은 현업 시니어 개발자입니다. 2라운드의 토론을 모두 검토하고 최종 입장을 정리하세요.

기사: {title}

=== Round 1 ===
[Researcher] {r1_researcher}
[Practitioner] {r1_practitioner}
[Devil's Advocate] {r1_devil}

=== Round 2 ===
[Researcher] {r2_researcher}
[Practitioner] {r2_practitioner}
[Devil's Advocate] {r2_devil}
===

지침:
- 토론을 통해 수정한 부분을 명시하세요
- 실무 관점에서의 최종 판단을 내리세요
- 다른 에이전트와의 합의/불합의를 명시하세요
- 한국어로 작성, 300자 이내""",

    "devil_r3": """당신은 Devil's Advocate입니다. 2라운드의 토론을 모두 검토하고 최종 입장을 정리하세요.

기사: {title}

=== Round 1 ===
[Researcher] {r1_researcher}
[Practitioner] {r1_practitioner}
[Devil's Advocate] {r1_devil}

=== Round 2 ===
[Researcher] {r2_researcher}
[Practitioner] {r2_practitioner}
[Devil's Advocate] {r2_devil}
===

지침:
- 여전히 유효한 반론과 철회하는 반론을 구분하세요
- 토론을 통해 설득된 부분이 있다면 인정하세요
- 최종적으로 남는 리스크/우려를 정리하세요
- 한국어로 작성, 300자 이내""",

    "judge": """당신은 공정한 심판입니다. 3라운드 토론 전체를 읽고 종합 판정을 내리세요.

기사: {title}
URL: {url}
HN Points: {points}
날짜: {date}

=== Round 1 ===
[Researcher] {r1_researcher}
[Practitioner] {r1_practitioner}
[Devil's Advocate] {r1_devil}

=== Round 2 ===
[Researcher] {r2_researcher}
[Practitioner] {r2_practitioner}
[Devil's Advocate] {r2_devil}

=== Round 3 ===
[Researcher] {r3_researcher}
[Practitioner] {r3_practitioner}
[Devil's Advocate] {r3_devil}
===

다음 형식으로 판정하세요:

카테고리: (다음 중 택1: {tag_options})

기술적 혁신도: (이 기사의 기술적 혁신이 어느 수준인지 1-2줄)

실무 적용 가능성: (실무에서 어떻게 적용할 수 있는지 1-2줄)

업계 영향력: (업계에 미치는 영향과 파급력 1-2줄)

최종 요약: (3명의 토론에서 가장 강한 논거를 종합한 2-3줄 요약. 약한 논거는 버리세요.)""",
}


def load_progress(path: str = PROGRESS_FILE) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def save_progress(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def init_progress(articles_path: str = COLLECTED_FILE, progress_path: str = PROGRESS_FILE) -> dict:
    with open(articles_path, "r", encoding="utf-8") as f:
        articles = json.load(f)

    progress = {
        "total": len(articles),
        "completed": 0,
        "posted_to_discord": 0,
        "current_batch": 1,
        "articles": {},
    }
    for oid in articles:
        progress["articles"][oid] = {
            "status": "pending",
            "rounds_done": 0,
            "judge_done": False,
            "posted": False,
            "thread_id": None,
        }
    save_progress(progress_path, progress)
    return progress


def save_debate_round(debates_dir: str, object_id: str, round_num, role: str, content: str):
    path = os.path.join(debates_dir, f"{object_id}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            debate = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        debate = {"object_id": object_id, "rounds": {}}

    round_key = str(round_num)
    if round_key not in debate["rounds"]:
        debate["rounds"][round_key] = {}
    debate["rounds"][round_key][role] = content

    with open(path, "w", encoding="utf-8") as f:
        json.dump(debate, f, ensure_ascii=False, indent=2)


def load_debate(debates_dir: str, object_id: str) -> dict | None:
    path = os.path.join(debates_dir, f"{object_id}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def get_pending_articles(progress: dict, articles: dict, batch_size: int = 100) -> list[dict]:
    pending = []
    for oid, state in progress["articles"].items():
        if state["status"] in ("pending", "debating"):
            if oid in articles:
                pending.append(articles[oid])
    pending.sort(key=lambda a: a.get("created_at", ""))
    return pending[:batch_size]


def update_article_status(progress: dict, object_id: str, **kwargs):
    if object_id in progress["articles"]:
        progress["articles"][object_id].update(kwargs)
        if kwargs.get("status") == "completed":
            progress["completed"] = sum(
                1 for a in progress["articles"].values() if a["status"] in ("completed", "posted")
            )
        if kwargs.get("status") == "posted":
            progress["posted_to_discord"] = sum(
                1 for a in progress["articles"].values() if a["status"] == "posted"
            )


def build_prompt(template_key: str, article: dict, debate: dict | None = None) -> str:
    tag_options = ", ".join(FORUM_TAGS.keys())
    params = {
        "title": article.get("title", ""),
        "url": article.get("url", ""),
        "points": article.get("points", 0),
        "date": article.get("created_at", "")[:10],
        "tag_options": tag_options,
    }
    if debate and "rounds" in debate:
        rounds = debate["rounds"]
        for rnum in ("1", "2", "3"):
            if rnum in rounds:
                params[f"r{rnum}_researcher"] = rounds[rnum].get("researcher", "")
                params[f"r{rnum}_practitioner"] = rounds[rnum].get("practitioner", "")
                params[f"r{rnum}_devil"] = rounds[rnum].get("devil", "")
    template = PROMPTS.get(template_key, "")
    return template.format(**{k: v for k, v in params.items() if f"{{{k}}}" in template})
