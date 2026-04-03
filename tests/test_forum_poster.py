import json
from unittest.mock import patch, MagicMock
from forum_poster import build_forum_post_body, build_debate_comment, parse_judge_tag


def test_build_forum_post_body():
    article = {
        "title": "OpenAI O3 breakthrough",
        "url": "https://example.com/o3",
        "points": 1724,
        "created_at": "2024-12-20T00:00:00Z",
    }
    body = build_forum_post_body(article)
    assert "OpenAI O3 breakthrough" in body["thread_name"]
    assert "1724" in body["content"]
    assert "2024-12-20" in body["content"]
    assert "https://example.com/o3" in body["content"]


def test_build_forum_post_body_truncates_long_title():
    article = {
        "title": "A" * 150,
        "url": "https://example.com",
        "points": 100,
        "created_at": "2024-12-20T00:00:00Z",
    }
    body = build_forum_post_body(article)
    assert len(body["thread_name"]) <= 100


def test_build_debate_comment():
    content = build_debate_comment(1, "researcher", "기술 분석 내용입니다.")
    assert "[Round 1 - Researcher]" in content
    assert "기술 분석 내용입니다." in content


def test_build_debate_comment_judge():
    content = build_debate_comment("judge", "judge", "종합 판정 내용")
    assert "[Judge 종합 판정]" in content
    assert "종합 판정 내용" in content


def test_parse_judge_tag_extracts_category():
    judge_text = """카테고리: Model - 벤치마크

기술적 혁신도: 매우 높음

실무 적용 가능성: 중간

업계 영향력: 높음

최종 요약: 중요한 벤치마크 결과입니다."""
    tag = parse_judge_tag(judge_text)
    assert tag == "Model - 벤치마크"


def test_parse_judge_tag_fallback():
    judge_text = "카테고리가 없는 판정문"
    tag = parse_judge_tag(judge_text)
    assert tag == "Community - 의견/토론"
