import os
import json
import asyncio
import logging
from datetime import date, datetime
from typing import List, Optional, Dict, Any, Union
from io import BytesIO

import fitz  # PyMuPDF
from PIL import Image
import pytesseract
from pdf2image import convert_from_bytes
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
import google.generativeai as genai

from models.models import Statement, FinancialTransaction, User

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# 1. Pydantic Models for Validation
# ============================================================================

class TransactionModel(BaseModel):
    date: date
    description: str
    amount: float
    category: Optional[str] = "Uncategorized"

    @validator('date', pre=True)
    def parse_date(cls, v):
        if isinstance(v, str):
            return datetime.strptime(v, '%Y-%m-%d').date()
        return v

class StatementMetadata(BaseModel):
    bank_name: Optional[str] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    total_credits: Optional[float] = 0.0
    total_debits: Optional[float] = 0.0
    account_number: Optional[str] = None

    @validator('period_start', 'period_end', pre=True)
    def parse_date(cls, v):
        if isinstance(v, str):
            try:
                return datetime.strptime(v, '%Y-%m-%d').date()
            except ValueError:
                return None
        return v

class ParsedStatement(BaseModel):
    metadata: StatementMetadata
    transactions: List[TransactionModel]

# ... (PDFProcessor omitted for brevity) ...

# ============================================================================
# 3. Gemini LLM Parsing
# ============================================================================

from core.config import get_settings

class GeminiParser:
    def __init__(self):
        settings = get_settings()
        api_key = settings.GEMINI_API_KEY
        
        if not api_key:
            logger.warning("GEMINI_API_KEY not found in settings. Parsing will fail.")
            
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    async def parse_pdf(self, pdf_bytes: bytes) -> ParsedStatement:
        """
        Sends PDF bytes directly to Gemini (Multimodal) to parse into structured JSON.
        This replicates the behavior of the Gemini UI.
        """
        prompt = """
        You are an expert financial analyst. Acknowledge that you are analyzing a bank statement PDF.
        
        TASK:
        1. Extract ALL transactions into a structured JSON format.
        2. **INTELLIGENTLY CATEGORIZE** each transaction based on the description.
           - Examples: "Starbucks" -> "Food & Drink", "Uber" -> "Transport", "Netflix" -> "Entertainment".
           - Use standard personal finance categories: Housing, Food & Drink, Transport, Utilities, Shopping, Entertainment, Health, Income, Transfers, Fees.

        Output ONLY valid JSON matching exactly this schema:

        {
          "metadata": {
            "bank_name": "string",
            "account_number": "string",
            "period_start": "YYYY-MM-DD",
            "period_end": "YYYY-MM-DD",
            "total_credits": number,
            "total_debits": number
          },
          "transactions": [
            {
              "date": "YYYY-MM-DD",
              "description": "string",
              "amount": number,
              "category": "string"
            }
          ]
        }

        Rules:
        - Dates must be ISO format YYYY-MM-DD.
        - Amounts: positive for credits, negative for debits.
        - Do not include currency symbols.
        - If a value does not exist, set it to null.
        - Output ONLY JSON. No commentary.
        """
        
        # Try available models based on account access
        # Prioritize 2.5-flash as it seems most reliable with current quotas
        models_to_try = [
            'models/gemini-2.5-flash',
            'models/gemini-2.0-flash', 
            'models/gemini-2.0-flash-lite', 
            'models/gemini-2.0-flash-exp'
        ]
        
        errors = []
        for model_name in models_to_try:
            try:
                logger.info(f"Attempting native PDF parse with model: {model_name}")
                model = genai.GenerativeModel(model_name)
                
                # Create the content part with PDF data
                pdf_part = {
                    "mime_type": "application/pdf",
                    "data": pdf_bytes
                }
                
                # Run in thread with INCREASED timeout
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        model.generate_content,
                        [prompt, pdf_part], # Pass prompt AND pdf part
                        generation_config={"response_mime_type": "application/json"}
                    ),
                    timeout=240.0 # Increased to 4 minutes per user request
                )
                
                response_text = response.text
                
                # --- DEBUG LOGGING ---
                logger.debug(f"Gemini Response ({model_name}): {response_text[:500]}...")
                # -----------------------------

                # Clean up potential markdown code blocks
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                
                try:
                    data = json.loads(response_text)
                    
                    # Handle case where LLM returns a list instead of a dict
                    if isinstance(data, list):
                        if len(data) == 1 and isinstance(data[0], dict):
                             data = data[0]
                        else:
                             # Fallback: if it looks like a list of transactions, try to wrap it
                             if all(isinstance(x, dict) and "amount" in x for x in data):
                                 logger.warning("Gemini returned list of transactions without metadata. wrapping.")
                                 data = {"metadata": {}, "transactions": data}
                             else:
                                 raise ValueError(f"Expected JSON object, got list: {data[:100]}")

                except json.JSONDecodeError as json_err:
                    raise ValueError(f"Invalid JSON returned: {json_err}. Content snippet: {response_text[:100]}...")
                
                # Validate with Pydantic
                return ParsedStatement(**data)

                msg = f"Model {model_name} timed out."
                logger.warning(msg)
                errors.append(msg)
                continue # Try next model
            except Exception as e:
                msg = f"Model {model_name} failed: {e}"
                logger.error(msg)
                errors.append(msg)
                continue # Try next model
        
        # If all multimodal attempts failed, try text-based fallback
        logger.warning("All multimodal attempts failed. Falling back to text-based parsing.")
        return await self.parse_text_fallback(pdf_bytes, errors)

    async def parse_text_fallback(self, pdf_bytes: bytes, previous_errors: list) -> ParsedStatement:
        """
        Fallback: Extract text from PDF (using PyMuPDF/OCR) and send text to Gemini.
        This is often lighter and avoids some quota/timeout issues with heavy PDF processing.
        """
        try:
            # 1. Extract Text
            # We can use the PDFProcessor class defined in this file. 
            # Since it's a static method service, we can call it directly.
            text_content = PDFProcessor.extract_text(pdf_bytes)
            
            if len(text_content) < 50:
                 raise ValueError("Extracted text is too short for parsing.")

            prompt = """
            You are a financial statement parser.
            Analyze the following bank statement text transactions.
            Extract ALL transactions into a structured JSON format.
            
            TEXT CONTENT:
            """ + text_content[:50000] + """ <TRUNCATED IF TOO LONG>
            
            Output ONLY valid JSON matching exactly this schema:
            {
              "metadata": {
                "bank_name": "string",
                "account_number": "string",
                "period_start": "YYYY-MM-DD",
                "period_end": "YYYY-MM-DD",
                "total_credits": number,
                "total_debits": number
              },
              "transactions": [
                {
                  "date": "YYYY-MM-DD",
                  "description": "string",
                  "amount": number
                }
              ]
            }

            Rules:
            - Dates must be ISO format YYYY-MM-DD.
            - Amounts: positive for credits, negative for debits.
            - Do not include currency symbols.
            - If a value does not exist, set it to null.
            - Output ONLY JSON.
            """

            # Try the most lightweight model first
            fallback_models = ['models/gemini-2.0-flash', 'models/gemini-2.0-flash-lite']
            
            for model_name in fallback_models:
                try:
                    model = genai.GenerativeModel(model_name)
                    response = await asyncio.wait_for(
                        asyncio.to_thread(
                            model.generate_content,
                            prompt,
                            generation_config={"response_mime_type": "application/json"}
                        ),
                        timeout=60.0
                    )
                    
                    data = json.loads(response.text)
                    return ParsedStatement(**data)
                except Exception as e:
                    logger.warning(f"Text fallback model {model_name} failed: {e}")
                    continue

            raise ValueError("All text fallback models failed.")

        except Exception as e:
            all_errors = "; ".join(previous_errors) + f"; Fallback error: {str(e)}"
            raise ValueError(f"Processing failed completely. Details: {all_errors}")

# ============================================================================
# 4. Statement Service (Orchestrator)
# ============================================================================

class StatementService:
    def __init__(self, db: Session):
        self.db = db
        self.pdf_processor = PDFProcessor()
        self.gemini_parser = GeminiParser()

    async def process_statement(self, user_id: str, file_content: bytes, filename: str, persist: bool = True) -> Dict[str, Any]:
        """
        Full pipeline: PDF -> Text -> Gemini -> JSON -> DB
        """
        start_time = datetime.utcnow()
        logger.info(f"Processing statement: {filename} for user {user_id} (Persist: {persist})")

        try:
            # 1. Parse PDF directly with Gemini (Native Multimodal)
            # We skip local OCR extraction and send the PDF bytes directly.
            parsed_data: ParsedStatement = await self.gemini_parser.parse_pdf(file_content)

            statement_id = None

            if persist and user_id:
                # 2. Clear existing transactions for default_user to ensure fresh data
                if user_id == "default_user":
                    logger.info("Clearing existing transactions for default_user")
                    self.db.query(FinancialTransaction).filter(FinancialTransaction.user_id == user_id).delete()
                    self.db.query(Statement).filter(Statement.user_id == user_id).delete()
                    self.db.commit()

                # 3. Insert into Database
                # Create Statement
                statement = Statement(
                    user_id=user_id,
                    bank_name=parsed_data.metadata.bank_name,
                    period_start=parsed_data.metadata.period_start,
                    period_end=parsed_data.metadata.period_end,
                    total_credits=parsed_data.metadata.total_credits,
                    total_debits=parsed_data.metadata.total_debits,
                    uploaded_at=datetime.utcnow()
                )
                self.db.add(statement)
                self.db.flush() # Get ID
                statement_id = statement.id

                # Create Transactions
                import hashlib
                transactions = []
                duplicates_count = 0
                
                # Fetch existing keys for this user to minimize DB hits (or check one by one)
                # For robustness, checking one by one or doing a bulk check is better.
                # Let's do a bulk check if list is small, or just try/except integrity error if we trust DB constraints.
                # But we want to "Prevent re-insertion" gracefully.
                
                for tx in parsed_data.transactions:
                    # Deterministic Key: Date + Amount + Description (slugified)
                    raw_str = f"{tx.date.isoformat()}_{tx.amount}_{tx.description.strip().lower()}"
                    dedup_key = hashlib.sha256(raw_str.encode()).hexdigest()
                    
                    # Check existence
                    exists = self.db.query(FinancialTransaction).filter(
                        FinancialTransaction.deduplication_key == dedup_key,
                        FinancialTransaction.user_id == user_id
                    ).first()
                    
                    if exists:
                        duplicates_count += 1
                        continue

                    transaction = FinancialTransaction(
                        user_id=user_id,
                        statement_id=statement.id,
                        transaction_date=tx.date,
                        description=tx.description,
                        amount=tx.amount,
                        currency_code="USD",
                        category_primary=tx.category or "Uncategorized",
                        deduplication_key=dedup_key
                    )
                    transactions.append(transaction)
                
                if transactions:
                    self.db.add_all(transactions)
                    self.db.commit()
                    logger.info(f"Imported {len(transactions)} new transactions. Skipped {duplicates_count} duplicates.")
                else:
                    logger.info(f"No new transactions found. Skipped {duplicates_count} duplicates.")
            else:
                logger.info("Persist=False: Skipping DB insertion.")


            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Statement processed successfully in {processing_time}s")

            return {
                "status": "success",
                "statement_id": statement_id,
                "data": parsed_data.dict(),
                "processing_time": processing_time
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to process statement: {e}")
            
            # Map technical errors to user-friendly messages
            error_str = str(e)
            user_friendly_error = "An unexpected error occurred while processing your statement."
            
            if "429" in error_str or "quota" in error_str.lower():
                user_friendly_error = "We're experiencing high demand. Please try again in a few minutes."
            elif "timed out" in error_str.lower():
                user_friendly_error = "The file processing timed out. Please try a smaller file or try again."
            elif "image_to_string" in error_str or "ocr" in error_str.lower():
                user_friendly_error = "Could not read text from this PDF. Please ensure it's a clear, readable bank statement."
            elif "pdf" in error_str.lower() and "cannot open" in error_str.lower():
                user_friendly_error = "The PDF file appears to be corrupted or password protected."
            elif "expecting value" in error_str.lower() or "json" in error_str.lower():
                user_friendly_error = "We couldn't understand the data format. Please try another statement or enter data manually."
            
            return {
                "status": "error",
                "error": user_friendly_error,
                "technical_details": error_str # Keep raw error for debugging if needed
            }
