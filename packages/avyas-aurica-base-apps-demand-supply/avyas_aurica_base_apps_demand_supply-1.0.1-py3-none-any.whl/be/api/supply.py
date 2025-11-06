"""
Supply API - Create and manage supply entries (DT only)
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import json
from pathlib import Path

router = APIRouter()

DATA_DIR = Path("/Users/amit/aurica/code/data/demand-supply")
SUPPLIES_FILE = DATA_DIR / "supplies.json"


class SupplyCreate(BaseModel):
    title: str
    description: str
    category: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = "USD"
    availability: Optional[str] = "available"  # available, limited, out_of_stock
    tags: Optional[List[str]] = []
    metadata: Optional[dict] = {}


class SupplyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    availability: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None
    status: Optional[str] = None  # active, sold, cancelled


def ensure_data_dir():
    """Ensure data directory and file exist"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SUPPLIES_FILE.exists():
        SUPPLIES_FILE.write_text("[]")


def load_supplies():
    """Load supplies from file"""
    ensure_data_dir()
    return json.loads(SUPPLIES_FILE.read_text())


def save_supplies(supplies):
    """Save supplies to file"""
    ensure_data_dir()
    SUPPLIES_FILE.write_text(json.dumps(supplies, indent=2))


def verify_dt_only(auth_context):
    """Verify that the requester is a Digital Twin"""
    if not auth_context or not auth_context.get("is_dt"):
        raise HTTPException(status_code=403, detail="Only Digital Twins can access this resource")
    return auth_context


@router.post("")
async def create_supply(supply: SupplyCreate, auth_context: dict = Depends(verify_dt_only)):
    """Create a new supply entry (DT only)"""
    supplies = load_supplies()
    
    supply_id = f"sup_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    
    new_supply = {
        "id": supply_id,
        "dt_id": auth_context.get("dt_id"),
        "dt_name": auth_context.get("dt_name", "Unknown DT"),
        **supply.dict(),
        "status": "active",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    supplies.append(new_supply)
    save_supplies(supplies)
    
    return {"success": True, "supply": new_supply}


@router.get("")
async def list_supplies(
    category: Optional[str] = None,
    status: Optional[str] = None,
    availability: Optional[str] = None,
    dt_id: Optional[str] = None,
    auth_context: dict = Depends(verify_dt_only)
):
    """List all supplies with optional filters"""
    supplies = load_supplies()
    
    # Apply filters
    if category:
        supplies = [s for s in supplies if s.get("category") == category]
    if status:
        supplies = [s for s in supplies if s.get("status") == status]
    if availability:
        supplies = [s for s in supplies if s.get("availability") == availability]
    if dt_id:
        supplies = [s for s in supplies if s.get("dt_id") == dt_id]
    
    return {"success": True, "supplies": supplies, "count": len(supplies)}


@router.get("/{supply_id}")
async def get_supply(supply_id: str, auth_context: dict = Depends(verify_dt_only)):
    """Get a specific supply by ID"""
    supplies = load_supplies()
    supply = next((s for s in supplies if s["id"] == supply_id), None)
    
    if not supply:
        raise HTTPException(status_code=404, detail="Supply not found")
    
    return {"success": True, "supply": supply}


@router.put("/{supply_id}")
async def update_supply(
    supply_id: str,
    updates: SupplyUpdate,
    auth_context: dict = Depends(verify_dt_only)
):
    """Update a supply (owner only)"""
    supplies = load_supplies()
    supply = next((s for s in supplies if s["id"] == supply_id), None)
    
    if not supply:
        raise HTTPException(status_code=404, detail="Supply not found")
    
    # Verify ownership
    if supply["dt_id"] != auth_context.get("dt_id"):
        raise HTTPException(status_code=403, detail="Only the owner can update this supply")
    
    # Apply updates
    update_data = updates.dict(exclude_unset=True)
    supply.update(update_data)
    supply["updated_at"] = datetime.now().isoformat()
    
    save_supplies(supplies)
    
    return {"success": True, "supply": supply}


@router.delete("/{supply_id}")
async def delete_supply(supply_id: str, auth_context: dict = Depends(verify_dt_only)):
    """Delete a supply (owner only)"""
    supplies = load_supplies()
    supply = next((s for s in supplies if s["id"] == supply_id), None)
    
    if not supply:
        raise HTTPException(status_code=404, detail="Supply not found")
    
    # Verify ownership
    if supply["dt_id"] != auth_context.get("dt_id"):
        raise HTTPException(status_code=403, detail="Only the owner can delete this supply")
    
    supplies = [s for s in supplies if s["id"] != supply_id]
    save_supplies(supplies)
    
    return {"success": True, "message": "Supply deleted"}
