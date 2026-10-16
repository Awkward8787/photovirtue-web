from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import sqlite3
from datetime import datetime
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import base64
import io
import json
from typing import Optional
import requests  # for ArtCraft and other remote services

app = FastAPI(title="PhotoVirtue Web Editor - Powered by ArtCraft Services + extensible providers")

# DB for subscriptions (same as bot)
DB_PATH = "photovirtue.db"

# ArtCraft Services integration (https://github.com/storytold/artcraft-services)
# Use the Omni API for real AI-powered generation, enhance, video, etc.
# After Telegram BTC payment, the bot provisions access (credits or key).
ARTCRAFT_BASE = "https://api.storyteller.ai"
ARTCRAFT_KEY = "YOUR_USER_ARTCRAFT_API_KEY"  # Issued or mapped on payment; use per-user key in prod

# Extensible providers (add more: replicate, local models, etc.)
PROVIDERS = {
    "local_pil": {"enabled": True, "desc": "Basic filters/effects (local)"},
    "artcraft": {"enabled": True, "desc": "AI image/video gen, enhance from ArtCraft Services"},
    # "other": {"enabled": False, "desc": "Add your service here"},
}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    return conn

def is_subscribed(user_id: int, token: str = None) -> bool:
    """Check subscription timer + optional token from bot BTC payment.
    Token is stored in last_payment_tx column."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT subscription_end, last_payment_tx FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return False
    end_date = datetime.fromisoformat(row[0])
    subscribed = datetime.now() < end_date
    if token:
        stored_token = row[1] or ""
        if token != stored_token:
            return False
    return subscribed

class ProcessRequest(BaseModel):
    user_id: int
    token: str = ""
    image_data: str  # base64
    action: str
    params: dict = {}

@app.get("/", response_class=HTMLResponse)
async def editor_page(request: Request, user_id: Optional[int] = None, token: Optional[str] = None):
    # PhotoVirtue browser editor - original by Anthony Jones.
    # Powered by ArtCraft Services (AI gen) + local + extensible providers.
    # Gated by Telegram BTC 1-year payments.
    # RE-inspired: layers, brush, filters, effects from Photo Craft analysis.
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PhotoVirtue Editor</title>
        <style>
            body { font-family: Arial; background: #2b2b2b; color: white; margin: 0; padding: 10px; }
            #canvas { border: 1px solid #555; background: white; cursor: crosshair; }
            .toolbar { display: flex; gap: 5px; margin-bottom: 10px; flex-wrap: wrap; }
            button, select { padding: 5px; background: #444; color: white; border: none; }
            .panel { background: #3c3c3c; padding: 10px; margin: 5px 0; }
            input[type=range] { width: 100px; }
        </style>
    </head>
    <body>
        <h1>PhotoVirtue - Browser Editor (ArtCraft Powered)</h1>
        <p>Pay $19 BTC via Telegram bot for 1 year. Timer starts on payment. Uses ArtCraft Services for AI + local tools. Original by Anthony Jones.</p>
        <div class="toolbar">
            <button onclick="setTool('brush')">Brush</button>
            <button onclick="setTool('eraser')">Eraser</button>
            <button onclick="setTool('fill')">Fill</button>
            <button onclick="applyFilter('sharpen')">Sharpen</button>
            <button onclick="applyFilter('blur')">Blur</button>
            <button onclick="applyEffect('shadow')">Drop Shadow</button>
            <button onclick="applyEffect('glow')">Outer Glow</button>
            <button onclick="aiEnhance()">AI Enhance (ArtCraft)</button>
            <button onclick="aiGenerate()">AI Generate (ArtCraft)</button>
            <label>Size: <input type="range" id="size" min="1" max="50" value="10" oninput="updateBrush()"></label>
            <label>Opacity: <input type="range" id="opacity" min="1" max="100" value="100" oninput="updateBrush()"></label>
            <button onclick="undo()">Undo</button>
            <button onclick="clearCanvas()">Clear</button>
            <button onclick="exportImage()">Export</button>
            <input type="file" id="upload" accept="image/*" onchange="loadImage(event)">
            <button onclick="checkSub()">Check Subscription</button>
        </div>
        <canvas id="canvas" width="800" height="600"></canvas>
        <div class="panel">
            <h3>Layers (simplified)</h3>
            <p>Basic layer support - add more in full version.</p>
            <button onclick="addLayer()">Add Layer</button>
        </div>
        <script>
            const canvas = document.getElementById('canvas');
            const ctx = canvas.getContext('2d');
            let currentTool = 'brush';
            let brushSize = 10;
            let brushOpacity = 1;
            let isDrawing = false;
            let lastX = 0, lastY = 0;
            let imageDataStack = []; // for undo
            let currentImage = null;
            let userId = new URLSearchParams(window.location.search).get('user_id') || 0;
            let token = new URLSearchParams(window.location.search).get('token') || '';

            function updateBrush() {
                brushSize = parseInt(document.getElementById('size').value);
                brushOpacity = parseInt(document.getElementById('opacity').value) / 100;
            }

            function setTool(tool) {
                currentTool = tool;
                canvas.style.cursor = tool === 'fill' ? 'crosshair' : 'crosshair';
            }

            canvas.addEventListener('mousedown', startDraw);
            canvas.addEventListener('mousemove', draw);
            canvas.addEventListener('mouseup', endDraw);
            canvas.addEventListener('mouseout', endDraw);

            function startDraw(e) {
                isDrawing = true;
                [lastX, lastY] = [e.offsetX, e.offsetY];
                saveState();
            }

            function draw(e) {
                if (!isDrawing) return;
                ctx.lineWidth = brushSize;
                ctx.lineCap = 'round';
                ctx.lineJoin = 'round';
                ctx.strokeStyle = currentTool === 'eraser' ? '#ffffff' : 'rgba(0,0,0,' + brushOpacity + ')';
                ctx.globalAlpha = brushOpacity;
                
                if (currentTool === 'brush' || currentTool === 'eraser') {
                    ctx.beginPath();
                    ctx.moveTo(lastX, lastY);
                    ctx.lineTo(e.offsetX, e.offsetY);
                    ctx.stroke();
                    [lastX, lastY] = [e.offsetX, e.offsetY];
                }
            }

            function endDraw() {
                isDrawing = false;
                ctx.globalAlpha = 1;
            }

            function saveState() {
                imageDataStack.push(ctx.getImageData(0, 0, canvas.width, canvas.height));
                if (imageDataStack.length > 10) imageDataStack.shift();
            }

            function undo() {
                if (imageDataStack.length > 1) {
                    imageDataStack.pop();
                    ctx.putImageData(imageDataStack[imageDataStack.length - 1], 0, 0);
                }
            }

            function clearCanvas() {
                ctx.fillStyle = '#ffffff';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                saveState();
            }

            function loadImage(event) {
                const file = event.target.files[0];
                const reader = new FileReader();
                reader.onload = function(e) {
                    const img = new Image();
                    img.onload = function() {
                        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                        saveState();
                    };
                    img.src = e.target.result;
                };
                reader.readAsDataURL(file);
            }

            async function applyFilter(filter) {
                // Send to backend for processing (local + ArtCraft extensible)
                const dataUrl = canvas.toDataURL('image/png');
                const response = await fetch('/process', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        user_id: parseInt(userId),
                        token: token,
                        image_data: dataUrl,
                        action: filter,
                        params: {}
                    })
                });
                const result = await response.json();
                if (result.image_data) {
                    const img = new Image();
                    img.onload = () => {
                        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                        saveState();
                    };
                    img.src = result.image_data;
                }
            }

            async function aiEnhance() {
                // Use ArtCraft Services for AI-powered enhance (real gen via Omni API after payment)
                const dataUrl = canvas.toDataURL('image/png');
                const response = await fetch('/process', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        user_id: parseInt(userId),
                        token: token,
                        image_data: dataUrl,
                        action: 'artcraft_enhance',
                        params: {prompt: 'enhance photo quality, details, lighting'}
                    })
                });
                const result = await response.json();
                if (result.image_data) {
                    const img = new Image();
                    img.onload = () => {
                        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                        saveState();
                    };
                    img.src = result.image_data;
                } else if (result.message) {
                    alert(result.message);
                }
            }

            async function aiGenerate() {
                // ArtCraft AI generation (extend to video etc. via their providers)
                const prompt = prompt('Enter prompt for ArtCraft generation:') || 'beautiful landscape photo';
                const dataUrl = canvas.toDataURL('image/png');
                const response = await fetch('/process', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        user_id: parseInt(userId),
                        token: token,
                        image_data: dataUrl,
                        action: 'artcraft_generate',
                        params: {prompt: prompt}
                    })
                });
                const result = await response.json();
                if (result.image_data) {
                    const img = new Image();
                    img.onload = () => {
                        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                        saveState();
                    };
                    img.src = result.image_data;
                } else if (result.message) {
                    alert(result.message + ' (ArtCraft integration active after payment)');
                }
            }

            async function applyEffect(effect) {
                // Similar to filter, extend with params
                const dataUrl = canvas.toDataURL('image/png');
                const response = await fetch('/process', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        user_id: parseInt(userId),
                        image_data: dataUrl,
                        action: effect,
                        params: {color: '#000000'}
                    })
                });
                const result = await response.json();
                if (result.image_data) {
                    const img = new Image();
                    img.onload = () => {
                        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                        saveState();
                    };
                    img.src = result.image_data;
                }
            }

            function addLayer() {
                // Simplified - in full version use Fabric.js for real layers
                alert('Layer added (demo). Full version supports multiple layers, masks, etc.');
            }

            async function checkSub() {
                const response = await fetch('/check_sub?user_id=' + userId + '&token=' + token);
                const data = await response.json();
                alert(data.message);
            }

            function exportImage() {
                const link = document.createElement('a');
                link.download = 'photovirtue_edit.png';
                link.href = canvas.toDataURL();
                link.click();
            }

            // Init white canvas
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            saveState();

            // Check sub on load (with token from bot)
            if (userId) {
                fetch('/check_sub?user_id=' + userId + '&token=' + token).then(r => r.json()).then(d => {
                    if (!d.subscribed) {
                        document.body.innerHTML = '<h1>Subscription Required</h1><p>Please subscribe via the Telegram bot first.</p>';
                    }
                });
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.post("/process")
async def process_image(req: ProcessRequest):
    if not is_subscribed(req.user_id, req.token):
        raise HTTPException(status_code=403, detail="Subscription required (pay via Telegram BTC bot)")
    
    action = req.action
    params = req.params
    
    # Extensible provider routing (ArtCraft for AI, local for basic)
    if action.startswith("artcraft_") and PROVIDERS.get("artcraft", {}).get("enabled"):
        # ArtCraft Services (https://github.com/storytold/artcraft-services)
        # Omni API for AI gen/enhance. Provisioned via bot on BTC payment.
        try:
            artcraft_payload = {
                "prompt": params.get("prompt", "enhance photo"),
                "input": req.image_data,
                "mode": action.replace("artcraft_", ""),
                "options": params
            }
            print(f"[ArtCraft] Would POST to {ARTCRAFT_BASE}/v1/omni_api/generate with {artcraft_payload}")
            # Real: requests.post(..., headers={"Authorization": f"Bearer {ARTCRAFT_KEY}"})
            # Stub simulation for now (stronger local effect)
            header, encoded = req.image_data.split(",", 1)
            img_data = base64.b64decode(encoded)
            img = Image.open(io.BytesIO(img_data)).convert("RGBA")
            img = img.filter(ImageFilter.SHARPEN)
            img = ImageEnhance.Contrast(img).enhance(1.4)
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            processed_data = base64.b64encode(buffer.getvalue()).decode()
            return {"image_data": f"data:image/png;base64,{processed_data}", "message": "ArtCraft AI simulated (add real key for live)"}
        except Exception as e:
            return {"message": f"ArtCraft error: {str(e)}"}
    
    # Fallback local (RE-inspired prototype)
    header, encoded = req.image_data.split(",", 1)
    img_data = base64.b64decode(encoded)
    img = Image.open(io.BytesIO(img_data)).convert("RGBA")
    
    if action == "sharpen":
        img = img.filter(ImageFilter.SHARPEN)
    elif action == "blur":
        img = img.filter(ImageFilter.GaussianBlur(2))
    elif action == "shadow":
        shadow = Image.new("RGBA", img.size, (0,0,0,0))
        ImageDraw.Draw(shadow).rectangle([5,5, img.width-5, img.height-5], fill=(0,0,0,100))
        shadow = shadow.filter(ImageFilter.GaussianBlur(5))
        img = Image.alpha_composite(shadow, img)
    elif action == "glow":
        glow = img.filter(ImageFilter.GaussianBlur(5))
        img = Image.alpha_composite(glow, img)
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    processed_data = base64.b64encode(buffer.getvalue()).decode()
    return {"image_data": f"data:image/png;base64,{processed_data}"}

@app.get("/check_sub")
async def check_subscription(user_id: int, token: Optional[str] = None):
    subscribed = is_subscribed(user_id, token)
    return {"subscribed": subscribed, "message": "Active" if subscribed else "Please subscribe via bot"}

# Mount static if needed
# app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
