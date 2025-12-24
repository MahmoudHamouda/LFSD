import sys
from unittest.mock import MagicMock

# Mock dependencies BEFORE importing the service
sys.modules["fitz"] = MagicMock()
sys.modules["pdf2image"] = MagicMock()
sys.modules["pytesseract"] = MagicMock()
sys.modules["PIL"] = MagicMock()
sys.modules["google.generativeai"] = MagicMock()

import pytest
from unittest.mock import patch, AsyncMock
from datetime import date
from services.statement_processing_service import StatementService, ParsedStatement, StatementMetadata, TransactionModel
from models.models import Statement, Transaction

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def statement_service(mock_db):
    return StatementService(mock_db)

@pytest.mark.asyncio
async def test_process_statement_success(statement_service, mock_db):
    # Mock PDF Processor
    statement_service.pdf_processor.extract_text = MagicMock(return_value="Mock PDF Text")
    
    # Mock Gemini Parser
    mock_parsed_data = ParsedStatement(
        metadata=StatementMetadata(
            bank_name="Test Bank",
            period_start=date(2023, 1, 1),
            period_end=date(2023, 1, 31),
            total_credits=1000.0,
            total_debits=500.0
        ),
        transactions=[
            TransactionModel(date=date(2023, 1, 15), description="Test Tx", amount=-50.0)
        ]
    )
    statement_service.gemini_parser.parse_text = AsyncMock(return_value=mock_parsed_data)
    
    # Mock DB objects
    mock_statement = MagicMock()
    mock_statement.id = "stmt_123"
    
    # Setup db.add to simulate setting ID
    def side_effect(obj):
        if isinstance(obj, Statement):
            obj.id = "stmt_123"
    mock_db.add.side_effect = side_effect
    
    # Execute
    result = await statement_service.process_statement("user_123", b"fake_pdf_content", "test.pdf")
    
    # Verify
    assert result["status"] == "success"
    assert result["statement_id"] == "stmt_123"
    assert result["data"]["metadata"]["bank_name"] == "Test Bank"
    
    # Verify DB calls
    mock_db.add.assert_called_once() # Statement
    mock_db.add_all.assert_called_once() # Transactions
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_process_statement_pdf_error(statement_service, mock_db):
    # Mock PDF Processor to fail
    statement_service.pdf_processor.extract_text = MagicMock(side_effect=Exception("PDF Error"))
    
    # Execute
    result = await statement_service.process_statement("user_123", b"fake_pdf_content", "test.pdf")
    
    # Verify
    assert result["status"] == "error"
    assert "PDF Error" in result["error"]
    mock_db.rollback.assert_called_once()

@pytest.mark.asyncio
async def test_process_statement_gemini_error(statement_service, mock_db):
    # Mock PDF Processor
    statement_service.pdf_processor.extract_text = MagicMock(return_value="Mock PDF Text")
    
    # Mock Gemini Parser to fail
    statement_service.gemini_parser.parse_text = AsyncMock(side_effect=Exception("Gemini Error"))
    
    # Execute
    result = await statement_service.process_statement("user_123", b"fake_pdf_content", "test.pdf")
    
    # Verify
    assert result["status"] == "error"
    assert "Gemini Error" in result["error"]
    mock_db.rollback.assert_called_once()

if __name__ == "__main__":
    import asyncio
    
    async def run_tests():
        print("Running tests...")
        
        print("Test 1: Success case")
        mock_db_1 = MagicMock()
        service_1 = StatementService(mock_db_1)
        await test_process_statement_success(service_1, mock_db_1)
        print("Test 1 Passed")
        
        print("Test 2: PDF Error")
        mock_db_2 = MagicMock()
        service_2 = StatementService(mock_db_2)
        await test_process_statement_pdf_error(service_2, mock_db_2)
        print("Test 2 Passed")
        
        print("Test 3: Gemini Error")
        mock_db_3 = MagicMock()
        service_3 = StatementService(mock_db_3)
        await test_process_statement_gemini_error(service_3, mock_db_3)
        print("Test 3 Passed")
        
        print("All tests passed!")

    asyncio.run(run_tests())
