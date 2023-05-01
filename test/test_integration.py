"""Integration test for serpapi-wrapper plugin."""
from steamship import Steamship
import api

PLUGIN_HANDLE = "serpapi-wrapper"


def test_run():

    test_cases = [
        ("How old was Abraham Lincoln when he died?", "56 years"),
        ("What year was the moon landing?", "July 16, 1969"),
        ("Who was the first president of the United States?", "George Washington"),
    ]

    with Steamship.temporary_workspace() as client:
        search = client.use_plugin(PLUGIN_HANDLE)

        for test_case in test_cases:
            task = search.tag(doc=test_case[0])
            task.wait()
            file = task.output.file
            assert file is not None
            assert file.blocks is not None
            assert len(file.blocks) == 1
            assert len(file.blocks[0].tags) == 1
            tag = file.blocks[0].tags[0]
            assert tag.kind == api.TAG_KIND
            assert tag.name == api.TAG_NAME
            assert len(tag.value.items()) == 2
            assert tag.value.get(api.VALUE_KEY_QUERY, "") == test_case[0]
            assert tag.value.get(api.VALUE_KEY_ANSWER, "") == test_case[1]
