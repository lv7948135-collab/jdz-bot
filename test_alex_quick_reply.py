"""
test_alex_quick_reply.py — unit-тесты для детерминированного pre-filter Alex-бота.

Нет реальных LLM/API вызовов. Нет сетевых зависимостей.
Все внешние зависимости (ai_engine, marketplace_service, config)
заменяются моками ДО импорта claude_client, поскольку те импортируются
на уровне модуля.

Запуск:
    cd /root/jdz-bot-new
    /root/jdz-bot-new/venv/bin/python -m pytest test_alex_quick_reply.py -v
    # или без pytest:
    /root/jdz-bot-new/venv/bin/python test_alex_quick_reply.py
"""
import sys
import types
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# ─── Pre-inject mocks ПЕРЕД импортом claude_client ───────────────────────────
# claude_client выполняет sys.path.append('/root/djavis-os') и сразу импортирует
# ai_engine + marketplace_service на уровне модуля. Эти модули требуют наличия
# ANTHROPIC_API_KEY в окружении. Подменяем их в sys.modules до первого импорта,
# чтобы не было ни реальной загрузки production-кода, ни сетевых вызовов.

_mock_ai_engine = types.ModuleType("ai_engine")
_mock_ai_engine.call_ai = AsyncMock(return_value="MOCK_LLM_RESPONSE")
_mock_ai_engine.ask = AsyncMock(return_value="MOCK_LLM_RESPONSE")
_mock_ai_engine.DEFAULT_MODEL = "mock-model"
_mock_ai_engine.FAST_MODEL = "mock-fast-model"
sys.modules.setdefault("ai_engine", _mock_ai_engine)

_mock_config = types.ModuleType("config")
_mock_config.LLM_ENABLED = True
_mock_config.MARKETPLACE_SERVICE_ENABLED = False
sys.modules.setdefault("config", _mock_config)

_mock_ms = types.ModuleType("marketplace_service")
_mock_ms.MarketplaceInput = MagicMock()
_mock_ms.MarketplaceResult = MagicMock()
_mock_ms.run = AsyncMock()
sys.modules.setdefault("marketplace_service", _mock_ms)

_mock_unit_eco = types.ModuleType("unit_economics")
sys.modules.setdefault("unit_economics", _mock_unit_eco)

sys.path.insert(0, "/root/jdz-bot-new")

from ai.claude_client import _alex_normalize, _alex_quick_reply, get_claude_response


# ─── _alex_normalize ──────────────────────────────────────────────────────────

class TestAlexNormalize(unittest.TestCase):

    def test_strips_whitespace(self):
        self.assertEqual(_alex_normalize("  привет  "), "привет")

    def test_lowercases(self):
        self.assertEqual(_alex_normalize("ПРИВЕТ"), "привет")
        self.assertEqual(_alex_normalize("Здравствуйте"), "здравствуйте")

    def test_removes_exclamation(self):
        self.assertEqual(_alex_normalize("Привет!"), "привет")

    def test_removes_question_mark(self):
        self.assertEqual(_alex_normalize("что ты умеешь?"), "что ты умеешь")

    def test_removes_comma(self):
        self.assertEqual(_alex_normalize("Алекс, привет"), "алекс привет")

    def test_removes_dot(self):
        self.assertEqual(_alex_normalize("спасибо."), "спасибо")

    def test_collapses_spaces(self):
        self.assertEqual(_alex_normalize("добрый  день"), "добрый день")

    def test_empty_string(self):
        self.assertEqual(_alex_normalize(""), "")

    def test_only_spaces(self):
        self.assertEqual(_alex_normalize("   "), "")

    def test_combined(self):
        self.assertEqual(_alex_normalize("  Алекс, ты работаешь?  "), "алекс ты работаешь")


# ─── SHOULD MATCH (ZERO-LLM) ─────────────────────────────────────────────────

class TestAlexQuickReplyMatch(unittest.TestCase):
    """Запросы, которые ДОЛЖНЫ перехватываться quick rules (возвращать не None)."""

    def assertMatches(self, text):
        result = _alex_quick_reply(text)
        self.assertIsNotNone(result, f"Expected quick reply for: {text!r}")
        return result

    # --- Greetings ---
    def test_privet(self):
        self.assertMatches("привет")

    def test_privet_upper(self):
        self.assertMatches("Привет")

    def test_privet_exclamation(self):
        self.assertMatches("Привет!")

    def test_zdravstvuyte(self):
        self.assertMatches("Здравствуйте")

    def test_zdravstvuy(self):
        self.assertMatches("Здравствуй")

    def test_dobroe_utro(self):
        self.assertMatches("Доброе утро")

    def test_dobryy_den(self):
        self.assertMatches("добрый день")

    def test_dobryy_vecher(self):
        self.assertMatches("Добрый вечер")

    def test_dobroy_nochi(self):
        self.assertMatches("доброй ночи")

    def test_hello(self):
        self.assertMatches("hello")

    def test_hello_upper(self):
        self.assertMatches("Hello")

    def test_hi(self):
        self.assertMatches("hi")

    def test_hay(self):
        self.assertMatches("хай")

    def test_privet_alex(self):
        self.assertMatches("Привет алекс")

    def test_alex_privet(self):
        self.assertMatches("Алекс привет")

    def test_privet_comma_alex(self):
        # "Привет, Алекс" → нормализуется в "привет алекс" → должен совпасть
        self.assertMatches("Привет, Алекс")

    # --- Thanks ---
    def test_spasibo(self):
        self.assertMatches("спасибо")

    def test_spasibo_upper(self):
        self.assertMatches("Спасибо")

    def test_spasibo_exclamation(self):
        self.assertMatches("Спасибо!")

    def test_spasibo_alex(self):
        self.assertMatches("Спасибо алекс")

    def test_alex_spasibo(self):
        self.assertMatches("Алекс спасибо")

    def test_blagodaryu(self):
        self.assertMatches("благодарю")

    def test_sps(self):
        self.assertMatches("спс")

    def test_blagodaryu_alex(self):
        self.assertMatches("благодарю алекс")

    # --- Help / Capabilities ---
    def test_chto_ty_umeesh_q(self):
        self.assertMatches("что ты умеешь?")

    def test_chto_ty_umeesh(self):
        self.assertMatches("что ты умеешь")

    def test_chto_umeesh(self):
        self.assertMatches("что умеешь")

    def test_chto_mozhesh(self):
        self.assertMatches("что можешь")

    def test_chem_mozhesh_pomoch(self):
        self.assertMatches("чем можешь помочь")

    def test_pomoshch(self):
        self.assertMatches("помощь")

    def test_slash_help(self):
        self.assertMatches("/help")

    def test_kak_ty_pomogaesh(self):
        self.assertMatches("как ты помогаешь")

    def test_chto_ty_delaesh(self):
        self.assertMatches("что ты делаешь")

    # --- Status / Availability ---
    def test_ty_rabotaesh(self):
        self.assertMatches("ты работаешь")

    def test_ty_rabotaesh_q(self):
        self.assertMatches("ты работаешь?")

    def test_alex_ty_rabotaesh(self):
        self.assertMatches("алекс ты работаешь")

    def test_alex_comma_ty_rabotaesh_q(self):
        self.assertMatches("Алекс, ты работаешь?")

    def test_rabotaesh(self):
        self.assertMatches("работаешь")

    def test_ty_online(self):
        self.assertMatches("ты онлайн")

    def test_bot_rabotaet(self):
        self.assertMatches("бот работает")

    def test_ty_zhivoy(self):
        self.assertMatches("ты живой")

    def test_ty_aktiven(self):
        self.assertMatches("ты активен")

    def test_greeting_response_contains_data_prompt(self):
        """Ответ на приветствие содержит приглашение написать данные."""
        result = _alex_quick_reply("привет")
        self.assertIn("данные", result)

    def test_status_response_contains_ok(self):
        """Ответ на статус-запрос содержит 'работаю'."""
        result = _alex_quick_reply("ты работаешь")
        self.assertIn("работаю", result)


# ─── SHOULD NOT MATCH (→ existing path) ──────────────────────────────────────

class TestAlexQuickReplyNoMatch(unittest.TestCase):
    """Запросы, которые НЕ должны перехватываться — уходят в existing path."""

    def assertNoMatch(self, text):
        result = _alex_quick_reply(text)
        self.assertIsNone(result, f"Expected None (no quick reply) for: {text!r}")

    # --- КРИТИЧЕСКИЕ ТЕСТЫ: смешанные ---
    def test_privet_s_voprosom_WB(self):
        """КРИТИЧЕСКИЙ: приветствие + содержательный вопрос — НЕ перехватывать."""
        self.assertNoMatch("Привет, почему падает выкуп?")

    def test_spasibo_s_zadachey(self):
        self.assertNoMatch("Спасибо, а теперь рассчитай прибыль")

    def test_help_s_wb_komissiya(self):
        self.assertNoMatch("Что ты умеешь по Wildberries и какая комиссия?")

    def test_alex_kak_ty_rabotaesh(self):
        # "как ты работаешь" ≠ "алекс ты работаешь" → no match
        self.assertNoMatch("Алекс, как ты работаешь?")

    # --- Marketplace metrics ---
    def test_marketplace_numbers(self):
        self.assertNoMatch("цена 1500 себестоимость 600 комиссия 15 возврат 30")

    def test_marketplace_full(self):
        msg = ("Цена: 2500\nСебестоимость: 900\nКомиссия: 20%\n"
               "Логистика: 120\nРеклама: 200\nВозврат: 35%")
        self.assertNoMatch(msg)

    # --- Стратегические вопросы ---
    def test_kak_uluchshit_kartochku(self):
        self.assertNoMatch("Как улучшить карточку WB?")

    def test_kak_podnyat_pozitsii(self):
        self.assertNoMatch("Как повысить позиции карточки на Wildberries?")

    # --- Edge cases ---
    def test_empty_string(self):
        self.assertNoMatch("")

    def test_only_spaces(self):
        self.assertNoMatch("   ")

    def test_long_message_over_limit(self):
        """Любое сообщение > 60 символов → None, даже если начинается с "привет"."""
        long_msg = "привет " + "x" * 55
        self.assertGreater(len(long_msg), 60)
        self.assertNoMatch(long_msg)

    def test_exactly_61_chars_greeting(self):
        """Ровно 61 символ → None."""
        msg = "привет " + "а" * 54  # 7 + 54 = 61
        self.assertEqual(len(msg), 61)
        self.assertNoMatch(msg)


# ─── INTEGRATION VIA MOCKS ────────────────────────────────────────────────────

class TestGetClaudeResponseIntegration(unittest.IsolatedAsyncioTestCase):
    """
    Проверяем поведение get_claude_response() через AsyncMock.
    Реальных LLM/API вызовов нет — всё через patch.
    """

    async def test_quick_match_skips_llm(self):
        """Quick rule сработал → LLM НЕ вызывается."""
        with patch("ai.claude_client.ai_engine") as mock_ae:
            mock_ae.call_ai = AsyncMock(return_value="SHOULD_NOT_REACH")
            result = await get_claude_response("привет")
            mock_ae.call_ai.assert_not_called()
            self.assertIsNotNone(result)
            self.assertIn("данные", result)

    async def test_quick_match_spasibo_skips_llm(self):
        """Благодарность → LLM НЕ вызывается."""
        with patch("ai.claude_client.ai_engine") as mock_ae:
            mock_ae.call_ai = AsyncMock(return_value="SHOULD_NOT_REACH")
            result = await get_claude_response("Спасибо!")
            mock_ae.call_ai.assert_not_called()
            self.assertIn("Пожалуйста", result)

    async def test_complex_non_match_calls_llm_once(self):
        """Non-match → ai_engine.call_ai вызывается ровно один раз."""
        with patch("ai.claude_client.ai_engine") as mock_ae:
            mock_ae.call_ai = AsyncMock(return_value="MOCK_LLM_RESPONSE")
            result = await get_claude_response("Как повысить позиции на WB?")
            mock_ae.call_ai.assert_called_once()
            self.assertEqual(result, "MOCK_LLM_RESPONSE")

    async def test_privet_plus_question_calls_llm(self):
        """КРИТИЧЕСКИЙ: "Привет, почему падает выкуп?" → НЕ перехвачен → LLM."""
        with patch("ai.claude_client.ai_engine") as mock_ae:
            mock_ae.call_ai = AsyncMock(return_value="LLM_ANSWER")
            result = await get_claude_response("Привет, почему падает выкуп?")
            mock_ae.call_ai.assert_called_once()
            self.assertEqual(result, "LLM_ANSWER")

    async def test_marketplace_path_untouched(self):
        """При наличии price+cost_price+commission → marketplace path, quick rules не мешают."""
        mock_result = MagicMock()
        mock_result.error = None
        mock_result.diagnosis = "MOCK_DIAGNOSIS"
        mock_result.unit_economics = {
            "profit_per_unit": 200.0,
            "profit_margin_percent": 15.0,
        }
        mock_result.verdict = "🟢 ПРИБЫЛЬ"
        mock_result.next_action = {"description": "Продолжать отслеживать"}
        with patch("ai.claude_client.ms") as mock_ms:
            mock_ms.run = AsyncMock(return_value=mock_result)
            mock_ms.MarketplaceInput = MagicMock(return_value=MagicMock())
            msg = "цена 1500 себестоимость 600 комиссия 15 возвратов нет"
            result = await get_claude_response(msg)
            mock_ms.run.assert_called_once()
            self.assertNotIn("Привет", result)

    async def test_long_greeting_calls_llm(self):
        """Сообщение длиннее 60 символов — quick rules игнорируются."""
        with patch("ai.claude_client.ai_engine") as mock_ae:
            mock_ae.call_ai = AsyncMock(return_value="LLM_RESPONSE_LONG")
            long_msg = "привет " + "x" * 55
            self.assertGreater(len(long_msg), 60)
            result = await get_claude_response(long_msg)
            mock_ae.call_ai.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
