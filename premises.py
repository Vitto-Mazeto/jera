"""
Premises data for Jera Onboarding Financial Simulator
"""

PREMISES = {
    "educacao": {
        "escolas": [
            # Escolas já definidas no código principal
            # Outras escolas podem ser adicionadas aqui
            {"nome": "Escola Exemplo", "idadeMin": 2, "idadeMax": 5, "precoAnual": 50000.0},
            {"nome": "Escola Exemplo", "idadeMin": 6, "idadeMax": 14, "precoAnual": 80000.0},
            {"nome": "Escola Exemplo", "idadeMin": 15, "idadeMax": 17, "precoAnual": 100000.0},
        ],
        "faculdade": {
            "brasil": 60000.0,  # Custo anual de faculdade no Brasil
            "exteriorUSD": 50000.0,  # Custo anual de faculdade no exterior em USD
        }
    },
    "saude": {
        "gastoAnualPorFaixa": [
            {"faixa": "0–18", "gasto": 15000.0},
            {"faixa": "19–35", "gasto": 20000.0},
            {"faixa": "36–50", "gasto": 30000.0},
            {"faixa": "51–65", "gasto": 45000.0},
            {"faixa": "66+", "gasto": 60000.0},
        ]
    },
    "moradia": {
        "bairros": [
            {"nome": "Jardins", "precoM2": 15000.0},
            {"nome": "Itaim Bibi", "precoM2": 12000.0},
            {"nome": "Vila Olimpia", "precoM2": 10000.0},
            {"nome": "Pinheiros", "precoM2": 9000.0},
            {"nome": "Moema", "precoM2": 8500.0},
            {"nome": "Brooklin", "precoM2": 8000.0},
            {"nome": "Alto de Pinheiros", "precoM2": 11000.0},
        ],
        "funcionariosPor1000m2": 2.0,  # Número de funcionários por 1000m²
        "custoFuncionario": 60000.0,  # Custo anual por funcionário
        "custoBasePorPessoa": 30000.0,  # Custo base anual por pessoa na residência
    },
    "veiculos": {
        "gastoAnualPorVeiculo": 50000.0,  # Gasto anual por veículo (manutenção, seguro, etc)
    },
    "lifestyle": {
        "viagensInternacionais": {
            "custoUSD": {
                "casal": 10000.0,  # Custo para o casal por viagem
                "filho0a6": 2000.0,  # Custo adicional por filho de 0-6 anos
                "filho7a12": 3000.0,  # Custo adicional por filho de 7-12 anos
                "filho13mais": 5000.0,  # Custo adicional por filho de 13+ anos
            }
        },
        "estilosDeVida": {
            1: {"nome": "Conservador", "casal": 20000.0, "porFilho": 5000.0},
            2: {"nome": "Moderado", "casal": 50000.0, "porFilho": 12000.0},
            3: {"nome": "Agressivo", "casal": 100000.0, "porFilho": 25000.0},
        }
    }
}
