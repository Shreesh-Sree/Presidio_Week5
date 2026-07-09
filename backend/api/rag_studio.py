"""AlgoQX Studio -- RAG Studio API Endpoints."""

import os
from pathlib import Path
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.settings import get_settings
from backend.database.engine import get_db
from backend.database.models import RAGDocument
from backend.models.schemas import (
    RAGUploadResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    ChunkResult,
    RAGCompareResponse,
    PromptResult,
)
from backend.rag import loaders, chunkers, vectorstore, evaluator
from backend.services import llm_service, observability_service, tokenizer_service

router = APIRouter(prefix="/rag", tags=["RAG Studio"])
settings = get_settings()


@router.post("/upload", response_model=RAGUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    chunking_strategy: str = "recursive",
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    embedding_model: str = "qwen3-embedding:8b",
    db: AsyncSession = Depends(get_db),
):
    """Upload and parse document, split into chunks, generate embeddings, and build FAISS index."""
    try:
        # Save file to upload directory
        settings.ensure_directories()
        file_path = Path(settings.upload_dir) / file.filename
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # Load document text
        doc_data = loaders.load_document(str(file_path))
        text = doc_data["text"]

        # Split document into chunks
        chunks = chunkers.chunk_text(
            text=text,
            strategy=chunking_strategy,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            metadata={"source": file.filename},
        )

        # Create FAISS Index
        index_name = file.filename
        vectorstore.create_index(
            chunks=chunks,
            index_name=index_name,
            model_name=embedding_model,
        )

        # Log document metadata to SQLite
        doc = RAGDocument(
            filename=file.filename,
            file_type=doc_data["file_type"],
            file_size=doc_data["metadata"]["file_size"],
            chunk_count=len(chunks),
            chunking_strategy=chunking_strategy,
            embedding_model=embedding_model,
            index_name=index_name,
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)

        return RAGUploadResponse(
            filename=file.filename,
            file_type=doc_data["file_type"],
            chunk_count=len(chunks),
            chunking_strategy=chunking_strategy,
            embedding_model=embedding_model,
            document_id=doc.id,
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=RAGQueryResponse)
async def query_rag(request: RAGQueryRequest, db: AsyncSession = Depends(get_db)):
    """Search vector store, build grounded prompt, generate LLM answer, and run evaluators."""
    trace_id = observability_service.generate_trace_id()
    tracer = observability_service.RequestTracer("rag_studio", trace_id)

    try:
        # Retrieve all index names/documents
        q = select(RAGDocument).order_by(RAGDocument.created_at.desc())
        res = await db.execute(q)
        docs = res.scalars().all()

        retrieved_chunks = []
        # Search all active document indices
        for doc in docs:
            chunks = vectorstore.search_index(
                query=request.query,
                index_name=doc.index_name,
                top_k=request.top_k,
                model_name=request.embedding_model,
                retriever_type=request.retriever_type,
            )
            retrieved_chunks.extend(chunks)

        # Sort combined results by similarity score (descending for Inner Product)
        retrieved_chunks.sort(key=lambda x: x["score"], reverse=True)
        retrieved_chunks = retrieved_chunks[: request.top_k]

        # Convert to schema model
        chunks_res = [
            ChunkResult(
                content=c["content"],
                score=c["score"],
                rank=i + 1,
                metadata=c["metadata"],
            )
            for i, c in enumerate(retrieved_chunks)
        ]

        # Construct context & prompt
        context = "\n\n".join([f"Source: {c.metadata.get('source', 'Unknown')}\n{c.content}" for c in chunks_res])
        rag_prompt = (
            "You are an assistant answering a query based only on the provided context.\n"
            "If the context does not contain the answer, say 'I don't know'. Do not make up facts.\n\n"
            f"Context:\n{context}\n\n"
            f"Query: {request.query}\n"
            "Answer:"
        )

        messages = [{"role": "user", "content": rag_prompt}]

        tracer.start_step("llm_generation", "rag_chat")
        result = await llm_service.chat_completion(messages=messages, model=request.model)
        tracer.end_step(output_data=result["response"])

        # Compute cost & quality evaluations
        cost = llm_service.estimate_cost(request.model, result["input_tokens"], result["output_tokens"])
        evals = evaluator.evaluate_response(
            query=request.query,
            response=result["response"],
            retrieved_chunks=[c.model_dump() for c in chunks_res],
        )

        # Log request to DB
        await observability_service.log_request(
            db=db,
            trace_id=trace_id,
            module="rag_studio",
            model=request.model,
            input_text=request.query,
            output_text=result["response"],
            input_tokens=result["input_tokens"],
            output_tokens=result["output_tokens"],
            latency_ms=result["latency_ms"],
            cost_usd=cost,
            status="success",
        )

        return RAGQueryResponse(
            query=request.query,
            answer=result["response"],
            chunks=chunks_res,
            hallucination_score=evals["hallucination_score"],
            groundedness_score=evals["groundedness_score"],
            input_tokens=result["input_tokens"],
            output_tokens=result["output_tokens"],
            latency_ms=result["latency_ms"],
            cost_usd=cost,
            trace_id=trace_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare", response_model=RAGCompareResponse)
async def compare_rag(request: RAGQueryRequest, db: AsyncSession = Depends(get_db)):
    """Compare Prompt-Only (zero-shot) vs RAG response side by side."""
    try:
        # Get Prompt-Only response
        start_time = time.perf_counter()
        prompt_only_msgs = [{"role": "user", "content": request.query}]
        p_res = await llm_service.chat_completion(messages=prompt_only_msgs, model=request.model)
        p_latency = (time.perf_counter() - start_time) * 1000
        p_cost = llm_service.estimate_cost(request.model, p_res["input_tokens"], p_res["output_tokens"])

        prompt_result = PromptResult(
            strategy="prompt_only",
            response=p_res["response"],
            input_tokens=p_res["input_tokens"],
            output_tokens=p_res["output_tokens"],
            total_tokens=p_res["total_tokens"],
            latency_ms=p_latency,
            cost_usd=p_cost,
        )

        # Get RAG response
        rag_result = await query_rag(request, db)

        # Perform comparison
        comparison = evaluator.compare_approaches(
            query=request.query,
            prompt_only_response=p_res["response"],
            rag_response=rag_result.answer,
            retrieved_chunks=[c.model_dump() for c in rag_result.chunks],
        )

        return RAGCompareResponse(
            query=request.query,
            prompt_only=prompt_result,
            rag_result=rag_result,
            comparison=comparison,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
async def list_documents(db: AsyncSession = Depends(get_db)):
    """List all uploaded documents."""
    try:
        q = select(RAGDocument).order_by(RAGDocument.created_at.desc())
        res = await db.execute(q)
        docs = res.scalars().all()
        return {
            "documents": [
                {
                    "id": d.id,
                    "filename": d.filename,
                    "file_type": d.file_type,
                    "file_size": d.file_size,
                    "chunk_count": d.chunk_count,
                    "chunking_strategy": d.chunking_strategy,
                    "embedding_model": d.embedding_model,
                    "created_at": d.created_at.isoformat(),
                }
                for d in docs
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chunks/{document_id}")
async def get_document_chunks(document_id: int, db: AsyncSession = Depends(get_db)):
    """Fetch stored chunks for a specific document."""
    try:
        q = select(RAGDocument).where(RAGDocument.id == document_id)
        res = await db.execute(q)
        doc = res.scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Load chunks from FAISS index metadata
        chunks = vectorstore._metadata_store.get(doc.index_name, [])
        return {"document_id": document_id, "filename": doc.filename, "chunks": chunks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
