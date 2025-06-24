from evolutionapi.client import EvolutionClient
from evolutionapi.models.message import TextMessage, MediaMessage, MediaType
import requests
import time

apikey = "3FECACA8A982-4B10-A363-7B291D432708"
phone_number = "5534991704671"
msg = "Teste api"
instanceid = "vendasai"

client = EvolutionClient(
    base_url="http://localhost:8080",
    api_token="429683C4C977415CAAFCCE10F7D57E11"
)

def get_campanhas():
    url = "https://wdoekloxjotwspmfwgla.supabase.co/rest/v1/campanhas?select=*"
    headers = {
        "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indkb2VrbG94am90d3NwbWZ3Z2xhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU1ODc1MTMsImV4cCI6MjA2MTE2MzUxM30.JdFqcKZDI1JOFW4ZW733SB1boGMzCXz3StkDqN6ztoI",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indkb2VrbG94am90d3NwbWZ3Z2xhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU1ODc1MTMsImV4cCI6MjA2MTE2MzUxM30.JdFqcKZDI1JOFW4ZW733SB1boGMzCXz3StkDqN6ztoI"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Lança exceção se houver erro HTTP
    return response.json()

def atualizar_status_campanha(campanha_id, novo_status):
    url = f"https://wdoekloxjotwspmfwgla.supabase.co/rest/v1/campanhas?id=eq.{campanha_id}"
    headers = {
        "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indkb2VrbG94am90d3NwbWZ3Z2xhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU1ODc1MTMsImV4cCI6MjA2MTE2MzUxM30.JdFqcKZDI1JOFW4ZW733SB1boGMzCXz3StkDqN6ztoI",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indkb2VrbG94am90d3NwbWZ3Z2xhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU1ODc1MTMsImV4cCI6MjA2MTE2MzUxM30.JdFqcKZDI1JOFW4ZW733SB1boGMzCXz3StkDqN6ztoI",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    data = {"status": novo_status}
    response = requests.patch(url, headers=headers, json=data)
    if response.status_code == 204:
        print(f"Status da campanha {campanha_id} atualizado para '{novo_status}'")
    else:
        print(f"Erro ao atualizar status da campanha {campanha_id}: {response.text}")


def sendmensage(phone_number, msg, image_url):
    from evolutionapi.models.message import TextMessage, MediaMessage, MediaType

    apikey = "3FECACA8A982-4B10-A363-7B291D432708"
    instanceid = "vendasai"
    client = EvolutionClient(
        base_url="http://localhost:8080",
        api_token="429683C4C977415CAAFCCE10F7D57E11"
    )

    if image_url:
        message = MediaMessage(
            number=phone_number,
            mediatype=MediaType.IMAGE.value,
            mimetype="image/jpeg",
            caption=msg,
            media=image_url,
            fileName="imagem.jpg"
        )
        response = client.messages.send_media(instance_id=instanceid, message=message, instance_token=apikey)
    else:
        message = TextMessage(number=phone_number, text=msg, delay=1000)
        response = client.messages.send_text(instance_id=instanceid, message=message, instance_token=apikey)

    return response

if __name__ == "__main__":
    # Telefones fixos para envio
    telefones = ["5534991169505", "5534991704671", "5534992091871"]

    while True:
        try:
            campanhas = get_campanhas()
            print("Campanhas retornadas do Supabase:")
            print(campanhas)
        except Exception as e:
            print(f"Erro ao buscar campanhas: {e}")
            time.sleep(10)
            continue

        # Verifica campanhas com status vazio e envia mensagem
        for campanha in campanhas:
            if not campanha.get("status"):  # status None ou vazio
                mensagem = campanha.get("mensagem_texto", "Mensagem padrão")
                print(f"Enviando mensagem da campanha '{campanha.get('nome')}' para os telefones:")
                for telefone in telefones:
                    resposta = sendmensage(telefone, mensagem, image_url=None)
                    print(f"Resposta para {telefone}: {resposta}")
                # Atualiza o status da campanha para "Enviado"
                atualizar_status_campanha(campanha.get("id"), "Enviado")

        # Aguarda 10 segundos antes de repetir
        time.sleep(10)