from entities.ticket import Ticket


def criar_ticket(data: dict) -> Ticket:
    return Ticket(
        id=data.get('idChamado'),
        protocolo=data.get('numeroProtocolo')
    )