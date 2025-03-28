import logging
from typing import Optional

from assistant.ai.domain import AIResponse
from assistant.ai.providers.base import AIDebugger
from assistant.bot.domain import Answer, SingleAnswer
from assistant.bot.assistant_bot import AssistantBot

logger = logging.getLogger(__name__)


class SimpleAIBot(AssistantBot):
    """
    A minimal bot that forwards requests to the AI.
    """

    async def get_answer_to_messages(self, messages, debug_info, do_interrupt) -> Answer:
        """
        Process incoming messages and forward to AI.

        :param messages: List of message dictionaries containing the conversation history
        :param debug_info: Dictionary for storing debug information
        :param do_interrupt: Function to check if processing should be interrupted
        :return: AI-generated response
        :rtype: Answer
        """
        with AIDebugger(self._strong_ai, debug_info, 'ai_response') as debugger:
            ai_response = await debugger.ai.get_response(messages)
            return SingleAnswer(ai_response.result)

    @AssistantBot.command('/start')
    async def command_start(self, *args, **kwargs):
        """
        Handle the start command.

        :return: Welcome message
        :rtype: Answer
        """
        return SingleAnswer("Hello! I'm a simple AI bot.")
