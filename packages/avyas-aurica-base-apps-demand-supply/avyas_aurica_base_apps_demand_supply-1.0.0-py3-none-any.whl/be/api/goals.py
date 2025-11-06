"""
Goals API - Manage goal-based conversations between DTs
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import json
from pathlib import Path

router = APIRouter()

DATA_DIR = Path("/Users/amit/aurica/code/data/demand-supply")
GOALS_FILE = DATA_DIR / "goals.json"
CONVERSATIONS_DIR = DATA_DIR / "conversations"


class GoalCreate(BaseModel):
    title: str
    description: str
    other_dt_id: str  # The other DT in this conversation
    demand_id: Optional[str] = None
    supply_id: Optional[str] = None
    goal_type: str = "negotiation"  # negotiation, collaboration, inquiry
    metadata: Optional[dict] = {}


class Message(BaseModel):
    content: str
    message_type: Optional[str] = "text"  # text, data, proposal, acceptance, rejection
    metadata: Optional[dict] = {}


class ConversationData(BaseModel):
    data: dict  # Flexible data structure for conversation-specific information


def ensure_data_dir():
    """Ensure data directory and files exist"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)
    if not GOALS_FILE.exists():
        GOALS_FILE.write_text("[]")


def load_goals():
    """Load goals from file"""
    ensure_data_dir()
    return json.loads(GOALS_FILE.read_text())


def save_goals(goals):
    """Save goals to file"""
    ensure_data_dir()
    GOALS_FILE.write_text(json.dumps(goals, indent=2))


def load_conversation(goal_id: str):
    """Load conversation data for a goal"""
    ensure_data_dir()
    conv_file = CONVERSATIONS_DIR / f"{goal_id}.json"
    if not conv_file.exists():
        default_data = {
            "goal_id": goal_id,
            "messages": [],
            "shared_data": {},
            "created_at": datetime.now().isoformat()
        }
        conv_file.write_text(json.dumps(default_data, indent=2))
        return default_data
    return json.loads(conv_file.read_text())


def save_conversation(goal_id: str, conversation):
    """Save conversation data for a goal"""
    ensure_data_dir()
    conv_file = CONVERSATIONS_DIR / f"{goal_id}.json"
    conversation["updated_at"] = datetime.now().isoformat()
    conv_file.write_text(json.dumps(conversation, indent=2))


def verify_dt_only(auth_context):
    """Verify that the requester is a Digital Twin"""
    if not auth_context or not auth_context.get("is_dt"):
        raise HTTPException(status_code=403, detail="Only Digital Twins can access this resource")
    return auth_context


def verify_goal_participant(goal, dt_id):
    """Verify that the DT is a participant in this goal"""
    if goal["dt_id_1"] != dt_id and goal["dt_id_2"] != dt_id:
        raise HTTPException(status_code=403, detail="You are not a participant in this goal")


@router.post("")
async def create_goal(goal: GoalCreate, auth_context: dict = Depends(verify_dt_only)):
    """Create a new goal-based conversation between two DTs"""
    goals = load_goals()
    dt_id = auth_context.get("dt_id")
    
    # Verify other DT exists (in a real system, you'd check against a DT registry)
    if goal.other_dt_id == dt_id:
        raise HTTPException(status_code=400, detail="Cannot create goal with yourself")
    
    goal_id = f"goal_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    
    new_goal = {
        "id": goal_id,
        "dt_id_1": dt_id,
        "dt_name_1": auth_context.get("dt_name", "Unknown DT"),
        "dt_id_2": goal.other_dt_id,
        "dt_name_2": "Unknown DT",  # Would be fetched from DT registry
        "title": goal.title,
        "description": goal.description,
        "demand_id": goal.demand_id,
        "supply_id": goal.supply_id,
        "goal_type": goal.goal_type,
        "metadata": goal.metadata,
        "status": "active",  # active, completed, cancelled
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    goals.append(new_goal)
    save_goals(goals)
    
    # Initialize conversation
    load_conversation(goal_id)
    
    return {"success": True, "goal": new_goal}


@router.get("")
async def list_goals(
    status: Optional[str] = None,
    goal_type: Optional[str] = None,
    auth_context: dict = Depends(verify_dt_only)
):
    """List all goals involving the authenticated DT"""
    goals = load_goals()
    dt_id = auth_context.get("dt_id")
    
    # Filter to only goals where this DT is a participant
    goals = [g for g in goals if g["dt_id_1"] == dt_id or g["dt_id_2"] == dt_id]
    
    # Apply additional filters
    if status:
        goals = [g for g in goals if g.get("status") == status]
    if goal_type:
        goals = [g for g in goals if g.get("goal_type") == goal_type]
    
    return {"success": True, "goals": goals, "count": len(goals)}


@router.get("/{goal_id}")
async def get_goal(goal_id: str, auth_context: dict = Depends(verify_dt_only)):
    """Get a specific goal with full conversation history"""
    goals = load_goals()
    goal = next((g for g in goals if g["id"] == goal_id), None)
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    # Verify participant
    dt_id = auth_context.get("dt_id")
    verify_goal_participant(goal, dt_id)
    
    # Load conversation
    conversation = load_conversation(goal_id)
    
    return {
        "success": True,
        "goal": goal,
        "conversation": conversation
    }


@router.post("/{goal_id}/message")
async def add_message(
    goal_id: str,
    message: Message,
    auth_context: dict = Depends(verify_dt_only)
):
    """Add a message to a goal conversation"""
    goals = load_goals()
    goal = next((g for g in goals if g["id"] == goal_id), None)
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    # Verify participant
    dt_id = auth_context.get("dt_id")
    verify_goal_participant(goal, dt_id)
    
    # Load conversation
    conversation = load_conversation(goal_id)
    
    # Add message
    new_message = {
        "id": f"msg_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        "dt_id": dt_id,
        "dt_name": auth_context.get("dt_name", "Unknown DT"),
        "content": message.content,
        "message_type": message.message_type,
        "metadata": message.metadata,
        "timestamp": datetime.now().isoformat()
    }
    
    conversation["messages"].append(new_message)
    save_conversation(goal_id, conversation)
    
    # Update goal timestamp
    goal["updated_at"] = datetime.now().isoformat()
    save_goals(goals)
    
    return {"success": True, "message": new_message}


@router.put("/{goal_id}/data")
async def update_conversation_data(
    goal_id: str,
    data_update: ConversationData,
    auth_context: dict = Depends(verify_dt_only)
):
    """Update conversation-specific shared data"""
    goals = load_goals()
    goal = next((g for g in goals if g["id"] == goal_id), None)
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    # Verify participant
    dt_id = auth_context.get("dt_id")
    verify_goal_participant(goal, dt_id)
    
    # Load conversation
    conversation = load_conversation(goal_id)
    
    # Update shared data
    conversation["shared_data"].update(data_update.data)
    save_conversation(goal_id, conversation)
    
    return {"success": True, "shared_data": conversation["shared_data"]}


@router.put("/{goal_id}/status")
async def update_goal_status(
    goal_id: str,
    status: str,
    auth_context: dict = Depends(verify_dt_only)
):
    """Update goal status (completed, cancelled)"""
    goals = load_goals()
    goal = next((g for g in goals if g["id"] == goal_id), None)
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    # Verify participant
    dt_id = auth_context.get("dt_id")
    verify_goal_participant(goal, dt_id)
    
    # Update status
    if status not in ["active", "completed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    goal["status"] = status
    goal["updated_at"] = datetime.now().isoformat()
    save_goals(goals)
    
    return {"success": True, "goal": goal}
