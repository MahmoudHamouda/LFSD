"""
Service for interacting with Anthropic Claude API.
"""
from anthropic import AsyncAnthropic
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import os
from services.connection_service import ConnectionService
from services.uber_service import UberService
from core.config import get_settings

settings = get_settings()

class ClaudeService:
    def __init__(self, db: Session):
        self.db = db
        self.connection_service = ConnectionService(db)
        self.uber_service = UberService()
        
        # Initialize Claude client
        api_key = os.getenv("ANTHROPIC_API_KEY") or settings.ANTHROPIC_API_KEY if hasattr(settings, 'ANTHROPIC_API_KEY') else None
        if api_key:
            self.client = AsyncAnthropic(api_key=api_key)
        else:
            self.client = None

    def get_connections(self) -> List[Dict[str, str]]:
        """
        Get a list of connected services for the current user.
        
        Returns:
            List of dictionaries containing provider names and status.
        """
        user_id = "user-123" 
        connections = self.connection_service.get_connections(user_id)
        return [{"provider": c.provider, "status": c.status} for c in connections]

    async def get_ride_estimates(self, start_address: str, end_address: str) -> Dict[str, Any]:
        """
        Get ride estimates from connected providers (e.g., Uber).
        
        Args:
            start_address: The starting location address or description.
            end_address: The destination address or description.
            
        Returns:
            Dictionary containing price estimates from connected providers.
        """
        # Using default Dubai coordinates for demo
        start_lat, start_lng = 25.2048, 55.2708
        end_lat, end_lng = 25.1972, 55.2744
        
        estimates = {}
        
        # Check Uber connection
        user_id = "user-123"
        uber_conn = self.connection_service.get_connection(user_id, "uber")
        
        if uber_conn and uber_conn.status == "connected":
            uber_data = await self.uber_service.get_price_estimates(
                start_latitude=start_lat,
                start_longitude=start_lng,
                end_latitude=end_lat,
                end_longitude=end_lng
            )
            estimates["uber"] = uber_data
            
        return estimates

    async def generate_response(self, history: List[Dict[str, str]], context: Dict[str, Any]) -> str:
        """
        Generate a response using Claude based on chat history and context.
        """
        import logging
        
        # Configure logging
        logger = logging.getLogger("claude_service")
        if not logger.handlers:
            fh = logging.FileHandler("debug_claude.log")
            fh.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            fh.setFormatter(formatter)
            logger.addHandler(fh)
            
        logger.info("generate_response called")

        if not self.client:
            logger.error("ANTHROPIC_API_KEY not set")
            return "I'm sorry, but I'm not fully configured yet. Please add a valid `ANTHROPIC_API_KEY` to the settings."

        try:
            # Build system prompt
            system_prompt = """You are FinWell, a helpful AI assistant for financial and lifestyle management.
You can help users with their finances, ride bookings (Uber), and general questions.
Be friendly, concise, and helpful."""
            
            # Convert history to Claude format
            messages = []
            for msg in history:
                role = "user" if msg["role"] == "user" else "assistant"
                messages.append({
                    "role": role,
                    "content": msg["content"]
                })
            
            logger.info(f"Sending request to Claude (messages: {len(messages)})")
            
            # Call Claude API
            response = await self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=system_prompt,
                messages=messages
            )
            
            logger.info("Claude response received")
            
            # Extract text from response
            if response.content and len(response.content) > 0:
                return response.content[0].text
            else:
                return "I received your message but couldn't generate a response."
            
        except Exception as e:
            logger.error(f"Claude API Error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return "I'm having trouble connecting to my brain right now. Please try again later."
