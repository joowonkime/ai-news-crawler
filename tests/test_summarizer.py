from unittest.mock import patch, MagicMock
from summarizer import build_prompt, parse_response, summarize


def test_build_prompt():
    prompt = build_prompt("Test title", "Test content about new AI features")
    assert "Test title" in prompt
    assert "Test content" in prompt
    assert "한국어" in prompt


def test_parse_response_valid():
    response_text = """중요도: 8
근거: 자동 완성 성능이 크게 향상되어 개발 생산성에 직접 영향
요약: 새로운 AI 코딩 기능이 추가되었습니다. 자동 완성 성능이 크게 향상되었습니다.
태그: 신기능, 성능"""
    result = parse_response(response_text)
    assert result["importance"] == 8
    assert "자동 완성" in result["reason"]
    assert "AI 코딩" in result["summary"]
    assert "신기능" in result["tags"]
    assert "성능" in result["tags"]


def test_parse_response_no_tags():
    response_text = "이것은 요약입니다. 새로운 기능이 추가되었습니다."
    result = parse_response(response_text)
    assert result["summary"]
    assert "기타" in result["tags"]


def test_tags_are_valid():
    from config import VALID_TAGS
    response_text = """중요도: 5
근거: 일반적인 업데이트
요약: 테스트 요약
태그: 신기능, 버그픽스"""
    result = parse_response(response_text)
    tag_list = [t.strip() for t in result["tags"].split(",")]
    for tag in tag_list:
        assert tag in VALID_TAGS


@patch("summarizer.genai")
def test_api_error_returns_none(mock_genai):
    mock_model = MagicMock()
    mock_model.generate_content.side_effect = Exception("API Error")
    mock_genai.GenerativeModel.return_value = mock_model
    result = summarize("title", "content", api_key="fake-key")
    assert result is None


def test_skip_when_no_api_key():
    result = summarize("title", "content", api_key="")
    assert result is None
