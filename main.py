from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from Vendor_agreement import DocumentGenerator
from typing import Dict, Optional

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (for development only)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

generator = DocumentGenerator()

class AgreementRequest(BaseModel):
    user_prompt: str  # Now accepts a natural language prompt instead of individual fields

@app.post("/generate_agreement")
async def generate_agreement(request: AgreementRequest):
    """Generate complete agreement from a natural language prompt"""
    try:
        agreement = generator.generate_agreement(request.user_prompt)
        return {
            "status": "success",
            "agreement": agreement
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/generate_block/{block_name}")
async def generate_single_block(
    block_name: str,
    user_prompt: Optional[str] = None
):
    """Generate a specific block of the agreement from a natural language prompt"""
    try:
        if not user_prompt:
            raise ValueError("user_prompt parameter is required")
            
        # First parse the user prompt to extract structured data
        generator._parse_user_prompt(user_prompt)
        
        # Generate the requested block
        if block_name == "title":
            content = generator._generate_title_block()
        elif block_name == "contract_id":
            content = generator._generate_contract_id() 
        elif block_name == "parties_intro":
            content = generator._generate_parties_intro()
        elif block_name == "buyer":
            content = generator._generate_buyer_block()
        elif block_name == "supplier":
            content = generator._generate_supplier_block()
        elif block_name == "scope":
            content = generator._generate_scope_block()
        elif block_name == "commercial":
            content = generator._generate_commercial_block()
        elif block_name == "delivery":
            content = generator._generate_delivery_block()
        elif block_name == "quality":
            content = generator._generate_quality_block()
        elif block_name == "penalties":
            content = generator._generate_penalties_block()
        elif block_name == "confidentiality":
            content = generator._generate_confidentiality_block()
        else:
            return {"error": "Invalid block name"}
        
        # Parse the block content to extract just the relevant section
        parsed = generator._parse_to_blocks(content)
        return {
            "status": "success",
            block_name: parsed.get(block_name, "")
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }