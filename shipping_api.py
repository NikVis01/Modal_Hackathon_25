# shipping_api.py - Modal FastAPI app for shipping recommendations

## OLD STUFF DONT USE
import time
import json
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import modal

# Define the FastAPI app
web_app = FastAPI()

# Add CORS middleware
web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define data models
class ContactInfo(BaseModel):
    email: str

class Dimensions(BaseModel):
    length: float
    width: float
    height: float
    unit: str

class Weight(BaseModel):
    value: float
    unit: str

class Product(BaseModel):
    name: str
    type: str
    dimensions: Dimensions
    weight: Weight

class Address(BaseModel):
    address: str
    city: str
    country: str
    postal_code: str

class Timeline(BaseModel):
    pickup_date: str
    delivery_deadline: str

class ShippingRequest(BaseModel):
    contact: ContactInfo
    product: Product
    origin: Address
    destination: Address
    transport_mode: str
    timeline: Timeline
    special_requirements: str
    prompt: Optional[str] = None
    packageInfo: Optional[Dict[str, Any]] = None
    temperature: Optional[float] = 0.7
    maxTokens: Optional[int] = 500

class ShippingRecommendation(BaseModel):
    text: str
    modelUsed: str = Field(default="Modal Shipping API")
    processingTime: float

# Define the Modal image with python dependencies
image = modal.Image.debian_slim().pip_install(
    "fastapi>=0.95.0",
    "pydantic>=2.0.0",
    "torch",
    "transformers",
    "accelerate"
)

# Define the Modal app
app = modal.App("shipping-logistics-fastapi")

# Set up the Modal web endpoint
@app.function(image=image)
@modal.web_endpoint(method="POST", label="api-shipping-recommend")
async def recommend(shipping_request: ShippingRequest):
    """Generate shipping recommendations based on package details."""
    try:
        # Record start time for processing time calculation
        start_time = time.time()
        
        # Extract key information
        product = shipping_request.product
        destination = shipping_request.destination
        special_requirements = shipping_request.special_requirements
        is_fragile = "fragile" in special_requirements.lower()
        
        # Calculate days between pickup and delivery
        from datetime import datetime
        pickup_date = datetime.strptime(shipping_request.timeline.pickup_date, "%Y-%m-%d")
        delivery_date = datetime.strptime(shipping_request.timeline.delivery_deadline, "%Y-%m-%d")
        delivery_days = (delivery_date - pickup_date).days
        
        # Calculate shipping prices based on weight and dimensions
        base_standard = 15 
        base_express = 25
        base_priority = 35
        
        # Weight factor
        weight_factor = product.weight.value * 2
        
        # Size factor (approximation of volume)
        volume = product.dimensions.length * product.dimensions.width * product.dimensions.height
        size_factor = volume / 10000  # Normalize
        
        # Fragile factor
        fragile_factor = 5 if is_fragile else 0
        
        # Distance factor (simplified)
        distance_factor = 10  # Would normally be calculated based on origin/destination
        
        # Calculate prices
        standard_price = base_standard + weight_factor + size_factor + fragile_factor
        express_price = base_express + weight_factor * 1.5 + size_factor * 1.2 + fragile_factor * 1.5
        priority_price = base_priority + weight_factor * 2 + size_factor * 1.5 + fragile_factor * 2
        
        # Generate shipping recommendations
        recommendations = f"""# Shipping Recommendations

Based on your package details:
- Contents: {product.name}
- Dimensions: {product.dimensions.length} × {product.dimensions.width} × {product.dimensions.height} {product.dimensions.unit}
- Weight: {product.weight.value} {product.weight.unit}
- Fragile: {"Yes" if is_fragile else "No"}
- Destination: {destination.city}, {destination.country}

## Option 1: Standard Delivery
- **Price**: €{standard_price:.2f}
- **Delivery Time**: 3-5 business days
- **Special Handling**: {"Fragile package protection included" if is_fragile else "Standard packaging"}

## Option 2: Express Delivery
- **Price**: €{express_price:.2f}
- **Delivery Time**: 2-3 business days
- **Special Handling**: {"Extra padding and fragile labeling" if is_fragile else "Expedited processing"}

## Option 3: Priority Shipping
- **Price**: €{priority_price:.2f}
- **Delivery Time**: 1-2 business days
- **Special Handling**: {"Premium protection with signature required" if is_fragile else "Premium handling with tracking"}

All options include tracking and insurance up to €100. Estimated delivery within {delivery_days} days to {destination.city}."""

        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Return the recommendation
        return ShippingRecommendation(
            text=recommendations,
            modelUsed="Modal Shipping Calculator",
            processingTime=processing_time
        )
        
    except Exception as e:
        # Log the error for debugging
        print(f"Error generating recommendation: {str(e)}")
        
        # Raise HTTP exception
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Error generating recommendation",
                "error": str(e)
            }
        )

# Add a simple health check endpoint
@app.function(image=image)
@modal.web_endpoint(method="GET")
async def health():
    return {"status": "healthy", "timestamp": time.time()}

# Serve the entire FastAPI app
@app.function(image=image)
@modal.asgi_app()
def fastapi_app():
    return web_app

if __name__ == "__main__":
    modal.runner.deploy_cli(app) 