import requests

class EmbeddingResponse:
    def __init__(self, embedding):
        self.embedding = embedding

class Amde:
    def __init__(self, api_key=None, base_url="https://ambade-py.onrender.com", password=None):
        self.api_key = api_key
        self.base_url = base_url
        self.password = password or api_key  # Use api_key as fallback

    def embed(self, model: str, input_data: str):
        data = {
            "model": model,
            "password": self.password,
            "input_text": input_data  # ← Changed from "data" to "input_text"
        }

        resp = requests.post(f"{self.base_url}/embed", json=data)  # ← Changed from data= to json=
        resp.raise_for_status()
        return EmbeddingResponse(resp.json()["data"])