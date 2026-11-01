from enum import Enum


class StatusOS(str, Enum):
    """Status oficiais da Ordem de Serviço exigidos pela Linguagem Ubíqua."""
    RECEBIDA = "Recebida"
    EM_DIAGNOSTICO = "Em diagnóstico"
    AGUARDANDO_APROVACAO = "Aguardando aprovação"
    EM_EXECUCAO = "Em execução"
    FINALIZADA = "Finalizada"
    ENTREGUE = "Entregue"
    CANCELADA = "Cancelada"

    @classmethod
    def can_transition(cls, current_status: "StatusOS", target_status: "StatusOS") -> bool:
        """Define a máquina de estados permitida para o ciclo de vida da OS."""
        allowed_transitions = {
            cls.RECEBIDA: {cls.EM_DIAGNOSTICO, cls.AGUARDANDO_APROVACAO, cls.CANCELADA},
            cls.EM_DIAGNOSTICO: {cls.AGUARDANDO_APROVACAO, cls.CANCELADA},
            cls.AGUARDANDO_APROVACAO: {cls.EM_EXECUCAO, cls.EM_DIAGNOSTICO, cls.CANCELADA},
            cls.EM_EXECUCAO: {cls.FINALIZADA, cls.AGUARDANDO_APROVACAO},
            cls.FINALIZADA: {cls.ENTREGUE},
            cls.ENTREGUE: set(),
            cls.CANCELADA: set(),
        }
        return target_status in allowed_transitions.get(current_status, set())