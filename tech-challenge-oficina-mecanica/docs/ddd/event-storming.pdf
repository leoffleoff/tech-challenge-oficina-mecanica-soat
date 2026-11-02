# Relatório de Event Storming - Fluxos Principais

O **Event Storming** modela os eventos de domínio, comandos do usuário e políticas de negócio da oficina mecânica.

## Fluxo 1: Criação e Orçamento da Ordem de Serviço
1. **Atores:** Recepcionista / Atendente.
2. **Comando:** `Cadastrar Cliente/Veículo` -> `Criar Ordem de Serviço`.
3. **Regra de Negócio:** 
   - O cliente deve ser identificado obrigatoriamente por CPF ou CNPJ válido.
   - O veículo deve pertencer ao cliente informado.
4. **Eventos Gerados:** `ClienteIdentificado`, `VeiculoVinculado`, `OrdemServicoCriada`.
5. **Cálculo Automótico:** O sistema soma os preços unitários dos serviços e das peças, gerando o `OrcamentoGerado`.
6. **Política:** Automaticamente, a OS transaciona para o status `Aguardando aprovação` e disponibiliza o link de consulta para o cliente.

## Fluxo 2: Acompanhamento e Ciclo de Vida da OS (Máquina de Estados)
O ciclo de vida oficial da Ordem de Serviço segue estritamente a seguinte progressão:
- `Recebida` ➔ `Em diagnóstico` ➔ `Aguardando aprovação` ➔ `Em execução` ➔ `Finalizada` ➔ `Entregue`.
- *Exceção:* A partir dos três primeiros estados, o orçamento pode ser rejeitado, levando a OS ao status `Cancelada`.

## Fluxo 3: Gestão de Peças e Controle de Estoque
1. **Comando:** `Incluir Peça na OS` ou `Cadastrar Nova Peça (SKU)`.
2. **Política de Transação (ACID):** 
   - Ao incluir uma peça na OS, o sistema valida se `quantidade_estoque >= quantidade_solicitada`.
   - Se verdadeiro, executa a baixa imediata no estoque (`baixar_estoque`).
   - Se o cliente **rejeitar** o orçamento, o sistema executa o estorno automático (`repor_estoque`), devolvendo as peças ao inventário.