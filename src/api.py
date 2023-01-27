"""Plugin to return Google Search answers for queries using SerpAPI"""
from typing import Dict, Type

from serpapi import GoogleSearch

from steamship import SteamshipError, Tag
from steamship.invocable import Config, InvocableResponse
from steamship.plugin.inputs.block_and_tag_plugin_input import BlockAndTagPluginInput
from steamship.plugin.outputs.block_and_tag_plugin_output import BlockAndTagPluginOutput
from steamship.plugin.request import PluginRequest
from steamship.plugin.tagger import Tagger

# tag consts
TAG_KIND = "search-result"
TAG_NAME = "GoogleSearch"
VALUE_KEY_QUERY = "query"
VALUE_KEY_ANSWER = "answer"


class SerpApiConfig(Config):
    """Configures the Serp API."""

    serpapi_api_key: str


class SerpApiWrapper(Tagger):
    """Tags files based on search results of their content."""

    config: SerpApiConfig

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        GoogleSearch.SERP_API_KEY = self.config.serpapi_api_key

    def config_cls(self) -> Type[Config]:
        """Return the Configuration class."""
        return SerpApiConfig

    def run(
        self, request: PluginRequest[BlockAndTagPluginInput]
    ) -> InvocableResponse[BlockAndTagPluginOutput]:
        """For each block in the submitted file, submit a search query and retrieve the answer."""

        file = request.data.file
        for block in request.data.file.blocks:
            search = GoogleSearch({"q": block.text})

            try:
                answer = self._answer_from_search_results(search.get_dict())
            except ValueError as ve:
                raise SteamshipError(
                    str=f"Error executing search for {block.text}",
                    suggestion="Please try again if you feel this should have succeeded",
                    error=ve,
                )

            block.tags.append(
                Tag(
                    kind=TAG_KIND,
                    name=TAG_NAME,
                    value={
                        VALUE_KEY_QUERY: block.text,
                        VALUE_KEY_ANSWER: answer,
                    },
                )
            )
        return InvocableResponse(data=BlockAndTagPluginOutput(file=file))

    @staticmethod
    def _answer_from_search_results(search_result: Dict[str, str]) -> str:
        # borrows heavily from the implementation in:
        # https://github.com/hwchase17/langchain/blob/master/langchain/serpapi.py
        # which itself was borrowed from:
        # https://github.com/ofirpress/self-ask
        if "error" in search_result.keys():
            raise ValueError(f"Got error from SerpAPI: {search_result['error']}")

        if (
            "answer_box" in search_result.keys()
            and "answer" in search_result["answer_box"].keys()
        ):
            return search_result["answer_box"]["answer"]

        if (
            "answer_box" in search_result.keys()
            and "snippet" in search_result["answer_box"].keys()
        ):
            return search_result["answer_box"]["snippet"]

        if (
            "answer_box" in search_result.keys()
            and "snippet_highlighted_words" in search_result["answer_box"].keys()
        ):
            return search_result["answer_box"]["snippet_highlighted_words"][0]

        if (
            "sports_results" in search_result.keys()
            and "game_spotlight" in search_result["sports_results"].keys()
        ):
            return search_result["sports_results"]["game_spotlight"]

        if (
            "knowledge_graph" in search_result.keys()
            and "description" in search_result["knowledge_graph"].keys()
        ):
            return search_result["knowledge_graph"]["description"]

        if "snippet" in search_result["organic_results"][0].keys():
            return search_result["organic_results"][0]["snippet"]

        return "No good search result found"
