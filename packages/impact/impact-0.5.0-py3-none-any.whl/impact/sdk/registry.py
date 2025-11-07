from __future__ import annotations
import importlib
from typing import Iterable

def _instrument(module: str, class_name: str) -> bool:
    """Try to import `module`, get `class_name`, and call `.instrument()`."""
    try:
        mod = importlib.import_module(module)
        cls = getattr(mod, class_name)
        inst = cls()
        inst.instrument()
        return True
    except Exception:
        return False


# Official OTel GenAI providers

def instrument_openai() -> bool:
    # return _instrument("opentelemetry.instrumentation.openai_v2", "OpenAIInstrumentor")
    return _instrument("opentelemetry.instrumentation.openai", "OpenAIInstrumentor")

def instrument_openai_agents() -> bool:
    return _instrument("opentelemetry.instrumentation.openai_agents", "OpenAIAgentsInstrumentor")

def instrument_google_genai() -> bool:
    return _instrument("opentelemetry.instrumentation.google_genai", "GoogleGenAiSdkInstrumentor")

def instrument_vertexai() -> bool:
    # OTel ecosystem (Python contrib): opentelemetry-instrumentation-vertexai
    return _instrument("opentelemetry.instrumentation.vertexai", "VertexAIInstrumentor")


# Official instrumentors - Azure AI Inference and AWS Bedrock via Botocore

def instrument_azure_ai_inference() -> bool:
    return _instrument("azure.ai.inference.tracing", "AIInferenceInstrumentor")

def instrument_aws_bedrock() -> bool:
    return _instrument("opentelemetry.instrumentation.botocore", "BotocoreInstrumentor")


# Community Instrumentors

def instrument_anthropic() -> bool:
    return _instrument("opentelemetry.instrumentation.anthropic", "AnthropicInstrumentor")

def instrument_ollama() -> bool:
    return _instrument("opentelemetry.instrumentation.ollama", "OllamaInstrumentor")

def instrument_mistral() -> bool:
    return _instrument("opentelemetry.instrumentation.mistralai", "MistralAiInstrumentor")

def instrument_cohere() -> bool:
    return _instrument("opentelemetry.instrumentation.cohere", "CohereInstrumentor")

def instrument_groq() -> bool:
    return _instrument("opentelemetry.instrumentation.groq", "GroqInstrumentor")

def instrument_langchain() -> bool:
    return _instrument("opentelemetry.instrumentation.langchain", "LangchainInstrumentor")

def instrument_llama_index() -> bool:
    return _instrument("opentelemetry.instrumentation.llamaindex", "LlamaIndexInstrumentor")


# Infrastructure Instrumentors

def instrument_httpx() -> bool:
    """Instrument HTTPX HTTP client library for outbound HTTP request tracing."""
    return _instrument("opentelemetry.instrumentation.httpx", "HTTPXClientInstrumentor")

def instrument_azure_aisearch() -> bool:
    """Instrument Azure AI Search SDK for search query tracing."""
    return _instrument("opentelemetry.instrumentation.azure_aisearch", "AzureSearchInstrumentor")


# Auto-instrument all available GenAI providers
def auto_instrument_all() -> list[bool]:
    """Auto-instrument all available GenAI providers."""
    results: list[bool] = []
    results.append(instrument_openai())
    results.append(instrument_openai_agents())
    results.append(instrument_azure_ai_inference())
    results.append(instrument_google_genai())
    results.append(instrument_vertexai())
    results.append(instrument_aws_bedrock())
    results.append(instrument_anthropic())
    results.append(instrument_ollama())
    results.append(instrument_cohere())
    results.append(instrument_mistral())
    results.append(instrument_groq())
    results.append(instrument_langchain())
    results.append(instrument_llama_index())
    results.append(instrument_azure_aisearch())
    return results

# Export all instrumentors
__all__ = [
    "instrument_openai", 
    "instrument_openai_agents", 
    "instrument_google_genai", 
    "instrument_vertexai", 
    "instrument_azure_ai_inference", 
    "instrument_aws_bedrock", 
    "instrument_anthropic", 
    "instrument_ollama", 
    "instrument_mistral", 
    "instrument_cohere", 
    "instrument_groq", 
    "instrument_langchain", 
    "instrument_llama_index",
    "instrument_httpx",
    "instrument_azure_aisearch",
    "auto_instrument_all"
]
