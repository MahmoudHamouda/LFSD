from fastapi import APIRouter, Depends, HTTPException, Body, Request, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from models.database import get_db
from models.models import OnboardingSession, Statement, FinancialTransaction
from pydantic import BaseModel
import json
import base64
import asyncio
import traceback
from datetime import datetime, date
from services.statement_processing_service import StatementService
from typing import List, Optional

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

class OnboardingUploadRequest(BaseModel):
    filename: str
    content_base64: str

@router.post("/parse-statement", summary="Parse a bank statement PDF")
async def parse_statement(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Parses a bank statement PDF and returns structured data.
    This is the microservice endpoint requested.
    """
    try:
        contents = await file.read()
        service = StatementService(db)
        
        # We pass None as user_id for anonymous/onboarding uploads
        result = await service.process_statement(
            user_id=None, 
            file_content=contents, 
            filename=file.filename
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["error"])
            
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-statement")
async def upload_statement(request: Request, db: Session = Depends(get_db)):
    """
    Upload one or more bank statements.
    Refactored to use StatementService while maintaining frontend compatibility.
    """
    try:
        print(f"DEBUG: HEADERS: {request.headers}")
        try:
            data = await request.json()
            print("DEBUG: JSON parsed successfully")
            print(f"DEBUG: Received payload keys: {list(data.keys())}")
        except Exception as json_error:
            print(f"DEBUG: JSON parse failed: {json_error}")
            raise HTTPException(status_code=400, detail="Invalid JSON payload")

        # Support both single file and multiple files
        files_data = data.get("files", [])
        if not files_data:
            # Backward compatibility: single file
            files_data = [{"filename": data.get("filename"), "content": data.get("content_base64")}]
        
        results = []
        service = StatementService(db)
        
        for file_data in files_data:
            filename = file_data.get("filename")
            file_content_b64 = file_data.get("content")
            
            if not filename or not file_content_b64:
                results.append({
                    "filename": filename or "unknown",
                    "status": "error",
                    "error": "Missing filename or content"
                })
                continue
            
            try:
                # Handle potential data URI header
                content_str = file_content_b64
                if "," in content_str:
                    content_str = content_str.split(",")[1]
                
                # Decode base64
                contents = base64.b64decode(content_str)
                
                # Process with new service
                # We pass "default_user" for anonymous uploads in onboarding context
                # Governance Fix: Do NOT persist "default_user" data to core tables.
                # Data will be stored in OnboardingSession.data_json only.
                process_result = await service.process_statement(
                    user_id="default_user",
                    file_content=contents,
                    filename=filename,
                    persist=False 
                )
                
                if process_result["status"] == "error":
                    results.append({
                        "filename": filename,
                        "status": "error",
                        "error": process_result["error"]
                    })
                    continue
                
                # Map to frontend expected format
                parsed_data = process_result["data"]
                metadata = parsed_data["metadata"]
                transactions = parsed_data["transactions"]
                
                # Convert Pydantic models to dicts for JSON serialization
                transactions_dict = [t.dict() if hasattr(t, 'dict') else t for t in transactions]
                metadata_dict = metadata.dict() if hasattr(metadata, 'dict') else metadata
                
                # Helper to serialize dates
                def serialize_dates(obj):
                    if isinstance(obj, (date, datetime)):
                        return obj.isoformat()
                    return obj

                # Serialize dates in metadata
                for k, v in metadata_dict.items():
                    metadata_dict[k] = serialize_dates(v)
                    
                # Serialize dates in transactions
                for tx in transactions_dict:
                    for k, v in tx.items():
                        tx[k] = serialize_dates(v)
                
                # Add filename to metadata as expected by frontend
                metadata_dict["filename"] = filename
                
                # Create session for backward compatibility
                session_data = {
                    "transactions": transactions_dict,
                    "filename": filename,
                    "metadata": metadata_dict,
                    "statement_id": process_result["statement_id"]
                }
                
                new_session = OnboardingSession(data_json=session_data)
                db.add(new_session)
                db.commit()
                db.refresh(new_session)
                
                results.append({
                    "filename": filename,
                    "status": "success",
                    "session_id": str(new_session.id),
                    "statement_id": process_result["statement_id"],
                    "transaction_count": len(transactions),
                    "preview": transactions_dict[:5],
                    "metadata": metadata_dict
                })
                
            except Exception as e:
                print(f"DEBUG: Error processing {filename}: {e}")
                results.append({
                    "filename": filename,
                    "status": "error",
                    "error": str(e)
                })
        
        # Return results for all files
        return {
            "files": results,
            "total_files": len(results),
            "successful": len([r for r in results if r["status"] == "success"]),
            "failed": len([r for r in results if r["status"] == "error"])
        }

    except Exception as e:
        error_msg = f"CRITICAL UPLOAD ERROR: {str(e)}\n{traceback.format_exc()}"
        print(f"DEBUG: Unexpected error: {e}")
        try:
            with open("upload_error.log", "w") as f:
                f.write(error_msg)
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Server processing failed: {str(e)}")
@router.post("/upload-whoop")
async def upload_whoop(request: Request, db: Session = Depends(get_db)):
    """
    Mock endpoint for Whoop report upload.
    """
    try:
        data = await request.json()
        files_data = data.get("files", [])
        
        results = []
        for file_data in files_data:
            filename = file_data.get("filename")
            # Mock processing
            results.append({
                "filename": filename,
                "status": "success",
                "session_id": "mock_whoop_session",
                "transaction_count": 0, # Not applicable really, but keeps frontend happy
                "message": "Whoop report analyzed successfully"
            })
            
        return {
            "files": results,
            "total_files": len(results),
            "successful": len(results),
            "failed": 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
