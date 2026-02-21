from . import ESGExtractorOllama, ESGExtractor

def create_extractor(backend: str = "ollama", **kwargs):
    """
    Choose LLM backend for extraction.
    Default is Ollama with Qwen2.5-14B.
    """
    if backend == "ollama":
        return ESGExtractorOllama(
            model=kwargs.get("model", "qwen2.5:14b")
        )
    # elif backend == "hf":
    #     return ESGExtractorHF(
    #         model_name=kwargs.get("model", "Qwen/Qwen2.5-14B-Instruct"),
    #         quantize_4bit=kwargs.get("quantize", True),
    #     )
    # elif backend in ("groq", "together", "huggingface"):
    #     return ESGExtractorCloud(
    #         provider=backend,
    #         api_key=kwargs.get("api_key", ""),
    #     )
    elif backend == "openai":
        return ESGExtractor(api_key=kwargs.get("api_key", ""))
    else:
        raise ValueError(f"Unknown backend: {backend}")

