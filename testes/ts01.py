import requests
import uuid

def send_text_via_http(
    phone_number,
    msg,
    msg_id=None,
    context_info=None,
    token="9C84DC7EBCC6-4B17-8625-A4A60018AC03",
    url="http://18.205.29.7:8080/chat/send/text"
):
    headers = {
        "Token": token,
        "Content-Type": "application/json"
    }
    if msg_id is None:
        msg_id = uuid.uuid4().hex.upper()
    payload = {
        "Phone": phone_number,
        "Body": msg,
        "Id": msg_id
    }
    if context_info:
        payload["ContextInfo"] = context_info
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

telefone = "553491704671"
mensagem = "oooooooooOlá, este é um teste de mensagem de texto!"
resposta = send_text_via_http(telefone, mensagem)
print("Resposta ao enviar mensagem via HTTP:")
print(resposta)