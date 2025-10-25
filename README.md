# Análise Completa do Simulador Financeiro Jera Capital

## 1. Visão Geral do Processo

O simulador segue uma sequência linear de 3 estágios principais:

1. **Coleta de Dados (Stage: inputs)**
2. **Avaliação de Risco (Stage: risk)**
3. **Projeções e Resultados (Stage: results)**

---

## 2. Coleta de Dados do Cliente

### 2.1 Dados Pessoais e Familiares

**Dados Profissionais:**
- Cargo
- Setor
- Empresa
- → Esses dados são enviados para um webhook externo para estimar salário automaticamente

**Estrutura Familiar:**
- Idade do cliente
- Idade do cônjuge (ou flag "não tenho cônjuge")
- Idade desejada de aposentadoria
- Número de filhos
- Para cada filho:
  - Idade atual
  - Escola (se idade ≤ 17)
  - Se estudará no exterior aos 18 anos

### 2.2 Dados de Moradia

- **Bairro do imóvel principal** → determina preço por m²
- **Metragem do imóvel** (m²)
- **Número de carros** (do casal)
- **Número de funcionários** contratados diretamente

**Fórmulas de Moradia:**

```markdown
Valor do imóvel = preço_m² × metragem

Custo de manutenção = valor_imovel × 2% × inflação_BRL^ano

Funcionários base = TETO(metragem × 0.002)

Custo empregados = (funcionarios_base × 60.000 + n_funcionarios × 48.000) × inflação_BRL^ano

Ocupantes = 1 + (0 se sem cônjuge, senão 1) + número_filhos

Custo base residencial = ocupantes × 30.000 × inflação_BRL^ano

CUSTO MORADIA TOTAL = custo_manutenção + custo_empregados + custo_base_residencial
```

### 2.3 Estilo de Vida

- **Estilo de vida:** 1 (conservador), 2 (moderado), 3 (agressivo)
  - Estilo 1: R$ 20k/ano (casal) + R$ 5k/ano por filho
  - Estilo 2: R$ 50k/ano (casal) + R$ 12k/ano por filho
  - Estilo 3: R$ 100k/ano (casal) + R$ 25k/ano por filho

- **Número de viagens internacionais por ano**

**Custo por viagem (USD):**
```markdown
Custo viagem = 10.000 (casal base)
+ Σ por filho: 
  - 2.000 se idade ≤ 6
  - 3.000 se 7 ≤ idade ≤ 12
  - 5.000 se idade ≥ 13

CUSTO VIAGENS TOTAL = n_viagens × custo_viagem × inflação_USD^ano
```

### 2.4 Gastos Adicionais

- **Ativos de luxo:** gasto mensal (R$) → ×12 para anual
- **Segunda residência:** gasto mensal (R$) → ×12 para anual
- **Filantropia:** gasto anual (R$)

### 2.5 Rendimentos Passivos

**Aluguéis:**
- Aluguéis mensais em BRL
- Taxa de crescimento esperada BRL (%)
- Aluguéis mensais em USD
- Taxa de crescimento esperada USD (%)

**Dividendos:**
- Dividendos anuais em BRL
- Taxa de crescimento esperada BRL (%)
- Dividendos anuais em USD
- Taxa de crescimento esperada USD (%)

**Fórmulas de Rendimentos:**
```markdown
Aluguel_ano_i = aluguel_mensal × 12 × (1 + taxa_crescimento)^i

Dividendos_ano_i = dividendos_anuais × (1 + taxa_crescimento)^i

# Conversão USD para BRL usa cotação dinâmica por ano:
Cotação_ano_i = cotação_inicial × [(1 + infl_BRL) / (1 + infl_USD)]^i
```

### 2.6 Patrimônios Ilíquidos

Para cada ativo ilíquido:
- Valor atual em BRL
- Taxa de crescimento esperada BRL (%)
- Valor atual em USD
- Taxa de crescimento esperada USD (%)

### 2.7 Premissas Macroeconômicas

- **Patrimônio investível inicial** (R$)
- **Número de anos a projetar**
- **Inflação BRL** (% a.a.)
- **Inflação USD** (% a.a.)
- **Cotação USD/BRL inicial**

---

## 3. Avaliação de Perfil de Risco

### 3.1 Questionário Adaptativo (3 perguntas)

Usa técnica de busca binária para convergir rapidamente ao Risk Number (1-99):

**Algoritmo:**
```markdown
Início: risk_low = 1, risk_high = 99, risk_current = 50

Para cada pergunta:
  Mapear risk_current para cenário (perda%, ganho%):
    perda = 2% + (risk_current - 1) × (30% - 2%) / 98
    ganho = 4% + (risk_current - 1) × (40% - 4%) / 98
  
  Se resposta = SIM (confortável):
    risk_low = risk_current
    risk_current = (risk_low + risk_high + 1) // 2
  
  Se resposta = NÃO:
    risk_high = risk_current
    risk_current = (risk_low + risk_high) // 2
```

### 3.2 Perguntas Comportamentais

Após as 3 perguntas adaptativas, são feitas 3 perguntas adicionais:

1. **Comportamento em queda:** -3 a +3 pontos
2. **Horizonte de investimento:** -3 a +3 pontos
3. **Objetivo principal:** -3 a +3 pontos

```markdown
Risk Number Final = risk_current + Σ ajustes comportamentais
Risk Number Final ∈ [1, 99]
```

### 3.3 Classificação de Perfil

```markdown
Se Risk Number ≤ 30: Conservador
Se 30 < Risk Number ≤ 60: Moderado
Se Risk Number > 60: Arrojado
```

---

## 4. Cálculo de Despesas Anuais

### 4.1 Educação

**Escola (até 17 anos):**
```markdown
Para cada filho com idade ≤ 17:
  Buscar custo anual da escola para faixa etária do filho
  Custo_educação_BRL += preço_anual × inflação_BRL^ano
```

**Faculdade (18-21 anos):**
```markdown
Se estuda no Brasil:
  Custo_educação_BRL += 60.000 × inflação_BRL^ano

Se estuda no exterior:
  Custo_educação_USD += 50.000 × inflação_USD^ano
```

**Mesadas:**
```markdown
Se 10 ≤ idade ≤ 13: R$ 500/mês
Se 14 ≤ idade ≤ 17: R$ 1.500/mês
Se 18 ≤ idade ≤ 21: R$ 2.500/mês

Mesadas anuais × inflação_BRL^ano
```

### 4.2 Saúde

**Custo base por idade:**
- 0-18 anos: R$ 15k/ano
- 19-35 anos: R$ 20k/ano
- 36-50 anos: R$ 30k/ano
- 51-65 anos: R$ 45k/ano
- 66+ anos: R$ 60k/ano

```markdown
Custo_saúde = Σ custos_faixa_etária(cliente, cônjuge, filhos<26)
            + (ocupantes × 10.000)  # plano de saúde base
            
Tudo × inflação_BRL^ano
```

### 4.3 Veículos

```markdown
# Carros do casal:
total_carros = n_carros_casal

# Carros dos filhos (18-25 anos):
Para cada filho:
  Se completa 18 anos no ano_i:
    veiculos_adicionais[filho] = 1
    Custo_compra += 200.000 × inflação_BRL^ano
  
  Se idade ≥ 26:
    veiculos_adicionais[filho] = 0

total_carros += Σ veiculos_adicionais

Custo_veículos = total_carros × 50.000 × inflação_BRL^ano + custo_compra
```

### 4.4 Despesas Totais por Ano

```markdown
DESPESAS_BRL = moradia + educação_BRL + saúde + veículos 
             + lifestyle + segunda_residência + luxo + filantropia
             + (viagens_USD × cotação_ano_i)

DESPESAS_USD = educação_USD + viagens_USD
```

---

## 5. Cálculo de Rendas Anuais

### 5.1 Salário

```markdown
Se idade_cliente < idade_aposentadoria:
  Salário_ano_i = salário_ano_0 × inflação_BRL^i
Senão:
  Salário_ano_i = 0
```

### 5.2 Rendimentos Passivos

```markdown
Aluguéis_BRL_ano_i = aluguel_mensal_BRL × 12 × (1 + taxa_aluguel_BRL)^i

Aluguéis_USD_ano_i = aluguel_mensal_USD × 12 × (1 + taxa_aluguel_USD)^i × cotação_ano_i

Dividendos_BRL_ano_i = dividendos_BRL × (1 + taxa_divid_BRL)^i

Dividendos_USD_ano_i = dividendos_USD × (1 + taxa_divid_USD)^i × cotação_ano_i

RENDA_TOTAL = salário + aluguéis_BRL + aluguéis_USD + dividendos_BRL + dividendos_USD
```

---

## 6. Estrutura Patrimonial

O patrimônio é dividido em **3 buckets:**

### 6.1 Capital Guard (Guarda de Capital)

**Função:** Reserva de segurança para cobrir despesas de curto prazo.

**Cálculo Dinâmico (recalculado anualmente):**

```markdown
# Ao início de cada ano i:
Soma_próximas_despesas = Σ(despesas dos próximos 4 anos)
Receita_ano_i = renda total do ano i
Diferença = soma_próximas_despesas - receita_ano_i

Se diferença < despesa_do_ano_i:
  Capital_Guard_necessário = patrimônio_investível × 10%
Senão:
  Capital_Guard_necessário = diferença

# Crescimento do Capital Guard:
Taxa_CG = 11,85% a.a. (70% × 15% BRL + 30% × 4,5% USD)
```

### 6.2 Aspirational (Patrimônio Ilíquido)

**Componentes:**

1. **Apartamentos de aluguel:**
```markdown
Valor_apartamento_BRL = (aluguel_anual_BRL) / (15% - taxa_crescimento_aluguel_BRL)

Valor_apartamento_USD = (aluguel_anual_USD) / (7% - taxa_crescimento_aluguel_USD)
```

2. **Participações (dividendos):**
```markdown
Valor_participação_BRL = dividendos_BRL / (19% - taxa_crescimento_divid_BRL)

Valor_participação_USD = dividendos_USD / (11% - taxa_crescimento_divid_USD)
```

3. **Ativos ilíquidos informados:**
```markdown
Para cada ativo:
  Valor_ano_i = valor_inicial × (1 + taxa_crescimento)^i
```

**Aspirational Total:**
```markdown
Aspirational_ano_i = apartamentos + participações + ilíquidos
                   (cada componente com sua taxa de crescimento)
```

### 6.3 Endowment (Patrimônio Investível Líquido)

**Cálculo Inicial:**
```markdown
Endowment_ano_0 = patrimônio_investível - Capital_Guard_ano_0
```

**Evolução Anual:**
```markdown
# Antes dos retornos:
Endowment_pré = endowment_ano_anterior + fluxo_caixa_líquido

Fluxo_caixa_líquido = renda_total - despesas_totais

# Retorno esperado do Endowment (conforme perfil de risco):
Retorno_total = 70% × retorno_doméstico + 30% × retorno_internacional

# Após retornos:
Endowment_maturado = endowment_pré × (1 + retorno_total)

# Rebalanceamento (transferência entre CG e Endowment):
Diferença_CG = CG_necessário_novo - CG_maturado
Endowment_final = endowment_maturado - diferença_CG
```

---

## 7. Perfis de Risco e Alocações

### 7.1 Conservador (Risk Number ≤ 30)

**Doméstico (70% do Endowment):**
- Retorno esperado: 17,4% a.a.
- Volatilidade: 3,4% a.a.

**Internacional (30% do Endowment):**
- Retorno esperado: 6,8% a.a.
- Volatilidade: 3,9% a.a.

### 7.2 Moderado (30 < Risk Number ≤ 60)

**Doméstico:**
- Retorno esperado: 18,8% a.a.
- Volatilidade: 4,9% a.a.

**Internacional:**
- Retorno esperado: 8,1% a.a.
- Volatilidade: 4,5% a.a.

### 7.3 Arrojado (Risk Number > 60)

**Doméstico:**
- Retorno esperado: 20,2% a.a.
- Volatilidade: 6,8% a.a.

**Internacional:**
- Retorno esperado: 9,5% a.a.
- Volatilidade: 5,6% a.a.

---

## 8. Projeção Patrimonial Final

### 8.1 Ajuste Cambial no Endowment

```markdown
# Para exibição, o endowment é ajustado pela variação cambial:
Fator_FX_ano_i = 0,7 + 0,3 × [(1 + infl_BRL) / (1 + infl_USD)]^i

Endowment_display = endowment_BRL_base × fator_FX
```

### 8.2 Patrimônio Total

```markdown
Patrimônio_Total_ano_i = Capital_Guard + Endowment + Aspirational
```

### 8.3 Crescimento Patrimonial Anual

```markdown
Crescimento_ano_i = Fluxo_caixa_líquido 
                  + Resultados_financeiros
                  + Valorização_ilíquidos

Onde:
  Resultados_financeiros = retorno_CG + retorno_Endowment
  
  Retorno_CG = CG × 11,85%
  
  Retorno_Endowment = endowment_pré × (70% × ret_dom + 30% × ret_int)
  
  Valorização_ilíquidos = Aspirational_ano_i - Aspirational_ano_(i-1)
```

---

## 9. Visualizações e Outputs

### 9.1 Tabelas Geradas

1. **Fluxo de Caixa:**
   - Salário, Aluguéis, Dividendos, Renda Total
   - Gastos BRL, Gastos USD, Gastos Totais
   - Ganhos - Gastos (net cash flow)
   - Resultados financeiros
   - Valorização dos patrimônios ilíquidos
   - Crescimento total do patrimônio

2. **Despesas Detalhadas:**
   - BRL: Moradia, Educação BRL, Saúde, Veículos, Lifestyle, Luxo, Filantropia
   - USD: Educação Exterior, Viagens Internacionais

3. **Evolução Patrimonial:**
   - Capital Guard
   - Endowment
   - Aspirational
   - Patrimônio Total

### 9.2 Gráficos

1. **Patrimônio Nominal:** evolução dos 3 buckets + total
2. **Patrimônio Real:** descontado pela inflação BRL
3. **Despesas Totais:** barras por ano
4. **Monte Carlo:** percentis P10, P50, P90 para doméstico e internacional

---

## 10. Simulação Monte Carlo

**Objetivo:** Mostrar distribuição de resultados possíveis para o Endowment.

**Metodologia:**
```markdown
n_simulações = 10.000
anos = horizonte_projeção

Para cada simulação:
  Para cada ano:
    retorno_anual ~ Normal(μ_portfolio, σ_portfolio)
    
  valor_final = valor_inicial × Π(1 + retornos_anuais)

P10, P50, P90 = percentis(10, 50, 90) dos valores finais

Onde:
  μ_portfolio = 70% × μ_dom + 30% × μ_int
  σ_portfolio = √[(0,7² × σ_dom²) + (0,3² × σ_int²)]
```

---

## 11. Sequência Lógica Completa

```
1. COLETA DE DADOS
   ↓
2. ESTIMATIVA DE SALÁRIO (webhook)
   ↓
3. AVALIAÇÃO DE RISCO
   ├─ Perguntas adaptativas (busca binária)
   ├─ Perguntas comportamentais
   └─ Classificação de perfil
   ↓
4. CÁLCULO DE DESPESAS (ano a ano)
   ├─ Moradia (2% valor imóvel + funcionários + base)
   ├─ Educação (escola + faculdade + mesadas)
   ├─ Saúde (faixa etária + plano base)
   ├─ Veículos (manutenção + compra aos 18)
   ├─ Lifestyle (estilo + viagens internacionais)
   ├─ Luxo e Segunda Residência
   └─ Filantropia
   ↓
5. CÁLCULO DE RENDAS
   ├─ Salário (até aposentadoria)
   ├─ Aluguéis (BRL + USD com crescimento)
   └─ Dividendos (BRL + USD com crescimento)
   ↓
6. ESTRUTURAÇÃO PATRIMONIAL
   ├─ Aspirational (apartamentos + participações + ilíquidos)
   ├─ Capital Guard (10% ou 4 anos de despesas)
   └─ Endowment (resto do patrimônio investível)
   ↓
7. PROJEÇÃO ANO A ANO
   ├─ Aplicar inflação em despesas
   ├─ Aplicar crescimento em rendas
   ├─ Calcular fluxo de caixa líquido
   ├─ Aplicar retornos esperados
   ├─ Rebalancear CG vs Endowment
   └─ Recalcular CG necessário
   ↓
8. SIMULAÇÃO MONTE CARLO
   └─ Gerar cenários probabilísticos (P10, P50, P90)
   ↓
9. VISUALIZAÇÕES E RELATÓRIOS
   └─ Gráficos, tabelas e download Excel
```
