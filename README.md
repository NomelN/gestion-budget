# Application de Suivi de Budget

Une application web simple développée avec Flask et SQLAlchemy pour suivre les revenus et les dépenses.

## Fonctionnalités

- **Gestion des Transactions :** Ajouter, modifier et supprimer des transactions.
- **Transactions Récurrentes :** Possibilité d'ajouter des transactions qui se répètent (hebdomadaire, mensuel, annuel).
- **Tableau de Bord :** Vue d'ensemble du solde actuel, des revenus et dépenses totaux.
- **Page de Rapports :** Visualisation des données financières avec un graphique en barres mensuel et un tableau de synthèse.
- **Base de Données :** Utilise SQLAlchemy pour la gestion de la base de données SQLite.
- **Interface :** Construite avec TailwindCSS, HTMX pour les interactions dynamiques, et Alpine.js.

## Installation et Lancement

Suivez ces étapes pour lancer le projet en local.

**1. Prérequis**

- Python 3.x
- pip

**2. Cloner le projet**

```bash
git clone <URL_DU_PROJET>
cd <NOM_DU_DOSSIER>
```

**3. Installer les dépendances**

Créez un environnement virtuel (recommandé) et installez les paquets nécessaires :

```bash
python3 -m venv venv
source venv/bin/activate  # Sur Windows, utilisez `venv\Scripts\activate`
pip install -r requirements.txt
```

**4. Initialiser la base de données**

La première fois, vous devez créer le schéma de la base de données :

```bash
python3 init_db.py
```

**5. Lancer l'application**

```bash
python3 app.py
```

L'application sera accessible à l'adresse `http://127.0.0.1:5000`.
