"""
OpenAI API client wrapper for LLM interactions.
"""

import asyncio
import json
import logging
from typing import List, Dict, Optional, Any
from openai import AsyncOpenAI, OpenAI

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Wrapper around OpenAI API for grading operations."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key
            model: Model name (gpt-4, gpt-4o, etc.)
            temperature: Temperature for response generation
            max_tokens: Maximum tokens in response
        """
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Initialize sync and async clients
        self.sync_client = OpenAI(api_key=api_key)
        self.async_client = AsyncOpenAI(api_key=api_key)

    def chat_completion(
        self,
        system: str,
        user: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Make a synchronous chat completion request.

        Args:
            system: System prompt
            user: User message/prompt
            temperature: Temperature for this request (overrides default)
            max_tokens: Max tokens for this request (overrides default)
            response_format: Response format specification (e.g., {"type": "json_object"})

        Returns:
            Response content from the model
        """
        try:
            temp = temperature if temperature is not None else self.temperature
            tokens = max_tokens if max_tokens is not None else self.max_tokens

            kwargs = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": temp,
                "max_tokens": tokens,
            }

            if response_format:
                kwargs["response_format"] = response_format

            response = self.sync_client.chat.completions.create(**kwargs)
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error in chat_completion: {str(e)}")
            raise

    async def chat_completion_async(
        self,
        system: str,
        user: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Make an asynchronous chat completion request.

        Args:
            system: System prompt
            user: User message/prompt
            temperature: Temperature for this request
            max_tokens: Max tokens for this request
            response_format: Response format specification

        Returns:
            Response content from the model
        """
        try:
            temp = temperature if temperature is not None else self.temperature
            tokens = max_tokens if max_tokens is not None else self.max_tokens

            kwargs = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": temp,
                "max_tokens": tokens,
            }

            if response_format:
                kwargs["response_format"] = response_format

            response = await self.async_client.chat.completions.create(**kwargs)
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error in chat_completion_async: {str(e)}")
            raise

    async def batch_chat_completions(
        self,
        requests: List[Dict[str, Any]],
    ) -> List[str]:
        """
        Execute multiple chat completions in parallel.

        Args:
            requests: List of request dicts, each containing:
                - system: System prompt
                - user: User message
                - temperature: (optional) Temperature
                - max_tokens: (optional) Max tokens
                - response_format: (optional) Response format

        Returns:
            List of responses in the same order as input
        """
        tasks = [
            self.chat_completion_async(
                system=req["system"],
                user=req["user"],
                temperature=req.get("temperature"),
                max_tokens=req.get("max_tokens"),
                response_format=req.get("response_format"),
            )
            for req in requests
        ]

        try:
            results = await asyncio.gather(*tasks)
            return results
        except Exception as e:
            logger.error(f"Error in batch_chat_completions: {str(e)}")
            raise

    def parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON response from LLM.

        Args:
            response: Response string from LLM

        Returns:
            Parsed JSON dict

        Raises:
            ValueError: If response is not valid JSON
        """
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            logger.error(f"Response content: {response[:500]}")
            raise ValueError(f"Invalid JSON in LLM response: {str(e)}")

    @staticmethod
    def create_json_request(
        system: str,
        user: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> Dict[str, Any]:
        """
        Create a chat completion request dict for batch processing.

        Args:
            system: System prompt
            user: User message
            temperature: Temperature
            max_tokens: Max tokens

        Returns:
            Request dict suitable for batch_chat_completions
        """
        return {
            "system": system,
            "user": user,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }
