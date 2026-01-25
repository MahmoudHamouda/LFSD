"""
History API Routes

Endpoints for unified history timeline aggregating all user activities.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
import json
from pydantic import BaseModel
from models.database import get_db
from models.models import FinancialTransaction, VivLog, HealthDailySummary, User
from core.authentication import get_current_user

router = APIRouter(prefix="/api/history", tags=["history"])

# Pydantic Models
# ============================================================================

class HistoryFilters(BaseModel):
    types: List[str] = []  # ["transaction", "viv_log", "health"]
    dateRange: Optional[dict] = None  # {start: str, end: str}
    importance: Optional[str] = None  # "high", "medium", "low", "all"
    category: Optional[str] = None  # "financial", "time", "health", "all"
    searchQuery: Optional[str] = None

class HistoryRequest(BaseModel):
    filters: HistoryFilters
    limit: int = 50
    cursor: Optional[str] = None

class HistoryItem(BaseModel):
    id: str
    type: str
    title: str
    subtitle: Optional[str] = None
    amount: Optional[float] = None
    metricValue: Optional[float] = None
    timestamp: str
    tags: List[str] = []
    sourceService: str
    icon: Optional[str] = None
    importance: Optional[str] = None
    raw: dict

class HistoryDayGroup(BaseModel):
    date: str
    label: str
    items: List[HistoryItem]

class HistoryResponse(BaseModel):
    groups: List[HistoryDayGroup]
    totalCount: int
    hasMore: bool
    nextCursor: Optional[str] = None

class ConversationRequest(BaseModel):
    messages: List[dict]
    context: Optional[dict] = None
    conversation_id: Optional[str] = None

# ============================================================================
# Helper Functions
# ============================================================================

def get_date_label(date: datetime) -> str:
    """Get human-readable label for a date."""
    today = datetime.now().date()
    item_date = date.date()
    
    if item_date == today:
        return "Today"
    elif item_date == today - timedelta(days=1):
        return "Yesterday"
    elif item_date >= today - timedelta(days=7):
        return "This Week"
    elif item_date >= today - timedelta(days=30):
        return "This Month"
    else:
        return item_date.strftime("%B %Y")

def group_by_date(items: List[HistoryItem]) -> List[HistoryDayGroup]:
    """Group history items by date."""
    groups = {}
    
    for item in items:
        item_date = datetime.fromisoformat(item.timestamp).date()
        date_key = item_date.isoformat()
        
        if date_key not in groups:
            groups[date_key] = {
                "date": date_key,
                "label": get_date_label(datetime.fromisoformat(item.timestamp)),
                "items": []
            }
        
        groups[date_key]["items"].append(item)
    
    # Sort groups by date (newest first)
    sorted_groups = sorted(groups.values(), key=lambda x: x["date"], reverse=True)
    
    return [HistoryDayGroup(**group) for group in sorted_groups]

# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/unified")
async def get_unified_history(
    request: HistoryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get unified history timeline with all user activities.
    
    Aggregates:
    - Transactions
    - Viv Logs (AI decisions)
    - Health Summaries
    """
    user_id = current_user.id
    all_items = []
    
    # Parse date range
    start_date = None
    end_date = None
    if request.filters.dateRange:
        if request.filters.dateRange.get("start"):
            start_date = datetime.fromisoformat(request.filters.dateRange.get("start"))
        if request.filters.dateRange.get("end"):
            end_date = datetime.fromisoformat(request.filters.dateRange.get("end"))
    
    # Fetch transactions
    if not request.filters.types or "transaction" in request.filters.types:
        transactions = db.query(FinancialTransaction).filter(
            FinancialTransaction.user_id == user_id
        )
        if start_date and end_date:
            transactions = transactions.filter(
                FinancialTransaction.transaction_date >= start_date,
                FinancialTransaction.transaction_date <= end_date
            )
        
        for txn in transactions.limit(request.limit).all():
            all_items.append(HistoryItem(
                id=txn.id,
                type="transaction",
                title=txn.merchant_name or "Transaction",
                subtitle=txn.category_primary,
                amount=txn.amount,
                timestamp=txn.transaction_date.isoformat(),
                tags=[txn.category_primary] if txn.category_primary else [],
                sourceService="financials",
                icon="Money",
                importance="medium",
                raw={
                    "id": txn.id,
                    "amount": txn.amount,
                    "category": txn.category_primary,
                    "merchant": txn.merchant_name
                }
            ))
    
    # Fetch Viv Logs
    if not request.filters.types or "viv_log" in request.filters.types:
        logs = db.query(VivLog).filter(
            VivLog.user_id == user_id
        )
        if start_date and end_date:
            logs = logs.filter(
                VivLog.timestamp >= start_date,
                VivLog.timestamp <= end_date
            )
        
        for log in logs.limit(request.limit).all():
            all_items.append(HistoryItem(
                id=log.id,
                type="viv_log",
                title=log.user_intent or "Viv Activity",
                subtitle=log.decision_logic[:50] + "..." if log.decision_logic else "AI Decision",
                timestamp=log.timestamp.isoformat(),
                tags=["ai", "viv"],
                sourceService="viv",
                icon="Robot",
                importance="low",
                raw={
                    "id": log.id,
                    "intent": log.user_intent,
                    "logic": log.decision_logic
                }
            ))
    
    # Fetch Health Summaries
    if not request.filters.types or "health" in request.filters.types:
        summaries = db.query(HealthDailySummary).filter(
            HealthDailySummary.user_id == user_id
        )
        if start_date and end_date:
            # Date comparison (HealthDailySummary uses Date, not DateTime)
            summaries = summaries.filter(
                HealthDailySummary.date >= start_date.date(),
                HealthDailySummary.date <= end_date.date()
            )
        
        for summary in summaries.limit(request.limit).all():
            # Create a timestamp from the date (noon)
            ts = datetime.combine(summary.date, datetime.min.time()) + timedelta(hours=12)
            
            all_items.append(HistoryItem(
                id=str(summary.id),
                type="health",
                title="Daily Health Summary",
                subtitle=f"Sleep: {summary.sleep_quality_score or 0}% | Steps: {summary.steps_count or 0}",
                metricValue=float(summary.sleep_quality_score or 0),
                timestamp=ts.isoformat(),
                tags=["health", "summary"],
                sourceService="health",
                icon="Health",
                importance="medium",
                raw={
                    "id": str(summary.id),
                    "sleep": summary.sleep_quality_score,
                    "steps": summary.steps_count
                }
            ))
    
    # Sort all items by timestamp (newest first)
    all_items.sort(key=lambda x: x.timestamp, reverse=True)
    
    # Apply search filter
    if request.filters.searchQuery:
        query = request.filters.searchQuery.lower()
        all_items = [
            item for item in all_items
            if query in item.title.lower() or (item.subtitle and query in item.subtitle.lower())
        ]
    
    # Group by date
    groups = group_by_date(all_items[:request.limit])
    
    return HistoryResponse(
        groups=groups,
        totalCount=len(all_items),
        hasMore=len(all_items) > request.limit,
        nextCursor=None
    )

@router.post("/generate")
async def generate_chat_response(
    request: ConversationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a chat response based on conversation history.
    Persists all interactions to the database.
    """
    import uuid
    from models.models import DBConversation, DBMessage
    
    # 1. Manage Conversation Context
    conversation_id = request.conversation_id
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        # Create new conversation
        title = "New Chat"
        if request.messages and len(request.messages) > 0:
            first_content = request.messages[0].get("content")
            if first_content:
                title = str(first_content)[:30]
        
        conversation = DBConversation(
            id=conversation_id,
            user_id=current_user.id,
            title=title,
            date=datetime.utcnow()
        )
        db.add(conversation)
        db.commit()
    else:
        # Verify exists or create if missing (sync issue)
        conversation = db.query(DBConversation).filter(DBConversation.id == conversation_id).first()
        if not conversation:
             conversation = DBConversation(
                id=conversation_id,
                user_id=current_user.id,
                title="New Chat",
                date=datetime.utcnow()
            )
             db.add(conversation)
             db.commit()

    # 2. Persist User Messages (Active Turn)
    # We assume reasonable frontend behavior sending the whole history or just new ones.
    # For now, let's assume we persist the LAST user message if it's new, or all if we treat this as a sync.
    # BUT, to be safe and avoid duplicates, we check IDs if provided, else we generate.
    # The request.messages usually contains the FULL history or the NEW prompt? 
    # Standard OpenAI format is FULL history.
    # We should find the LAST User message and persist it if not exists. 
    # OR better: The "Prompt" is usually the last message.
    
    last_user_msg = None
    if request.messages and request.messages[-1].get('role') == 'user':
        last_user_msg = request.messages[-1]
    
    if last_user_msg:
         # Check by content hash or simplistic "latest" check? 
         # Best: Always insert current turn.
         user_msg_id = str(uuid.uuid4())
         db_msg = DBMessage(
             id=user_msg_id,
             conversation_id=conversation_id,
             user_id=current_user.id,
             role="user",
             content=last_user_msg.get('content', ''),
             date=datetime.utcnow()
         )
         db.add(db_msg)
         db.commit()

    # 3. Call GeminiService
    from services.gemini_service import GeminiService
    service = GeminiService(db)
    
    # Format history for Gemini
    history = []
    for msg in request.messages:
        history.append({
            "role": "user" if msg.get('role') == 'user' else "model",
            "content": msg.get('content', '')
        })
    
    response_data = {}
    try:
        # Pass user_id in context for GeminiService usage tracking
        gen_context = (request.context or {}).copy()
        gen_context['user_id'] = current_user.id
        
        response_json_str = await service.generate_response(history, gen_context)
        response_data = json.loads(response_json_str)
        content = response_data.get('text', '')
        structured_data = response_data.get('data')
    except Exception as e:
        print(f"Gemini Error: {e}")
        content = "I'm having trouble thinking right now."
        structured_data = None

    # 4. Persist AI Response
    ai_msg_id = str(uuid.uuid4())
    usage = response_data.get('usage', {})
    
    db_response = DBMessage(
        id=ai_msg_id,
        conversation_id=conversation_id,
        user_id=current_user.id,
        role="assistant",
        content=content,
        date=datetime.utcnow(),
        input_tokens=usage.get('input_tokens', 0),
        output_tokens=usage.get('output_tokens', 0),
        model_used=getattr(service, 'model_name', 'gemini-1.5-flash')
    )
    db.add(db_response)
    
    # 5. Emit Event
    from models.models import DBActivity
    activity = DBActivity(
        user_id=current_user.id,
        type="GEMINI_USAGE_RECORDED",
        description=f"AI Interaction: {usage.get('input_tokens', 0) + usage.get('output_tokens', 0)} tokens",
        date=datetime.utcnow(),
        metadata_json=json.dumps({
            "conversation_id": conversation_id,
            "tokens": usage.get('input_tokens', 0) + usage.get('output_tokens', 0),
            "model": getattr(service, 'model_name', 'gemini-1.5-flash')
        })
    )
    db.add(activity)
    
    db.commit()
    
    return {
        "choices": [
            {
                "messages": [
                    {
                        "id": ai_msg_id,
                        "role": "assistant",
                        "content": content,
                        "date": datetime.utcnow().isoformat(),
                        "data": structured_data
                    }
                ]
            }
        ],
        "conversation_id": conversation_id 
    }
