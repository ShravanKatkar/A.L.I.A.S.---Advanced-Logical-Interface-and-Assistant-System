"""
Friday AI Assistant - FastAPI Wrapper
This file implements a modern async REST API using FastAPI.
It provides validation using Pydantic, interactive Swagger docs (/docs),
and endpoints to generate, serve, and list image history.
"""

import os
from typing import Optional
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

import image_generator

# Initialize FastAPI app with custom metadata
app = FastAPI(
    title="Friday AI - Image Generation API",
    description="A high-performance FastAPI wrapper for generating images using Pollinations AI. Part of the Friday AI Assistant system.",
    version="1.0.0"
)

# Ensure folders exist
image_generator.ensure_directories()


# Pydantic Schemas for request bodies
class ImageGenerationParams(BaseModel):
    prompt: str = Field(..., example="cyberpunk city in heavy rain, futuristic flying cars, 4k", description="Text description of the image to generate.")
    width: Optional[int] = Field(1024, ge=256, le=2048, description="Width of the image in pixels.")
    height: Optional[int] = Field(1024, ge=256, le=2048, description="Height of the image in pixels.")
    model: Optional[str] = Field("flux", description="Generation model to use: 'flux' (premium) or 'default'.")
    seed: Optional[int] = Field(None, description="Optional seed number for reproducibility. Leave blank for random.")
    raw: Optional[bool] = Field(False, description="If true, returns the raw image file directly. Otherwise returns JSON metadata.")


@app.get("/", tags=["Info"])
async def root(request: Request):
    """
    Returns information about the API and its endpoints.
    """
    base_url = str(request.base_url)
    return {
        "app": "Friday AI - Image Generation API (FastAPI)",
        "docs_url": f"{base_url}docs",
        "endpoints": {
            "/generate (GET)": "Generate image using query parameters.",
            "/generate (POST)": "Generate image using JSON payload.",
            "/history (GET)": "Retrieve generation logs.",
            "/images/{filename} (GET)": "Retrieve a generated image file."
        }
    }


@app.get("/images/{filename}", tags=["Images"])
async def get_image(filename: str):
    """
    Retrieves and serves the generated image file.
    """
    filepath = os.path.join(image_generator.IMAGE_FOLDER, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Image file not found.")
        
    return FileResponse(filepath, media_type="image/jpeg")


@app.get("/history", tags=["History"])
async def get_history():
    """
    Retrieves the history of all image generation attempts.
    """
    history = image_generator.load_history()
    return {
        "total_items": len(history),
        "history": history
    }


@app.get("/generate", tags=["Generation"])
async def generate_get(
    request: Request,
    prompt: str = Query(..., description="Prompt describing the image"),
    width: int = Query(1024, ge=256, le=2048, description="Image width"),
    height: int = Query(1024, ge=256, le=2048, description="Image height"),
    model: str = Query("flux", description="Model name: 'flux' or 'default'"),
    seed: Optional[int] = Query(None, description="Optional seed"),
    raw: bool = Query(False, description="If true, returns binary image directly")
):
    """
    Generates an image via GET request using query strings.
    """
    return run_generation(prompt, width, height, model, seed, raw, request)


@app.post("/generate", tags=["Generation"])
async def generate_post(payload: ImageGenerationParams, request: Request):
    """
    Generates an image via POST request using a JSON body.
    """
    return run_generation(
        prompt=payload.prompt,
        width=payload.width,
        height=payload.height,
        model=payload.model,
        seed=payload.seed,
        raw=payload.raw,
        request=request
    )


def run_generation(prompt: str, width: int, height: int, model: str, seed: Optional[int], raw: bool, request: Request):
    """
    Helper function to call core generator, handle response type, and catch exceptions.
    """
    # Trigger image generation
    saved_path = image_generator.generate_custom_image(
        prompt=prompt,
        width=width,
        height=height,
        seed=seed,
        model=model
    )

    if saved_path and os.path.exists(saved_path):
        filename = os.path.basename(saved_path)
        
        # If raw is requested, return FileResponse immediately
        if raw:
            return FileResponse(saved_path, media_type="image/jpeg")
            
        # Otherwise, construct the static URL for the image and return JSON
        base_url = str(request.base_url)
        image_url = f"{base_url}images/{filename}"
        
        return {
            "status": "success",
            "message": "Image generated successfully.",
            "prompt": prompt,
            "filename": filename,
            "image_url": image_url,
            "local_path": saved_path,
            "width": width,
            "height": height,
            "model": model,
            "seed": seed if seed is not None else "random"
        }
    else:
        raise HTTPException(
            status_code=500, 
            detail="Failed to generate image. Please check API status or try again."
        )


if __name__ == "__main__":
    import uvicorn
    print("[+] Starting Friday Image Gen FastAPI Server on port 8000...")
    print("[i] Interactive documentation will be available at http://127.0.0.1:8000/docs")
    # Run uvicorn on localhost, port 8000
    uvicorn.run(app, host="127.0.0.1", port=8000)
