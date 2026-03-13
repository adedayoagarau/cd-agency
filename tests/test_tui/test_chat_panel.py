"""Tests for the ChatPanel widget."""

from __future__ import annotations

import pytest

from textual.app import App, ComposeResult

from runtime.tui.widgets.chat_panel import ChatPanel, ChatMessage


class ChatTestApp(App):
    def compose(self) -> ComposeResult:
        yield ChatPanel(id="chat")


class TestChatPanel:
    @pytest.mark.asyncio
    async def test_initial_state(self):
        app = ChatTestApp()
        async with app.run_test() as pilot:
            chat = app.query_one("#chat", ChatPanel)
            assert chat.messages == []
            assert chat._last_agent_text == ""

    @pytest.mark.asyncio
    async def test_add_user_message(self):
        app = ChatTestApp()
        async with app.run_test() as pilot:
            chat = app.query_one("#chat", ChatPanel)
            chat.add_user_message("Hello")
            assert len(chat.messages) == 1
            assert chat.messages[0]["role"] == "user"
            assert chat.messages[0]["content"] == "Hello"

    @pytest.mark.asyncio
    async def test_add_agent_message(self):
        app = ChatTestApp()
        async with app.run_test() as pilot:
            chat = app.query_one("#chat", ChatPanel)
            chat.add_agent_message("Hi there!")
            assert len(chat.messages) == 1
            assert chat.messages[0]["role"] == "assistant"
            assert chat._last_agent_text == "Hi there!"

    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self):
        app = ChatTestApp()
        async with app.run_test() as pilot:
            chat = app.query_one("#chat", ChatPanel)
            chat.add_user_message("Fix this error: 500")
            chat.add_agent_message("What context?")
            chat.add_user_message("User saving a form")
            chat.add_agent_message("Here are 3 options...")
            assert len(chat.messages) == 4
            assert chat.messages[0]["role"] == "user"
            assert chat.messages[1]["role"] == "assistant"
            assert chat.messages[2]["role"] == "user"
            assert chat.messages[3]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_clear_chat(self):
        app = ChatTestApp()
        async with app.run_test() as pilot:
            chat = app.query_one("#chat", ChatPanel)
            chat.add_user_message("Hello")
            chat.add_agent_message("Hi!")
            chat.clear_chat()
            assert chat.messages == []
            assert chat._last_agent_text == ""

    @pytest.mark.asyncio
    async def test_loading_state(self):
        app = ChatTestApp()
        async with app.run_test() as pilot:
            chat = app.query_one("#chat", ChatPanel)
            chat.set_loading(True)
            assert chat._is_loading is True
            chat.set_loading(False)
            assert chat._is_loading is False


class TestChatMessage:
    def test_user_message_role(self):
        msg = ChatMessage("Hello", "user")
        assert msg.role == "user"
        assert msg.content_text == "Hello"

    def test_agent_message_role(self):
        msg = ChatMessage("Hi!", "assistant")
        assert msg.role == "assistant"
        assert msg.content_text == "Hi!"
