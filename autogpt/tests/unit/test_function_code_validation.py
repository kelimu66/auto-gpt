import pytest
from forge.utils.function.code_validation import CodeValidator, FunctionDef


@pytest.mark.asyncio
async def test_code_validation():
    validator = CodeValidator(
        available_functions={
            "read_webpage": FunctionDef(
                name="read_webpage",
                arg_types=[("url", "str"), ("query", "str")],
                arg_descs={
                    "url": "URL to read",
                    "query": "Query to search",
                    "return_type": "Type of return value",
                },
                return_type="str",
                return_desc="Information matching the query",
                function_desc="Read a webpage and return the info matching the query",
                is_async=True,
            ),
            "web_search": FunctionDef(
                name="web_search",
                arg_types=[("query", "str")],
                arg_descs={"query": "Query to search"},
                return_type="list[(str,str)]",
                return_desc="List of tuples with title and URL",
                function_desc="Search the web and return the search results",
                is_async=True,
            ),
            "main": FunctionDef(
                name="main",
                arg_types=[],
                arg_descs={},
                return_type="str",
                return_desc="Answer in the text format",
                function_desc="Get the num of contributors to the autogpt github repo",
                is_async=False,
            ),
        },
        available_objects={},
    )
    response = await validator.validate_code(
        raw_code="""
def crawl_info(url: str, query: str) -> str | None:
    info = await read_webpage(url, query)
    if info:
        return info

    urls = await read_webpage(url, "autogpt github contributor page")
    for url in urls.split('\\n'):
        info = await crawl_info(url, query)
        if info:
            return info

    return None

def hehe():
    return 'hehe'

def main() -> str:
    query = "Find the number of contributors to the autogpt github repository"
    for title, url in ("autogpt github contributor page"):
        info = await crawl_info(url, query)
        if info:
            return info
    x = await hehe()
    return "No info found"
""",
        packages=[],
    )
    assert response.functionCode is not None
    assert "async def crawl_info" in response.functionCode  # async is added
    assert "async def main" in response.functionCode
    assert "x = hehe()" in response.functionCode  # await is removed
