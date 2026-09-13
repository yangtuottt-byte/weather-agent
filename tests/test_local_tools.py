from datetime import date

from weather_agent.local_tools import get_today, get_weather


def test_get_today_returns_valid_date():
    result = get_today()

    parsed_date = date.fromisoformat(result)

    assert parsed_date == date.today()


def test_get_weather_rejects_unknown_city():
    result = get_weather("杭州")

    assert result == "目前只支持北京、上海和广州。"


def test_get_weather_uses_api_response(monkeypatch):
    calls = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "current": {
                    "temperature_2m": 25.5,
                }
            }

    def fake_get(url, params, timeout):
        calls["url"] = url
        calls["params"] = params
        calls["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(
        "weather_agent.local_tools.requests.get",
        fake_get,
    )

    result = get_weather("北京")

    assert result == "北京当前气温：25.5摄氏度"
    assert calls["params"]["latitude"] == 39.90
    assert calls["params"]["longitude"] == 116.40
    assert calls["timeout"] == 20
