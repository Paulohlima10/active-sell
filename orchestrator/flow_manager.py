import datetime

class EventFlowManager:
    def __init__(self):
        self.state = {
            "current_event": None,
            "history": [],
            "payloads": {}
        }

    def log(self, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")

    def handle_event(self, event_name, payload=None):
        self.log(f"Evento recebido: {event_name}")
        self.state["current_event"] = event_name
        self.state["history"].append(event_name)

        if payload:
            self.state["payloads"][event_name] = payload

        try:
            match event_name:
                case "start_import":
                    self.import_data()
                case "data_imported":
                    self.analyze_data()
                case "data_analyzed":
                    self.generate_offers()
                case "offers_generated":
                    self.send_campaign()
                case "campaign_sent":
                    self.activate_agents()
                case _:
                    self.log(f"[ERRO] Evento desconhecido: {event_name}")
        except Exception as e:
            self.log(f"[ERRO] Falha ao processar '{event_name}': {str(e)}")

    def import_data(self):
        self.log("Importando dados do banco do cliente...")
        # Simula importação
        self.handle_event("data_imported")

    def analyze_data(self):
        self.log("Analisando dados de compra e comportamento...")
        # Simula análise
        self.handle_event("data_analyzed")

    def generate_offers(self):
        self.log("Gerando ofertas personalizadas...")
        # Simula geração
        self.handle_event("offers_generated")

    def send_campaign(self):
        self.log("Enviando campanha via WhatsApp...")
        # Simula envio
        self.handle_event("campaign_sent")

    def activate_agents(self):
        self.log("Ativando agentes de IA para interação com clientes...")
        # Simula ativação
        self.log("✅ Fluxo finalizado com sucesso.")
        self.log(f"Histórico de eventos: {self.state['history']}")


# Executa o fluxo
if __name__ == "__main__":
    flow = EventFlowManager()
    flow.handle_event("start_import")
