"""AlgoQX Studio -- Application Builder API Endpoints."""

from fastapi import APIRouter, HTTPException

from backend.models.schemas import AppGenerateRequest, AppGenerateResponse

router = APIRouter(prefix="/app", tags=["App Builder"])

TEMPLATES = {
    "chatbot": {
        "fastapi": (
            "from fastapi import FastAPI, HTTPException\n"
            "from pydantic import BaseModel\n"
            "from openai import OpenAI\n\n"
            "app = FastAPI(title='Generated Chatbot API')\n"
            "client = OpenAI(base_url='https://ollama.algoqx.tech/v1', api_key='sk-ollama-algoqx-2024')\n\n"
            "class ChatRequest(BaseModel):\n"
            "    message: str\n"
            "    history: list[dict[str, str]] = []\n"
            "    model: str = '{model}'\n\n"
            "@app.post('/chat')\n"
            "async def chat(request: ChatRequest):\n"
            "    messages = request.history + [{'role': 'user', 'content': request.message}]\n"
            "    try:\n"
            "        res = client.chat.completions.create(\n"
            "            model=request.model,\n"
            "            messages=messages\n"
            "        )\n"
            "        return {{'response': res.choices[0].message.content}}\n"
            "    except Exception as e:\n"
            "        raise HTTPException(status_code=500, detail=str(e))\n"
        ),
        "streamlit": (
            "import streamlit as st\n"
            "import requests\n\n"
            "st.title('AlgoQX Chatbot')\n"
            "if 'messages' not in st.session_state:\n"
            "    st.session_state.messages = []\n\n"
            "for msg in st.session_state.messages:\n"
            "    with st.chat_message(msg['role']):\n"
            "        st.markdown(msg['content'])\n\n"
            "user_input = st.chat_input('Type your message here...')\n"
            "if user_input:\n"
            "    with st.chat_message('user'):\n"
            "        st.markdown(user_input)\n"
            "    st.session_state.messages.append({{'role': 'user', 'content': user_input}})\n"
            "    \n"
            "    # Call FastAPI chatbot endpoint\n"
            "    try:\n"
            "        res = requests.post(\n"
            "            'http://localhost:8000/api/app/chatbot/run',\n"
            "            json={{'message': user_input, 'history': st.session_state.messages[:-1]}}\n"
            "        )\n"
            "        ans = res.json().get('response', 'Error fetching reply.')\n"
            "        with st.chat_message('assistant'):\n"
            "            st.markdown(ans)\n"
            "        st.session_state.messages.append({{'role': 'assistant', 'content': ans}})\n"
            "    except Exception as e:\n"
            "        st.error(f'Failed to connect: {{e}}')\n"
        ),
        "swagger": {
            "paths": {
                "/chat": {
                    "post": {
                        "summary": "Chat completion",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "message": {"type": "string"},
                                            "history": {"type": "array", "items": {"type": "object"}},
                                        },
                                        "required": ["message"],
                                    }
                                }
                            }
                        },
                        "responses": {"200": {"description": "Successful Response"}},
                    }
                }
            }
        },
    },
    "summarizer": {
        "fastapi": (
            "from fastapi import FastAPI, HTTPException\n"
            "from pydantic import BaseModel\n"
            "from openai import OpenAI\n\n"
            "app = FastAPI(title='Generated Summarizer API')\n"
            "client = OpenAI(base_url='https://ollama.algoqx.tech/v1', api_key='sk-ollama-algoqx-2024')\n\n"
            "class SummarizeRequest(BaseModel):\n"
            "    text: str\n"
            "    max_words: int = 150\n"
            "    model: str = '{model}'\n\n"
            "@app.post('/summarize')\n"
            "async def summarize(request: SummarizeRequest):\n"
            "    system = f'Summarize the following text in under {{request.max_words}} words.'\n"
            "    messages = [\n"
            "        {{'role': 'system', 'content': system}},\n"
            "        {{'role': 'user', 'content': request.text}}\n"
            "    ]\n"
            "    try:\n"
            "        res = client.chat.completions.create(\n"
            "            model=request.model,\n"
            "            messages=messages\n"
            "        )\n"
            "        return {{'summary': res.choices[0].message.content}}\n"
            "    except Exception as e:\n"
            "        raise HTTPException(status_code=500, detail=str(e))\n"
        ),
        "streamlit": (
            "import streamlit as st\n"
            "import requests\n\n"
            "st.title('AlgoQX Text Summarizer')\n"
            "text_input = st.text_area('Paste text to summarize', height=250)\n"
            "max_words = st.slider('Max summary word count', 50, 500, 150)\n\n"
            "if st.button('Generate Summary'):\n"
            "    if not text_input.strip():\n"
            "        st.warning('Please enter text first.')\n"
            "    else:\n"
            "        with st.spinner('Summarizing...'):\n"
            "            try:\n"
            "                res = requests.post(\n"
            "                    'http://localhost:8000/api/app/summarizer/run',\n"
            "                    json={{'text': text_input, 'max_words': max_words}}\n"
            "                )\n"
            "                st.subheader('Summary')\n"
            "                st.write(res.json().get('summary', 'Error generating summary.'))\n"
            "            except Exception as e:\n"
            "                st.error(f'Failed to connect: {{e}}')\n"
        ),
        "swagger": {
            "paths": {
                "/summarize": {
                    "post": {
                        "summary": "Summarize text",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "text": {"type": "string"},
                                            "max_words": {"type": "integer"},
                                        },
                                        "required": ["text"],
                                    }
                                }
                            }
                        },
                        "responses": {"200": {"description": "Successful Response"}},
                    }
                }
            }
        },
    },
    "document_qa": {
        "fastapi": (
            "from fastapi import FastAPI, HTTPException\n"
            "from pydantic import BaseModel\n"
            "from openai import OpenAI\n\n"
            "app = FastAPI(title='Generated Document QA API')\n"
            "client = OpenAI(base_url='https://ollama.algoqx.tech/v1', api_key='sk-ollama-algoqx-2024')\n\n"
            "class QARequest(BaseModel):\n"
            "    document_text: str\n"
            "    question: str\n"
            "    model: str = '{model}'\n\n"
            "@app.post('/qa')\n"
            "async def document_qa(request: QARequest):\n"
            "    prompt = (\n"
            "        f'Use the document content below to answer the question.\\n\\n'\n"
            "        f'Document:\\n{{request.document_text}}\\n\\n'\n"
            "        f'Question: {{request.question}}\\n'\n"
            "        f'Answer:'\n"
            "    )\n"
            "    messages = [{{'role': 'user', 'content': prompt}}]\n"
            "    try:\n"
            "        res = client.chat.completions.create(\n"
            "            model=request.model,\n"
            "            messages=messages\n"
            "        )\n"
            "        return {{'answer': res.choices[0].message.content}}\n"
            "    except Exception as e:\n"
            "        raise HTTPException(status_code=500, detail=str(e))\n"
        ),
        "streamlit": (
            "import streamlit as st\n"
            "import requests\n\n"
            "st.title('AlgoQX Document QA')\n"
            "doc_text = st.text_area('Document Content', height=200)\n"
            "question = st.text_input('Ask a question about this document')\n\n"
            "if st.button('Ask Question'):\n"
            "    if not doc_text or not question:\n"
            "        st.warning('Please enter both document text and a question.')\n"
            "    else:\n"
            "        with st.spinner('Answering...'):\n"
            "            try:\n"
            "                res = requests.post(\n"
            "                    'http://localhost:8000/api/app/doc_qa/run',\n"
            "                    json={{'document_text': doc_text, 'question': question}}\n"
            "                )\n"
            "                st.subheader('Answer')\n"
            "                st.write(res.json().get('answer', 'Error generating answer.'))\n"
            "            except Exception as e:\n"
            "                st.error(f'Failed to connect: {{e}}')\n"
        ),
        "swagger": {
            "paths": {
                "/qa": {
                    "post": {
                        "summary": "Document QA",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "document_text": {"type": "string"},
                                            "question": {"type": "string"},
                                        },
                                        "required": ["document_text", "question"],
                                    }
                                }
                            }
                        },
                        "responses": {"200": {"description": "Successful Response"}},
                    }
                }
            }
        },
    },
    "sentiment_analyzer": {
        "fastapi": (
            "from fastapi import FastAPI, HTTPException\n"
            "from pydantic import BaseModel\n"
            "from openai import OpenAI\n\n"
            "app = FastAPI(title='Generated Sentiment Analyzer API')\n"
            "client = OpenAI(base_url='https://ollama.algoqx.tech/v1', api_key='sk-ollama-algoqx-2024')\n\n"
            "class SentimentRequest(BaseModel):\n"
            "    text: str\n"
            "    model: str = '{model}'\n\n"
            "@app.post('/sentiment')\n"
            "async def analyze_sentiment(request: SentimentRequest):\n"
            "    prompt = (\n"
            "        f'Analyze the sentiment of the following text. Respond with exactly one word: '\n"
            "        f'POSITIVE, NEGATIVE, or NEUTRAL. Do not include explanation.\\n\\n'\n"
            "        f'Text: {{request.text}}\\n'\n"
            "        f'Sentiment:'\n"
            "    )\n"
            "    messages = [{{'role': 'user', 'content': prompt}}]\n"
            "    try:\n"
            "        res = client.chat.completions.create(\n"
            "            model=request.model,\n"
            "            messages=messages\n"
            "        )\n"
            "        sentiment = res.choices[0].message.content.strip().upper()\n"
            "        return {{'sentiment': sentiment}}\n"
            "    except Exception as e:\n"
            "        raise HTTPException(status_code=500, detail=str(e))\n"
        ),
        "streamlit": (
            "import streamlit as st\n"
            "import requests\n\n"
            "st.title('AlgoQX Sentiment Analyzer')\n"
            "text_input = st.text_input('Enter text to analyze')\n\n"
            "if st.button('Analyze Sentiment'):\n"
            "    if not text_input:\n"
            "        st.warning('Please enter text first.')\n"
            "    else:\n"
            "        with st.spinner('Analyzing...'):\n"
            "            try:\n"
            "                res = requests.post(\n"
            "                    'http://localhost:8000/api/app/sentiment/run',\n"
            "                    json={{'text': text_input}}\n"
            "                )\n"
            "                sentiment = res.json().get('sentiment', 'UNKNOWN')\n"
            "                st.metric('Sentiment', sentiment)\n"
            "            except Exception as e:\n"
            "                st.error(f'Failed to connect: {{e}}')\n"
        ),
        "swagger": {
            "paths": {
                "/sentiment": {
                    "post": {
                        "summary": "Sentiment Analysis",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "text": {"type": "string"},
                                        },
                                        "required": ["text"],
                                    }
                                }
                            }
                        },
                        "responses": {"200": {"description": "Successful Response"}},
                    }
                }
            }
        },
    },
}


@router.post("/generate", response_model=AppGenerateResponse)
async def generate_application(request: AppGenerateRequest):
    """Automatically build FastAPI backend endpoints and Streamlit pages."""
    app_type = request.app_type.lower()
    if app_type not in TEMPLATES:
        raise HTTPException(status_code=400, detail=f"Unsupported app type: {request.app_type}")

    tpl = TEMPLATES[app_type]
    fastapi_code = tpl["fastapi"].format(model=request.model)
    streamlit_code = tpl["streamlit"]

    # Requirements file list
    requirements = [
        "fastapi>=0.115.0",
        "uvicorn[standard]>=0.34.0",
        "pydantic>=2.10.0",
        "openai>=1.60.0",
        "streamlit>=1.41.0",
        "requests>=2.32.0",
    ]

    return AppGenerateResponse(
        app_type=request.app_type,
        fastapi_code=fastapi_code,
        streamlit_code=streamlit_code,
        swagger_spec=tpl["swagger"],
        requirements=requirements,
    )


@router.get("/templates")
async def get_templates():
    """List available templates."""
    return {
        "templates": [
            {
                "id": "chatbot",
                "name": "SaaS Chatbot",
                "description": "Standard context-aware chatbot workspace.",
            },
            {
                "id": "summarizer",
                "name": "Text Summarizer",
                "description": "Condense long logs, articles, or transcripts.",
            },
            {
                "id": "document_qa",
                "name": "Document QA",
                "description": "Question answering over paste-in manuals.",
            },
            {
                "id": "sentiment_analyzer",
                "name": "Sentiment Analyzer",
                "description": "Classify text emotions into POSITIVE, NEGATIVE, or NEUTRAL.",
            },
        ]
    }
