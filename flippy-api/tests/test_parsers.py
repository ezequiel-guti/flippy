from app.modules.documents.parsers import extract_text


def test_extract_text_strips_nul_bytes():
    content = "antes\x00despues".encode("utf-8")
    text = extract_text(content, "txt")
    assert "\x00" not in text
    assert text == "antesdespues"
