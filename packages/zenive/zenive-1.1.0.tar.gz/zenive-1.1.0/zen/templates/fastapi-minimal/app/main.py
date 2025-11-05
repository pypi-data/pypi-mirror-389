"""
{{project_name}} - FastAPI Application

A minimal FastAPI application with example endpoints and proper error handling.
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn

from .config import settings
from .models import HealthResponse, ItemCreate, ItemResponse, ErrorResponse

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="{{project_name}}",
    description="{{description}}",
    version="1.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for demo purposes
items_db = {}
item_counter = 0


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal Server Error",
            message="An unexpected error occurred"
        ).dict()
    )


@app.get("/", response_model=dict)
async def root():
    """Root endpoint returning basic API information."""
    return {
        "message": "Welcome to {{project_name}}",
        "version": "1.0.0",
        "docs": "/docs" if settings.environment != "production" else "disabled"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        environment=settings.environment,
        debug=settings.debug
    )


@app.get("/items", response_model=list[ItemResponse])
async def get_items():
    """Get all items."""
    return list(items_db.values())


@app.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int):
    """Get a specific item by ID."""
    if item_id not in items_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )
    return items_db[item_id]


@app.post("/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(item: ItemCreate):
    """Create a new item."""
    global item_counter
    item_counter += 1
    
    new_item = ItemResponse(
        id=item_counter,
        name=item.name,
        description=item.description,
        price=item.price,
        is_active=True
    )
    
    items_db[item_counter] = new_item
    logger.info(f"Created item: {new_item.name} (ID: {item_counter})")
    
    return new_item


@app.put("/items/{item_id}", response_model=ItemResponse)
async def update_item(item_id: int, item: ItemCreate):
    """Update an existing item."""
    if item_id not in items_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )
    
    updated_item = ItemResponse(
        id=item_id,
        name=item.name,
        description=item.description,
        price=item.price,
        is_active=items_db[item_id].is_active
    )
    
    items_db[item_id] = updated_item
    logger.info(f"Updated item: {updated_item.name} (ID: {item_id})")
    
    return updated_item


@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int):
    """Delete an item."""
    if item_id not in items_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )
    
    deleted_item = items_db.pop(item_id)
    logger.info(f"Deleted item: {deleted_item.name} (ID: {item_id})")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )