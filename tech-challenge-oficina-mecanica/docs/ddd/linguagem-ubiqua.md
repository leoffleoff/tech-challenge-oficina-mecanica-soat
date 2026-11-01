# Linguagem Ubíqua e Glossário de Domínio - Oficina Mecânica

Este documento define a **Linguagem Ubíqua** utilizada no domínio da aplicação e modelada no código-fonte do sistema de acordo com os princípios de **Domain-Driven Design (DDD)**.

## 1. Glossário de Termos do Domínio

| Termo | Definição / Descrição no Contexto da Oficina |
| :--- | :--- |
| **Cliente** | Pessoa física (CPF) ou jurídica (CNPJ) cadastrada que possui veículos e solicita serviços de manutenção. |
| **Veículo** | Automóvel vinculado a um cliente, identificado unicamente por sua placa (padrão Antigo ou Mercosul), marca, modelo e ano. |
| **Serviço** | Operação de mão de obra ofertada pela oficina (ex: alinhamento, troca de óleo), contendo preço base e tempo estimado de execução. |
| **Peça / Insumo** | Item físico de reposição utilizado nos reparos (ex: pastilha de freio, filtro), controlado por código SKU e nível de estoque. |
| **Ordem de Serviço (OS)** | **Agregado Raiz** que centraliza todo o atendimento, englobando cliente, veículo, itens de serviço, peças aplicadas, status atual e histórico de tempo. |
| **Orçamento** | Valor total calculado automaticamente pela soma dos serviços e peças incluídos na OS, enviado para aprovação do cliente. |
| **Máquina de Estados** | Regra de transição estrita que governa o ciclo de vida da Ordem de Serviço. |

## 2. Atores do Sistema
- **Recepcionista / Atendente:** Cadastra clientes, veículos e abre ordens de serviço iniciais.
- **Mecânico / Diagnóstico:** Realiza o diagnóstico técnico, inclui peças/serviços adicionais e executa os reparos.
- **Cliente (Externo):** Consulta o progresso do veículo via API pública e aprova ou rejeita o orçamento.
- **Administrador:** Gerencia o catálogo de serviços, o estoque de peças, usuários e indicadores de desempenho.

## 3. Eventos de Domínio
1. `OrdemServicoCriada`: Disparado quando uma nova OS é aberta no sistema.
2. `OrcamentoDisponibilizadoParaAprovacao`: Disparado quando os itens iniciais são inseridos e o orçamento fica pendente de aceite.
3. `OrcamentoAprovado`: Disparado quando o cliente aceita o orçamento, autorizando a transição para execução.
4. `OrcamentoRejeitado`: Disparado quando o cliente recusa o orçamento, cancelando a OS e estornando peças ao estoque.
5. `EstoqueBaixado` / `EstoqueEstornado`: Movimentações de inventário decorrentes de itens vinculados à OS.