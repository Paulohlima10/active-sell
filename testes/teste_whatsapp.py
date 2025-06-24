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
    # Exemplo de uso da função get_campanhas
    try:
        campanhas = get_campanhas()
        print("Campanhas retornadas do Supabase:")
        print(campanhas)
    except Exception as e:
        print(f"Erro ao buscar campanhas: {e}")

    # Exemplo de uso da função sendmensage para mensagem de texto
    telefone = "5534991704671"
    mensagem = "Olá, este é um teste de mensagem de texto!"
    resposta_texto = sendmensage(telefone, mensagem, image_url=None)
    print("Resposta ao enviar mensagem de texto:")
    print(resposta_texto)

    # Exemplo de uso da função sendmensage para mensagem com imagem
    imagem_url = "https://cdn.prod.website-files.com/62cc56fc2b55bd9bafba3478/653027f631dfa4d287f357d6_Processos%2520Gerenciais-2.jpeg"  # Substitua por uma URL real ou base64
    mensagem_imagem = "Olá, esta é uma mensagem com imagem!"
    resposta_imagem = sendmensage(telefone, mensagem_imagem, image_url=imagem_url)
    print("Resposta ao enviar mensagem com imagem:")
    print(resposta_imagem)



