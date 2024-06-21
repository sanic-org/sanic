from pathlib import Path
from sanic.pages.css import _extract_style

def expectedFileTest():
    expectedFile = "p {text-align: center; color: red;} "
    Path("test_style.css").write_text(expectedFile, encoding="UTF-8")
    results = _extract_style("test_style.css", "test")
    assert results == expectedFile, f"Expected {expectedFile},{results}"

def nonExistingFileTest():
    nonExistingFile = "nonexistent_style.css"
    results = _extract_style(nonExistingFile, "test")
    assert results == nonExistingFile, f"Expected {nonExistingFile},{results}"

def noFilesTest():
    results = _extract_style(None, "nonexistent_page")
    assert results == "", f"Expected '',{results}"

expectedFileTest()
nonExistingFileTest()
noFilesTest()