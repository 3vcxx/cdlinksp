import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Shopee Affiliate Link Converter")

# Lấy cookie từ biến môi trường trên Render
SHOPEE_COOKIE = os.getenv("SHOPEE_COOKIE", "").strip().replace('"', '').replace("'", "")

class LinkRequest(BaseModel):
    link: str

@app.post("/convert")
def convert_shopee_link(req: LinkRequest):
    if not SHOPEE_COOKIE:
        raise HTTPException(status_code=500, detail="SHOPEE_COOKIE chưa được cấu hình trên Render")

    payload = {
        "operationName": "batchGetCustomLink",
        "query": (
            "query batchGetCustomLink($linkParams: [CustomLinkParam!], $sourceCaller: SourceCaller) { "
            "batchCustomLink(linkParams: $linkParams, sourceCaller: $sourceCaller) { shortLink, failCode } }"
        ),
        "variables": {
            "linkParams": [{"originalLink": req.link}],
            "sourceCaller": "CUSTOM_LINK_CALLER",
        },
    }
    
    headers = {
        "content-type": "application/json",
        "cookie": SHOPEE_COOKIE,
        "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
    }

    try:
        resp = requests.post(
            "https://affiliate.shopee.vn/api/v3/gql?q=batchCustomLink",
            headers=headers,
            json=payload,
            timeout=15,
        )
        data = resp.json()
        batch = data.get("data", {}).get("batchCustomLink", [])
        
        if batch and len(batch) > 0:
            short_link = batch[0].get("shortLink")
            fail_code = batch[0].get("failCode")
            
            if short_link:
                return {"success": True, "affiliate_link": short_link}
            else:
                return {"success": False, "error": f"Shopee API từ chối: {fail_code}"}
        else:
            return {"success": False, "error": "Phản hồi không hợp lệ từ Shopee API"}
            
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Lỗi kết nối: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint kiểm tra sức khỏe
@app.get("/")
def health_check():
    return {"status": "ok", "cookie_configured": bool(SHOPEE_COOKIE)}
