import fs_tools


def test_list_and_filter():
    all_files = fs_tools.list_files("resumes")
    pdfs = fs_tools.list_files("resumes", ".pdf")
    assert len(all_files) >= 5
    assert pdfs and all(f["name"].endswith(".pdf") for f in pdfs)
    assert {"name", "size_bytes", "modified"} <= set(all_files[0])


def test_read_all_formats():
    for name in ("resume_john_doe.pdf", "resume_arjun_mehta.docx", "resume_ravi_kumar.txt"):
        r = fs_tools.read_file(f"resumes/{name}")
        assert r["success"] and r["content"].strip(), name


def test_search_case_insensitive():
    r = fs_tools.search_in_file("resumes/resume_john_doe.pdf", "PYTHON")
    assert r["success"] and r["match_count"] >= 1 and r["matches"][0]["context"]


def test_write_creates_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(fs_tools, "BASE_DIR", tmp_path)
    r = fs_tools.write_file("a/b/out.md", "hi")
    assert r["success"] and (tmp_path / "a/b/out.md").read_text() == "hi"


def test_errors_and_sandbox():
    assert not fs_tools.read_file("resumes/missing.pdf")["success"]
    assert not fs_tools.read_file("../../Windows/win.ini")["success"]
    assert not fs_tools.write_file("x.exe", "no")["success"]
