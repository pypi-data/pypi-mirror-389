"""
Matches API - Find potential demand-supply matches
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from datetime import datetime
import json
from pathlib import Path

router = APIRouter()

DATA_DIR = Path("/Users/amit/aurica/code/data/demand-supply")
DEMANDS_FILE = DATA_DIR / "demands.json"
SUPPLIES_FILE = DATA_DIR / "supplies.json"


def load_demands():
    """Load demands from file"""
    if not DEMANDS_FILE.exists():
        return []
    return json.loads(DEMANDS_FILE.read_text())


def load_supplies():
    """Load supplies from file"""
    if not SUPPLIES_FILE.exists():
        return []
    return json.loads(SUPPLIES_FILE.read_text())


def verify_dt_only(auth_context):
    """Verify that the requester is a Digital Twin"""
    if not auth_context or not auth_context.get("is_dt"):
        raise HTTPException(status_code=403, detail="Only Digital Twins can access this resource")
    return auth_context


def calculate_match_score(demand, supply):
    """Calculate match score between demand and supply"""
    score = 0.0
    
    # Category match (highest weight)
    if demand.get("category") == supply.get("category"):
        score += 50
    
    # Tag overlap
    demand_tags = set(demand.get("tags", []))
    supply_tags = set(supply.get("tags", []))
    tag_overlap = len(demand_tags & supply_tags)
    score += tag_overlap * 10
    
    # Price/budget compatibility
    if demand.get("budget") and supply.get("price"):
        if supply["price"] <= demand["budget"]:
            score += 20
            # Better score for closer match
            ratio = supply["price"] / demand["budget"]
            score += (1 - abs(0.8 - ratio)) * 10
    
    # Quantity match
    if demand.get("quantity") and supply.get("quantity"):
        if supply["quantity"] >= demand["quantity"]:
            score += 10
    
    # Availability and urgency
    if supply.get("availability") == "available":
        score += 5
    if demand.get("urgency") == "high" and supply.get("availability") == "available":
        score += 5
    
    return score


@router.get("")
async def find_matches(
    match_type: str = "all",  # all, demand, supply
    category: Optional[str] = None,
    min_score: float = 30.0,
    auth_context: dict = Depends(verify_dt_only)
):
    """Find potential demand-supply matches for the authenticated DT"""
    dt_id = auth_context.get("dt_id")
    demands = load_demands()
    supplies = load_supplies()
    
    matches = []
    
    if match_type in ["all", "demand"]:
        # Find supplies that match this DT's demands
        my_demands = [d for d in demands if d["dt_id"] == dt_id and d["status"] == "active"]
        other_supplies = [s for s in supplies if s["dt_id"] != dt_id and s["status"] == "active"]
        
        for demand in my_demands:
            if category and demand.get("category") != category:
                continue
            
            for supply in other_supplies:
                score = calculate_match_score(demand, supply)
                if score >= min_score:
                    matches.append({
                        "match_type": "demand",
                        "score": score,
                        "demand": demand,
                        "supply": supply,
                        "my_id": demand["id"],
                        "their_id": supply["id"],
                        "other_dt_id": supply["dt_id"],
                        "other_dt_name": supply["dt_name"]
                    })
    
    if match_type in ["all", "supply"]:
        # Find demands that match this DT's supplies
        my_supplies = [s for s in supplies if s["dt_id"] == dt_id and s["status"] == "active"]
        other_demands = [d for d in demands if d["dt_id"] != dt_id and d["status"] == "active"]
        
        for supply in my_supplies:
            if category and supply.get("category") != category:
                continue
            
            for demand in other_demands:
                score = calculate_match_score(demand, supply)
                if score >= min_score:
                    matches.append({
                        "match_type": "supply",
                        "score": score,
                        "demand": demand,
                        "supply": supply,
                        "my_id": supply["id"],
                        "their_id": demand["id"],
                        "other_dt_id": demand["dt_id"],
                        "other_dt_name": demand["dt_name"]
                    })
    
    # Sort by score descending
    matches.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "success": True,
        "matches": matches,
        "count": len(matches)
    }


@router.get("/suggestions")
async def get_suggestions(
    category: Optional[str] = None,
    auth_context: dict = Depends(verify_dt_only)
):
    """Get intelligent suggestions for creating demands or supplies"""
    dt_id = auth_context.get("dt_id")
    demands = load_demands()
    supplies = load_supplies()
    
    # Analyze what categories are active
    all_demands = [d for d in demands if d["status"] == "active"]
    all_supplies = [s for s in supplies if s["status"] == "active"]
    
    # Count by category
    demand_categories = {}
    supply_categories = {}
    
    for d in all_demands:
        cat = d.get("category", "other")
        demand_categories[cat] = demand_categories.get(cat, 0) + 1
    
    for s in all_supplies:
        cat = s.get("category", "other")
        supply_categories[cat] = supply_categories.get(cat, 0) + 1
    
    # Find gaps (high demand, low supply)
    suggestions = []
    for cat, demand_count in demand_categories.items():
        supply_count = supply_categories.get(cat, 0)
        if demand_count > supply_count * 2:  # More than 2x demand
            suggestions.append({
                "type": "supply_opportunity",
                "category": cat,
                "demand_count": demand_count,
                "supply_count": supply_count,
                "message": f"High demand for {cat} with limited supply"
            })
    
    # Find oversupply opportunities
    for cat, supply_count in supply_categories.items():
        demand_count = demand_categories.get(cat, 0)
        if supply_count > demand_count * 2:  # More than 2x supply
            suggestions.append({
                "type": "demand_opportunity",
                "category": cat,
                "demand_count": demand_count,
                "supply_count": supply_count,
                "message": f"High supply for {cat} with limited demand"
            })
    
    return {
        "success": True,
        "suggestions": suggestions,
        "market_overview": {
            "total_active_demands": len(all_demands),
            "total_active_supplies": len(all_supplies),
            "demand_by_category": demand_categories,
            "supply_by_category": supply_categories
        }
    }
