<div align="center">

<!-- Bannière avec logo en filigrane -->
<img src="./assets/banner_watermark.png" alt="thibeq-sdk - Python SDK avec logo en filigrane" width="100%" style="max-width: 800px;">

<br>

[![PyPI version](https://img.shields.io/pypi/v/thibeq-sdk?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/thibeq-sdk/)
[![Python versions](https://img.shields.io/pypi/pyversions/thibeq-sdk.svg?style=for-the-badge&logo=python)](https://pypi.org/project/thibeq-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-FFD700.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Downloads](https://img.shields.io/pypi/dm/thibeq-sdk?style=for-the-badge&color=0A1628)]()

*Calcul de scores d'anomalie et conversions astronomiques*

### ⚠️ **AVERTISSEMENT BÊTA**

Cette API est en version bêta. **Ne l'utilisez PAS pour des applications cliniques, critiques ou de sécurité.**  
Usage recommandé : **Recherche et expérimentation uniquement**.

</div>

---

## Installation

```bash
pip install thibeq-sdk
```

## Démarrage rapide

```python
from thibeq_sdk import ThibEqClient

# Initialiser le client
client = ThibEqClient(
    base_url="http://api.thibequation.com",
    api_key="your-api-key"
)

# Calculer un score ThibEquation
result = client.score(
    G=0.6,  # Facteur Géométrique/Physique
    K=0.7,  # Facteur Contextuel
    S=0.4,  # Facteur Documentation
    C=0.5   # Coefficient Fiabilité Témoin
)
print(f"ThibScore: {result['thibscore']}")

# Convertir des coordonnées astronomiques
coords = client.convert(
    lat=46.03,
    lon=-73.11,
    utc="2025-11-03T21:15:00Z",
    az=257.3,
    alt=42.1
)
print(f"RA: {coords['ra_h']}h, Dec: {coords['dec_deg']}°")
```

## Fonctionnalités

### Calcul de Score ThibEquation

La formule ThibEquation quantifie l'anomalie d'une observation :

```
ThibScore = (G × w_G + K × w_K + S × w_S) × C × 100
```

- **G** (0-1): Facteur Géométrique/Physique
- **K** (0-1): Facteur Contextuel
- **S** (0-1): Facteur Documentation
- **C** (0-1): Coefficient Fiabilité Témoin

### Conversion de Coordonnées

Convertit des coordonnées horizontales (Azimut/Altitude) en coordonnées équatoriales (RA/Dec) avec calcul du Temps Sidéral Local (LST).

### Gestion des Erreurs

Le SDK inclut des exceptions personnalisées :

```python
from thibeq_sdk import (
    ThibEqError,
    ThibEqAuthError,
    ThibEqValidationError,
    ThibEqNetworkError
)

try:
    result = client.score(G=0.6, K=0.7, S=0.4, C=0.5)
except ThibEqAuthError:
    print("Authentification échouée")
except ThibEqValidationError as e:
    print(f"Paramètres invalides: {e}")
except ThibEqNetworkError as e:
    print(f"Erreur réseau: {e}")
```

### Configuration Avancée

```python
client = ThibEqClient(
    base_url="http://localhost:5000",
    api_key="your-key",
    timeout=10.0,      # Timeout en secondes (défaut: 5.0)
    max_retries=3      # Tentatives en cas d'erreur 502/503 (défaut: 1)
)
```

## Développement

### Installation des dépendances de développement

```bash
pip install -e ".[dev]"
```

### Tests

```bash
# Tests unitaires
pytest

# Tests avec coverage
pytest --cov=thibeq_sdk

# Smoke test (nécessite une API en cours d'exécution)
python test_smoke.py
```

### Linting et formatage

```bash
# Vérifier le code
ruff check .

# Formater le code
ruff format .

# Type checking
mypy thibeq_sdk.py
```

## Documentation

- **Repository**: [https://github.com/Thib4204/thibequation-api](https://github.com/Thib4204/thibequation-api)
- **Issues**: [https://github.com/Thib4204/thibequation-api/issues](https://github.com/Thib4204/thibequation-api/issues)

## Citation

Si vous utilisez ce SDK dans vos recherches, veuillez citer :

**Thibodeau, Pascal. (2025). THIBEQUATION – Certificat de complétion 2025 (v4.0). Zenodo.**  
[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.17510899-FFD700?style=for-the-badge&logo=doi)](https://doi.org/10.5281/zenodo.17510899)

```bibtex
@software{thibodeau_thibequation_2025,
  author       = {Thibodeau, Pascal},
  title        = {THIBEQUATION – Certificat de complétion 2025 (v4.0)},
  year         = 2025,
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.17510899},
  url          = {https://doi.org/10.5281/zenodo.17510899}
}
```

## Licence

MIT License - Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## Auteur

**Pascal Thibodeau** (Thib4204)  
[![ORCID](https://img.shields.io/badge/ORCID-0009--0005--7447--7703-A6CE39?style=for-the-badge&logo=orcid&logoColor=white)](https://orcid.org/0009-0005-7447-7703)

---

---

<div align="center">

<br>

<img src="./assets/logo_transparent.png" alt="ThibEquation" width="200">

<br><br>

**ThibEquation SDK Python v0.1.0**

⚠️ *API en bêta - Pas d'usage clinique/critique*

<br>

[![Repository](https://img.shields.io/badge/GitHub-thibequation--api-FFD700?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Thib4204/thibequation-api)

<br>

</div>
