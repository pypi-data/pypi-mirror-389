"""
Demand API - Create and manage demand entries (DT only)
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import json
import os
from pathlib import Path

router = APIRouter()

DATA_DIR = Path("/Users/amit/aurica/code/data/demand-supply")
DEMANDS_FILE = DATA_DIR / "demands.json"


class DemandCreate(BaseModel):
    title: str
    description: str
    category: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    budget: Optional[float] = None
    currency: Optional[str] = "USD"
    urgency: Optional[str] = "medium"  # low, medium, high
    tags: Optional[List[str]] = []
    metadata: Optional[dict] = {}


class DemandUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    budget: Optional[float] = None
    currency: Optional[str] = None
    urgency: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None
    status: Optional[str] = None  # active, fulfilled, cancelled


def ensure_data_dir():
    """Ensure data directory and file exist"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DEMANDS_FILE.exists():
        DEMANDS_FILE.write_text("[]")


def load_demands():
    """Load demands from file"""
    ensure_data_dir()
    return json.loads(DEMANDS_FILE.read_text())


def save_demands(demands):
    """Save demands to file"""
    ensure_data_dir()
    DEMANDS_FILE.write_text(json.dumps(demands, indent=2))


def verify_dt_only(auth_context):
    """Verify that the requester is a Digital Twin"""
    if not auth_context or not auth_context.get("is_dt"):
        raise HTTPException(status_code=403, detail="Only Digital Twins can access this resource")
    return auth_context


@router.post("")
async def create_demand(demand: DemandCreate, auth_context: dict = Depends(verify_dt_only)):
    """Create a new demand entry (DT only)"""
    demands = load_demands()
    
    demand_id = f"dem_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    
    new_demand = {
        "id": demand_id,
        "dt_id": auth_context.get("dt_id"),
        "dt_name": auth_context.get("dt_name", "Unknown DT"),
        **demand.dict(),
        "status": "active",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    demands.append(new_demand)
    save_demands(demands)
    
    return {"success": True, "demand": new_demand}


@router.get("")
async def list_demands(
    category: Optional[str] = None,
    status: Optional[str] = None,
    dt_id: Optional[str] = None,
    auth_context: dict = Depends(verify_dt_only)
):
    """List all demands with optional filters"""
    demands = load_demands()
    
    # Apply filters
    if category:
        demands = [d for d in demands if d.get("category") == category]
    if status:
        demands = [d for d in demands if d.get("status") == status]
    if dt_id:
        demands = [d for d in demands if d.get("dt_id") == dt_id]
    
    return {"success": True, "demands": demands, "count": len(demands)}


@router.get("/{demand_id}")
async def get_demand(demand_id: str, auth_context: dict = Depends(verify_dt_only)):
    """Get a specific demand by ID"""
    demands = load_demands()
    demand = next((d for d in demands if d["id"] == demand_id), None)
    
    if not demand:
        raise HTTPException(status_code=404, detail="Demand not found")
    
    return {"success": True, "demand": demand}


@router.put("/{demand_id}")
async def update_demand(
    demand_id: str,
    updates: DemandUpdate,
    auth_context: dict = Depends(verify_dt_only)
):
    """Update a demand (owner only)"""
    demands = load_demands()
    demand = next((d for d in demands if d["id"] == demand_id), None)
    
    if not demand:
        raise HTTPException(status_code=404, detail="Demand not found")
    
    # Verify ownership
    if demand["dt_id"] != auth_context.get("dt_id"):
        raise HTTPException(status_code=403, detail="Only the owner can update this demand")
    
    # Apply updates
    update_data = updates.dict(exclude_unset=True)
    demand.update(update_data)
    demand["updated_at"] = datetime.now().isoformat()
    
    save_demands(demands)
    
    return {"success": True, "demand": demand}


@router.delete("/{demand_id}")
async def delete_demand(demand_id: str, auth_context: dict = Depends(verify_dt_only)):
    """Delete a demand (owner only)"""
    demands = load_demands()
    demand = next((d for d in demands if d["id"] == demand_id), None)
    
    if not demand:
        raise HTTPException(status_code=404, detail="Demand not found")
    
    # Verify ownership
    if demand["dt_id"] != auth_context.get("dt_id"):
        raise HTTPException(status_code=403, detail="Only the owner can delete this demand")
    
    demands = [d for d in demands if d["id"] != demand_id]
    save_demands(demands)
    
    return {"success": True, "message": "Demand deleted"}
