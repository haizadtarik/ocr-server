import modal
import urllib.request


def modal_client():

    fn = modal.Function.from_name("nanonets-server", "receipt_parser")

    receipt_url = "https://modal-cdn.com/cdnbot/Brandys-walmart-receipt-8g68_a_hk_f9c25fce.webp"
    request = urllib.request.Request(receipt_url)
    with urllib.request.urlopen(request) as response:
        image = response.read()
        print(f"running OCR on sample from URL {receipt_url}")
        result = fn.remote(image)
        print(result)

def fastapi_client(server_url):
    import requests

    receipt_url = "https://modal-cdn.com/cdnbot/Brandys-walmart-receipt-8g68_a_hk_f9c25fce.webp"
    response = requests.get(receipt_url)
    
    if response.status_code == 200:
        files = {"file": ("receipt.webp", response.content, "image/webp")}
                
        print(f"Sending request to: {server_url}")
        
        try:
            result = requests.post(server_url, files=files, timeout=30)
            
            print(f"Response status: {result.status_code}")
            print(f"Response headers: {dict(result.headers)}")
            
            if result.status_code == 200:
                print(f"Success: {result.json()}")
            else:
                print(f"Error response: {result.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            
    else:
        print(f"Failed to fetch image: {response.status_code}")


if __name__ == "__main__":
    # modal_client()
    
    server_url = "https://haizadtarik--fastapi-server-fastapi-app.modal.run/parse"
    fastapi_client(server_url)
