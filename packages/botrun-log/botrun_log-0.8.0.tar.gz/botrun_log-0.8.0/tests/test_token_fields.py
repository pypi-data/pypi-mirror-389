"""測試 token 欄位功能"""
from botrun_log.log_entry import TextLogEntry, AudioLogEntry, ImageLogEntry, VectorDBLogEntry


def test_text_log_entry_with_tokens():
    """測試 TextLogEntry 包含 token 欄位"""
    log_entry = TextLogEntry(
        "2021-01-01T00:00:00Z", 'botrun.ai', "test_org", "user_1", "127.0.0.1",
        "session_1", "llm_input", "JcXGTcW", "gpt-4o", "波程.botrun",
        "測試內容", "user_agent", "resource_1",
        input_tokens=150,
        output_tokens=300,
        total_tokens=450
    )

    log_dict = log_entry.to_dict()
    assert log_dict["input_tokens"] == 150
    assert log_dict["output_tokens"] == 300
    assert log_dict["total_tokens"] == 450


def test_text_log_entry_without_tokens():
    """測試向後相容：不提供 token 欄位"""
    log_entry = TextLogEntry(
        "2021-01-01T00:00:00Z", 'botrun.ai', "test_org", "user_1", "127.0.0.1",
        "session_1", "llm_input", "JcXGTcW", "gpt-4o", "波程.botrun",
        "測試內容", "user_agent", "resource_1"
    )

    log_dict = log_entry.to_dict()
    assert log_dict["input_tokens"] is None
    assert log_dict["output_tokens"] is None
    assert log_dict["total_tokens"] is None


def test_audio_log_entry_with_tokens():
    """測試 AudioLogEntry 包含 token 欄位"""
    log_entry = AudioLogEntry(
        "2021-01-01T00:00:00Z", 'botrun.ai', "test_org", "user_1", "127.0.0.1",
        "session_1", "audio_upload", "JcXGTcW", "whisper-1", "波程.botrun",
        20, "音檔上傳", "user_agent", "audio_1",
        input_tokens=100,
        output_tokens=200,
        total_tokens=300
    )

    log_dict = log_entry.to_dict()
    assert log_dict["input_tokens"] == 100
    assert log_dict["output_tokens"] == 200
    assert log_dict["total_tokens"] == 300


def test_image_log_entry_with_tokens():
    """測試 ImageLogEntry 包含 token 欄位"""
    log_entry = ImageLogEntry(
        "2021-01-01T00:00:00Z", 'botrun.ai', "test_org", "user_1", "127.0.0.1",
        "session_1", "image_upload", "JcXGTcW", "dall-e-3", "波程.botrun",
        1.5, "圖片上傳", "user_agent", "image_1",
        input_tokens=50,
        output_tokens=75,
        total_tokens=125
    )

    log_dict = log_entry.to_dict()
    assert log_dict["input_tokens"] == 50
    assert log_dict["output_tokens"] == 75
    assert log_dict["total_tokens"] == 125


def test_vector_log_entry_with_tokens():
    """測試 VectorDBLogEntry 包含 token 欄位"""
    log_entry = VectorDBLogEntry(
        "2021-01-01T00:00:00Z", 'botrun.ai', "test_org", "user_1", "127.0.0.1",
        "session_1", "vector_operation", "JcXGTcW", "text-embedding-ada-002",
        "波程.botrun", 10, "向量操作", "user_agent", "vector_1",
        input_tokens=25,
        output_tokens=0,
        total_tokens=25
    )

    log_dict = log_entry.to_dict()
    assert log_dict["input_tokens"] == 25
    assert log_dict["output_tokens"] == 0
    assert log_dict["total_tokens"] == 25
