from evolutionapi.client import EvolutionClient
from evolutionapi.models.message import TextMessage, MediaMessage, MediaType

def sendmensage(phone_number, msg, image_url):
    from evolutionapi.models.message import TextMessage, MediaMessage, MediaType

    apikey = "429683C4C977415CAAFCCE10F7D57E11"
    instanceid = "Activesell-01"
    client = EvolutionClient(
        base_url="http://18.205.29.7:8080",
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
    # Exemplo de uso da função sendmensage para mensagem de texto
    telefone = "5534991704671"
    mensagem = "Olá, este é um teste de mensagem de texto!"
    resposta_texto = sendmensage(telefone, mensagem, image_url=None)
    print("Resposta ao enviar mensagem de texto:")
    print(resposta_texto)

    


