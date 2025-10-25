"""
Jera Onboarding Financial Simulator
----------------------------------

This Streamlit application provides a linear onboarding experience for
family‑office clients of Jera Capital.  Users enter personal and
financial information, and the app automatically calls an external
webhook to estimate salary, assesses risk tolerance through a
questionnaire, and generates year‑by‑year projections of income,
expenses and patrimony.  The projections separate expenses in BRL and
USD and allow users to specify their aspirational bucket directly.

The entire application resides in a single file (``jera_onboarding.py``)
and embeds all necessary data, including the Jera logo and cost
premises.  Run it with ``streamlit run jera_onboarding.py``.
"""

import base64
import math
from io import BytesIO
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

from premises import PREMISES

# -----------------------------------------------------------------------------
# Extend the list of schools for education cost projections
#
# Several new schools were requested by the user.  Each school is represented
# by one or more entries specifying the age range (idadeMin to idadeMax) and
# the annual cost (precoAnual).  We append these entries to the existing
# list of schools in PREMISES["educacao"]["escolas"].  Since the UI sorts
# school names alphabetically when displaying options, we don't need to
# maintain order here—alphabetical ordering will be applied when building
# the selectbox.

_new_school_entries = [
    {"nome": "Beacon School", "idadeMin": 2, "idadeMax": 4, "precoAnual": 78000.0},
    {"nome": "Beacon School", "idadeMin": 5, "idadeMax": 14, "precoAnual": 118300.0},
    {"nome": "Beacon School", "idadeMin": 15, "idadeMax": 17, "precoAnual": 152100.0},
    {"nome": "Colégio bandeirantes", "idadeMin": 12, "idadeMax": 17, "precoAnual": 77168.0},
    {"nome": "Colégio santa cruz", "idadeMin": 12, "idadeMax": 17, "precoAnual": 87360.0},
    {"nome": "Escola Alef Peretz", "idadeMin": 2, "idadeMax": 17, "precoAnual": 89609.0},
    {"nome": "Escola Beit Yaacov", "idadeMin": 2, "idadeMax": 4, "precoAnual": 52996.0},
    {"nome": "Escola Beit Yaacov", "idadeMin": 5, "idadeMax": 14, "precoAnual": 115206.0},
    {"nome": "Escola Beit Yaacov", "idadeMin": 15, "idadeMax": 17, "precoAnual": 140093.0},
]

# Append new schools only if they do not already exist.  We check for an
# existing entry with the same name and age range to avoid duplicate
# definitions in case the code is executed multiple times (e.g. in a
# development environment where modules may be reloaded).
existing_entries = {(e["nome"], e["idadeMin"], e["idadeMax"]) for e in PREMISES["educacao"]["escolas"]}
for entry in _new_school_entries:
    key = (entry["nome"], entry["idadeMin"], entry["idadeMax"])
    if key not in existing_entries:
        PREMISES["educacao"]["escolas"].append(entry)

# -----------------------------------------------------------------------------
# Formatting helpers
# -----------------------------------------------------------------------------

def format_brl_value(x: float) -> str:
    """Format a numeric value into Brazilian currency format.

    Uses a dot as the thousands separator and a comma for decimals.  Negative
    values will include the minus sign before the currency symbol.

    Parameters
    ----------
    x : float
        Value to format.

    Returns
    -------
    str
        Formatted string with "R$ " prefix.
    """
    try:
        # Handle NaN gracefully
        if x is None or (isinstance(x, float) and (x != x)):
            return "R$ 0,00"
        sign = "-" if x < 0 else ""
        x = abs(float(x))
        formatted = f"{x:,.2f}"
        integer_part, decimal_part = formatted.split(".")
        integer_part = integer_part.replace(",", ".")
        return f"{sign}R$ {integer_part},{decimal_part}"
    except Exception:
        return f"R$ {x}"


def format_usd_value(x: float) -> str:
    """Format a numeric value into USD currency format.

    Uses a dot as the thousands separator and a comma for decimals.  Negative
    values will include the minus sign before the currency symbol.

    Parameters
    ----------
    x : float
        Value to format.

    Returns
    -------
    str
        Formatted string with "$ " prefix.
    """
    try:
        if x is None or (isinstance(x, float) and (x != x)):
            return "$ 0,00"
        sign = "-" if x < 0 else ""
        x = abs(float(x))
        formatted = f"{x:,.2f}"
        integer_part, decimal_part = formatted.split(".")
        integer_part = integer_part.replace(",", ".")
        return f"{sign}$ {integer_part},{decimal_part}"
    except Exception:
        return f"$ {x}"

# -----------------------------------------------------------------------------
# Embedded assets and constants
# -----------------------------------------------------------------------------

# Base64 encoded Jera logo (same as in ``jera_webapp.py``).  Only the
# beginning is shown here for brevity; the full string is embedded so
# the app remains self‑contained.
JERA_LOGO_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAMgAAADICAIAAAAiOjnJAAAAAXNSR0IArs4c6QAAAERlWElmTU0AKgAAAAgA"
    "AYdpAAQAAAABAAAAIIdpAAQAAAABAAAAIgAAAAABAAOgAQADAAAAAQABAACgAgAEAAAAAQAAAMygAwAEAAAA"
    "AQAAAMgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
)

# Small decorative photo encoded in base64 (JPEG).
# This image evokes Jera's colour palette in an abstract style and is
# displayed on the "Dados" tab.  It is intentionally small (about 300px
# wide) so that the encoded string remains manageable.  The image was
# generated and resized offline; you can replace it by encoding your own
# JPEG and splitting it into roughly 80‑character chunks.
JERA_PHOTO_SMALL_B64 = (
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYa"
    "HSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgo"
    "KCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAHCASwDASIAAhEBAxEB/8QA"
    "HwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIh"
    "MUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVW"
    "V1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXG"
    "x8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQF"
    "BgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAV"
    "YnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOE"
    "hYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq"
    "8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD5rpaSlrtOEKWkpaBC0UUUxC0tJS0CFFOFIKUUxCilFIKWmSKK"
    "cKQUopiFpaSlpkhS0AUtMQU4U2nCgQopwpopwpkscKcKaKeKZDHClFIKcKCWOFOFNFOFIhjhTxTRThQQ"
    "xafTRTqCWKKdTRTh1oJY4DilFJS0EhS5pKSgDjhSim0orA94WlpKUUCFoFFLTEKKWkpaBCinCminUyRa"
    "UUgpRTELS0UUyRRSikFO6fWmIKWkFLTEKKUUClFBIopwpBThTJYopwpBSimSxwpwpBThQSxwpwpop46"
    "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"
)

# -----------------------------------------------------------------------------
# Embedded decorative image for the Jera photo
#
# The user requested that an image from Jera Capital be displayed in the
# application.  Since direct downloading of the LinkedIn/Google image is
# prohibited inside this environment, a custom illustration was generated
# programmatically using an image generation model.  The image evokes the
# brand colours of Jera (deep blue and green) with flowing abstract waves
# suggesting innovation and finance.  The JPEG was resized and encoded
# directly into a base64 string so that it can be embedded without any
# external dependencies.  Should you wish to replace this image with a
# different one, simply update the string below with your own JPEG encoded
# using base64.
JERA_PHOTO_B64 = (
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYa"
    "HSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgo"
    "KCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAOEAlgDASIAAhEBAxEB/8QA"
    "HwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIh"
    "MUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVW"
    "V1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXG"
    "x8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQF"
    "BgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAV"
    "YnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOE"
    "hYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq"
    "8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD5rooorsOEWiiigApaTNLTEFFFH0oAKWiigApaSimIWlpOKPxo"
    "Adziik/GloEFLSUopiFopKXtQIXrQKKWgApaSlFMQClpO1KKBAKUUnalpiAUoo/lR1oAWiiimIKKKWgAA"
    "zR360vQZ7mk7UxC0tJS0CD60tJS0AFLRSimIBS0UooEFOpBS0EiilpKWmIUUtIKWgQopaSlFAhRSikHW"
    "lpEi0tFLQIKUUClFBIopRSUooELS0lKKBCilpBS0CCl7UUooEFLSCloEAp+OaQUtBLClFJR9aBC0UlFA"
    "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"
)

# Standard portfolios for each risk category
# New portfolio definitions for each risk profile.  The client's endowment is allocated
# 70% to domestic assets and 30% to international assets, regardless of the profile.  Each
# segment has its own strategic distribution across asset classes and expected return
# and volatility (annualized).  These values are used to compute deterministic
# endowment growth (no Monte Carlo) and to present the recommended portfolio.
PORTFOLIOS: Dict[str, Dict[str, Dict[str, object]]] = {
    "conservador": {
        "dom": {
            "classes": {
                "Liquidez CDI": 37.50,
                "RF BR Crédito Pós-Fixado": 17.50,
                "RF BR Pré-Fixado": 0.00,
                "RF BR Inflação": 10.00,
                "Retorno Absoluto BR": 15.00,
                "Renda Variável BR": 10.00,
                "Private Equity BR": 7.50,
                "Real Estate BR": 2.50,
            },
            "expected_return": 0.174,
            "vol": 0.034,
        },
        "intl": {
            "classes": {
                "Cash Equivalent": 31.50,
                "RF Intl Pré-Fixado": 13.00,
                "RF Intl Inflação": 3.25,
                "RF Intl Crédito Privado": 7.25,
                "Retorno Absoluto Intl": 13.00,
                "Renda Variável Intl": 16.25,
                "Private Equity Intl": 8.50,
                "Real Estate Intl": 4.00,
                "Commodities": 3.25,
            },
            "expected_return": 0.068,
            "vol": 0.039,
        },
    },
    "moderado": {
        "dom": {
            "classes": {
                "Liquidez CDI": 22.50,
                "RF BR Crédito Pós-Fixado": 17.50,
                "RF BR Pré-Fixado": 0.00,
                "RF BR Inflação": 12.50,
                "Retorno Absoluto BR": 12.50,
                "Renda Variável BR": 15.00,
                "Private Equity BR": 15.00,
                "Real Estate BR": 5.00,
            },
            "expected_return": 0.188,
            "vol": 0.049,
        },
        "intl": {
            "classes": {
                "Cash Equivalent": 12.00,
                "RF Intl Pré-Fixado": 14.00,
                "RF Intl Inflação": 3.50,
                "RF Intl Crédito Privado": 8.88,
                "Retorno Absoluto Intl": 14.00,
                "Renda Variável Intl": 17.50,
                "Private Equity Intl": 21.25,
                "Real Estate Intl": 5.38,
                "Commodities": 3.50,
            },
            "expected_return": 0.081,
            "vol": 0.045,
        },
    },
    "arrojado": {
        "dom": {
            "classes": {
                "Liquidez CDI": 10.00,
                "RF BR Crédito Pós-Fixado": 14.50,
                "RF BR Pré-Fixado": 0.00,
                "RF BR Inflação": 15.00,
                "Retorno Absoluto BR": 10.00,
                "Renda Variável BR": 22.50,
                "Private Equity BR": 21.00,
                "Real Estate BR": 7.00,
            },
            "expected_return": 0.202,
            "vol": 0.068,
        },
        "intl": {
            "classes": {
                "Cash Equivalent": 4.25,
                "RF Intl Pré-Fixado": 8.50,
                "RF Intl Inflação": 2.13,
                "RF Intl Crédito Privado": 7.44,
                "Retorno Absoluto Intl": 8.50,
                "Renda Variável Intl": 25.63,
                "Private Equity Intl": 36.13,
                "Real Estate Intl": 5.31,
                "Commodities": 2.13,
            },
            "expected_return": 0.095,
            "vol": 0.056,
        },
    },
}


def estimate_salary(cargo: str, setor: str, empresa: str) -> float:
    """Estimate annual salary using an external n8n webhook.

    Returns NaN if the call fails or no salary is found.  Timeout is set
    to avoid hanging.  The webhook should return HTML with the salary
    embedded in a ``srcdoc="..."`` attribute.
    """
    try:
        payload = {"cargo": cargo, "setor": setor, "empresa": empresa}
        resp = requests.post(
            "http://localhost:5678/webhook-test/estimar-salário",
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()
        import re

        m = re.search(r'srcdoc="([\d\.]+)"', resp.text)
        if not m:
            return float("nan")
        return float(m.group(1))
    except Exception:
        return float("nan")


def risk_assessment(answers: List[int]) -> int:
    """Scale a raw questionnaire score (sum of answers) into a 1–99 risk number."""
    if not answers:
        return 1
    raw_score = sum(answers)
    min_raw, max_raw = 5, 25
    scaled = (raw_score - min_raw) / (max_raw - min_raw)
    number = int(scaled * 98) + 1
    return max(1, min(99, number))


def profile_from_risk_number(number: int) -> str:
    """Map a risk number to a portfolio profile."""
    if number <= 30:
        return "conservador"
    elif number <= 60:
        return "moderado"
    else:
        return "arrojado"


def simular_monte_carlo(
    endowment_inicial: float,
    carteira: Dict[str, Dict[str, float]],
    anos: int,
    n_sim: int = 1000,
    seed: int = 42,
) -> List[float]:
    """Simulate the endowment growth using Monte Carlo and return median values."""
    np.random.seed(seed)
    weights = np.array([v["peso"] for v in carteira.values()])
    means = np.array([v["media"] for v in carteira.values()])
    vols = np.array([v["vol"] for v in carteira.values()])
    returns = np.random.normal(means, vols, size=(n_sim, anos, len(weights)))
    weighted = np.sum(returns * weights, axis=2)
    values = np.full((n_sim,), endowment_inicial, dtype=float)
    medians = []
    for year in range(anos):
        values = values * (1 + weighted[:, year])
        medians.append(float(np.median(values)))
    return medians


def health_cost_for_age(age: int) -> float:
    """Return healthcare cost for a given age from PREMISES; extrapolate for older ages."""
    ranges = PREMISES.get("saude", {}).get("gastoAnualPorFaixa", [])
    if not ranges:
        return 0.0

    last_cost = ranges[-1].get("gasto", 0)

    for entry in ranges:
        faixa = entry.get("faixa", "")
        gasto = entry.get("gasto", 0)

        try:
            if "–" in faixa:
                min_age, max_age = faixa.split("–")
                min_age = int(min_age.strip())
                max_age = int(max_age.strip())
            elif "+" in faixa:
                min_age = int(faixa.replace("+", "").strip())
                max_age = 200
            else:
                min_age = max_age = int(faixa.strip())

            if min_age <= age <= max_age:
                return float(gasto)
        except (ValueError, AttributeError):
            continue

    return float(last_cost)


def compute_costs_and_incomes(
    idade_cliente: int,
    idade_conjuge: int,
    idades_filhos: List[int],
    escolas_filhos: List[str],
    estudam_fora: List[bool],
    bairro: str,
    metragem: float,
    n_carros: int,
    estilo_vida: int,
    n_viagens: int,
    n_funcionarios: int,
    luxo_mensal: float,
    # Monthly cost of second residence (BRL).  Added as a separate
    # recurring expense similar to luxury spending.  This parameter
    # must precede all parameters with defaults; it is provided
    # explicitly when the function is called.
    segunda_resid_mensal: float,
    # New income parameters
    aluguel_mensal_brl: float,
    aluguel_growth_brl: float,
    aluguel_mensal_usd: float,
    aluguel_growth_usd: float,
    dividendos_brl: float,
    divid_growth_brl: float,
    dividendos_usd: float,
    divid_growth_usd: float,
    # Old extra parameters removed: renda_extra_mensal, dividendos_anuais, taxa_crescimento_dividendo
    patrimonio_inicial: float,
    filantropia_anual: float,
    anos_proj: int,
    infl_brl_pct: float,
    infl_usd_pct: float,
    cotacao_usd: float,
    salario_anual0: float,
    idade_aposentadoria: int,
    # When True, indicates the user has no spouse.  Spouse age is
    # ignored in projections and only one adult is counted for base
    # expenses.  Default is False (assume spouse present when age > 0).
    no_conjuge: bool = False,
    scales: Dict[str, float] | None = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, float]:
    """Compute projected expenses (BRL & USD) and incomes.

    Returns
    -------
    df_brl : DataFrame
        Expenses in BRL by category and total.
    df_usd : DataFrame
        Expenses in USD by category and total.
    df_incomes : DataFrame
        Incomes (salary, dividends, extras, total) by year.
    capital_guard : float
        Amount allocated to the capital guard (sum of first 4 years of expenses minus first year's income).
    """
    infl_brl = 1 + infl_brl_pct / 100.0
    infl_usd = 1 + infl_usd_pct / 100.0

    # Precompute annual USD/BRL exchange rates.  The initial rate comes
    # from user input and each subsequent year is adjusted by the
    # relative inflation: BRL inflation divided by USD inflation.  This
    # mirrors the requested formula: nova_cotacao = cotacao_anterior *
    # (1 + infl_brl) / (1 + infl_usd).
    cotacoes: List[float] = [cotacao_usd]
    for _ in range(anos_proj - 1):
        cotacoes.append(cotacoes[-1] * (infl_brl) / (infl_usd))

    anos = list(range(anos_proj))

    # Validações e carregamento de dados de moradia
    try:
        bairros = {b["nome"]: b["precoM2"] for b in PREMISES.get("moradia", {}).get("bairros", [])
                   if "nome" in b and "precoM2" in b}
    except (KeyError, TypeError):
        bairros = {}
    preco_m2 = bairros.get(bairro, 0)

    func_por_m2 = PREMISES.get("moradia", {}).get("funcionariosPor1000m2", 0) / 1000.0
    base_func = max(1, math.ceil(metragem * func_por_m2))
    custo_func = PREMISES.get("moradia", {}).get("custoFuncionario", 0)
    custo_base_pessoa = PREMISES.get("moradia", {}).get("custoBasePorPessoa", 0)

    # Validações e carregamento de dados de educação
    escolas_map: Dict[str, List[Tuple[int, int, float]]] = {}
    try:
        for esc in PREMISES.get("educacao", {}).get("escolas", []):
            if all(k in esc for k in ["nome", "idadeMin", "idadeMax", "precoAnual"]):
                escolas_map.setdefault(esc["nome"], []).append(
                    (int(esc["idadeMin"]), int(esc["idadeMax"]), float(esc["precoAnual"]))
                )
    except (KeyError, ValueError, TypeError):
        pass

    faculdade_br = PREMISES.get("educacao", {}).get("faculdade", {}).get("brasil", 0)
    faculdade_ext = PREMISES.get("educacao", {}).get("faculdade", {}).get("exteriorUSD", 0)

    # Validações e carregamento de dados de lifestyle
    viagem_custos = PREMISES.get("lifestyle", {}).get("viagensInternacionais", {}).get("custoUSD", {})
    if not isinstance(viagem_custos, dict):
        viagem_custos = {"casal": 10000.0, "filho0a6": 2000.0, "filho7a12": 3000.0, "filho13mais": 5000.0}

    estilos = PREMISES.get("lifestyle", {}).get("estilosDeVida", {})
    if not estilos:
        estilos = {1: {"casal": 20000.0, "porFilho": 5000.0},
                   2: {"casal": 50000.0, "porFilho": 12000.0},
                   3: {"casal": 100000.0, "porFilho": 25000.0}}

    # Pega estilo configurado ou usa moderado (2) como padrão
    estilo_cfg = estilos.get(estilo_vida, estilos.get(2, estilos.get(1, {})))


    brl_rows = []
    # We'll store only USD denominated expenses: overseas education and international trips.
    usd_only_rows = []
    incomes_rows = []

    salario = salario_anual0

    # Rastreia veículos adicionais para cada filho ao longo dos anos. Cada filho recebe
    # um carro ao completar 18 anos (com custo de compra de 200k) e mantém o carro
    # até completar 26 anos. Após 26, o carro é removido da contagem. O número de
    # carros informado inicialmente em `n_carros` refere‑se aos veículos do casal.
    veiculos_adicionais = [0] * len(idades_filhos)
    for ano in anos:
        infl_factor_brl = infl_brl ** ano
        infl_factor_usd = infl_usd ** ano
        # Determine current exchange rate for this year
        cot_curr = cotacoes[ano] if ano < len(cotacoes) else cotacoes[-1]
        idade_cli = idade_cliente + ano
        # Compute spouse age for this year.  If the user has indicated
        # no spouse, use zero to avoid adding health costs and extra base
        # expenses.  Otherwise increment the provided age.
        idade_conj = (idade_conjuge + ano) if not no_conjuge else 0
        idades_f = [age + ano for age in idades_filhos]
        # Moradia
        valor_imovel = preco_m2 * metragem
        custo_manut = valor_imovel * 0.02 * infl_factor_brl
        # Combine cost of base employees and user-specified employees (each extra costs 48k/year)
        custo_empregados = (base_func * custo_func + n_funcionarios * 48000) * infl_factor_brl
        # Compute number of occupants: one adult client plus spouse (if present) plus children.
        occupants = 1 + (0 if no_conjuge else 1) + len(idades_filhos)
        custo_base = occupants * custo_base_pessoa * infl_factor_brl
        custo_moradia_brl = custo_manut + custo_empregados + custo_base
        # Educação & mesadas
        custo_educ_brl = 0.0
        custo_educ_usd = 0.0
        custo_mesadas_brl = 0.0
        for idx, idade_f in enumerate(idades_f):
            esc_name = escolas_filhos[idx]
            if idade_f <= 17 and esc_name:
                for idadeMin, idadeMax, preco in escolas_map.get(esc_name, []):
                    if idadeMin <= idade_f <= idadeMax:
                        custo_educ_brl += preco * infl_factor_brl
                        break
            if 18 <= idade_f <= 21:
                if estudam_fora[idx]:
                    custo_educ_usd += faculdade_ext * infl_factor_usd
                else:
                    custo_educ_brl += faculdade_br * infl_factor_brl
            if 10 <= idade_f <= 13:
                custo_mesadas_brl += 500 * 12 * infl_factor_brl
            elif 14 <= idade_f <= 17:
                custo_mesadas_brl += 1500 * 12 * infl_factor_brl
            elif 18 <= idade_f <= 21:
                custo_mesadas_brl += 2500 * 12 * infl_factor_brl
        # Saúde
        custo_saude_brl = (
            health_cost_for_age(idade_cli)
            + (0 if no_conjuge else health_cost_for_age(idade_conj))
            + sum(health_cost_for_age(age) for age in idades_f if age < 26)
        ) * infl_factor_brl
        # Base health insurance cost of 10k per person per year.  Adjust number of people
        # according to presence of spouse.
        custo_saude_brl += occupants * 10000 * infl_factor_brl
        # Veículos
        # Para cada filho que completa 18 anos, concedemos um carro extra com um custo único
        # de compra de 200 mil reais (corrigido pela inflação BRL). Esse carro permanece na
        # frota até o filho completar 26 anos; após isso ele é removido. O custo anual por
        # veículo é aplicado tanto aos carros do casal quanto aos veículos extras de filhos.
        custo_compra_veic = 0.0
        for idx, idade_f in enumerate(idades_f):
            # Remove carro de filho que ultrapassou 25 anos (>=26)
            if idade_f >= 26 and veiculos_adicionais[idx] == 1:
                veiculos_adicionais[idx] = 0
            # Se o filho completar exatamente 18 neste ano e ainda não possui carro, compra um carro
            if idade_f == 18 and veiculos_adicionais[idx] == 0:
                veiculos_adicionais[idx] = 1
                custo_compra_veic += 200_000 * infl_factor_brl
        total_carros = n_carros + sum(veiculos_adicionais)
        gasto_veiculo = PREMISES.get("veiculos", {}).get("gastoAnualPorVeiculo", 0)
        custo_veic_brl = total_carros * gasto_veiculo * infl_factor_brl + custo_compra_veic
        # Lifestyle (base + mesadas)
        estilo_casal = estilo_cfg.get("casal", 0.0)
        estilo_filhos = estilo_cfg.get("porFilho", 0.0) * len(idades_filhos)
        custo_lifestyle_brl = (estilo_casal + estilo_filhos) * infl_factor_brl + custo_mesadas_brl
        # Viagens internacionais (USD)
        custo_viagens_usd = 0.0
        for _ in range(n_viagens):
            trip = viagem_custos["casal"]
            for idade_f in idades_f:
                if idade_f <= 6:
                    trip += viagem_custos["filho0a6"]
                elif 7 <= idade_f <= 12:
                    trip += viagem_custos["filho7a12"]
                else:
                    trip += viagem_custos["filho13mais"]
            custo_viagens_usd += trip * infl_factor_usd
        # Luxury & philanthropy
        luxo_brl = luxo_mensal * 12.0 * infl_factor_brl
        # Second residence expense (monthly) converted to annual and inflated
        seg_resid_brl = segunda_resid_mensal * 12.0 * infl_factor_brl
        fil_brl = filantropia_anual * infl_factor_brl
        # Apply scaling factors if provided (scales dict may contain multipliers for certain categories)
        sc = scales or {}
        custo_moradia_brl *= sc.get("moradia", 1.0)
        custo_educ_brl *= sc.get("educacao_brl", 1.0)
        custo_educ_usd *= sc.get("educacao_usd", 1.0)
        custo_saude_brl *= sc.get("saude", 1.0)
        custo_veic_brl *= sc.get("veiculos", 1.0)
        custo_lifestyle_brl *= sc.get("lifestyle", 1.0)
        custo_viagens_usd *= sc.get("viagens_usd", 1.0)
        # Totals BRL and USD
        # Education total in BRL includes overseas education converted from USD.
        # Use the dynamic exchange rate (cot_curr) for the current year rather
        # than the initial fixed rate.  This ensures that the BRL value of
        # USD‑denominated education expenses grows according to the inflation
        # differential formula.
        custo_educ_total_brl = custo_educ_brl + custo_educ_usd * cot_curr
        total_brl = (
            custo_moradia_brl
            + custo_educ_total_brl
            + custo_saude_brl
            + custo_veic_brl
            + custo_lifestyle_brl
            + seg_resid_brl
            + luxo_brl
            + fil_brl
        ) + (custo_viagens_usd * cot_curr)
        # total_usd is simply the sum of USD denominated expenses
        total_usd = custo_educ_usd + custo_viagens_usd
        brl_rows.append([
            ano + 1,
            custo_moradia_brl,
            custo_educ_total_brl,
            custo_saude_brl,
            custo_veic_brl,
            custo_lifestyle_brl,
            custo_viagens_usd * cot_curr,
            seg_resid_brl,
            luxo_brl,
            fil_brl,
            total_brl,
        ])
        # Append USD expenses only for categories that are actually denominated in USD
        usd_only_rows.append([
            ano + 1,
            custo_educ_usd,
            custo_viagens_usd,
            custo_educ_usd + custo_viagens_usd,
        ])
        # Income
        sal = salario if (idade_cliente + ano) < idade_aposentadoria else 0.0
        # Rental income: monthly values converted to annual and grown by respective rates.
        # Convert the USD portion using the dynamic exchange rate (cot_curr) for this year.
        aluguel_brl = aluguel_mensal_brl * 12 * ((1 + aluguel_growth_brl / 100.0) ** ano)
        aluguel_usd_brl = aluguel_mensal_usd * 12 * ((1 + aluguel_growth_usd / 100.0) ** ano) * cot_curr
        # Dividend income: annual values grown by respective rates.  Convert USD dividends
        # using the dynamic exchange rate (cot_curr) for consistency with expenses.
        dividendos_brl_ano = dividendos_brl * ((1 + divid_growth_brl / 100.0) ** ano)
        dividendos_usd_brl_ano = dividendos_usd * ((1 + divid_growth_usd / 100.0) ** ano) * cot_curr
        total_renda = sal + aluguel_brl + aluguel_usd_brl + dividendos_brl_ano + dividendos_usd_brl_ano
        incomes_rows.append([
            ano + 1,
            sal,
            aluguel_brl,
            aluguel_usd_brl,
            dividendos_brl_ano,
            dividendos_usd_brl_ano,
            total_renda,
        ])
        # Update salary for next year
        salario = salario * infl_brl
    # Create DataFrames
    df_brl = pd.DataFrame(
        brl_rows,
        columns=[
            "Ano",
            "Moradia (R$)",
            "Educação (R$)",
            "Saúde (R$)",
            "Veículos (R$)",
            "Lifestyle (R$)",
            "Viagens Internacionais (R$)",
            "Segunda Residência (R$)",
            "Ativos de Luxo (R$)",
            "Filantropia (R$)",
            "Total (R$)",
        ],
    )
    # Only include USD categories for expenses actually denominated in USD: travel and overseas education
    # Build USD DataFrame from the collected usd_only_rows
    df_usd = pd.DataFrame(
        usd_only_rows,
        columns=["Ano", "Educação Exterior ($)", "Viagens Internacionais ($)", "Total ($)"],
    )
    df_incomes = pd.DataFrame(
        incomes_rows,
        columns=[
            "Ano",
            "Salário (R$)",
            "Aluguéis BRL (R$)",
            "Aluguéis USD (R$)",
            "Dividendos BRL (R$)",
            "Dividendos USD (R$)",
            "Total Renda (R$)",
        ],
    )
    # Compute capital guard
    gastos_4anos = df_brl["Total (R$)"].iloc[: min(4, anos_proj)].sum()
    ganho_primeiro_ano = df_incomes["Total Renda (R$)"].iloc[0]
    diff_cg = gastos_4anos - ganho_primeiro_ano
    # If the difference between expenses of the first four years and first year income
    # is less than the expenses of the first year, set the capital guard to
    # 10% of investible patrimony; otherwise use the difference.
    primeira_despesa = df_brl["Total (R$)"].iloc[0]
    if diff_cg < primeira_despesa:
        capital_guard = patrimonio_inicial * 0.10
    else:
        capital_guard = diff_cg
    return df_brl, df_usd, df_incomes, capital_guard


def compute_patrimony_dynamic(
    patrimonio_inicial: float,
    aspirational_inicial: float,
    aspirational_growth_pct: float,
    capital_growth_pct: float,
    anos_proj: int,
    risk_profile: str,
    df_brl_totals: List[float],
    df_incomes_totals: List[float],
    infl_brl_pct: float,
    infl_usd_pct: float,
    cotacao_usd: float,
    net_cash: List[float] | None = None,
    aspirational_series: List[float] | None = None,
) -> pd.DataFrame:
    """Compute patrimony evolution with dynamic capital guard and aspirational growth.

    This version recomputes the required capital guard at the start of each
    year based on the projected expenses of the next four years and the
    current investible patrimony.  If the difference between the sum of the
    next four years' expenses and the current year's income is less than
    the expenses of the current year, the required capital guard is set to
    10% of the investible patrimony.  Otherwise it is the computed
    difference.  The endowment grows at the expected return given the
    selected risk profile, and the capital guard grows at the provided
    capital growth rate.  Net cash flows (income minus expenses) are
    allocated to the endowment.  The total patrimony recorded at the end
    of each year is the sum of the capital guard, aspirational and
    endowment.

    Parameters
    ----------
    patrimonio_inicial : float
        Investible patrimony at year 0 (i.e., capital guard + endowment at the
        start).  The initial capital guard will be computed based on this
        value.
    aspirational_inicial : float
        Initial aspirational amount.  Used when ``aspirational_series`` is not provided.
    aspirational_growth_pct : float
        Annual growth rate for aspirational (%).  Applied before rebalancing if
        ``aspirational_series`` is None.  Ignored when ``aspirational_series`` is provided.
    capital_growth_pct : float
        Annual growth rate for capital guard (%).  Applied before rebalancing.
    anos_proj : int
        Number of years to project.
    risk_profile : str
        Risk profile key to look up expected return.
    df_brl_totals : List[float]
        List of total expenses in BRL for each year.
    df_incomes_totals : List[float]
        List of total incomes in BRL for each year.
    infl_brl_pct : float
        Annual inflation rate in BRL (%), used to project FX when adjusting the
        endowment for currency effects.
    infl_usd_pct : float
        Annual inflation rate in USD (%), used to project FX when adjusting the
        endowment for currency effects.
    cotacao_usd : float
        Initial USD/BRL exchange rate.
    net_cash : list of float, optional
        Net cash flow (income minus expenses) for each year.  If None, uses zeros.
    aspirational_series : list of float, optional
        Precomputed aspirational amounts for each year.  When provided, these values
        override the growth given by ``aspirational_growth_pct`` and are used directly
        for each year of the projection.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: Ano, Capital Guard (R$), Aspirational (R$), Endowment (R$), Patrimônio Total (R$).
    """
    # Ensure net_cash length
    if net_cash is None:
        net_cash = [0.0] * anos_proj
    elif len(net_cash) < anos_proj:
        net_cash = list(net_cash) + [0.0] * (anos_proj - len(net_cash))
    # Determine expected returns for domestic and international based on risk profile
    profile = PORTFOLIOS.get(risk_profile, PORTFOLIOS["moderado"])
    mu_dom = profile["dom"]["expected_return"]
    mu_int = profile["intl"]["expected_return"]
    # Capital guard growth factor (mix of 70% BRL at 15% and 30% USD at 4.5%)
    cap_growth_factor = 1 + capital_growth_pct / 100.0
    # Aspirational growth factor
    asp_growth_factor = 1 + aspirational_growth_pct / 100.0
    # Compute initial required capital guard based on expenses and incomes for year 0
    # Sum expenses from year 0 to year 3 (max 4 years)
    sum_exp0 = sum(df_brl_totals[:4]) if df_brl_totals else 0.0
    income0 = df_incomes_totals[0] if df_incomes_totals else 0.0
    diff0 = sum_exp0 - income0
    first_expense0 = df_brl_totals[0] if df_brl_totals else 0.0
    # Investible patrimony at start is patrimonio_inicial
    if diff0 < first_expense0:
        cap = patrimonio_inicial * 0.10
    else:
        cap = diff0
    # Compute initial endowment as remainder of investible patrimony
    end = patrimonio_inicial - cap
    if end < 0.0:
        end = 0.0
    # Initialize aspirational current value
    asp = aspirational_inicial
    # Lists to store results
    caps: List[float] = []
    asps: List[float] = []
    ends: List[float] = []
    totals: List[float] = []
    # Precompute FX ratio for USD projection
    fx_ratio = (1 + infl_brl_pct / 100.0) / (1 + infl_usd_pct / 100.0) if (1 + infl_usd_pct / 100.0) != 0 else 1.0
    # Ensure net_cash length
    net_cash_local = list(net_cash) if net_cash is not None else [0.0] * anos_proj
    if len(net_cash_local) < anos_proj:
        net_cash_local += [0.0] * (anos_proj - len(net_cash_local))
    for i in range(anos_proj):
        # Determine current aspirational amount for display
        if aspirational_series is not None:
            current_asp = aspirational_series[i] if i < len(aspirational_series) else aspirational_series[-1]
        else:
            current_asp = asp
        # Record current values before applying returns and rebalancing
        caps.append(cap)
        asps.append(current_asp)
        # Apply currency adjustment for endowment display: 70% BRL + 30% USD*FX
        factor_fx_display = 0.7 + 0.3 * (fx_ratio ** i)
        ends.append(end * factor_fx_display)
        totals.append(cap + current_asp + end * factor_fx_display)
        # Update aspirational for next year
        if aspirational_series is None:
            asp = asp * asp_growth_factor
        else:
            if i + 1 < len(aspirational_series):
                asp = aspirational_series[i + 1]
            else:
                asp = current_asp * asp_growth_factor
        # Apply net cash flow before returns
        netcash_i = net_cash_local[i]
        # Grow capital guard to start of next period
        matured_cap = cap * cap_growth_factor
        # Grow endowment to start of next period (before rebalancing).  Include net cash flows
        matured_end = (end + netcash_i) * (1 + 0.7 * mu_dom + 0.3 * mu_int)
        # Compute current investible patrimony (after returns)
        investible_i = matured_cap + matured_end
        # Compute required capital guard for next year based on next 4 years of expenses and current income
        sum_exp_i4 = sum(df_brl_totals[i : i + 4]) if df_brl_totals else 0.0
        income_i = df_incomes_totals[i] if i < len(df_incomes_totals) else 0.0
        diff_i = sum_exp_i4 - income_i
        first_expense_i = df_brl_totals[i] if i < len(df_brl_totals) else 0.0
        if diff_i < first_expense_i:
            req_cap_i = investible_i * 0.10
        else:
            req_cap_i = diff_i
        # Ensure non-negative required capital guard
        req_cap_i = max(req_cap_i, 0.0)
        # Rebalance: transfer between endowment and capital guard so that capital guard equals req_cap_i
        diff_cap = req_cap_i - matured_cap
        # Update endowment after rebalancing
        end = matured_end - diff_cap
        if end < 0.0:
            end = 0.0
        # Set capital guard for next period
        cap = req_cap_i
    df_pat = pd.DataFrame(
        {
            "Ano": [i + 1 for i in range(anos_proj)],
            "Capital Guard (R$)": caps,
            "Aspirational (R$)": asps,
            "Endowment (R$)": ends,
            "Patrimônio Total (R$)": totals,
        }
    )
    return df_pat


def build_excel_download(
    df_brl: pd.DataFrame,
    df_usd: pd.DataFrame,
    df_incomes: pd.DataFrame,
    df_pat: pd.DataFrame,
) -> Tuple[str, bytes]:
    """Create an Excel file with separate sheets for BRL, USD, incomes and patrimony."""
    out = BytesIO()
    with pd.ExcelWriter(out, engine="xlsxwriter") as writer:
        df_brl.to_excel(writer, index=False, sheet_name="Gastos BRL")
        df_usd.to_excel(writer, index=False, sheet_name="Gastos USD")
        df_incomes.to_excel(writer, index=False, sheet_name="Rendas")
        df_pat.to_excel(writer, index=False, sheet_name="Patrimônio")
    return "projecao_jera.xlsx", out.getvalue()


def main():
    st.set_page_config(page_title="Jera Onboarding", layout="wide")
    # Sidebar with logo and title
    st.sidebar.markdown(
        f"<img src='data:image/png;base64,{JERA_LOGO_B64}' style='width:150px;margin-bottom:20px;'>",
        unsafe_allow_html=True,
    )
    st.sidebar.title("Jera Capital")
    st.sidebar.write("Onboarding Financeiro")

    # Check query parameter to reset the session when the link is clicked
    # Use the new query_params API instead of experimental functions
    params = st.query_params
    if "restart" in params:
        # Clear session state and remove the restart parameter
        st.session_state.clear()
        # Clear all query params
        st.query_params.clear()
        st.session_state.stage = "inputs"

    # Display a large, centered link that resets the app when clicked
    st.markdown(
        """
        <div style='text-align:center;margin-top:10px;margin-bottom:20px;'>
            <a href='?restart=1' style='font-size:40px;font-weight:600;color:#00a79d;text-decoration:none;'>
                Jera Capital
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Initialise stage
    if "stage" not in st.session_state:
        st.session_state.stage = "inputs"
    # Data storage
    # Initialise keys in session_state with default values for quick testing.
    # Users can modify these values in the UI.
    defaults = {
        "cargo": "CEO",
        "setor": "Tecnologia",
        "empresa": "Tech Corp",
        "idade_cliente": 45,
        "idade_conjuge": 42,
        "idade_aposentadoria": 65,
        "n_filhos": 2,
        "idades_filhos": [10, 8],
        "escolas_filhos": ["", ""],
        "estudam_fora": [False, False],
        "bairro": "Jardins",
        "metragem": 300.0,
        "n_carros": 2,
        "estilo_vida": 2,
        "n_viagens": 4,
        "n_funcionarios": 2,
        "luxo_mensal": 10000.0,
        "segunda_resid_mensal": 5000.0,
        "aluguel_mensal_brl": 20000.0,
        "aluguel_growth_brl": 5.0,
        "aluguel_mensal_usd": 5000.0,
        "aluguel_growth_usd": 3.0,
        "dividendos_brl": 100000.0,
        "divid_growth_brl": 5.0,
        "dividendos_usd": 20000.0,
        "divid_growth_usd": 3.0,
        "has_iliquido": True,
        "n_iliquidos": 2,
        "iliquido_vals_brl": [1000000.0, 500000.0],
        "iliquido_growth_brl": [10.0, 8.0],
        "iliquido_vals_usd": [200000.0, 100000.0],
        "iliquido_growth_usd": [5.0, 5.0],
        "patrimonio_inicial": 5000000.0,
        "filantropia_anual": 50000.0,
        "anos_proj": 20,
        "infl_brl_pct": 4.5,
        "infl_usd_pct": 2.5,
        "cotacao_usd": 5.0,
        "salario_anual0": 500000.0,
        "risk_number": None,
        "risk_profile": None,
        "nao_tem_conjuge": False,
        "salario_manual_input": False,
        "api_failed": False,
        "warning_no_salary": False,
        "aspirational_inicial": None,
        "aspirational_growth_rate": None,
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

    # Stage: Input collection
    if st.session_state.stage == "inputs":
        st.header("Dados Pessoais e Premissas")
        # Text inputs for job and company
        st.session_state.cargo = st.text_input("Cargo", value=st.session_state.cargo or "")
        st.session_state.setor = st.text_input("Setor", value=st.session_state.setor or "")
        st.session_state.empresa = st.text_input("Empresa", value=st.session_state.empresa or "")
        # Ages.  Allow zero as default so that the form starts blank.  Minimums set to 0 to avoid
        # forcing a default age.  Users must provide sensible ages themselves.
        col1, col2, col3 = st.columns(3)
        st.session_state.idade_cliente = col1.number_input(
            "Idade do cliente", min_value=0, max_value=120, value=int(st.session_state.idade_cliente or 0), step=1
        )
        st.session_state.idade_conjuge = col2.number_input(
            "Idade do cônjuge", min_value=0, max_value=120, value=int(st.session_state.idade_conjuge or 0), step=1
        )
        # Allow the user to indicate that they do not have a spouse.  When checked,
        # the age of the spouse is ignored in the projections and only one adult
        # is considered for base expenses.
        st.session_state.nao_tem_conjuge = col2.checkbox(
            "Não tenho cônjuge",
            value=bool(st.session_state.nao_tem_conjuge) if st.session_state.nao_tem_conjuge is not None else False,
        )
        st.session_state.idade_aposentadoria = col3.number_input(
            "Idade desejada de aposentadoria", min_value=0, max_value=120, value=int(st.session_state.idade_aposentadoria or 0), step=1
        )
        # Children
        st.session_state.n_filhos = st.number_input(
            "Número de filhos", min_value=0, max_value=10, value=int(st.session_state.n_filhos or 0), step=1
        )
        # Ensure lists have correct length
        n = int(st.session_state.n_filhos)
        if st.session_state.idades_filhos is None or len(st.session_state.idades_filhos) != n:
            st.session_state.idades_filhos = [10] * n
        if st.session_state.escolas_filhos is None or len(st.session_state.escolas_filhos) != n:
            st.session_state.escolas_filhos = ["" for _ in range(n)]
        if st.session_state.estudam_fora is None or len(st.session_state.estudam_fora) != n:
            st.session_state.estudam_fora = [False] * n
        if n > 0:
            st.subheader("Filhos")
            try:
                school_names = sorted({esc["nome"] for esc in PREMISES.get("educacao", {}).get("escolas", [])
                                       if "nome" in esc})
            except (KeyError, TypeError):
                school_names = []
            for i in range(n):
                colA, colB, colC = st.columns([1, 2, 2])
                st.session_state.idades_filhos[i] = colA.number_input(
                    f"Idade do filho {i+1}", min_value=0, max_value=40, value=st.session_state.idades_filhos[i], step=1
                )
                idade_f = st.session_state.idades_filhos[i]
                if idade_f <= 17:
                    escol = colB.selectbox(
                        f"Escola do filho {i+1}",
                        options=["Nenhuma"] + school_names,
                        index=(
                            1 + school_names.index(st.session_state.escolas_filhos[i])
                            if st.session_state.escolas_filhos[i] in school_names
                            else 0
                        ),
                        key=f"escola_filho_{i}",
                    )
                    st.session_state.escolas_filhos[i] = escol if escol != "Nenhuma" else ""
                    est_ext = colC.selectbox(
                        f"Estuda fora aos 18?",
                        options=["Não", "Sim"],
                        index=1 if st.session_state.estudam_fora[i] else 0,
                        key=f"estuda_fora_{i}",
                    )
                    st.session_state.estudam_fora[i] = True if est_ext == "Sim" else False
                else:
                    st.session_state.escolas_filhos[i] = ""
                    if 18 <= idade_f <= 21:
                        est_ext = colC.selectbox(
                            f"Faz faculdade fora?",
                            options=["Não", "Sim"],
                            index=1 if st.session_state.estudam_fora[i] else 0,
                            key=f"faculdade_fora_{i}",
                        )
                        st.session_state.estudam_fora[i] = True if est_ext == "Sim" else False
                    else:
                        st.session_state.estudam_fora[i] = False
        # Residence.  Add a "Selecione" option to avoid pre‑selecting a neighborhood and allow
        # users to leave it blank.  Metragem starts at zero.
        col4, col5 = st.columns(2)
        try:
            bairro_options = ["Selecione"] + [b["nome"] for b in PREMISES.get("moradia", {}).get("bairros", [])
                                              if "nome" in b]
        except (KeyError, TypeError):
            bairro_options = ["Selecione"]
        bairro_index = 0
        if st.session_state.bairro and st.session_state.bairro in bairro_options:
            bairro_index = bairro_options.index(st.session_state.bairro)
        st.session_state.bairro = col4.selectbox(
            "Bairro do imóvel principal",
            options=bairro_options,
            index=bairro_index,
        )
        # If the user selects "Selecione", treat bairro as empty string
        if st.session_state.bairro == "Selecione":
            st.session_state.bairro = ""
        st.session_state.metragem = col5.number_input(
            "Metragem do imóvel (m²)", min_value=0.0, max_value=5000.0, value=float(st.session_state.metragem or 0.0), step=10.0
        )
        # Cars, lifestyle, trips
        col6, col7, col8 = st.columns(3)
        st.session_state.n_carros = col6.number_input(
            "Número de carros", min_value=0, max_value=10, value=int(st.session_state.n_carros or 0), step=1
        )
        # Lifestyle: display numeric labels 1, 2, 3 for low/medium/high.
        # The underlying values remain 1, 2, 3 for internal computations.
        estilo_labels = ["1", "2", "3"]
        estilo_map = {"1": 1, "2": 2, "3": 3}
        # Determine the currently selected lifestyle as a string.
        # Default to "2" (medium) if no value exists.
        estilo_reverse = {v: k for k, v in estilo_map.items()}
        estilo_str_current = estilo_reverse.get(st.session_state.estilo_vida, "2")
        estilo_str = col7.selectbox(
            "Estilo de vida",
            estilo_labels,
            index=estilo_labels.index(estilo_str_current),
        )
        st.session_state.estilo_vida = estilo_map[estilo_str]
        st.session_state.n_viagens = col8.number_input(
            "Número de viagens internacionais por ano", min_value=0, max_value=12, value=int(st.session_state.n_viagens or 0), step=1
        )
        # Number of employees directly employed by the client (each adds 48k/year to housing costs)
        st.session_state.n_funcionarios = st.number_input(
            "Número de funcionários", min_value=0, max_value=20, value=int(st.session_state.n_funcionarios or 0), step=1
        )
        # Luxury
        possui_luxo = st.selectbox("Possui ativos de luxo?", ["Não", "Sim"], index=1 if (st.session_state.luxo_mensal or 0) > 0 else 0)
        if possui_luxo == "Sim":
            st.session_state.luxo_mensal = st.number_input(
                "Gasto mensal com ativos de luxo (R$)", min_value=0.0, max_value=10_000_000.0, value=st.session_state.luxo_mensal or 0.0, step=1000.0
            )
        else:
            st.session_state.luxo_mensal = 0.0
        # Second residence: similar to luxury but treated as its own category.  Users
        # can specify a monthly cost for a second home, which will be added as a
        # separate line in the expenses table.
        possui_seg_res = st.selectbox(
            "Possui segunda residência?",
            ["Não", "Sim"],
            index=1 if (st.session_state.segunda_resid_mensal or 0) > 0 else 0,
        )
        if possui_seg_res == "Sim":
            # Allow second residence costs without an arbitrary maximum.  Previously a
            # max_value of 10M caused the application to hang when clients entered
            # higher values.  Removing the limit avoids freezes for large inputs.
            st.session_state.segunda_resid_mensal = st.number_input(
                "Gasto mensal com segunda residência (R$)",
                min_value=0.0,
                value=st.session_state.segunda_resid_mensal or 0.0,
                step=1000.0,
            )
        else:
            st.session_state.segunda_resid_mensal = 0.0
        # Rendimentos passivos: aluguéis e dividendos (BRL e USD) + dividend yield
        st.subheader("Rendimentos passivos")
        col_r1, col_r2 = st.columns(2)
        # Aluguéis
        st.session_state.aluguel_mensal_brl = col_r1.number_input(
            "Aluguéis mensais (R$)",
            min_value=0.0,
            value=st.session_state.aluguel_mensal_brl or 0.0,
            step=1000.0,
        )
        st.session_state.aluguel_growth_brl = col_r1.number_input(
            "Crescimento esperado aluguel BRL (%)", min_value=0.0, max_value=50.0, value=st.session_state.aluguel_growth_brl or 0.0, step=0.5
        )
        st.session_state.aluguel_mensal_usd = col_r2.number_input(
            "Aluguéis mensais (USD)",
            min_value=0.0,
            value=st.session_state.aluguel_mensal_usd or 0.0,
            step=1000.0,
        )
        st.session_state.aluguel_growth_usd = col_r2.number_input(
            "Crescimento esperado aluguel USD (%)", min_value=0.0, max_value=50.0, value=st.session_state.aluguel_growth_usd or 0.0, step=0.5
        )
        # Dividendos
        st.session_state.dividendos_brl = col_r1.number_input(
            "Dividendos anuais (R$)",
            min_value=0.0,
            value=st.session_state.dividendos_brl or 0.0,
            step=1000.0,
        )
        st.session_state.divid_growth_brl = col_r1.number_input(
            "Crescimento esperado dividendos BRL (%)", min_value=0.0, max_value=50.0, value=st.session_state.divid_growth_brl or 0.0, step=0.5
        )
        st.session_state.dividendos_usd = col_r2.number_input(
            "Dividendos anuais (USD)",
            min_value=0.0,
            value=st.session_state.dividendos_usd or 0.0,
            step=1000.0,
        )
        st.session_state.divid_growth_usd = col_r2.number_input(
            "Crescimento esperado dividendos USD (%)", min_value=0.0, max_value=50.0, value=st.session_state.divid_growth_usd or 0.0, step=0.5
        )
        # Dividend Yield is no longer an input.  The return assumptions for participations
        # are fixed (19% for empresas brasileiras e 11% para empresas internacionais).

        # Patrimônio ilíquido extra
        possui_iliq = st.selectbox(
            "Possui patrimônio ilíquido extra?",
            ["Não", "Sim"],
            index=1 if st.session_state.get("has_iliquido", False) else 0,
        )
        st.session_state.has_iliquido = True if possui_iliq == "Sim" else False
        if st.session_state.has_iliquido:
            # Number of illiquid assets
            st.session_state.n_iliquidos = st.number_input(
                "Número de patrimônios ilíquidos", min_value=1, max_value=10, value=int(st.session_state.n_iliquidos or 1), step=1
            )
            n_il = int(st.session_state.n_iliquidos)
            # Ensure lists have correct length
            if st.session_state.get("iliquido_vals_brl") is None or len(st.session_state.iliquido_vals_brl) != n_il:
                st.session_state.iliquido_vals_brl = [0.0] * n_il
            if st.session_state.get("iliquido_growth_brl") is None or len(st.session_state.iliquido_growth_brl) != n_il:
                st.session_state.iliquido_growth_brl = [0.0] * n_il
            if st.session_state.get("iliquido_vals_usd") is None or len(st.session_state.iliquido_vals_usd) != n_il:
                st.session_state.iliquido_vals_usd = [0.0] * n_il
            if st.session_state.get("iliquido_growth_usd") is None or len(st.session_state.iliquido_growth_usd) != n_il:
                st.session_state.iliquido_growth_usd = [0.0] * n_il
            # Input fields for each illiquid asset
            for i in range(n_il):
                st.markdown(f"##### Patrimônio ilíquido {i+1}")
                col_il1, col_il2, col_il3, col_il4 = st.columns(4)
                st.session_state.iliquido_vals_brl[i] = col_il1.number_input(
                    f"Valor (R$) – bem {i+1}", min_value=0.0, max_value=1_000_000_000.0, value=float(st.session_state.iliquido_vals_brl[i] or 0.0), step=10_000.0,
                    key=f"iliquido_val_brl_{i}"
                )
                st.session_state.iliquido_growth_brl[i] = col_il2.number_input(
                    f"Crescimento BRL (%) – bem {i+1}", min_value=0.0, max_value=50.0, value=float(st.session_state.iliquido_growth_brl[i] or 0.0), step=0.5,
                    key=f"iliquido_growth_brl_{i}"
                )
                st.session_state.iliquido_vals_usd[i] = col_il3.number_input(
                    f"Valor (USD) – bem {i+1}", min_value=0.0, max_value=1_000_000_000.0, value=float(st.session_state.iliquido_vals_usd[i] or 0.0), step=10_000.0,
                    key=f"iliquido_val_usd_{i}"
                )
                st.session_state.iliquido_growth_usd[i] = col_il4.number_input(
                    f"Crescimento USD (%) – bem {i+1}", min_value=0.0, max_value=50.0, value=float(st.session_state.iliquido_growth_usd[i] or 0.0), step=0.5,
                    key=f"iliquido_growth_usd_{i}"
                )
        else:
            st.session_state.n_iliquidos = 0
            st.session_state.iliquido_vals_brl = []
            st.session_state.iliquido_growth_brl = []
            st.session_state.iliquido_vals_usd = []
            st.session_state.iliquido_growth_usd = []
        # Patrimony and aspirational
        col12, col13 = st.columns(2)
        st.session_state.patrimonio_inicial = col12.number_input(
            "Patrimônio investível (R$)", min_value=0.0, max_value=1_000_000_000.0, value=float(st.session_state.patrimonio_inicial or 0.0), step=50_000.0
        )
        # Philanthropy & projections
        col14, col15, col16 = st.columns(3)
        st.session_state.filantropia_anual = col14.number_input(
            "Gasto anual com filantropia (R$)", min_value=0.0, max_value=10_000_000.0, value=float(st.session_state.filantropia_anual or 0.0), step=1000.0
        )
        st.session_state.anos_proj = col15.number_input(
            "Número de anos a projetar", min_value=1, max_value=100, value=int(st.session_state.anos_proj or 30), step=1
        )
        # Inflation and FX
        col17, col18, col19 = st.columns(3)
        st.session_state.infl_brl_pct = col17.number_input(
            "Inflação BRL (%)", min_value=0.0, max_value=20.0, value=float(st.session_state.infl_brl_pct or 0.0), step=0.1
        )
        st.session_state.infl_usd_pct = col18.number_input(
            "Inflação USD (%)", min_value=0.0, max_value=20.0, value=float(st.session_state.infl_usd_pct or 0.0), step=0.1
        )
        st.session_state.cotacao_usd = col19.number_input(
            "Cotação USD/BRL", min_value=0.0, max_value=20.0, value=float(st.session_state.cotacao_usd or 0.0), step=0.01
        )
        # Salary manual input appears only if the API has failed in a previous submission
        if st.session_state.get("api_failed"):
            st.session_state.salario_manual_input = st.number_input(
                "Salário anual (R$) – informe manualmente",
                min_value=0.0,
                max_value=100_000_000.0,
                value=st.session_state.salario_manual_input or 0.0,
                step=10_000.0,
                key="manual_salary_input",
            )
        # Continue button – use on_click callback to avoid double‑click behaviour
        def submit_inputs():
            """Submit initial data and move to risk stage if salary is determined."""
            salario_estimado = estimate_salary(
                st.session_state.cargo or "",
                st.session_state.setor or "",
                st.session_state.empresa or "",
            )
            if not math.isnan(salario_estimado):
                st.session_state.salario_anual0 = salario_estimado
                st.session_state.api_failed = False
                st.session_state.stage = "risk"
            else:
                # mark that the API failed; manual input may be required
                st.session_state.api_failed = True
                if st.session_state.salario_manual_input and st.session_state.salario_manual_input > 0:
                    st.session_state.salario_anual0 = st.session_state.salario_manual_input
                    st.session_state.api_failed = False
                    st.session_state.stage = "risk"
                else:
                    st.session_state.salario_anual0 = 0.0
                    # show a message using st.warning after rerun
                    st.session_state.warning_no_salary = True
        # Button to continue triggers the callback
        st.button("Continuar →", key="continue_inputs", on_click=submit_inputs)
        # Display warning if no salary set on previous attempt
        if st.session_state.get("warning_no_salary"):
            st.warning(
                "Não foi possível estimar a renda automaticamente. Informe o salário anual no campo acima.")
            # reset flag so it doesn't persist between reruns
            st.session_state.warning_no_salary = False

    # Stage: Risk questionnaire and profile
    elif st.session_state.stage == "risk":
        """
        Etapa de avaliação de risco. Utiliza um questionário adaptativo inspirado
        no modelo da Nitrogen/Riskalyze. O usuário responde a uma sequência
        de perguntas de conforto sobre possíveis perdas e ganhos; a próxima
        pergunta é ajustada com base na resposta anterior (técnica de
        busca binária) para estimar o Risk Number (1–99). Após
        três perguntas, coletamos algumas informações adicionais sobre
        comportamento e horizonte de investimento para ajustar o número final.
        O resultado final define o perfil de risco (conservador, moderado ou
        arrojado) e leva automaticamente à etapa de projeções.
        """
        st.header("Avaliação de Perfil de Risco")
        st.subheader("Responda às perguntas para determinar seu Risk Number.")
        # Display the salary using Brazilian number formatting
        st.success(f"Salário anual utilizado: {format_brl_value(st.session_state.salario_anual0)}")
        # Inicialize variáveis do processo adaptativo se ainda não existirem
        if "risk_low" not in st.session_state:
            st.session_state.risk_low = 1
            st.session_state.risk_high = 99
            st.session_state.risk_current = 50
            st.session_state.risk_step = 1
            st.session_state.risk_answers = []
        # Mapeia um Risk Number (1-99) para um par de (perda%, ganho%) via interpolação linear
        def risk_to_range(risk_num: int) -> tuple[float, float]:
            # Cenários extremos: risco 1 (~2% perda, 4% ganho) e risco 99 (~30% perda, 40% ganho)
            min_loss, max_loss = 2.0, 30.0
            min_gain, max_gain = 4.0, 40.0
            t = (risk_num - 1) / 98
            loss = min_loss + t * (max_loss - min_loss)
            gain = min_gain + t * (max_gain - min_gain)
            return round(loss, 1), round(gain, 1)
        # Etapa de perguntas adaptativas
        if st.session_state.risk_step <= 3:
            loss_pct, gain_pct = risk_to_range(st.session_state.risk_current)
            st.markdown(
                f"### Pergunta de Conforto\nSeu investimento de R$100.000 pode variar em 6 meses entre perda de **{loss_pct}%** e ganho de **{gain_pct}%**. Você se sentiria confortável?"
            )
            col_yes, col_no = st.columns(2)
            def risk_yes():
                st.session_state.risk_answers.append(True)
                st.session_state.risk_low = st.session_state.risk_current
                st.session_state.risk_current = int((st.session_state.risk_low + st.session_state.risk_high + 1) // 2)
                st.session_state.risk_step += 1
            def risk_no():
                st.session_state.risk_answers.append(False)
                st.session_state.risk_high = st.session_state.risk_current
                st.session_state.risk_current = int((st.session_state.risk_low + st.session_state.risk_high) // 2)
                st.session_state.risk_step += 1
            col_yes.button("Sim", key=f"risk_yes_{st.session_state.risk_step}", on_click=risk_yes)
            col_no.button("Não", key=f"risk_no_{st.session_state.risk_step}", on_click=risk_no)
        else:
            # Calcule o Risk Number intermediário após as perguntas adaptativas
            risk_num = st.session_state.risk_current
            # Perguntas adicionais para ajustar a pontuação final
            st.markdown("#### Perguntas adicionais")
            q_behav = st.selectbox(
                "Se seus investimentos perdessem 1% do valor em um mês, como você reagiria?",
                [
                    "Venderia tudo imediatamente",
                    "Venderia parte dos investimentos",
                    "Manteria a posição",
                    "Aumentaria a posição",
                ],
                index=2,
                key="risk_behaviour",
            )
            q_horizon = st.selectbox(
                "Qual o seu horizonte de investimento?",
                [
                    "Até 1 ano",
                    "1 a 3 anos",
                    "3 a 5 anos",
                    "Mais de 5 anos",
                ],
                index=2,
                key="risk_horizon",
            )
            q_objective = st.selectbox(
                "Qual o seu objetivo principal de investimento?",
                [
                    "Preservar o capital",
                    "Proteger contra a inflação",
                    "Equilibrar crescimento e segurança",
                    "Crescimento de capital",
                ],
                index=2,
                key="risk_objective",
            )
            # Pontuações adicionais para cada resposta
            behav_scores = {
                "Venderia tudo imediatamente": -3,
                "Venderia parte dos investimentos": -1,
                "Manteria a posição": 1,
                "Aumentaria a posição": 3,
            }
            horizon_scores = {
                "Até 1 ano": -3,
                "1 a 3 anos": -1,
                "3 a 5 anos": 1,
                "Mais de 5 anos": 3,
            }
            objective_scores = {
                "Preservar o capital": -3,
                "Proteger contra a inflação": -1,
                "Equilibrar crescimento e segurança": 1,
                "Crescimento de capital": 3,
            }
            total_mod = behav_scores[q_behav] + horizon_scores[q_horizon] + objective_scores[q_objective]
            final_risk = max(1, min(99, risk_num + total_mod))
            # Determinar perfil de risco
            if final_risk <= 30:
                profile = "conservador"
            elif final_risk <= 60:
                profile = "moderado"
            else:
                profile = "arrojado"
            # Guardar no estado
            st.session_state.risk_number = final_risk
            st.session_state.risk_profile = profile
            st.success(f"Seu Risk Number é {final_risk} – perfil {profile.title()}")
            # Botão para prosseguir às projeções
            def goto_results():
                st.session_state.stage = "results"
            st.button("Ver Carteira Recomendada", key="go_to_portfolio", on_click=goto_results)

    # Stage: Results and projections
    elif st.session_state.stage == "results":
        st.header("Recomendações e Projeções")
        # Compute projections if not already done
        if "projections" not in st.session_state or st.session_state.projections is None:
            df_brl, df_usd, df_incomes, capital_guard = compute_costs_and_incomes(
                st.session_state.idade_cliente,
                st.session_state.idade_conjuge,
                st.session_state.idades_filhos,
                st.session_state.escolas_filhos,
                st.session_state.estudam_fora,
                st.session_state.bairro,
                st.session_state.metragem,
                st.session_state.n_carros,
                st.session_state.estilo_vida,
                st.session_state.n_viagens,
                st.session_state.n_funcionarios,
                st.session_state.luxo_mensal,
                st.session_state.segunda_resid_mensal,
                # novos inputs de renda: alugueis e dividendos
                st.session_state.aluguel_mensal_brl,
                st.session_state.aluguel_growth_brl,
                st.session_state.aluguel_mensal_usd,
                st.session_state.aluguel_growth_usd,
                st.session_state.dividendos_brl,
                st.session_state.divid_growth_brl,
                st.session_state.dividendos_usd,
                st.session_state.divid_growth_usd,
                st.session_state.patrimonio_inicial,
                st.session_state.filantropia_anual,
                int(st.session_state.anos_proj),
                st.session_state.infl_brl_pct,
                st.session_state.infl_usd_pct,
                st.session_state.cotacao_usd,
                st.session_state.salario_anual0,
                st.session_state.idade_aposentadoria,
                no_conjuge=bool(st.session_state.get("nao_tem_conjuge", False)),
                scales=st.session_state.get("scales"),
            )
            # Net cash flows: income minus BRL expenses including USD conversion.  Persist this
            # series in session state so it can be reused later for financial return calculations.
            net_cash_series = (df_incomes["Total Renda (R$)"] - df_brl["Total (R$)"]).tolist()
            st.session_state.net_cash_series = net_cash_series
            anos_proj = int(st.session_state.anos_proj)
            # Compute required capital guard for each year as the sum of the next
            # four years of expenses minus the income in year i.  This yields
            # the capital needed to cover four years of expenditures without
            # relying on investment returns.  For the first year, we will
            # override this value with the capital_guard computed in
            # compute_costs_and_incomes (which already applies the 10% rule
            # when expenses minus income is less than the first year's
            # expenses).
            required_caps: List[float] = []
            for i in range(anos_proj):
                # Sum expenses from year i to year i+3 inclusive (or until end of projection)
                sum_exp = df_brl["Total (R$)"].iloc[i : i + 4].sum()
                income_i = df_incomes["Total Renda (R$)"].iloc[i]
                required_caps.append(sum_exp - income_i)
            # Override the first required capital guard with the value computed
            # by compute_costs_and_incomes.  This enforces the condition that
            # the capital guard must be at least 10% of the investible patrimony
            # when the projected expenses of the first four years minus the
            # first year's income are less than the first year's expenses.
            if required_caps:
                required_caps[0] = capital_guard
            # Compute aspirational initial value and its growth rate based on rentals, dividends and illiquid assets
            # Apartments in Brazil and US
            aluguel_ano_brl = st.session_state.aluguel_mensal_brl * 12.0
            aluguel_ano_usd = st.session_state.aluguel_mensal_usd * 12.0
            g_alug_brl = st.session_state.aluguel_growth_brl / 100.0
            g_alug_usd = st.session_state.aluguel_growth_usd / 100.0
            # Avoid division by zero or negative denominator
            valor_apart_br = 0.0
            # For Brazilian rentals, use a required return of 15%
            if 0.15 - g_alug_brl > 0:
                valor_apart_br = aluguel_ano_brl / (0.15 - g_alug_brl)
            valor_apart_usd = 0.0
            if 0.07 - g_alug_usd > 0:
                valor_apart_usd = aluguel_ano_usd / (0.07 - g_alug_usd)
            valor_apart_usd_brl = valor_apart_usd * st.session_state.cotacao_usd
            # Participations based on dividends and fixed return assumptions (19% BR, 11% US)
            g_div_brl = st.session_state.divid_growth_brl / 100.0
            g_div_usd = st.session_state.divid_growth_usd / 100.0
            valor_part_brl = 0.0
            if (0.19 - g_div_brl) > 0:
                valor_part_brl = st.session_state.dividendos_brl / (0.19 - g_div_brl)
            valor_part_usd = 0.0
            if (0.11 - g_div_usd) > 0:
                valor_part_usd = st.session_state.dividendos_usd / (0.11 - g_div_usd)
            # Convert international participations to BRL
            valor_participacoes = valor_part_brl + valor_part_usd * st.session_state.cotacao_usd
            # Illiquid assets
            valor_iliq_total = 0.0
            g_iliq_num = 0.0
            if st.session_state.has_iliquido:
                for vb, gb, vu, gu in zip(
                    st.session_state.iliquido_vals_brl or [],
                    st.session_state.iliquido_growth_brl or [],
                    st.session_state.iliquido_vals_usd or [],
                    st.session_state.iliquido_growth_usd or [],
                ):
                    v_brl = vb + vu * st.session_state.cotacao_usd
                    valor_iliq_total += v_brl
                    g_iliq_num += v_brl * (gb / 100.0 if v_brl > 0 else 0.0)
            # Total aspirational initial
            asp_initial = valor_apart_br + valor_apart_usd_brl + valor_participacoes + valor_iliq_total
            # Compute weighted growth rate for aspirational
            weighted_growth_sum = 0.0
            weights_sum = 0.0
            if valor_apart_br > 0:
                weighted_growth_sum += valor_apart_br * g_alug_brl
                weights_sum += valor_apart_br
            if valor_apart_usd_brl > 0:
                weighted_growth_sum += valor_apart_usd_brl * g_alug_usd
                weights_sum += valor_apart_usd_brl
            # Weighted growth for participations (BRL and USD portions)
            if valor_participacoes > 0:
                v_brl_part = valor_part_brl
                v_usd_part_brl = valor_part_usd * st.session_state.cotacao_usd
                total_part_brl = v_brl_part + v_usd_part_brl
                if total_part_brl > 0:
                    g_part = 0.0
                    # Growth is weighted by the BRL value of each portion
                    if v_brl_part > 0:
                        g_part += (v_brl_part / total_part_brl) * g_div_brl
                    if v_usd_part_brl > 0:
                        g_part += (v_usd_part_brl / total_part_brl) * g_div_usd
                else:
                    g_part = 0.0
                weighted_growth_sum += valor_participacoes * g_part
                weights_sum += valor_participacoes
            if valor_iliq_total > 0:
                # g_iliq_num accumulated above uses growth*value; now divide by total value
                g_iliq = g_iliq_num / valor_iliq_total
                weighted_growth_sum += valor_iliq_total * g_iliq
                weights_sum += valor_iliq_total
            asp_growth = (weighted_growth_sum / asp_initial) if asp_initial > 0 and weights_sum > 0 else 0.0
            # Persist aspirational initial and growth rate in session_state for reference
            st.session_state.aspirational_inicial = asp_initial
            st.session_state.aspirational_growth_rate = asp_growth * 100.0  # percent
            # Build aspirational series year by year using individual component growths.
            asp_series: List[float] = []
            for i in range(anos_proj):
                total_asp_i = 0.0
                # Apartments
                total_asp_i += valor_apart_br * ((1 + g_alug_brl) ** i)
                total_asp_i += valor_apart_usd_brl * ((1 + g_alug_usd) ** i)
                # Participations
                total_asp_i += valor_part_brl * ((1 + g_div_brl) ** i)
                total_asp_i += (valor_part_usd * st.session_state.cotacao_usd) * ((1 + g_div_usd) ** i)
                # Illiquid assets
                if st.session_state.has_iliquido:
                    for vb, gb, vu, gu in zip(
                        st.session_state.iliquido_vals_brl or [],
                        st.session_state.iliquido_growth_brl or [],
                        st.session_state.iliquido_vals_usd or [],
                        st.session_state.iliquido_growth_usd or [],
                    ):
                        val_brl_i = vb * ((1 + (gb / 100.0)) ** i)
                        val_usd_brl_i = vu * st.session_state.cotacao_usd * ((1 + (gu / 100.0)) ** i)
                        total_asp_i += val_brl_i + val_usd_brl_i
                asp_series.append(total_asp_i)
            # Compute total patrimony at year 0: investible patrimony plus initial
            # aspirational amount.  Do not add the capital guard again here
            # because compute_patrimony_dynamic splits the investible
            # patrimony into capital guard and endowment based on
            # required_caps[0].  Adding it here would double count the
            # capital guard and inflate the starting patrimony.
            patrimonio_total_start = st.session_state.patrimonio_inicial + (asp_series[0] if asp_series else 0.0)
            # Compute patrimony with dynamic capital guard and aspirational series.  The capital
            # guard return reflects a mix of 70% domestic assets at 15% a.a. and 30% foreign
            # assets at 4.5% a.a., resulting in an effective growth rate of 11.85% per year.
            # Build lists of total expenses and total incomes for each year to feed into the
            # patrimony calculation.  These lists will be used to recompute the capital guard
            # requirements dynamically within compute_patrimony_dynamic.
            df_brl_totals_list = df_brl["Total (R$)"].tolist()
            df_incomes_totals_list = df_incomes["Total Renda (R$)"].tolist()
            df_pat = compute_patrimony_dynamic(
                # Only the investible patrimony (input) is passed here.  The aspirational
                # portion is supplied separately via aspirational_series and should not
                # inflate the investible amount used to compute the capital guard and
                # endowment.  Passing patrimonio_total_start here was causing the
                # endowment and capital guard to start with an inflated base.
                st.session_state.patrimonio_inicial,
                asp_series[0] if asp_series else asp_initial,
                asp_growth * 100.0,
                11.85,
                anos_proj,
                st.session_state.risk_profile,
                df_brl_totals_list,
                df_incomes_totals_list,
                st.session_state.infl_brl_pct,
                st.session_state.infl_usd_pct,
                st.session_state.cotacao_usd,
                net_cash=net_cash_series,
                aspirational_series=asp_series,
            )
            st.session_state.projections = (df_brl, df_usd, df_incomes, df_pat)
            # Store the actual capital guard series computed for later visualisations.
            st.session_state.capital_guard_list = df_pat["Capital Guard (R$)"].tolist()
        else:
            df_brl, df_usd, df_incomes, df_pat = st.session_state.projections
        # Build cash flow table (years as columns starting from year 0)
        def build_cash_flow(df_brl: pd.DataFrame, df_usd: pd.DataFrame, df_incomes: pd.DataFrame) -> pd.DataFrame:
            anos = df_brl["Ano"].values - 1  # start at year 0
            cols = [f"Ano {int(a)}" for a in anos]
            data = {}
            # Income entries: aggregate rentals and dividends separately
            data["Salário (R$)"] = df_incomes["Salário (R$)"].values
            # Sum dividend components
            if {"Dividendos BRL (R$)", "Dividendos USD (R$)"}.issubset(df_incomes.columns):
                data["Dividendos (R$)"] = (
                    df_incomes["Dividendos BRL (R$)"] + df_incomes["Dividendos USD (R$)"]
                ).values
            else:
                data["Dividendos (R$)"] = df_incomes.get("Dividendos (R$)", pd.Series([0.0] * len(df_incomes))).values
            # Sum rental components
            if {"Aluguéis BRL (R$)", "Aluguéis USD (R$)"}.issubset(df_incomes.columns):
                data["Aluguéis (R$)"] = (
                    df_incomes["Aluguéis BRL (R$)"] + df_incomes["Aluguéis USD (R$)"]
                ).values
            else:
                data["Aluguéis (R$)"] = df_incomes.get("Renda Extra (R$)", pd.Series([0.0] * len(df_incomes))).values
            data["Renda Total (R$)"] = df_incomes["Total Renda (R$)"].values
            # Expenses: separate BRL and USD
            # Convert USD-denominated expenses to BRL using the projected FX for each year
            # rather than the initial constant rate.  The FX projection follows the
            # inflation differential: cotacao * ((1+infl_brl)/(1+infl_usd))**year.
            n_years = len(df_usd)
            cot_init = st.session_state.cotacao_usd if hasattr(st.session_state, "cotacao_usd") else 1.0
            try:
                ratio = (1 + st.session_state.infl_brl_pct / 100.0) / (1 + st.session_state.infl_usd_pct / 100.0)
            except Exception:
                ratio = 1.0
            fx_series = np.array([cot_init * (ratio ** i) for i in range(n_years)])
            gastos_usd_brl = df_usd["Total ($)"].values * fx_series
            # BRL-only expenses are total expenses minus USD expenses converted to BRL
            gastos_brl_only = df_brl["Total (R$)"].values - gastos_usd_brl
            gastos_total_brl = df_brl["Total (R$)"].values
            data["Gastos (BRL)"] = gastos_brl_only
            data["Gastos (USD)"] = gastos_usd_brl
            data["Gastos Totais (R$)"] = gastos_total_brl
            # Net result (income minus total expenses)
            # Rename the net result row to "Ganhos - Gastos" according to the specification
            result = df_incomes["Total Renda (R$)"] - gastos_total_brl
            data["Ganhos - Gastos (R$)"] = result.values
            df_cf = pd.DataFrame(data, index=cols).T
            return df_cf
        df_cf = build_cash_flow(df_brl, df_usd, df_incomes)
        # Setup tabs: data review, recommended portfolio, results, adjustments
        # "Dados" allows users to review and edit all input assumptions after
        # running the initial projections.  Changes made here will trigger
        # recalculation of the projections on save.
        # Present tabs in the order: recommended portfolio first, then results,
        # adjustments and finally data.  This ensures that after completing the
        # risk questionnaire the user lands on the portfolio tab automatically.
        tab1, tab2, tab3, tab_dados = st.tabs([
            "Carteira recomendada",
            "Resultados",
            "Ajustes",
            "Dados",
        ])

        # Tab 0: Dados (client data review & edit)
        with tab_dados:
            st.subheader("Dados do Cliente")
            # Decorative photo removed at client's request; keeping the layout unchanged
            # Capture current values into local variables for editing.  We don't
            # update session state until the user clicks the save button.
            # Text inputs
            cargo_val = st.text_input("Cargo", value=st.session_state.cargo or "")
            setor_val = st.text_input("Setor", value=st.session_state.setor or "")
            empresa_val = st.text_input("Empresa", value=st.session_state.empresa or "")
            # Age inputs
            col_dat1, col_dat2, col_dat3 = st.columns(3)
            idade_cli_val = col_dat1.number_input(
                "Idade do cliente", min_value=0, max_value=120, value=int(st.session_state.idade_cliente or 0), step=1
            )
            idade_conj_val = col_dat2.number_input(
                "Idade do cônjuge", min_value=0, max_value=120, value=int(st.session_state.idade_conjuge or 0), step=1
            )
            # Checkbox to indicate absence of a spouse.  When checked, the spouse age
            # is ignored in projections and only one adult is counted for expenses.
            nao_tem_conjuge_val = col_dat2.checkbox(
                "Não tenho cônjuge",
                value=bool(st.session_state.nao_tem_conjuge) if st.session_state.nao_tem_conjuge is not None else False,
            )
            idade_apos_val = col_dat3.number_input(
                "Idade desejada de aposentadoria", min_value=0, max_value=120, value=int(st.session_state.idade_aposentadoria or 0), step=1
            )
            # Number of children
            n_filhos_val = st.number_input(
                "Número de filhos", min_value=0, max_value=10, value=int(st.session_state.n_filhos or 0), step=1
            )
            # Prepare lists for children ages, schools and abroad flags
            n_children = int(n_filhos_val)
            # Ensure existing lists have correct length
            idades_filhos_val = list(st.session_state.idades_filhos) if st.session_state.idades_filhos else []
            escolas_filhos_val = list(st.session_state.escolas_filhos) if st.session_state.escolas_filhos else []
            estudam_fora_val = list(st.session_state.estudam_fora) if st.session_state.estudam_fora else []
            if len(idades_filhos_val) != n_children:
                idades_filhos_val = [10] * n_children
            if len(escolas_filhos_val) != n_children:
                escolas_filhos_val = [""] * n_children
            if len(estudam_fora_val) != n_children:
                estudam_fora_val = [False] * n_children
            if n_children > 0:
                st.markdown("### Filhos")
                try:
                    school_names = sorted({esc["nome"] for esc in PREMISES.get("educacao", {}).get("escolas", [])
                                           if "nome" in esc})
                except (KeyError, TypeError):
                    school_names = []
                for i in range(n_children):
                    colA, colB, colC = st.columns([1, 2, 2])
                    idades_filhos_val[i] = colA.number_input(
                        f"Idade do filho {i+1}", min_value=0, max_value=40, value=int(idades_filhos_val[i]), step=1, key=f"dados_idade_filho_{i}"
                    )
                    idade_f = idades_filhos_val[i]
                    # Escola para idades até 17
                    if idade_f <= 17:
                        escol_options = ["Nenhuma"] + school_names
                        selected = escolas_filhos_val[i] if escolas_filhos_val[i] else "Nenhuma"
                        escol_val = colB.selectbox(
                            f"Escola do filho {i+1}", escol_options, index=escol_options.index(selected), key=f"dados_escola_filho_{i}"
                        )
                        escolas_filhos_val[i] = escol_val if escol_val != "Nenhuma" else ""
                        ext_val = colC.selectbox(
                            f"Estuda fora aos 18?", ["Não", "Sim"], index=1 if estudam_fora_val[i] else 0, key=f"dados_estuda_fora_{i}"
                        )
                        estudam_fora_val[i] = True if ext_val == "Sim" else False
                    else:
                        escolas_filhos_val[i] = ""
                        if 18 <= idade_f <= 21:
                            ext_val = colC.selectbox(
                                f"Faz faculdade fora?", ["Não", "Sim"], index=1 if estudam_fora_val[i] else 0, key=f"dados_faculdade_fora_{i}"
                            )
                            estudam_fora_val[i] = True if ext_val == "Sim" else False
                        else:
                            estudam_fora_val[i] = False
            # Residence and lifestyle.  Include a "Selecione" option for bairro and start metragem
            # at zero.  Cars and trips default to zero as well.
            col_r1, col_r2 = st.columns(2)
            try:
                bairro_opts = ["Selecione"] + [b["nome"] for b in PREMISES.get("moradia", {}).get("bairros", [])
                                               if "nome" in b]
            except (KeyError, TypeError):
                bairro_opts = ["Selecione"]
            bairro_idx = 0
            if st.session_state.bairro and st.session_state.bairro in bairro_opts:
                bairro_idx = bairro_opts.index(st.session_state.bairro)
            bairro_val = col_r1.selectbox(
                "Bairro do imóvel principal",
                options=bairro_opts,
                index=bairro_idx,
            )
            if bairro_val == "Selecione":
                bairro_val = ""
            metragem_val = col_r2.number_input(
                "Metragem do imóvel (m²)", min_value=0.0, max_value=5000.0, value=float(st.session_state.metragem or 0.0), step=10.0
            )
            col_r3, col_r4, col_r5 = st.columns(3)
            n_carros_val = col_r3.number_input(
                "Número de carros", min_value=0, max_value=10, value=int(st.session_state.n_carros or 0), step=1
            )
            # Lifestyle selection (numeric labels 1, 2, 3).
            estilo_labels_local = ["1", "2", "3"]
            estilo_map_local = {"1": 1, "2": 2, "3": 3}
            estilo_reverse_local = {v: k for k, v in estilo_map_local.items()}
            estilo_str_current_val = estilo_reverse_local.get(st.session_state.estilo_vida, "2")
            estilo_str_val = col_r4.selectbox(
                "Estilo de vida",
                estilo_labels_local,
                index=estilo_labels_local.index(estilo_str_current_val),
            )
            estilo_vida_val = estilo_map_local[estilo_str_val]
            n_viagens_val = col_r5.number_input(
                "Número de viagens internacionais por ano", min_value=0, max_value=12, value=int(st.session_state.n_viagens or 0), step=1
            )
            # Number of employees employed by the client
            n_funcionarios_val = st.number_input(
                "Número de funcionários",
                min_value=0,
                max_value=20,
                value=int(st.session_state.n_funcionarios or 0),
                step=1,
            )
            # Luxury
            possui_luxo_val = st.selectbox(
                "Possui ativos de luxo?", ["Não", "Sim"], index=1 if (st.session_state.luxo_mensal or 0) > 0 else 0
            )
            if possui_luxo_val == "Sim":
                luxo_mensal_val = st.number_input(
                    "Gasto mensal com ativos de luxo (R$)",
                    min_value=0.0,
                    max_value=10_000_000.0,
                    value=float(st.session_state.luxo_mensal or 0.0),
                    step=1000.0,
                )
            else:
                luxo_mensal_val = 0.0
            # Second residence (monthly cost), analogous to luxury spending.
            possui_seg_res_val = st.selectbox(
                "Possui segunda residência?",
                ["Não", "Sim"],
                index=1 if (st.session_state.segunda_resid_mensal or 0) > 0 else 0,
            )
            if possui_seg_res_val == "Sim":
                # Remove the arbitrary 10M cap so users with very high expenses can enter
                # any positive value without causing the app to freeze.
                seg_resid_mensal_val = st.number_input(
                    "Gasto mensal com segunda residência (R$)",
                    min_value=0.0,
                    value=float(st.session_state.segunda_resid_mensal or 0.0),
                    step=1000.0,
                )
            else:
                seg_resid_mensal_val = 0.0
            # Passive income: aluguéis e dividendos
            st.markdown("### Rendimentos passivos")
            col_i1, col_i2 = st.columns(2)
            aluguel_brl_val = col_i1.number_input(
                "Aluguéis mensais (R$)",
                min_value=0.0,
                value=float(st.session_state.aluguel_mensal_brl or 0.0),
                step=1000.0,
            )
            aluguel_growth_brl_val = col_i1.number_input(
                "Crescimento esperado aluguel BRL (%)", min_value=0.0, max_value=50.0, value=float(st.session_state.aluguel_growth_brl or 0.0), step=0.5
            )
            aluguel_usd_val = col_i2.number_input(
                "Aluguéis mensais (USD)",
                min_value=0.0,
                value=float(st.session_state.aluguel_mensal_usd or 0.0),
                step=1000.0,
            )
            aluguel_growth_usd_val = col_i2.number_input(
                "Crescimento esperado aluguel USD (%)", min_value=0.0, max_value=50.0, value=float(st.session_state.aluguel_growth_usd or 0.0), step=0.5
            )
            dividendos_brl_val = col_i1.number_input(
                "Dividendos anuais (R$)",
                min_value=0.0,
                value=float(st.session_state.dividendos_brl or 0.0),
                step=1000.0,
            )
            divid_growth_brl_val = col_i1.number_input(
                "Crescimento esperado dividendos BRL (%)", min_value=0.0, max_value=50.0, value=float(st.session_state.divid_growth_brl or 0.0), step=0.5
            )
            dividendos_usd_val = col_i2.number_input(
                "Dividendos anuais (USD)",
                min_value=0.0,
                value=float(st.session_state.dividendos_usd or 0.0),
                step=1000.0,
            )
            divid_growth_usd_val = col_i2.number_input(
                "Crescimento esperado dividendos USD (%)", min_value=0.0, max_value=50.0, value=float(st.session_state.divid_growth_usd or 0.0), step=0.5
            )
            # Dividend Yield is removed from user inputs.  Yield assumptions are fixed (19% BRL, 11% USD).
            # Illiquid assets
            possui_iliq_val = st.selectbox(
                "Possui patrimônio ilíquido extra?", ["Não", "Sim"], index=1 if st.session_state.get("has_iliquido", False) else 0
            )
            has_iliq = True if possui_iliq_val == "Sim" else False
            if has_iliq:
                n_il_val = st.number_input(
                    "Número de patrimônios ilíquidos", min_value=1, max_value=10, value=int(st.session_state.n_iliquidos or 1), step=1
                )
                n_il = int(n_il_val)
                # Ensure arrays have correct length
                iliq_vals_brl = list(st.session_state.iliquido_vals_brl) if st.session_state.iliquido_vals_brl else []
                iliq_growth_brl = list(st.session_state.iliquido_growth_brl) if st.session_state.iliquido_growth_brl else []
                iliq_vals_usd = list(st.session_state.iliquido_vals_usd) if st.session_state.iliquido_vals_usd else []
                iliq_growth_usd = list(st.session_state.iliquido_growth_usd) if st.session_state.iliquido_growth_usd else []
                if len(iliq_vals_brl) != n_il:
                    iliq_vals_brl = [0.0] * n_il
                if len(iliq_growth_brl) != n_il:
                    iliq_growth_brl = [0.0] * n_il
                if len(iliq_vals_usd) != n_il:
                    iliq_vals_usd = [0.0] * n_il
                if len(iliq_growth_usd) != n_il:
                    iliq_growth_usd = [0.0] * n_il
                for i in range(n_il):
                    st.markdown(f"##### Patrimônio ilíquido {i+1}")
                    c1, c2, c3, c4 = st.columns(4)
                    iliq_vals_brl[i] = c1.number_input(
                        f"Valor (R$) – bem {i+1}", min_value=0.0, max_value=1_000_000_000.0, value=float(iliq_vals_brl[i] or 0.0), step=10_000.0, key=f"dados_iliq_val_brl_{i}"
                    )
                    iliq_growth_brl[i] = c2.number_input(
                        f"Crescimento BRL (%) – bem {i+1}", min_value=0.0, max_value=50.0, value=float(iliq_growth_brl[i] or 0.0), step=0.5, key=f"dados_iliq_growth_brl_{i}"
                    )
                    iliq_vals_usd[i] = c3.number_input(
                        f"Valor (USD) – bem {i+1}", min_value=0.0, max_value=1_000_000_000.0, value=float(iliq_vals_usd[i] or 0.0), step=10_000.0, key=f"dados_iliq_val_usd_{i}"
                    )
                    iliq_growth_usd[i] = c4.number_input(
                        f"Crescimento USD (%) – bem {i+1}", min_value=0.0, max_value=50.0, value=float(iliq_growth_usd[i] or 0.0), step=0.5, key=f"dados_iliq_growth_usd_{i}"
                    )
            else:
                n_il = 0
                iliq_vals_brl, iliq_growth_brl, iliq_vals_usd, iliq_growth_usd = [], [], [], []
            # Patrimony
            col_p1 = st.columns(1)[0]
            patrimonio_inicial_val = col_p1.number_input(
                "Patrimônio investível (R$)", min_value=0.0, max_value=1_000_000_000.0, value=float(st.session_state.patrimonio_inicial or 0.0), step=50_000.0
            )
            # Philanthropy and projections
            col_ph1, col_ph2, col_ph3 = st.columns(3)
            filantropia_val = col_ph1.number_input(
                "Gasto anual com filantropia (R$)", min_value=0.0, max_value=10_000_000.0, value=float(st.session_state.filantropia_anual or 0.0), step=1000.0
            )
            anos_proj_val = col_ph2.number_input(
                "Número de anos a projetar", min_value=1, max_value=100, value=int(st.session_state.anos_proj or 30), step=1
            )
            # Inflation and FX
            col_inf1, col_inf2, col_inf3 = st.columns(3)
            infl_brl_val = col_inf1.number_input(
                "Inflação BRL (%)", min_value=0.0, max_value=20.0, value=float(st.session_state.infl_brl_pct or 0.0), step=0.1
            )
            infl_usd_val = col_inf2.number_input(
                "Inflação USD (%)", min_value=0.0, max_value=20.0, value=float(st.session_state.infl_usd_pct or 0.0), step=0.1
            )
            cotacao_usd_val = col_inf3.number_input(
                "Cotação USD/BRL", min_value=0.0, max_value=20.0, value=float(st.session_state.cotacao_usd or 0.0), step=0.01
            )
            # Salary manual override
            salario_manual_val = st.number_input(
                "Salário anual (R$)", min_value=0.0, max_value=100_000_000.0, value=float(st.session_state.salario_anual0 or 0.0), step=10_000.0
            )
            # Save button updates session state and triggers recalculation
            if st.button("Salvar Dados", key="save_dados"):
                st.session_state.cargo = cargo_val
                st.session_state.setor = setor_val
                st.session_state.empresa = empresa_val
                st.session_state.idade_cliente = int(idade_cli_val)
                st.session_state.idade_conjuge = int(idade_conj_val)
                st.session_state.idade_aposentadoria = int(idade_apos_val)
                st.session_state.n_filhos = int(n_filhos_val)
                st.session_state.idades_filhos = [int(v) for v in idades_filhos_val]
                st.session_state.escolas_filhos = list(escolas_filhos_val)
                st.session_state.estudam_fora = list(estudam_fora_val)
                st.session_state.bairro = bairro_val
                st.session_state.metragem = float(metragem_val)
                st.session_state.n_carros = int(n_carros_val)
                st.session_state.estilo_vida = int(estilo_vida_val)
                st.session_state.n_viagens = int(n_viagens_val)
                st.session_state.n_funcionarios = int(n_funcionarios_val)
                st.session_state.luxo_mensal = float(luxo_mensal_val)
                st.session_state.segunda_resid_mensal = float(seg_resid_mensal_val)
                st.session_state.nao_tem_conjuge = bool(nao_tem_conjuge_val)
                # Update passive incomes
                st.session_state.aluguel_mensal_brl = float(aluguel_brl_val)
                st.session_state.aluguel_growth_brl = float(aluguel_growth_brl_val)
                st.session_state.aluguel_mensal_usd = float(aluguel_usd_val)
                st.session_state.aluguel_growth_usd = float(aluguel_growth_usd_val)
                st.session_state.dividendos_brl = float(dividendos_brl_val)
                st.session_state.divid_growth_brl = float(divid_growth_brl_val)
                st.session_state.dividendos_usd = float(dividendos_usd_val)
                st.session_state.divid_growth_usd = float(divid_growth_usd_val)
                # Illiquid assets
                st.session_state.has_iliquido = has_iliq
                st.session_state.n_iliquidos = int(n_il)
                st.session_state.iliquido_vals_brl = [float(v) for v in iliq_vals_brl]
                st.session_state.iliquido_growth_brl = [float(v) for v in iliq_growth_brl]
                st.session_state.iliquido_vals_usd = [float(v) for v in iliq_vals_usd]
                st.session_state.iliquido_growth_usd = [float(v) for v in iliq_growth_usd]
                # Patrimony and other parameters
                st.session_state.patrimonio_inicial = float(patrimonio_inicial_val)
                st.session_state.filantropia_anual = float(filantropia_val)
                st.session_state.anos_proj = int(anos_proj_val)
                st.session_state.infl_brl_pct = float(infl_brl_val)
                st.session_state.infl_usd_pct = float(infl_usd_val)
                st.session_state.cotacao_usd = float(cotacao_usd_val)
                st.session_state.salario_anual0 = float(salario_manual_val)
                # Reset projections so that recalculation happens on next load
                st.session_state.projections = None
                # On save, reset risk stage to results so user can review the changes
                # (but do not modify stage here; next load will recompute)
        # Tab 1: recommended portfolio
        with tab1:
            st.subheader("Carteira Recomendada")
            st.success(
                f"Seu Risk Number é {st.session_state.risk_number} – perfil {st.session_state.risk_profile.title()}"
            )
            st.write("A alocação sugerida para o endowment é 70% em ativos domésticos e 30% em ativos internacionais.")
            prof = PORTFOLIOS.get(st.session_state.risk_profile, PORTFOLIOS["moderado"])
            # Domestic and international tables with recommended values
            dom_classes = prof["dom"]["classes"]
            intl_classes = prof["intl"]["classes"]
            # Retrieve recommended capital guard, aspirational and endowment from the projections
            cap_rec = df_pat["Capital Guard (R$)"].iloc[0] if not df_pat.empty else 0.0
            asp_rec = df_pat["Aspirational (R$)"].iloc[0] if not df_pat.empty else 0.0
            end_rec = df_pat["Endowment (R$)"].iloc[0] if not df_pat.empty else 0.0
            # We no longer display recommended values for Capital Guard, Aspirational and Endowment.
            # Calculate domestic and international portions of the endowment
            dom_endowment_brl = 0.70 * end_rec
            intl_endowment_brl = 0.30 * end_rec
            intl_endowment_usd = intl_endowment_brl / st.session_state.cotacao_usd if st.session_state.cotacao_usd else 0.0
            # Build allocation tables with values
            # Build allocation tables with values.  We interpret the weights in
            # PORTFOLIOS as percentages (e.g., 37.50 = 37.5%).  Display the
            # weight as given and convert it to a decimal when computing
            # absolute values.  Note: these weights are for display only and
            # are not used directly in the Monte Carlo simulation.
            df_dom = pd.DataFrame(
                {
                    "Classe de Ativo": list(dom_classes.keys()),
                    # Display weight directly as percentage with two decimals
                    "Peso (%)": [f"{float(w):.2f}%" for w in dom_classes.values()],
                    # Convert weight percentage into a decimal fraction for value calculation
                    "Valor (R$)": [float(w) / 100.0 * dom_endowment_brl for w in dom_classes.values()],
                }
            )
            df_int = pd.DataFrame(
                {
                    "Classe de Ativo": list(intl_classes.keys()),
                    "Peso (%)": [f"{float(w):.2f}%" for w in intl_classes.values()],
                    "Valor (USD)": [float(w) / 100.0 * intl_endowment_usd for w in intl_classes.values()],
                }
            )
            col_dom, col_int = st.columns(2)
            with col_dom:
                st.write("**Carteira Doméstica (70% do Endowment)**")
                # Format domestic values using Brazilian currency formatting
                st.table(df_dom.style.format({"Valor (R$)": format_brl_value}))
                st.write(
                    f"Retorno esperado (a.a): {prof['dom']['expected_return']*100:.1f}%  \nVolatilidade (a.a): {prof['dom']['vol']*100:.1f}%"
                )
            with col_int:
                st.write("**Carteira Internacional (30% do Endowment)**")
                # Format international values using USD formatting with Brazilian separators
                st.table(df_int.style.format({"Valor (USD)": format_usd_value}))
                st.write(
                    f"Retorno esperado (a.a): {prof['intl']['expected_return']*100:.1f}%  \nVolatilidade (a.a): {prof['intl']['vol']*100:.1f}%"
                )
            # Combined expected return (weighted)
            exp_comb = 0.7 * prof["dom"]["expected_return"] + 0.3 * prof["intl"]["expected_return"]
            st.write(f"Retorno esperado combinado (a.a): {exp_comb*100:.2f}%")
            # Monte Carlo simulation for endowment scenarios (P10, P50, P90)
            def simulate_endowment(end_initial: float, years: int, risk_profile: str, n_sim: int = 10000) -> Tuple[float, float, float]:
                """
                Perform a simple Monte Carlo simulation on the endowment using the expected
                return and volatility of the chosen risk profile.  Assumes normally
                distributed annual returns and no additional cash flows.

                Parameters
                ----------
                end_initial : float
                    Initial endowment value in BRL.
                years : int
                    Number of years to simulate.
                risk_profile : str
                    The risk profile key used to look up portfolio metrics.
                n_sim : int
                    Number of simulations.

                Returns
                -------
                Tuple[float, float, float]
                    Percentile 10, 50 and 90 of the simulated endowment after `years` years.
                """
                prof_m = PORTFOLIOS.get(risk_profile, PORTFOLIOS["moderado"])
                # Use aggregate expected return and volatility for domestic and international
                mu_dom = prof_m["dom"]["expected_return"]
                sigma_dom = prof_m["dom"]["vol"]
                mu_int = prof_m["intl"]["expected_return"]
                sigma_int = prof_m["intl"]["vol"]
                # Overall mean and standard deviation (assuming no correlation between dom/int)
                mu_total = 0.7 * mu_dom + 0.3 * mu_int
                sigma_total = math.sqrt((0.7 ** 2) * (sigma_dom ** 2) + (0.3 ** 2) * (sigma_int ** 2))
                # Precompute random returns matrix
                rng = np.random.default_rng()
                # Each simulation is a product of (1 + r) over `years`
                # Generate a (n_sim, years) matrix of returns
                rets = rng.normal(loc=mu_total, scale=sigma_total, size=(n_sim, years))
                # Compute cumulative growth factors
                growth = np.prod(1 + rets, axis=1)
                # Final values
                finals = end_initial * growth
                p10 = np.percentile(finals, 10)
                p50 = np.percentile(finals, 50)
                p90 = np.percentile(finals, 90)
                return p10, p50, p90
            # Execute simulation using current endowment and projection horizon
            if end_rec > 0:
                try:
                    # ------------------------------------------------------------------
                    # Additional Monte Carlo simulation for domestic and international
                    # segments, producing P10/P50/P90 percentiles for each year.
                    # The simulations use the expected returns and volatilities defined
                    # in the portfolio specification.  The resulting figures show the
                    # distribution of possible outcomes for each segment separately,
                    # benchmarked against CDI and Treasury.
                    try:
                        years_mc = int(st.session_state.anos_proj)
                        # Increase the number of simulations for a more robust Monte Carlo
                        n_sim_mc = 10000
                        # Extract expected return and volatility for domestic and international segments
                        mu_dom_mc = prof["dom"]["expected_return"]
                        sigma_dom_mc = prof["dom"]["vol"]
                        mu_int_mc = prof["intl"]["expected_return"]
                        sigma_int_mc = prof["intl"]["vol"]
                        # Domestic simulation (BRL)
                        if dom_endowment_brl > 0 and years_mc > 0:
                            rng_mc_dom = np.random.default_rng()
                            # Convert annual return and volatility to monthly metrics for finer simulation
                            mu_month_dom = mu_dom_mc / 12.0
                            sigma_month_dom = sigma_dom_mc / np.sqrt(12.0)
                            # Generate monthly returns for the entire horizon
                            rets_dom_month = rng_mc_dom.normal(loc=mu_month_dom, scale=sigma_month_dom, size=(n_sim_mc, years_mc * 12))
                            # Compute cumulative product of (1 + monthly return)
                            cum_prod_dom = np.cumprod(1 + rets_dom_month, axis=1)
                            # Determine indices corresponding to the end of each year (0-indexed)
                            year_indices = (np.arange(years_mc) + 1) * 12 - 1
                            # Compute value path for each simulation at the end of each year
                            path_dom = dom_endowment_brl * cum_prod_dom[:, year_indices]
                            # Compute percentiles across simulations
                            p10_dom = np.percentile(path_dom, 10, axis=0)
                            p50_dom = np.percentile(path_dom, 50, axis=0)
                            p90_dom = np.percentile(path_dom, 90, axis=0)
                            x_vals_dom = list(range(1, years_mc + 1))
                            fig_dom_mc = go.Figure()
                            # Add percentile curves with user-friendly labels
                            fig_dom_mc.add_trace(go.Scatter(x=x_vals_dom, y=p10_dom, name="Cenário pessimista (P10)", mode="lines", line=dict(color="#e74c3c", width=2)))
                            fig_dom_mc.add_trace(go.Scatter(x=x_vals_dom, y=p50_dom, name="Cenário conservador (P50)", mode="lines", line=dict(color="#f5a623", width=2)))
                            fig_dom_mc.add_trace(go.Scatter(x=x_vals_dom, y=p90_dom, name="Cenário otimista (P90)", mode="lines", line=dict(color="#8cc63f", width=2)))
                            # Benchmark line for domestic portfolio: CDI at 15% per annum
                            benchmark_dom = [dom_endowment_brl * ((1 + 0.15) ** j) for j in range(1, years_mc + 1)]
                            fig_dom_mc.add_trace(go.Scatter(x=x_vals_dom, y=benchmark_dom, name="CDI 15%", mode="lines", line=dict(color="#ffffff", width=2, dash="dash")))
                            fig_dom_mc.update_layout(
                                title="Carteira Doméstica - Benchmark: CDI",
                                xaxis_title="Ano",
                                yaxis_title="Valor (R$)",
                                plot_bgcolor="#071d2b",
                                paper_bgcolor="#071d2b",
                                font=dict(color="#f2f2f2"),
                                xaxis=dict(gridcolor="#143857"),
                                yaxis=dict(gridcolor="#143857", tickformat=".2s"),
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                            )
                            st.plotly_chart(fig_dom_mc, use_container_width=True)
                        # International simulation (USD)
                        if intl_endowment_usd > 0 and years_mc > 0:
                            rng_mc_int = np.random.default_rng()
                            # Convert annual return and volatility to monthly metrics for finer simulation
                            mu_month_int = mu_int_mc / 12.0
                            sigma_month_int = sigma_int_mc / np.sqrt(12.0)
                            # Generate monthly returns for the entire horizon
                            rets_int_month = rng_mc_int.normal(loc=mu_month_int, scale=sigma_month_int, size=(n_sim_mc, years_mc * 12))
                            # Compute cumulative product of (1 + monthly return)
                            cum_prod_int = np.cumprod(1 + rets_int_month, axis=1)
                            # Determine indices corresponding to the end of each year
                            year_indices_int = (np.arange(years_mc) + 1) * 12 - 1
                            # Compute value path for each simulation at the end of each year
                            path_int = intl_endowment_usd * cum_prod_int[:, year_indices_int]
                            # Compute percentiles across simulations
                            p10_int = np.percentile(path_int, 10, axis=0)
                            p50_int = np.percentile(path_int, 50, axis=0)
                            p90_int = np.percentile(path_int, 90, axis=0)
                            x_vals_int = list(range(1, years_mc + 1))
                            fig_int_mc = go.Figure()
                            # Add percentile curves with user-friendly labels
                            fig_int_mc.add_trace(go.Scatter(x=x_vals_int, y=p10_int, name="Cenário pessimista (P10)", mode="lines", line=dict(color="#e74c3c", width=2)))
                            fig_int_mc.add_trace(go.Scatter(x=x_vals_int, y=p50_int, name="Cenário conservador (P50)", mode="lines", line=dict(color="#f5a623", width=2)))
                            fig_int_mc.add_trace(go.Scatter(x=x_vals_int, y=p90_int, name="Cenário otimista (P90)", mode="lines", line=dict(color="#8cc63f", width=2)))
                            # Benchmark line for international portfolio: T-Bill at 4% per annum
                            benchmark_int = [intl_endowment_usd * ((1 + 0.04) ** j) for j in range(1, years_mc + 1)]
                            fig_int_mc.add_trace(go.Scatter(x=x_vals_int, y=benchmark_int, name="T-Bill 4%", mode="lines", line=dict(color="#ffffff", width=2, dash="dash")))
                            fig_int_mc.update_layout(
                                title="Carteira Internacional - Benchmark: Treasury",
                                xaxis_title="Ano",
                                yaxis_title="Valor (USD)",
                                plot_bgcolor="#071d2b",
                                paper_bgcolor="#071d2b",
                                font=dict(color="#f2f2f2"),
                                xaxis=dict(gridcolor="#143857"),
                                yaxis=dict(gridcolor="#143857", tickformat=".2s"),
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                            )
                            st.plotly_chart(fig_int_mc, use_container_width=True)
                    except Exception:
                        # If simulation fails for any reason, silently ignore so the app continues.
                        pass
                except Exception:
                    pass
        # Tab 2: results (cash flow and graphs)
        with tab2:
            st.subheader("Fluxo de Caixa Completo")
            # Build per-year arrays for the patrimony components
            years_cols = df_cf.columns.tolist()
            caps = df_pat["Capital Guard (R$)"].values
            ends = df_pat["Endowment (R$)"].values
            asps = df_pat["Aspirational (R$)"].values
            tots = df_pat["Patrimônio Total (R$)"].values
            # Load the net cash series and required capital guard from session state
            net_cash = st.session_state.get("net_cash_series", [0.0] * len(tots))
            req_caps = st.session_state.get("capital_guard_list", [0.0] * len(tots))
            # Expected return for endowment
            prof_for_returns = PORTFOLIOS.get(st.session_state.risk_profile, PORTFOLIOS["moderado"])
            exp_dom = prof_for_returns["dom"]["expected_return"]
            exp_int = prof_for_returns["intl"]["expected_return"]
            expected_total_ret = 0.7 * exp_dom + 0.3 * exp_int
            # Compute the annual appreciation of the aspirational bucket (illiquid patrimony).
            # Rather than calculating appreciation from individual illiquid assets, we derive
            # it directly from the change in the aspirational values recorded in the
            # patrimony projection.  This ensures that the line "Valorização dos patrimônios
            # ilíquidos" matches exactly the growth of the aspirational bucket and the
            # total patrimony appreciation reflects the actual change in value.
            asp_vals = df_pat["Aspirational (R$)"].values
            valuations_ilq_growth = []
            # Calculate annual appreciation as the change in aspirational values between
            # consecutive years.  For year 0, use the difference between year 1 and year 0.
            # For the final year, repeat the previous year's growth to preserve the length.
            for idx in range(len(asp_vals)):
                if idx < len(asp_vals) - 1:
                    valuations_ilq_growth.append(asp_vals[idx + 1] - asp_vals[idx])
                else:
                    # Last year: repeat the last known growth or zero if only one year
                    if len(asp_vals) > 1:
                        valuations_ilq_growth.append(asp_vals[-1] - asp_vals[-2])
                    else:
                        valuations_ilq_growth.append(0.0)
            # Compute financial returns for each year: return from capital guard and endowment
            financial_returns = []
            for idx in range(len(tots)):
                cap_i = caps[idx]
                end_i = ends[idx]
                req = req_caps[idx] if idx < len(req_caps) else req_caps[-1]
                matured_cap = cap_i * (1 + 0.1185)
                diff = req - matured_cap
                end_before = end_i + (net_cash[idx] if idx < len(net_cash) else 0.0) - diff
                if end_before < 0.0:
                    end_before = 0.0
                ret_cap = cap_i * 0.1185
                ret_end = end_before * expected_total_ret
                financial_returns.append(ret_cap + ret_end)
            # Compute total patrimony growth per year
            total_growth = []
            for idx in range(len(tots)):
                nc = net_cash[idx] if idx < len(net_cash) else 0.0
                fin_ret = financial_returns[idx] if idx < len(financial_returns) else 0.0
                illiq = valuations_ilq_growth[idx] if idx < len(valuations_ilq_growth) else 0.0
                total_growth.append(nc + fin_ret + illiq)
            # First table: display only totals and major buckets (no percentages)
            overview_rows = [
                [format_brl_value(v) for v in tots],
                [format_brl_value(v) for v in caps],
                [format_brl_value(v) for v in ends],
                [format_brl_value(v) for v in asps],
            ]
            overview_idx = [
                "Patrimônio total (R$)",
                "Capital Guard (R$)",
                "Endowment (R$)",
                "Aspirational (R$)",
            ]
            df_pat_overview = pd.DataFrame(overview_rows, index=overview_idx, columns=years_cols)
            st.dataframe(df_pat_overview, use_container_width=True)
            # Second table: append financial results and illiquid appreciation to cash flow table
            df_cf_full = df_cf.copy()
            df_cf_full.loc["Resultados financeiros (R$)"] = financial_returns
            df_cf_full.loc["Valorização dos patrimônios ilíquidos (R$)"] = valuations_ilq_growth
            df_cf_full.loc["Crescimento total do patrimônio (R$)"] = total_growth
            # Convert numeric values to formatted strings for display
            df_cf_display = df_cf_full.astype(object).copy()
            for row in df_cf_display.index:
                for col in df_cf_display.columns:
                    val = df_cf_display.loc[row, col]
                    if isinstance(val, (int, float, np.number)):
                        df_cf_display.loc[row, col] = format_brl_value(val)
            st.dataframe(df_cf_display, use_container_width=True)
            # Detailed expenses table right after cash flow
            st.subheader("Detalhe de Gastos")
            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                st.write("**Gastos em BRL (por categoria)**")
                years = (df_brl["Ano"] - 1).astype(int)
                # Build BRL category table with years horizontal
                # Convert the USD portion of education expenses to BRL using the projected FX for each year.
                n_years_ed = len(df_usd)
                cot_init_ed = st.session_state.cotacao_usd if hasattr(st.session_state, "cotacao_usd") else 1.0
                try:
                    ratio_ed = (1 + st.session_state.infl_brl_pct / 100.0) / (1 + st.session_state.infl_usd_pct / 100.0)
                except Exception:
                    ratio_ed = 1.0
                fx_series_ed = np.array([cot_init_ed * (ratio_ed ** i) for i in range(n_years_ed)])
                educ_brl_only = df_brl["Educação (R$)"].values - df_usd["Educação Exterior ($)"].values * fx_series_ed
                gastos_brl_dict = {
                    "Moradia (R$)": df_brl["Moradia (R$)"].values,
                    "Educação BRL (R$)": educ_brl_only,
                    "Saúde (R$)": df_brl["Saúde (R$)"].values,
                    "Veículos (R$)": df_brl["Veículos (R$)"].values,
                    "Lifestyle (R$)": df_brl["Lifestyle (R$)"].values,
                    "Ativos de Luxo (R$)": df_brl["Ativos de Luxo (R$)"].values,
                    "Filantropia (R$)": df_brl["Filantropia (R$)"].values,
                }
                df_gastos_brl_table = pd.DataFrame(gastos_brl_dict).T
                df_gastos_brl_table.columns = [f"Ano {int(y)}" for y in years]
                st.dataframe(
                    df_gastos_brl_table.style.format(format_brl_value),
                    use_container_width=True,
                )
            with col_exp2:
                st.write("**Gastos em USD (por categoria)**")
                years = (df_usd["Ano"] - 1).astype(int)
                gastos_usd_dict = {
                    "Educação USD ($)": df_usd["Educação Exterior ($)"].values,
                    "Viagens Internacionais ($)": df_usd["Viagens Internacionais ($)"].values,
                }
                df_gastos_usd_table = pd.DataFrame(gastos_usd_dict).T
                df_gastos_usd_table.columns = [f"Ano {int(y)}" for y in years]
                st.dataframe(
                    df_gastos_usd_table.style.format(format_usd_value),
                    use_container_width=True,
                )
            # After presenting the detailed expenses, include a notes section that
            # highlights significant future events related to the children.  These
            # annotations help the user understand upcoming changes in the cash flow
            # such as schooling transitions, car purchases and when each child
            # leaves the household budget.  The events are computed relative to
            # the current ages of the children and will only be displayed if
            # they occur within the projection horizon.
            try:
                eventos = []
                idades_ini = st.session_state.get("idades_filhos", []) or []
                anos_total = len(df_pat)
                for idx_child, idade_ini in enumerate(idades_ini):
                    # Age 17: school to university transition
                    off17 = 17 - int(idade_ini)
                    if 0 <= off17 < anos_total:
                        eventos.append(f"Filho {idx_child+1} sai da escola e entra na faculdade no ano {off17} (aos 17 anos)")
                    # Age 18: receives a car
                    off18 = 18 - int(idade_ini)
                    if 0 <= off18 < anos_total:
                        eventos.append(f"Filho {idx_child+1} ganha carro no ano {off18} (aos 18 anos)")
                    # Age 22: finishes university (four-year course starting at 18)
                    off22 = 22 - int(idade_ini)
                    if 0 <= off22 < anos_total:
                        eventos.append(f"Filho {idx_child+1} sai da faculdade no ano {off22} (aos 22 anos)")
                    # Age 26: leaves cash flow
                    off26 = 26 - int(idade_ini)
                    if 0 <= off26 < anos_total:
                        eventos.append(f"Filho {idx_child+1} sai do fluxo de caixa no ano {off26} (aos 26 anos)")
                # Display events if any were generated
                if eventos:
                    st.markdown("**Eventos previstos no fluxo de caixa:**")
                    for ev in eventos:
                        st.write(f"- {ev}")
            except Exception:
                # If any error occurs (e.g. no child data), silently ignore to avoid
                # interrupting the user experience.
                pass
            # Display separate charts for nominal and real patrimony.  Real values are
            # discounted by BRL inflation to reflect present value (ano 0).
            # Nominal patrimony: show the evolution of each block (Capital Guard, Endowment, Aspirational)
            st.subheader("Evolução do Patrimônio Nominal")
            fig_nominal = go.Figure()
            # Add each patrimony component as a separate line
            fig_nominal.add_trace(
                go.Scatter(
                    x=df_pat["Ano"],
                    y=df_pat["Capital Guard (R$)"],
                    name="Capital Guard",
                    mode="lines",
                    line=dict(color="#00b8d9", width=3),
                )
            )
            fig_nominal.add_trace(
                go.Scatter(
                    x=df_pat["Ano"],
                    y=df_pat["Endowment (R$)"],
                    name="Endowment",
                    mode="lines",
                    line=dict(color="#0072a8", width=3),
                )
            )
            fig_nominal.add_trace(
                go.Scatter(
                    x=df_pat["Ano"],
                    y=df_pat["Aspirational (R$)"],
                    name="Aspirational",
                    mode="lines",
                    line=dict(color="#8cc63f", width=3),
                )
            )
            # Add a trace for total patrimony (sum of the three buckets)
            fig_nominal.add_trace(
                go.Scatter(
                    x=df_pat["Ano"],
                    y=df_pat["Patrimônio Total (R$)"],
                    name="Patrimônio total",
                    mode="lines",
                    line=dict(color="#f5a623", width=3, dash="dash"),
                )
            )
            fig_nominal.update_layout(
                xaxis_title="Ano",
                yaxis_title="Valor (R$)",
                plot_bgcolor="#071d2b",
                paper_bgcolor="#071d2b",
                font=dict(color="#f2f2f2"),
                xaxis=dict(gridcolor="#143857"),
                yaxis=dict(gridcolor="#143857", tickformat=".2s"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig_nominal, use_container_width=True)
            # Real patrimony: adjust each block by inflation factor
            st.subheader("Evolução do Patrimônio Real")
            infl_factor = 1 + st.session_state.infl_brl_pct / 100.0
            real_cap = []
            real_end = []
            real_asp = []
            real_tot = []
            for idx in range(len(df_pat)):
                real_cap.append(df_pat["Capital Guard (R$)"].iloc[idx] / (infl_factor ** idx))
                real_end.append(df_pat["Endowment (R$)"].iloc[idx] / (infl_factor ** idx))
                real_asp.append(df_pat["Aspirational (R$)"].iloc[idx] / (infl_factor ** idx))
                real_tot.append(df_pat["Patrimônio Total (R$)"].iloc[idx] / (infl_factor ** idx))
            fig_real = go.Figure()
            fig_real.add_trace(
                go.Scatter(
                    x=df_pat["Ano"],
                    y=real_cap,
                    name="Capital Guard",
                    mode="lines",
                    line=dict(color="#00b8d9", width=3),
                )
            )
            fig_real.add_trace(
                go.Scatter(
                    x=df_pat["Ano"],
                    y=real_end,
                    name="Endowment",
                    mode="lines",
                    line=dict(color="#0072a8", width=3),
                )
            )
            fig_real.add_trace(
                go.Scatter(
                    x=df_pat["Ano"],
                    y=real_asp,
                    name="Aspirational",
                    mode="lines",
                    line=dict(color="#8cc63f", width=3),
                )
            )
            # Add total real patrimony line
            fig_real.add_trace(
                go.Scatter(
                    x=df_pat["Ano"],
                    y=real_tot,
                    name="Patrimônio total",
                    mode="lines",
                    line=dict(color="#f5a623", width=3, dash="dash"),
                )
            )
            fig_real.update_layout(
                xaxis_title="Ano",
                yaxis_title="Valor (R$)",
                plot_bgcolor="#071d2b",
                paper_bgcolor="#071d2b",
                font=dict(color="#f2f2f2"),
                xaxis=dict(gridcolor="#143857"),
                yaxis=dict(gridcolor="#143857", tickformat=".2s"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig_real, use_container_width=True)
            # The unified chart has been removed because the nominal and real charts above
            # now display the evolution of each patrimonial block separately.
            # Bar chart for expenses with dark theme
            st.subheader("Gastos Totais (BRL) por Ano")
            fig_gastos = go.Figure()
            fig_gastos.add_trace(
                go.Bar(
                    x=df_brl["Ano"],
                    y=df_brl["Total (R$)"],
                    name="Gastos Totais",
                    marker_color="#00b8d9",
                )
            )
            fig_gastos.update_layout(
                xaxis_title="Ano",
                yaxis_title="Gastos (R$)",
                plot_bgcolor="#071d2b",
                paper_bgcolor="#071d2b",
                font=dict(color="#f2f2f2"),
                xaxis=dict(gridcolor="#143857"),
                yaxis=dict(gridcolor="#143857", tickformat=".2s"),
                showlegend=False,
            )
            st.plotly_chart(fig_gastos, use_container_width=True)
            # Download
            fname, excel_bytes = build_excel_download(df_brl, df_usd, df_incomes, df_pat)
            st.download_button(
                "📥 Baixar projeção em Excel",
                data=excel_bytes,
                file_name=fname,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        # Tab 3: adjustments
        with tab3:
            st.subheader("Ajustes de Premissas")
            # General assumptions
            colX, colY, colZ = st.columns(3)
            new_infl_brl = colX.number_input(
                "Inflação BRL (%)",
                min_value=0.0,
                max_value=20.0,
                value=st.session_state.infl_brl_pct,
                step=0.1,
                key="adj_infl_brl",
            )
            new_infl_usd = colY.number_input(
                "Inflação USD (%)",
                min_value=0.0,
                max_value=20.0,
                value=st.session_state.infl_usd_pct,
                step=0.1,
                key="adj_infl_usd",
            )
            new_cot = colZ.number_input(
                "Cotação USD/BRL",
                min_value=1.0,
                max_value=20.0,
                value=st.session_state.cotacao_usd,
                step=0.01,
                key="adj_cotacao",
            )
            new_n_viagens = st.number_input(
                "Número de viagens internacionais por ano",
                min_value=0,
                max_value=12,
                value=st.session_state.n_viagens,
                step=1,
                key="adj_n_viagens",
            )
            new_luxo = st.number_input(
                "Gasto mensal com ativos de luxo (R$)",
                min_value=0.0,
                max_value=10_000_000.0,
                value=st.session_state.luxo_mensal,
                step=1000.0,
                key="adj_luxo",
            )
            # As alocações de dividendos e suas taxas de crescimento são agora
            # definidas nas etapas de entrada e não precisam ser ajustadas
            # manualmente aqui.  Por isso, removemos os campos de ajuste para
            # dividendos e suas taxas de crescimento.
            new_fil = st.number_input(
                "Gasto anual com filantropia (R$)",
                min_value=0.0,
                max_value=10_000_000.0,
                value=st.session_state.filantropia_anual,
                step=1000.0,
                key="adj_filantropia",
            )
            # O valor do aspirational é calculado automaticamente a partir dos
            # aluguéis, dividendos e patrimônios ilíquidos informados pelo usuário;
            # não permitimos sua edição manual nesta aba.
            # Baseline costs for subjective categories
            # Initialize baseline and slider values once
            if "baseline_costs" not in st.session_state or st.session_state.baseline_costs is None:
                # Compute baseline from first year (index 0) of current projections
                idx0 = 0
                # Avoid recomputing if projections empty
                try:
                    baseline_educ_usd = df_usd.loc[idx0, "Educação Exterior ($)"]
                    baseline_educ_brl = df_brl.loc[idx0, "Educação (R$)"] - baseline_educ_usd * st.session_state.cotacao_usd
                    st.session_state.baseline_costs = {
                        "moradia": float(df_brl.loc[idx0, "Moradia (R$)"]),
                        "veiculos": float(df_brl.loc[idx0, "Veículos (R$)"]),
                        "lifestyle": float(df_brl.loc[idx0, "Lifestyle (R$)"]),
                        "educacao_brl": float(baseline_educ_brl),
                        "educacao_usd": float(baseline_educ_usd),
                        "viagens_usd": float(df_usd.loc[idx0, "Viagens Internacionais ($)"]),
                    }
                except Exception:
                    st.session_state.baseline_costs = {}
            # Initialise scales dict if not present
            if "scales" not in st.session_state or st.session_state.scales is None:
                st.session_state.scales = {k: 1.0 for k in st.session_state.baseline_costs.keys()}
            # Slider controls for subjective expenses
            st.markdown("### Ajustar gastos anuais (ano 0)")
            slider_values = {}
            for cat, base_val in st.session_state.baseline_costs.items():
                # Determine display name
                display_name = {
                    "moradia": "Moradia (R$)",
                    "veiculos": "Veículos (R$)",
                    "lifestyle": "Lifestyle (R$)",
                    "educacao_brl": "Educação BRL (R$)",
                    "educacao_usd": "Educação USD ($)",
                    "viagens_usd": "Viagens Internacionais USD ($)",
                }.get(cat, cat)
                # Determine min and max; allow 0 to 2x baseline
                min_val = 0.0
                max_val = base_val * 2 if base_val > 0 else 1.0
                step = base_val / 20 if base_val != 0 else 1.0
                if cat.endswith("usd"):
                    fmt = "$ %,.0f"
                else:
                    fmt = "R$ %,.0f"
                slider_values[cat] = st.slider(
                    display_name,
                    min_value=min_val,
                    max_value=max_val,
                    value=base_val,
                    step=step,
                    key=f"slider_{cat}",
                )
            # Update button
            if st.button("Atualizar Projeções", key="update_projections"):
                # Update general assumptions
                st.session_state.infl_brl_pct = new_infl_brl
                st.session_state.infl_usd_pct = new_infl_usd
                st.session_state.cotacao_usd = new_cot
                st.session_state.n_viagens = new_n_viagens
                st.session_state.luxo_mensal = new_luxo
                # Actualize only the assumptions that remain user‑adjustable.  Dividend and
                # aspirational values are computed automatically from the income inputs and
                # are therefore not set here.  Philanthropy remains adjustable.
                st.session_state.filantropia_anual = new_fil
                # Recompute scales based on slider values
                new_scales = {}
                for cat, base_val in st.session_state.baseline_costs.items():
                    slider_val = slider_values.get(cat, base_val)
                    if base_val != 0:
                        new_scales[cat] = slider_val / base_val
                    else:
                        new_scales[cat] = 1.0
                st.session_state.scales = new_scales
                # Reset projections to force recalculation
                st.session_state.projections = None
                # No explicit rerun call; the session state update triggers a rerun automatically


if __name__ == "__main__":
    main()