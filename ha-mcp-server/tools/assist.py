from tools._base import mcp, default_language, _ws


@mcp.tool()
def list_assist_pipelines() -> dict:
    """
    List all Assist voice pipelines configured in Home Assistant.

    Returns: {preferred_pipeline, pipelines: [{id, name, language,
              conversation_engine, stt_engine, tts_engine, tts_voice}]}

    Assist pipelines define which STT (speech-to-text), conversation agent,
    and TTS (text-to-speech) engine are used for voice commands.
    """
    result = _ws({"type": "assist_pipeline/pipeline/list"})
    if not result.get("success", True):
        err = result.get("error", {})
        return {"error": err.get("code", "unknown"), "detail": err.get("message", "")}
    data = result.get("result") or {}
    pipelines = data.get("pipelines", [])
    return {
        "preferred_pipeline": data.get("preferred_pipeline"),
        "pipelines": [
            {
                "id": p.get("id"),
                "name": p.get("name"),
                "language": p.get("language"),
                "conversation_engine": p.get("conversation_engine"),
                "conversation_language": p.get("conversation_language"),
                "stt_engine": p.get("stt_engine"),
                "stt_language": p.get("stt_language"),
                "tts_engine": p.get("tts_engine"),
                "tts_language": p.get("tts_language"),
                "tts_voice": p.get("tts_voice"),
                "wake_word_entity": p.get("wake_word_entity"),
                "wake_word_id": p.get("wake_word_id"),
            }
            for p in pipelines
        ],
    }


@mcp.tool()
def create_assist_pipeline(
    name: str,
    language: str = "",
    conversation_engine: str = "homeassistant",
    conversation_language: str = "",
    stt_engine: str = "",
    stt_language: str = "",
    tts_engine: str = "",
    tts_language: str = "",
    tts_voice: str = "",
) -> dict:
    """
    Create a new Assist voice pipeline.

    name:                 display name for the pipeline
    language:             primary language code, e.g. 'en', 'de'; defaults to the
                          language configured in Home Assistant
    conversation_engine:  entity_id of the conversation agent, e.g. 'homeassistant'
                          or a custom LLM like 'conversation.openai_gpt4'
    conversation_language: language for the conversation agent; same default
    stt_engine:           entity_id of the STT engine (speech-to-text),
                          e.g. 'stt.whisper' or '' for none
    stt_language:         language for STT, e.g. 'en-GB'
    tts_engine:           entity_id of the TTS engine (text-to-speech),
                          e.g. 'tts.piper' or 'tts.google_translate'
    tts_language:         language for TTS
    tts_voice:            voice ID for TTS (engine-specific)

    Use list_assist_pipelines() to see examples from existing pipelines.
    """
    language = language or default_language()
    conversation_language = conversation_language or language
    msg: dict = {
        "type": "assist_pipeline/pipeline/create",
        "name": name,
        "language": language,
        "conversation_engine": conversation_engine,
        "conversation_language": conversation_language,
        "stt_engine": stt_engine or None,
        "stt_language": stt_language or None,
        "tts_engine": tts_engine or None,
        "tts_language": tts_language or None,
        "tts_voice": tts_voice or None,
    }
    result = _ws(msg)
    if not result.get("success", True):
        err = result.get("error", {})
        return {"error": err.get("code", "unknown"), "detail": err.get("message", "")}
    return result.get("result", result)


@mcp.tool()
def update_assist_pipeline(
    pipeline_id: str,
    name: str = "",
    language: str = "",
    conversation_engine: str = "",
    stt_engine: str = "",
    tts_engine: str = "",
    tts_voice: str = "",
) -> dict:
    """
    Update an existing Assist pipeline.

    pipeline_id: pipeline ID (use list_assist_pipelines() to find it)
    Only non-empty fields are updated.
    """
    msg: dict = {"type": "assist_pipeline/pipeline/update", "pipeline_id": pipeline_id}
    if name:
        msg["name"] = name
    if language:
        msg["language"] = language
    if conversation_engine:
        msg["conversation_engine"] = conversation_engine
    if stt_engine:
        msg["stt_engine"] = stt_engine
    if tts_engine:
        msg["tts_engine"] = tts_engine
    if tts_voice:
        msg["tts_voice"] = tts_voice
    result = _ws(msg)
    if not result.get("success", True):
        err = result.get("error", {})
        return {"error": err.get("code", "unknown"), "detail": err.get("message", "")}
    return result.get("result", result)


@mcp.tool()
def delete_assist_pipeline(pipeline_id: str) -> dict:
    """
    Delete an Assist voice pipeline.

    pipeline_id: pipeline ID (use list_assist_pipelines() to find it).
    Note: the preferred (default) pipeline cannot be deleted.
    """
    result = _ws({"type": "assist_pipeline/pipeline/delete", "pipeline_id": pipeline_id})
    if not result.get("success", True):
        err = result.get("error", {})
        return {"error": err.get("code", "unknown"), "detail": err.get("message", "")}
    return {"deleted": pipeline_id, "success": True}


@mcp.tool()
def set_preferred_assist_pipeline(pipeline_id: str) -> dict:
    """
    Set the default (preferred) Assist pipeline.

    pipeline_id: pipeline ID to set as default (use list_assist_pipelines() to find it).
    """
    result = _ws({"type": "assist_pipeline/pipeline/set_preferred", "pipeline_id": pipeline_id})
    if not result.get("success", True):
        err = result.get("error", {})
        return {"error": err.get("code", "unknown"), "detail": err.get("message", "")}
    return {"preferred_pipeline": pipeline_id, "success": True}
