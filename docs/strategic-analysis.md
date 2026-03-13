# Decisão Estratégica: On-Premise vs VPN/Data Center

**Autor:** Agente Arquiteto de Soluções
**Data:** 2026-03-13
**Status:** Aprovado para MVP/Beta

---

## Comparativo Executivo

| Critério | On-Premise | VPN/Data Center |
|---|---|---|
| **Custo inicial (cliente)** | Baixo (Docker em infra existente) | Médio (assinatura mensal) |
| **Custo inicial (nós)** | Muito baixo (zero infra) | Alto (R$ 3-8k/mês servidores) |
| **Complexidade de deploy** | Média (Docker + cert CA) | Baixa (cliente instala agente VPN) |
| **Tempo para beta** | 2-4 semanas | 6-8 semanas |
| **Escalabilidade** | Limitada por hardware do cliente | Alta (horizontal em cloud) |
| **Confiança do cliente** | Máxima (dados nunca saem) | Média (depende de confiança no nosso DC) |
| **Custo por cliente** | ~R$ 0 para nós | R$ 500-2.000/mês por cliente |
| **Compliance LGPD/GDPR** | Nativo (dados ficam no cliente) | Requer DPA, contratos, ISO 27001 |
| **Latência adicional** | < 5ms (processamento local) | 20-80ms (VPN + proxy remoto) |
| **Facilidade de atualização** | Manual (docker pull) | Centralizada (automática) |
| **Suporte/debug** | Difícil (acesso remoto) | Fácil (acesso direto) |

---

## RECOMENDAÇÃO PARA MVP/BETA: On-Premise

### Justificativa

1. **Zero custo de infraestrutura para nós** — Não precisamos investir em servidores antes de validar o produto. O cliente roda tudo localmente via Docker.

2. **Argumento de venda imbatível** — "Seus dados NUNCA saem da sua rede" é o diferencial #1 para CISOs preocupados com LGPD e soberania de dados.

3. **Time-to-market 2x mais rápido** — Não precisamos configurar VPN, multi-tenancy, isolamento de dados, billing por uso, etc.

4. **Confiança imediata** — Empresas em fase de avaliação preferem testar localmente antes de confiar dados sensíveis a um terceiro.

5. **Validação de produto sem risco financeiro** — Se o beta não funcionar, não temos custos fixos de infraestrutura.

### Quando migrar para VPN/Data Center (Fase 2)

Após validar com 3-5 clientes on-premise e confirmar product-market fit:
- Oferecer como **opção adicional** para PMEs sem infra de TI
- Usar modelo híbrido: on-premise para enterprises, cloud para startups
- Timeline: mês 6-9 do roadmap

---

## Plano de Ação para Beta (Primeiros 3 Clientes)

### Timeline

| Período | Ação | Responsável |
|---|---|---|
| **Semana 1-2** | MVP funcional: proxy + DLP + dashboard básico | Dev Team |
| **Semana 3** | Testes de segurança e performance | QA + Security |
| **Semana 4** | Documentação + empacotamento Docker | DevOps |
| **Mês 2** | POC com Cliente Beta #1 (empresa conhecida/parceira) | Founder + DevOps |
| **Mês 2-3** | Iteração baseada em feedback do Beta #1 | Dev Team |
| **Mês 3-4** | Onboarding de Clientes Beta #2 e #3 | Founder + Suporte |
| **Mês 5** | Consolidação de feedback, ajuste de pricing | Founder |
| **Mês 6** | Decisão: escalar on-premise ou adicionar cloud | Todos |

### Custo Estimado (6 meses)

| Item | Custo |
|---|---|
| Infraestrutura (nossa) | R$ 0 (on-premise no cliente) |
| Desenvolvimento (2 devs part-time) | R$ 0 se founders / R$ 15-25k/mês se contratados |
| Domínio + landing page | R$ 200/ano |
| Ferramentas (GitHub, CI) | R$ 0 (tiers gratuitos) |
| **Total mínimo (founders)** | **< R$ 500 para 6 meses** |

### Modelo de Preço Sugerido (Beta)

| Plano | Preço | Inclui |
|---|---|---|
| **POC Gratuita** | R$ 0 por 30 dias | Até 10 usuários, suporte por email |
| **Starter** | R$ 1.500/mês | Até 50 usuários, suporte via Slack |
| **Business** | R$ 4.500/mês | Até 200 usuários, SLA 99.5%, suporte prioritário |
| **Enterprise** | Sob consulta | Ilimitado, customizações, suporte dedicado |

---

## Critérios de Sucesso do Beta

| Métrica | Target |
|---|---|
| Falsos negativos (dados críticos não detectados) | 0% |
| Falsos positivos | < 2% do tráfego |
| Latência adicional por requisição | < 50ms (p95) |
| Uptime do proxy | > 99.5% |
| Tempo de setup no cliente | < 30 minutos |
| NPS dos clientes beta | > 8/10 |

---

## Roadmap Técnico 6 Meses

```
Mês 1-2: MVP On-Premise
  ├── Proxy interceptador (mitmproxy) ✅
  ├── DLP Engine (regex + padrões BR) ✅
  ├── API REST (FastAPI) ✅
  ├── Dashboard web (React) ✅
  └── Docker Compose stack ✅

Mês 3: Hardening + Beta #1
  ├── Testes de penetração
  ├── Otimização de performance (< 50ms)
  ├── Certificação CA automatizada
  └── Onboarding do primeiro cliente

Mês 4: Feedback Loop
  ├── Incorporar feedback do Beta #1
  ├── Detecção semântica via Presidio/NLP
  ├── Alertas em tempo real (WebSocket/SSE)
  └── Onboarding Beta #2 e #3

Mês 5: Inteligência
  ├── LLM local via Ollama para análise contextual
  ├── Detecção de código-fonte proprietário
  ├── Relatórios executivos para CISO
  └── Integração SIEM (Splunk, ELK)

Mês 6: Decisão de Escala
  ├── Validar product-market fit
  ├── Definir se adiciona modelo cloud/VPN
  ├── Preparar material de vendas
  └── Prospectar próximos 10 clientes
```
