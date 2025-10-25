# Fórmulas do Simulador Financeiro Jera Capital

## 1. Premissas Básicas

### 1.1 Inflação e Câmbio

**Fator de Inflação BRL:**
```
inflação_BRL_ano_i = (1 + taxa_inflação_BRL/100)^i
```

**Fator de Inflação USD:**
```
inflação_USD_ano_i = (1 + taxa_inflação_USD/100)^i
```

**Cotação USD/BRL Projetada:**
```
cotação_ano_i = cotação_inicial × [(1 + infl_BRL/100) / (1 + infl_USD/100)]^i
```

---

## 2. Despesas - Moradia

### 2.1 Valor do Imóvel
```
valor_imóvel = preço_m² × metragem
```

### 2.2 Custo de Manutenção
```
custo_manutenção_ano_i = valor_imóvel × 0.02 × (1 + infl_BRL/100)^i
```

### 2.3 Funcionários

**Funcionários Base (pela metragem):**
```
funcionários_base = ⌈metragem × 0.002⌉

onde ⌈x⌉ = menor inteiro ≥ x (função teto)
```

**Custo Total de Funcionários:**
```
custo_funcionários_ano_i = [funcionários_base × 60.000 + n_funcionários_extras × 48.000] × (1 + infl_BRL/100)^i
```

### 2.4 Custo Base por Ocupante
```
n_ocupantes = 1 + cônjuge_presente + n_filhos

onde cônjuge_presente = {
  0  se nao_tem_conjuge = true
  1  caso contrário
}

custo_base_ano_i = n_ocupantes × 30.000 × (1 + infl_BRL/100)^i
```

### 2.5 Total Moradia
```
MORADIA_TOTAL_ano_i = custo_manutenção_ano_i 
                    + custo_funcionários_ano_i 
                    + custo_base_ano_i
```

---

## 3. Despesas - Educação

### 3.1 Escola (até 17 anos)

Para cada filho com idade_filho ≤ 17:
```
custo_escola_filho_ano_i = preço_anual_escola × (1 + infl_BRL/100)^i

EDUCAÇÃO_ESCOLA_ano_i = Σ custo_escola_filho_ano_i
                        (todos os filhos ≤ 17 anos)
```

### 3.2 Faculdade (18-21 anos)

**No Brasil:**
```
Se 18 ≤ idade_filho ≤ 21 e estuda_fora = false:
  custo_faculdade_BRL_ano_i += 60.000 × (1 + infl_BRL/100)^i
```

**No Exterior:**
```
Se 18 ≤ idade_filho ≤ 21 e estuda_fora = true:
  custo_faculdade_USD_ano_i += 50.000 × (1 + infl_USD/100)^i
```

### 3.3 Mesadas

Para cada filho:
```
mesada_mensal = {
  500   se 10 ≤ idade ≤ 13
  1.500 se 14 ≤ idade ≤ 17
  2.500 se 18 ≤ idade ≤ 21
  0     caso contrário
}

mesada_anual_filho_ano_i = mesada_mensal × 12 × (1 + infl_BRL/100)^i

MESADAS_TOTAL_ano_i = Σ mesada_anual_filho_ano_i
```

### 3.4 Total Educação
```
EDUCAÇÃO_BRL_ano_i = EDUCAÇÃO_ESCOLA_ano_i 
                   + custo_faculdade_BRL_ano_i 
                   + MESADAS_TOTAL_ano_i

EDUCAÇÃO_USD_ano_i = custo_faculdade_USD_ano_i

EDUCAÇÃO_TOTAL_BRL_ano_i = EDUCAÇÃO_BRL_ano_i 
                         + (EDUCAÇÃO_USD_ano_i × cotação_ano_i)
```

---

## 4. Despesas - Saúde

### 4.1 Custo por Faixa Etária

```
custo_saúde_idade(idade) = {
  15.000  se 0 ≤ idade ≤ 18
  20.000  se 19 ≤ idade ≤ 35
  30.000  se 36 ≤ idade ≤ 50
  45.000  se 51 ≤ idade ≤ 65
  60.000  se idade ≥ 66
}
```

### 4.2 Total Saúde
```
idade_cliente_ano_i = idade_cliente_inicial + i
idade_cônjuge_ano_i = idade_cônjuge_inicial + i
idade_filho_j_ano_i = idade_filho_j_inicial + i

pessoas_cobertas = [cliente] 
                 + [cônjuge] se cônjuge_presente
                 + [filhos com idade < 26]

SAÚDE_FAIXA_ano_i = Σ custo_saúde_idade(pessoa) 
                    × (1 + infl_BRL/100)^i
                    para pessoa ∈ pessoas_cobertas

SAÚDE_PLANO_BASE_ano_i = n_ocupantes × 10.000 × (1 + infl_BRL/100)^i

SAÚDE_TOTAL_ano_i = SAÚDE_FAIXA_ano_i + SAÚDE_PLANO_BASE_ano_i
```

---

## 5. Despesas - Veículos

### 5.1 Veículos dos Filhos

Para cada filho j:
```
Evento aos 18 anos (compra):
  Se idade_filho_j_ano_i = 18 e veículos_adicionais[j] = 0:
    veículos_adicionais[j] = 1
    custo_compra_ano_i += 200.000 × (1 + infl_BRL/100)^i

Manutenção (18-25 anos):
  Se 18 ≤ idade_filho_j_ano_i ≤ 25:
    veículos_adicionais[j] permanece 1

Saída aos 26 anos:
  Se idade_filho_j_ano_i ≥ 26:
    veículos_adicionais[j] = 0
```

### 5.2 Total Veículos
```
total_carros_ano_i = n_carros_casal + Σ veículos_adicionais[j]

VEÍCULOS_MANUTENÇÃO_ano_i = total_carros_ano_i × 50.000 × (1 + infl_BRL/100)^i

VEÍCULOS_TOTAL_ano_i = VEÍCULOS_MANUTENÇÃO_ano_i + custo_compra_ano_i
```

---

## 6. Despesas - Lifestyle

### 6.1 Custo Base por Estilo

```
estilo_vida_custos = {
  1: {casal: 20.000,  por_filho: 5.000},   // Conservador
  2: {casal: 50.000,  por_filho: 12.000},  // Moderado
  3: {casal: 100.000, por_filho: 25.000}   // Agressivo
}

LIFESTYLE_BASE_ano_i = [estilo_vida_custos[estilo].casal 
                      + estilo_vida_custos[estilo].por_filho × n_filhos]
                      × (1 + infl_BRL/100)^i
```

### 6.2 Viagens Internacionais

**Custo por Viagem:**
```
custo_viagem_base = 10.000  // Casal

Para cada filho:
  custo_adicional_filho = {
    2.000  se idade_filho ≤ 6
    3.000  se 7 ≤ idade_filho ≤ 12
    5.000  se idade_filho ≥ 13
  }

custo_viagem_ano_i = [custo_viagem_base + Σ custo_adicional_filho] 
                   × (1 + infl_USD/100)^i

VIAGENS_TOTAL_USD_ano_i = n_viagens × custo_viagem_ano_i
```

### 6.3 Total Lifestyle
```
LIFESTYLE_BRL_ano_i = LIFESTYLE_BASE_ano_i

LIFESTYLE_TOTAL_COM_VIAGENS_BRL_ano_i = LIFESTYLE_BRL_ano_i 
                                       + (VIAGENS_TOTAL_USD_ano_i × cotação_ano_i)
```

---

## 7. Despesas - Outros

### 7.1 Ativos de Luxo
```
LUXO_ano_i = luxo_mensal × 12 × (1 + infl_BRL/100)^i
```

### 7.2 Segunda Residência
```
SEGUNDA_RESIDÊNCIA_ano_i = segunda_resid_mensal × 12 × (1 + infl_BRL/100)^i
```

### 7.3 Filantropia
```
FILANTROPIA_ano_i = filantropia_anual × (1 + infl_BRL/100)^i
```

---

## 8. Despesas Totais

### 8.1 Total BRL
```
DESPESAS_BRL_ano_i = MORADIA_TOTAL_ano_i
                   + EDUCAÇÃO_TOTAL_BRL_ano_i
                   + SAÚDE_TOTAL_ano_i
                   + VEÍCULOS_TOTAL_ano_i
                   + LIFESTYLE_BRL_ano_i
                   + (VIAGENS_TOTAL_USD_ano_i × cotação_ano_i)
                   + SEGUNDA_RESIDÊNCIA_ano_i
                   + LUXO_ano_i
                   + FILANTROPIA_ano_i
```

### 8.2 Total USD (apenas categorias em USD)
```
DESPESAS_USD_ano_i = EDUCAÇÃO_USD_ano_i + VIAGENS_TOTAL_USD_ano_i
```

---

## 9. Rendimentos

### 9.1 Salário
```
idade_cliente_ano_i = idade_cliente_inicial + i

SALÁRIO_ano_i = {
  salário_inicial × (1 + infl_BRL/100)^i  se idade_cliente_ano_i < idade_aposentadoria
  0                                        caso contrário
}
```

### 9.2 Aluguéis

**BRL:**
```
ALUGUÉIS_BRL_ano_i = aluguel_mensal_BRL × 12 × (1 + taxa_crescimento_aluguel_BRL/100)^i
```

**USD (convertido para BRL):**
```
aluguéis_USD_nativos_ano_i = aluguel_mensal_USD × 12 × (1 + taxa_crescimento_aluguel_USD/100)^i

ALUGUÉIS_USD_BRL_ano_i = aluguéis_USD_nativos_ano_i × cotação_ano_i
```

### 9.3 Dividendos

**BRL:**
```
DIVIDENDOS_BRL_ano_i = dividendos_BRL_anuais × (1 + taxa_crescimento_divid_BRL/100)^i
```

**USD (convertido para BRL):**
```
dividendos_USD_nativos_ano_i = dividendos_USD_anuais × (1 + taxa_crescimento_divid_USD/100)^i

DIVIDENDOS_USD_BRL_ano_i = dividendos_USD_nativos_ano_i × cotação_ano_i
```

### 9.4 Total Rendimentos
```
RENDA_TOTAL_ano_i = SALÁRIO_ano_i
                  + ALUGUÉIS_BRL_ano_i
                  + ALUGUÉIS_USD_BRL_ano_i
                  + DIVIDENDOS_BRL_ano_i
                  + DIVIDENDOS_USD_BRL_ano_i
```

---

## 10. Fluxo de Caixa

### 10.1 Fluxo de Caixa Líquido
```
FLUXO_CAIXA_LÍQUIDO_ano_i = RENDA_TOTAL_ano_i - DESPESAS_BRL_ano_i
```

---

## 11. Patrimônio Aspirational

### 11.1 Valor de Apartamentos

**Fórmula de Gordon Growth (Perpetuidade Crescente):**

**Apartamentos BRL:**
```
valor_apartamentos_BRL = aluguel_anual_BRL / (retorno_requerido_BRL - taxa_crescimento_aluguel_BRL)

onde:
  aluguel_anual_BRL = aluguel_mensal_BRL × 12
  retorno_requerido_BRL = 0.15 (15% a.a.)
  taxa_crescimento_aluguel_BRL = taxa_crescimento_aluguel_BRL / 100
```

**Apartamentos USD (convertido para BRL):**
```
valor_apartamentos_USD_nativo = aluguel_anual_USD / (retorno_requerido_USD - taxa_crescimento_aluguel_USD)

onde:
  aluguel_anual_USD = aluguel_mensal_USD × 12
  retorno_requerido_USD = 0.07 (7% a.a.)
  taxa_crescimento_aluguel_USD = taxa_crescimento_aluguel_USD / 100

valor_apartamentos_USD_BRL = valor_apartamentos_USD_nativo × cotação_inicial
```

### 11.2 Valor de Participações

**Participações BRL:**
```
valor_participações_BRL = dividendos_BRL_anuais / (retorno_esperado_BRL - taxa_crescimento_divid_BRL)

onde:
  retorno_esperado_BRL = 0.19 (19% a.a. - fixo para empresas brasileiras)
  taxa_crescimento_divid_BRL = taxa_crescimento_divid_BRL / 100
```

**Participações USD (convertido para BRL):**
```
valor_participações_USD_nativo = dividendos_USD_anuais / (retorno_esperado_USD - taxa_crescimento_divid_USD)

onde:
  retorno_esperado_USD = 0.11 (11% a.a. - fixo para empresas internacionais)
  taxa_crescimento_divid_USD = taxa_crescimento_divid_USD / 100

valor_participações_USD_BRL = valor_participações_USD_nativo × cotação_inicial
```

### 11.3 Ativos Ilíquidos

Para cada ativo ilíquido j:
```
valor_ilíquido_j_ano_i = valor_ilíquido_j_BRL_inicial × (1 + taxa_crescimento_j_BRL/100)^i
                       + valor_ilíquido_j_USD_inicial × cotação_inicial × (1 + taxa_crescimento_j_USD/100)^i
```

### 11.4 Aspirational Total Inicial
```
ASPIRATIONAL_inicial = valor_apartamentos_BRL
                     + valor_apartamentos_USD_BRL
                     + valor_participações_BRL
                     + valor_participações_USD_BRL
                     + Σ valor_ilíquido_j_ano_0
```

### 11.5 Taxa de Crescimento Ponderada do Aspirational

```
peso_apartamentos_BRL = valor_apartamentos_BRL / ASPIRATIONAL_inicial
peso_apartamentos_USD = valor_apartamentos_USD_BRL / ASPIRATIONAL_inicial
peso_participações_BRL = valor_participações_BRL / ASPIRATIONAL_inicial
peso_participações_USD = valor_participações_USD_BRL / ASPIRATIONAL_inicial
peso_ilíquido_j = valor_ilíquido_j_ano_0 / ASPIRATIONAL_inicial

taxa_crescimento_aspirational = peso_apartamentos_BRL × taxa_crescimento_aluguel_BRL
                              + peso_apartamentos_USD × taxa_crescimento_aluguel_USD
                              + peso_participações_BRL × taxa_crescimento_divid_BRL
                              + peso_participações_USD × taxa_crescimento_divid_USD
                              + Σ (peso_ilíquido_j × taxa_crescimento_média_j)

onde:
  taxa_crescimento_média_j = (valor_j_BRL × taxa_j_BRL + valor_j_USD × taxa_j_USD) / valor_j_total
```

### 11.6 Aspirational ao Longo dos Anos

**Método Detalhado (usado no sistema):**
```
ASPIRATIONAL_ano_i = valor_apartamentos_BRL × (1 + taxa_crescimento_aluguel_BRL/100)^i
                   + valor_apartamentos_USD_BRL × (1 + taxa_crescimento_aluguel_USD/100)^i
                   + valor_participações_BRL × (1 + taxa_crescimento_divid_BRL/100)^i
                   + valor_participações_USD_BRL × (1 + taxa_crescimento_divid_USD/100)^i
                   + Σ valor_ilíquido_j_ano_i
```

---

## 12. Capital Guard

### 12.1 Cálculo Dinâmico Anual

**Capital Guard Requerido no Ano i:**
```
soma_próximas_despesas_i = Σ DESPESAS_BRL_ano_k  para k ∈ [i, i+3]
                          (máximo 4 anos ou até fim da projeção)

receita_ano_i = RENDA_TOTAL_ano_i

diferença_i = soma_próximas_despesas_i - receita_ano_i

CAPITAL_GUARD_requerido_ano_i = {
  patrimônio_investível_ano_i × 0.10  se diferença_i < DESPESAS_BRL_ano_i
  diferença_i                          caso contrário
}
```

**Nota:** No ano 0, o Capital Guard é calculado pela função `compute_costs_and_incomes` e pode usar uma lógica ligeiramente diferente para inicialização.

### 12.2 Taxa de Retorno do Capital Guard

```
taxa_retorno_CG = 0.70 × 0.15 + 0.30 × 0.045 = 0.1185 = 11.85% a.a.

onde:
  70% em ativos domésticos com retorno de 15% a.a.
  30% em ativos internacionais com retorno de 4.5% a.a.
```

### 12.3 Maturação do Capital Guard
```
CAPITAL_GUARD_maturado_ano_i = CAPITAL_GUARD_ano_(i-1) × (1 + 0.1185)
```

---

## 13. Endowment (Patrimônio Investível Líquido)

### 13.1 Endowment Inicial (Ano 0)
```
ENDOWMENT_ano_0 = patrimônio_investível_inicial - CAPITAL_GUARD_ano_0

Se ENDOWMENT_ano_0 < 0:
  ENDOWMENT_ano_0 = 0
```

### 13.2 Retornos Esperados por Perfil de Risco

**Conservador:**
```
retorno_doméstico_conservador = 0.174 (17.4% a.a.)
retorno_internacional_conservador = 0.068 (6.8% a.a.)

volatilidade_doméstica = 0.034 (3.4% a.a.)
volatilidade_internacional = 0.039 (3.9% a.a.)
```

**Moderado:**
```
retorno_doméstico_moderado = 0.188 (18.8% a.a.)
retorno_internacional_moderado = 0.081 (8.1% a.a.)

volatilidade_doméstica = 0.049 (4.9% a.a.)
volatilidade_internacional = 0.045 (4.5% a.a.)
```

**Arrojado:**
```
retorno_doméstico_arrojado = 0.202 (20.2% a.a.)
retorno_internacional_arrojado = 0.095 (9.5% a.a.)

volatilidade_doméstica = 0.068 (6.8% a.a.)
volatilidade_internacional = 0.056 (5.6% a.a.)
```

### 13.3 Retorno Combinado do Endowment
```
retorno_endowment = 0.70 × retorno_doméstico + 0.30 × retorno_internacional
```

### 13.4 Evolução do Endowment (Ano a Ano)

**Passo 1: Adicionar Fluxo de Caixa Líquido**
```
endowment_pré_retorno_ano_i = ENDOWMENT_ano_(i-1) + FLUXO_CAIXA_LÍQUIDO_ano_i
```

**Passo 2: Aplicar Retornos**
```
endowment_maturado_ano_i = endowment_pré_retorno_ano_i × (1 + retorno_endowment)
```

**Passo 3: Rebalancear com Capital Guard**
```
diferença_CG_ano_i = CAPITAL_GUARD_requerido_ano_i - CAPITAL_GUARD_maturado_ano_i

ENDOWMENT_ano_i = endowment_maturado_ano_i - diferença_CG_ano_i

Se ENDOWMENT_ano_i < 0:
  ENDOWMENT_ano_i = 0

CAPITAL_GUARD_ano_i = CAPITAL_GUARD_requerido_ano_i
```

### 13.5 Ajuste Cambial para Display

```
fator_FX_ano_i = 0.70 + 0.30 × [(1 + infl_BRL/100) / (1 + infl_USD/100)]^i

ENDOWMENT_display_ano_i = ENDOWMENT_ano_i × fator_FX_ano_i
```

**Nota:** Este ajuste é apenas para visualização. Os cálculos internos usam o valor base do endowment.

---

## 14. Patrimônio Total

### 14.1 Patrimônio Total por Ano
```
PATRIMÔNIO_TOTAL_ano_i = CAPITAL_GUARD_ano_i 
                       + ENDOWMENT_display_ano_i 
                       + ASPIRATIONAL_ano_i
```

### 14.2 Crescimento do Patrimônio

**Resultados Financeiros:**
```
resultado_financeiro_CG_ano_i = CAPITAL_GUARD_ano_i × 0.1185

resultado_financeiro_endowment_ano_i = endowment_pré_retorno_ano_i × retorno_endowment

RESULTADOS_FINANCEIROS_ano_i = resultado_financeiro_CG_ano_i 
                             + resultado_financeiro_endowment_ano_i
```

**Valorização de Ilíquidos:**
```
VALORIZAÇÃO_ILÍQUIDOS_ano_i = ASPIRATIONAL_ano_i - ASPIRATIONAL_ano_(i-1)
```

**Crescimento Total:**
```
CRESCIMENTO_PATRIMÔNIO_ano_i = FLUXO_CAIXA_LÍQUIDO_ano_i
                             + RESULTADOS_FINANCEIROS_ano_i
                             + VALORIZAÇÃO_ILÍQUIDOS_ano_i
```

---

## 15. Patrimônio Real (Descontado pela Inflação)

### 15.1 Desconto pela Inflação BRL
```
CAPITAL_GUARD_real_ano_i = CAPITAL_GUARD_ano_i / (1 + infl_BRL/100)^i

ENDOWMENT_real_ano_i = ENDOWMENT_display_ano_i / (1 + infl_BRL/100)^i

ASPIRATIONAL_real_ano_i = ASPIRATIONAL_ano_i / (1 + infl_BRL/100)^i

PATRIMÔNIO_TOTAL_real_ano_i = CAPITAL_GUARD_real_ano_i
                            + ENDOWMENT_real_ano_i
                            + ASPIRATIONAL_real_ano_i
```

---

## 16. Perfil de Risco - Risk Number

### 16.1 Mapeamento Risk Number → Cenário

```
perda_percentual = 2.0 + (risk_number - 1) × (30.0 - 2.0) / 98

ganho_percentual = 4.0 + (risk_number - 1) × (40.0 - 4.0) / 98

onde:
  risk_number ∈ [1, 99]
  perda_percentual ∈ [2%, 30%]
  ganho_percentual ∈ [4%, 40%]
```

### 16.2 Busca Binária (Questionário Adaptativo)

**Inicialização:**
```
risk_low = 1
risk_high = 99
risk_current = 50
```

**Iteração (3 perguntas):**
```
Para cada pergunta:
  Apresentar cenário baseado em risk_current
  
  Se resposta = SIM (confortável):
    risk_low = risk_current
    risk_current = ⌊(risk_low + risk_high + 1) / 2⌋
  
  Se resposta = NÃO (desconfortável):
    risk_high = risk_current
    risk_current = ⌊(risk_low + risk_high) / 2⌋
```

### 16.3 Ajustes Comportamentais

**Pontuação por Resposta:**

Comportamento em Queda:
```
ajuste_comportamento = {
  -3  se "Venderia tudo imediatamente"
  -1  se "Venderia parte dos investimentos"
  +1  se "Manteria a posição"
  +3  se "Aumentaria a posição"
}
```

Horizonte de Investimento:
```
ajuste_horizonte = {
  -3  se "Até 1 ano"
  -1  se "1 a 3 anos"
  +1  se "3 a 5 anos"
  +3  se "Mais de 5 anos"
}
```

Objetivo Principal:
```
ajuste_objetivo = {
  -3  se "Preservar o capital"
  -1  se "Proteger contra a inflação"
  +1  se "Equilibrar crescimento e segurança"
  +3  se "Crescimento de capital"
}
```

### 16.4 Risk Number Final
```
risk_number_final = risk_current + ajuste_comportamento + ajuste_horizonte + ajuste_objetivo

risk_number_final = max(1, min(99, risk_number_final))
```

### 16.5 Classificação de Perfil
```
perfil_risco = {
  "conservador"  se risk_number_final ≤ 30
  "moderado"     se 30 < risk_number_final ≤ 60
  "arrojado"     se risk_number_final > 60
}
```

---

## 17. Simulação Monte Carlo

### 17.1 Parâmetros da Simulação

```
n_simulações = 10.000
anos = anos_proj

μ_portfolio = 0.70 × μ_doméstico + 0.30 × μ_internacional

σ_portfolio = √[(0.70² × σ_doméstico²) + (0.30² × σ_internacional²)]
```

### 17.2 Simulação Anual

Para cada simulação s ∈ [1, n_simulações]:
```
valor[s][0] = endowment_inicial

Para cada ano i ∈ [1, anos]:
  retorno[s][i] ~ Normal(μ_portfolio, σ_portfolio)
  
  valor[s][i] = valor[s][i-1] × (1 + retorno[s][i])
```

### 17.3 Percentis

```
P10_ano_i = percentil_10(valores de todas simulações no ano i)
P50_ano_i = percentil_50(valores de todas simulações no ano i)
P90_ano_i = percentil_90(valores de todas simulações no ano i)
```

### 17.4 Simulação Mensal (versão refinada)

```
μ_mensal = μ_anual / 12
σ_mensal = σ_anual / √12

Para cada simulação s:
  Para cada mês m ∈ [1, anos × 12]:
    retorno_mensal[s][m] ~ Normal(μ_mensal, σ_mensal)
  
  Para cada ano i:
    índice_final_ano = i × 12
    valor[s][i] = endowment_inicial × ∏(1 + retorno_mensal[s][m]) para m ∈ [1, índice_final_ano]
```

---

## 18. Escalas e Ajustes Customizados

### 18.1 Aplicação de Escalas

Para cada categoria de despesa:
```
categoria_ajustada_ano_i = categoria_base_ano_i × scale[categoria]

onde:
  scale[categoria] ∈ [0, 2]  (0% a 200% do valor base)
  
  categorias = {
    "moradia",
    "educacao_brl",
    "educacao_usd",
    "saude",
    "veiculos",
    "lifestyle",
    "viagens_usd"
  }
```

### 18.2 Cálculo de Scale a partir de Slider

```
scale[categoria] = valor_slider / baseline_cost[categoria]

onde:
  valor_slider = valor escolhido pelo usuário no ajuste
  baseline_cost[categoria] = custo calculado no ano 0 (primeira projeção)
```

---

## 19. Fórmulas Auxiliares

### 19.1 Número de Ocupantes Domiciliares
```
n_ocupantes = 1 + cônjuge_presente + n_filhos

cônjuge_presente = {
  0  se nao_tem_conjuge = true OU idade_cônjuge = 0
  1  caso contrário
}
```

### 19.2 Filhos Elegíveis para Despesas

Para saúde (menores de 26):
```
filhos_saúde_ano_i = {filho_j | idade_filho_j_ano_i < 26}
```

Para educação escolar (até 17):
```
filhos_escola_ano_i = {filho_j | idade_filho_j_ano_i ≤ 17}
```

Para faculdade (18-21):
```
filhos_faculdade_ano_i = {filho_j | 18 ≤ idade_filho_j_ano_i ≤ 21}
```

### 19.3 Idade no Ano i
```
idade_pessoa_ano_i = idade_pessoa_inicial + i
```

---

## 20. Condições de Contorno

### 20.1 Proteções contra Valores Negativos

```
∀ custo: custo = max(0, custo)
∀ patrimônio_bucket: patrimônio_bucket = max(0, patrimônio_bucket)
```

### 20.2 Divisão por Zero

**Na Fórmula de Gordon Growth:**
```
Se (retorno_requerido - taxa_crescimento) ≤ 0:
  valor = 0

Caso contrário:
  valor = fluxo_anual / (retorno_requerido - taxa_crescimento)
```

### 20.3 Tratamento de Arrays Vazios

```
Se n_filhos = 0:
  Σ custos_filhos = 0
  
Se n_iliquidos = 0:
  valor_ilíquidos = 0
```

---

## 21. Benchmarks

### 21.1 CDI (Doméstico)
```
benchmark_CDI_ano_i = valor_inicial × (1 + 0.15)^i
```

### 21.2 T-Bill/Treasury (Internacional)
```
benchmark_treasury_ano_i = valor_inicial × (1 + 0.04)^i
```

---

## 22. Notações e Convenções

### 22.1 Símbolos
- `i` = ano da projeção (0-indexed: i ∈ [0, anos_proj-1])
- `j` = índice de filho ou ativo ilíquido
- `s` = índice de simulação Monte Carlo
- `⌈x⌉` = função teto (menor inteiro ≥ x)
- `⌊x⌋` = função piso (maior inteiro ≤ x)
- `Σ` = somatório
- `∏` = produtório
- `~` = distribuído segundo (estatística)

### 22.2 Tipos de Valores
- Valores monetários sempre em formato decimal (ex: 100000.0)
- Percentuais sempre divididos por 100 antes de usar em fórmulas
- Taxas de retorno em decimal (ex: 0.15 = 15%)

### 22.3 Moedas
- BRL = Real Brasileiro
- USD = Dólar Americano
- Conversões sempre usam cotação projetada do ano correspondente
