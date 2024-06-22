from pathlib import Path
from sanic.pages.css import _extract_style, print_extract_style_coverage

def test_initial_print_extract_style():
    print("\nBranch coverage before: ")
    print_extract_style_coverage()
    print("\n")

def expected_file_path_test():
    expected_file = "p {text-align: center; color: red;} "
    Path("test_style.css").write_text(expected_file, encoding="UTF-8")
    results = _extract_style("test_style.css", "test")
    assert results == expected_file, f"Expected {expected_file},{results}"

def non_existing_file_path_test():
    non_existingFile = "nonexistent_style.css"
    results = _extract_style(non_existingFile, "test")
    assert results == non_existingFile, f"Expected {non_existingFile},{results}"

def no_files_path_test():
    results = _extract_style(None, "nonexistent_page")
    assert results == "", f"Expected '',{results}"

def test_final_print_extract_style():
    print("\nBranch coverage after: ")
    print_extract_style_coverage()
    print("\n")

test_initial_print_extract_style()
expected_file_path_test()
non_existing_file_path_test()
no_files_path_test()
test_final_print_extract_style()