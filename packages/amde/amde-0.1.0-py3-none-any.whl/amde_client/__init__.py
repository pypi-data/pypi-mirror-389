import requests

class EmbeddingResponse:
    def __init__(self, embedding):
        self.embedding = embedding

class Amde:
    def __init__(self, api_key=None, base_url="https://ambade-py.onrender.com"):
        self.api_key = api_key
        self.base_url = base_url

    def embed(self, model: str, input_data: str):
        
        data = {"model": model, "input_text": input_data}
        
      
        resp = requests.post(f"{self.base_url}/embed", json=data)
        
     
        resp.raise_for_status()
        
      
        return EmbeddingResponse(resp.json()["data"]["embedding"])





