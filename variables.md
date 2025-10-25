# Mapeamento Completo de Variáveis por Usuário

## 1. Dados Profissionais e Pessoais

### 1.1 Informações Profissionais
```typescript
{
  cargo: string,                    // Obrigatório
  setor: string,                    // Obrigatório
  empresa: string,                  // Obrigatório
  salario_anual: number,            // Calculado via API ou manual
  salario_manual_input: boolean,    // Flag se foi entrada manual
  api_failed: boolean,              // Flag se API de salário falhou
}
```

### 1.2 Informações Pessoais
```typescript
{
  idade_cliente: number,            // Obrigatório, 0-120
  idade_conjuge: number,            // 0-120, pode ser 0
  nao_tem_conjuge: boolean,         // Flag: true se sem cônjuge
  idade_aposentadoria: number,      // Obrigatório, 0-120
}
```

## 2. Estrutura Familiar

### 2.1 Filhos
```typescript
{
  n_filhos: number,                 // 0-10
  
  // Arrays paralelos (mesmo tamanho = n_filhos)
  idades_filhos: number[],          // Idade de cada filho (0-40)
  escolas_filhos: string[],         // Nome da escola ou "" se não aplicável
  estudam_fora: boolean[],          // Se estudará/estuda no exterior
}
```

**Exemplo:**
```json
{
  "n_filhos": 2,
  "idades_filhos": [10, 8],
  "escolas_filhos": ["Beacon School", "Escola Alef Peretz"],
  "estudam_fora": [false, true]
}
```

## 3. Moradia e Residências

### 3.1 Imóvel Principal
```typescript
{
  bairro: string,                   // Nome do bairro ou ""
  metragem: number,                 // m², 0-5000
  n_funcionarios: number,           // Funcionários contratados, 0-20
}
```

### 3.2 Segunda Residência
```typescript
{
  segunda_resid_mensal: number,     // Gasto mensal em R$, >= 0
}
```

## 4. Lifestyle e Consumo

### 4.1 Veículos e Mobilidade
```typescript
{
  n_carros: number,                 // Carros do casal, 0-10
}
```

### 4.2 Estilo de Vida
```typescript
{
  estilo_vida: number,              // 1, 2 ou 3 (conservador, moderado, agressivo)
  n_viagens: number,                // Viagens internacionais/ano, 0-12
}
```

### 4.3 Gastos Discricionários
```typescript
{
  luxo_mensal: number,              // Gastos com ativos de luxo/mês, >= 0
  filantropia_anual: number,        // Doações anuais, >= 0
}
```

## 5. Rendimentos Passivos

### 5.1 Aluguéis
```typescript
{
  // Aluguéis em BRL
  aluguel_mensal_brl: number,       // Receita mensal, >= 0
  aluguel_growth_brl: number,       // Taxa crescimento % a.a., 0-50
  
  // Aluguéis em USD
  aluguel_mensal_usd: number,       // Receita mensal, >= 0
  aluguel_growth_usd: number,       // Taxa crescimento % a.a., 0-50
}
```

### 5.2 Dividendos
```typescript
{
  // Dividendos em BRL
  dividendos_brl: number,           // Receita anual, >= 0
  divid_growth_brl: number,         // Taxa crescimento % a.a., 0-50
  
  // Dividendos em USD
  dividendos_usd: number,           // Receita anual, >= 0
  divid_growth_usd: number,         // Taxa crescimento % a.a., 0-50
}
```

## 6. Patrimônios Ilíquidos

### 6.1 Estrutura de Ilíquidos
```typescript
{
  has_iliquido: boolean,            // Possui patrimônios ilíquidos?
  n_iliquidos: number,              // Quantidade, 0-10
  
  // Arrays paralelos (mesmo tamanho = n_iliquidos)
  iliquido_vals_brl: number[],     // Valor atual de cada ativo em BRL
  iliquido_growth_brl: number[],   // Taxa crescimento % de cada (BRL)
  iliquido_vals_usd: number[],     // Valor atual de cada ativo em USD
  iliquido_growth_usd: number[],   // Taxa crescimento % de cada (USD)
}
```

**Exemplo:**
```json
{
  "has_iliquido": true,
  "n_iliquidos": 2,
  "iliquido_vals_brl": [1000000.0, 500000.0],
  "iliquido_growth_brl": [10.0, 8.0],
  "iliquido_vals_usd": [200000.0, 100000.0],
  "iliquido_growth_usd": [5.0, 5.0]
}
```

## 7. Patrimônio e Premissas Financeiras

### 7.1 Patrimônio Inicial
```typescript
{
  patrimonio_inicial: number,       // Patrimônio investível em R$, >= 0
}
```

### 7.2 Premissas Macroeconômicas
```typescript
{
  anos_proj: number,                // Anos de projeção, 1-100
  infl_brl_pct: number,            // Inflação BRL % a.a., 0-20
  infl_usd_pct: number,            // Inflação USD % a.a., 0-20
  cotacao_usd: number,             // Cotação USD/BRL inicial, 0-20
}
```

## 8. Perfil de Risco

### 8.1 Avaliação de Risco
```typescript
{
  // Estado do questionário adaptativo
  risk_low: number,                 // Limite inferior busca binária, 1-99
  risk_high: number,                // Limite superior busca binária, 1-99
  risk_current: number,             // Valor atual testado, 1-99
  risk_step: number,                // Etapa atual do questionário, 1-4
  risk_answers: boolean[],          // Respostas SIM/NÃO das perguntas
  
  // Resultado final
  risk_number: number,              // Risk Number final, 1-99
  risk_profile: string,             // "conservador" | "moderado" | "arrojado"
}
```

## 9. Ajustes e Escalas Customizadas

### 9.1 Escalas de Gastos
```typescript
{
  scales: {
    moradia: number,                // Multiplicador, default 1.0
    educacao_brl: number,
    educacao_usd: number,
    saude: number,
    veiculos: number,
    lifestyle: number,
    viagens_usd: number,
  },
  
  baseline_costs: {                 // Custos base do ano 0
    moradia: number,
    educacao_brl: number,
    educacao_usd: number,
    saude: number,
    veiculos: number,
    lifestyle: number,
    viagens_usd: number,
  }
}
```

## 10. Dados Calculados/Derivados (Cache)

### 10.1 Aspirational Calculado
```typescript
{
  aspirational_inicial: number,     // Valor inicial calculado
  aspirational_growth_rate: number, // Taxa crescimento ponderada %
}
```

### 10.2 Projeções Computadas
```typescript
{
  projections: {
    df_brl: DataFrame,              // Gastos em BRL por ano
    df_usd: DataFrame,              // Gastos em USD por ano
    df_incomes: DataFrame,          // Rendas por ano
    df_pat: DataFrame,              // Patrimônio por ano
  },
  
  net_cash_series: number[],        // Fluxo caixa líquido por ano
  capital_guard_list: number[],     // Capital Guard por ano
}
```

## 11. Estado da Aplicação

### 11.1 Navegação e Estágios
```typescript
{
  stage: string,                    // "inputs" | "risk" | "results"
}
```

### 11.2 Flags de Controle
```typescript
{
  warning_no_salary: boolean,       // Mostrar aviso de salário
}
```

## 12. Schema de Banco de Dados Sugerido

### 12.1 Tabela: `usuarios`
```sql
CREATE TABLE usuarios (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  nome VARCHAR(255),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### 12.2 Tabela: `onboarding_data`
```sql
CREATE TABLE onboarding_data (
  id UUID PRIMARY KEY,
  usuario_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
  
  -- Dados profissionais
  cargo VARCHAR(255),
  setor VARCHAR(255),
  empresa VARCHAR(255),
  salario_anual DECIMAL(15,2),
  
  -- Dados pessoais
  idade_cliente INTEGER,
  idade_conjuge INTEGER,
  nao_tem_conjuge BOOLEAN DEFAULT FALSE,
  idade_aposentadoria INTEGER,
  
  -- Moradia
  bairro VARCHAR(255),
  metragem DECIMAL(10,2),
  n_funcionarios INTEGER,
  segunda_resid_mensal DECIMAL(15,2),
  
  -- Lifestyle
  n_carros INTEGER,
  estilo_vida INTEGER,
  n_viagens INTEGER,
  luxo_mensal DECIMAL(15,2),
  filantropia_anual DECIMAL(15,2),
  
  -- Rendimentos passivos
  aluguel_mensal_brl DECIMAL(15,2),
  aluguel_growth_brl DECIMAL(5,2),
  aluguel_mensal_usd DECIMAL(15,2),
  aluguel_growth_usd DECIMAL(5,2),
  dividendos_brl DECIMAL(15,2),
  divid_growth_brl DECIMAL(5,2),
  dividendos_usd DECIMAL(15,2),
  divid_growth_usd DECIMAL(5,2),
  
  -- Patrimônio
  patrimonio_inicial DECIMAL(15,2),
  
  -- Premissas
  anos_proj INTEGER,
  infl_brl_pct DECIMAL(5,2),
  infl_usd_pct DECIMAL(5,2),
  cotacao_usd DECIMAL(10,4),
  
  -- Perfil de risco
  risk_number INTEGER,
  risk_profile VARCHAR(50),
  
  -- Metadata
  stage VARCHAR(50) DEFAULT 'inputs',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(usuario_id)
);
```

### 12.3 Tabela: `filhos`
```sql
CREATE TABLE filhos (
  id UUID PRIMARY KEY,
  onboarding_id UUID REFERENCES onboarding_data(id) ON DELETE CASCADE,
  
  ordem INTEGER NOT NULL,           -- Posição no array (0-based)
  idade INTEGER NOT NULL,
  escola VARCHAR(255),
  estuda_fora BOOLEAN DEFAULT FALSE,
  
  created_at TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(onboarding_id, ordem)
);
```

### 12.4 Tabela: `patrimonios_iliquidos`
```sql
CREATE TABLE patrimonios_iliquidos (
  id UUID PRIMARY KEY,
  onboarding_id UUID REFERENCES onboarding_data(id) ON DELETE CASCADE,
  
  ordem INTEGER NOT NULL,           -- Posição no array (0-based)
  valor_brl DECIMAL(15,2),
  growth_brl DECIMAL(5,2),
  valor_usd DECIMAL(15,2),
  growth_usd DECIMAL(5,2),
  
  created_at TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(onboarding_id, ordem)
);
```

### 12.5 Tabela: `ajustes_customizados`
```sql
CREATE TABLE ajustes_customizados (
  id UUID PRIMARY KEY,
  onboarding_id UUID REFERENCES onboarding_data(id) ON DELETE CASCADE,
  
  categoria VARCHAR(100) NOT NULL,  -- "moradia", "educacao_brl", etc
  scale DECIMAL(10,4),              -- Multiplicador
  baseline_cost DECIMAL(15,2),      -- Custo base
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(onboarding_id, categoria)
);
```

### 12.6 Tabela: `projecoes_cache` (opcional)
```sql
CREATE TABLE projecoes_cache (
  id UUID PRIMARY KEY,
  onboarding_id UUID REFERENCES onboarding_data(id) ON DELETE CASCADE,
  
  ano INTEGER NOT NULL,
  
  -- Despesas
  gastos_brl DECIMAL(15,2),
  gastos_usd DECIMAL(15,2),
  
  -- Rendas
  renda_total DECIMAL(15,2),
  
  -- Patrimônio
  capital_guard DECIMAL(15,2),
  endowment DECIMAL(15,2),
  aspirational DECIMAL(15,2),
  patrimonio_total DECIMAL(15,2),
  
  -- Fluxos
  net_cash DECIMAL(15,2),
  
  created_at TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(onboarding_id, ano)
);
```

## 13. Exemplo de Documento JSON Completo

```json
{
  "usuario_id": "uuid-do-usuario",
  
  "dados_profissionais": {
    "cargo": "CEO",
    "setor": "Tecnologia",
    "empresa": "Tech Corp",
    "salario_anual": 500000.00
  },
  
  "dados_pessoais": {
    "idade_cliente": 45,
    "idade_conjuge": 42,
    "nao_tem_conjuge": false,
    "idade_aposentadoria": 65
  },
  
  "familia": {
    "n_filhos": 2,
    "filhos": [
      {
        "ordem": 0,
        "idade": 10,
        "escola": "Beacon School",
        "estuda_fora": false
      },
      {
        "ordem": 1,
        "idade": 8,
        "escola": "Escola Alef Peretz",
        "estuda_fora": true
      }
    ]
  },
  
  "moradia": {
    "bairro": "Jardins",
    "metragem": 300.0,
    "n_funcionarios": 2,
    "segunda_resid_mensal": 5000.0
  },
  
  "lifestyle": {
    "n_carros": 2,
    "estilo_vida": 2,
    "n_viagens": 4,
    "luxo_mensal": 10000.0,
    "filantropia_anual": 50000.0
  },
  
  "rendimentos_passivos": {
    "alugueis": {
      "brl": {
        "mensal": 20000.0,
        "crescimento_pct": 5.0
      },
      "usd": {
        "mensal": 5000.0,
        "crescimento_pct": 3.0
      }
    },
    "dividendos": {
      "brl": {
        "anual": 100000.0,
        "crescimento_pct": 5.0
      },
      "usd": {
        "anual": 20000.0,
        "crescimento_pct": 3.0
      }
    }
  },
  
  "patrimonios_iliquidos": {
    "has_iliquido": true,
    "n_iliquidos": 2,
    "ativos": [
      {
        "ordem": 0,
        "valor_brl": 1000000.0,
        "growth_brl": 10.0,
        "valor_usd": 200000.0,
        "growth_usd": 5.0
      },
      {
        "ordem": 1,
        "valor_brl": 500000.0,
        "growth_brl": 8.0,
        "valor_usd": 100000.0,
        "growth_usd": 5.0
      }
    ]
  },
  
  "patrimonio_financeiro": {
    "patrimonio_inicial": 5000000.0
  },
  
  "premissas": {
    "anos_proj": 20,
    "infl_brl_pct": 4.5,
    "infl_usd_pct": 2.5,
    "cotacao_usd": 5.0
  },
  
  "perfil_risco": {
    "risk_number": 55,
    "risk_profile": "moderado",
    "historico_questionario": {
      "risk_answers": [true, false, true],
      "comportamento": "Manteria a posição",
      "horizonte": "Mais de 5 anos",
      "objetivo": "Crescimento de capital"
    }
  },
  
  "ajustes_customizados": {
    "scales": {
      "moradia": 1.0,
      "educacao_brl": 1.0,
      "educacao_usd": 1.0,
      "saude": 1.0,
      "veiculos": 1.0,
      "lifestyle": 1.0,
      "viagens_usd": 1.0
    },
    "baseline_costs": {
      "moradia": 180000.0,
      "educacao_brl": 120000.0,
      "educacao_usd": 50000.0,
      "saude": 85000.0,
      "veiculos": 100000.0,
      "lifestyle": 98000.0,
      "viagens_usd": 60000.0
    }
  },
  
  "calculados": {
    "aspirational_inicial": 2500000.0,
    "aspirational_growth_rate": 7.8
  },
  
  "metadata": {
    "stage": "results",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T11:45:00Z",
    "versao_calculo": "1.0"
  }
}
```

## 14. Considerações de Implementação

### 14.1 Validações Necessárias
- Todos os valores numéricos devem ser >= 0
- Arrays paralelos devem ter mesmo tamanho
- Risk number deve estar entre 1-99
- Datas/idades devem ser válidas
- Somas de percentuais de alocação devem = 100%

### 14.2 Campos Opcionais vs Obrigatórios

**Obrigatórios:**
- Dados profissionais (cargo, setor, empresa)
- Idade do cliente
- Patrimônio inicial
- Premissas macroeconômicas

**Opcionais (podem ser 0 ou vazios):**
- Idade do cônjuge (se nao_tem_conjuge = true)
- Número de filhos
- Rendimentos passivos
- Patrimônios ilíquidos
- Segunda residência
- Luxo
- Filantropia

### 14.3 Índices Recomendados
```sql
-- Performance queries
CREATE INDEX idx_onboarding_usuario ON onboarding_data(usuario_id);
CREATE INDEX idx_filhos_onboarding ON filhos(onboarding_id);
CREATE INDEX idx_iliquidos_onboarding ON patrimonios_iliquidos(onboarding_id);
CREATE INDEX idx_ajustes_onboarding ON ajustes_customizados(onboarding_id);
CREATE INDEX idx_cache_onboarding ON projecoes_cache(onboarding_id);

-- Ordenação
CREATE INDEX idx_filhos_ordem ON filhos(onboarding_id, ordem);
CREATE INDEX idx_iliquidos_ordem ON patrimonios_iliquidos(onboarding_id, ordem);
CREATE INDEX idx_cache_ano ON projecoes_cache(onboarding_id, ano);
```