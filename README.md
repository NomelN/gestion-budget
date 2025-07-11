# Application de Suivi de Budget

Une application web simple développée avec Flask et SQLAlchemy pour suivre les revenus et les dépenses.

## Fonctionnalités

- **Gestion des Transactions :** Ajouter, modifier et supprimer des transactions.
- **Transactions Récurrentes :** Possibilité d'ajouter des transactions qui se répètent (hebdomadaire, mensuel, annuel).
- **Tableau de Bord :** Vue d'ensemble du solde actuel, des revenus et dépenses totaux.
- **Page de Rapports :** Visualisation des données financières avec un graphique en barres mensuel et un tableau de synthèse.
- **Base de Données :** Utilise SQLAlchemy pour la gestion de la base de données SQLite avec Alembic pour les migrations.
- **Interface :** Construite avec TailwindCSS, HTMX pour les interactions dynamiques, et Alpine.js.

## Installation et Lancement

Suivez ces étapes pour lancer le projet en local.

**1. Prérequis**

- Python 3.x
- [uv](https://github.com/astral-sh/uv)

**2. Cloner le projet**

```bash
git clone <URL_DU_PROJET>
cd <NOM_DU_DOSSIER>
```

**3. Installer uv**

`uv` est un résolveur de paquets et un installateur Python extrêmement rapide. Si vous ne l'avez pas encore, installez-le avec la commande suivante :

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**4. Créer l'environnement virtuel et installer les dépendances**

Créez un environnement virtuel et installez les dépendances du projet avec `uv` :

```bash
uv venv
source .venv/bin/activate  # Sur Windows, utilisez `.venv\Scripts\activate`
uv pip install -r requirements.txt
```

**5. Initialiser la base de données**

Ce projet utilise Alembic pour gérer les migrations de la base de données. Pour créer la base de données et appliquer les migrations, exécutez la commande suivante :

```bash
alembic upgrade head
```

**6. Lancer l'application**

```bash
uv python run.py
```

L'application sera accessible à l'adresse `http://127.0.0.1:5000`.
