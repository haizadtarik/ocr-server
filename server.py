import modal

app = modal.App("ocr-server")

image = modal.Image.debian_slim().pip_install("fastapi[standard]")
fn = modal.Function.from_name("nanonets-server", "receipt_parser")

@app.function(image=image)
@modal.concurrent(max_inputs=100)
@modal.asgi_app()
def fastapi_app():
    from fastapi import FastAPI, UploadFile, File, HTTPException
    from fastapi.middleware.cors import CORSMiddleware

    web_app = FastAPI()
    
    # Add CORS middleware
    web_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allows all origins
        allow_credentials=True,
        allow_methods=["*"],  # Allows all methods
        allow_headers=["*"],  # Allows all headers
    )

    @web_app.post("/parse")
    async def parse(file: UploadFile = File(...)):
        # Check if a file was uploaded
        if not file:
            raise HTTPException(status_code=400, detail="No file uploaded")
        
        # Check if it's an image file
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read the binary data from the uploaded file
        image_bytes = await file.read()
        
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        # Call the receipt_parser function remotely
        result = fn.remote(image_bytes)
        return {"result": result, "filename": file.filename}

    return web_app