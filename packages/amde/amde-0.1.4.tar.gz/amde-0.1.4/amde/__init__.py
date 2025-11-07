import requests

class EmbeddingResponse:

    def __init__(self, embedding):

        self.embedding = embedding

 
class Amde:

    def __init__(self, api_key=None, base_url="https://api.amde.dev/v1"):

        self.api_key = api_key

        self.base_url = base_url

 

    def embed(self, model: str, input_data: str):

        data = {

            "model": model,

            "api_key": self.api_key,

            "input_text": input_data  

        }

        resp = requests.post(f"{self.base_url}/embedding", json=data)  

        resp.raise_for_status()

        return EmbeddingResponse(resp.json()["data"])

 
