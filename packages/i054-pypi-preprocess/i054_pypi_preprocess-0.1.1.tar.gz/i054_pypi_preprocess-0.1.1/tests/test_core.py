from i054_pypi_preprocess import normalize_text, remove_punct, tokenize_simple, remove_stopwords, preprocess

def test_basic_functions():
    assert normalize_text("  Hello   WORLD ") == "hello world"
    assert remove_punct("hello, world!") == "hello world"
    assert tokenize_simple("Hello, World!") == ["hello", "world"]

def test_stopword_removal():
    tokens = ["this", "is", "anumay", "testing"]
    filtered = remove_stopwords(tokens)
    assert "this" not in filtered and "anumay" in filtered

def test_full_pipeline():
    out = preprocess("Hello, this is Anumay!")
    assert "hello" in out and "this" not in out
