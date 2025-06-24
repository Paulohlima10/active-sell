import requests

url = "http://localhost:8080/message/sendMedia/vendasai"


payload = {
    "number": "5534991704671",  # número com DDI (55) + DDD + número
    "options": {
        "delay": 1000,
        "presence": "composing"
    },
    "mediaMessage": {
        "mediaType": "image",  # esse é o tipo MIME (obrigatório)
        "fileName": "promocao.jpg",
        "caption": "Confira",
        "media": "https://gzzvydiznhwaxrahzkjt.supabase.co/storage/v1/object/public/campaign-files/e5aae4e8-f0ad-4f62-8914-08ceaf8ab125-image-1747667899628.jpg"
    }
}

headers = {
    "apikey": "3FECACA8A982-4B10-A363-7B291D432708",  # sua chave
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print("Status:", response.status_code)
print("Resposta:", response.json())
