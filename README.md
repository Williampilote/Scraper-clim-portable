# Scraper Clim Portable

Surveille la disponibilite de climatiseurs mobiles chez les grandes enseignes
(Leroy Merlin en priorite, puis Darty / Boulanger / autres) et **envoie un email**
des qu'un produit devient disponible — en particulier **en retrait magasin** pour
Leroy Merlin (alerte si au moins un magasin en France a le stock).

Le suivi tourne **en continu** via un **GitHub Actions planifie** (toutes les ~15 min),
donc sans laisser de PC allume.

## Comment ca marche

- `config.yaml` liste les produits a suivre (URL + enseigne + mode).
- Pour chaque produit, un **adaptateur** (`src/adapters/`) ouvre la page avec
  **Playwright + Chromium**, contourne le bandeau cookies, et detecte la dispo
  (interception des API de stock + repli sur le texte de la page).
- A chaque passage de **disponible** (transition indisponible -> disponible),
  un **email** est envoye (`src/notifier.py`). L'etat est garde dans `state.json`
  pour ne pas spammer.

## Configuration des secrets (GitHub)

Dans le depot : **Settings -> Secrets and variables -> Actions -> New repository secret**.

| Secret          | Valeur                                  | Obligatoire |
|-----------------|-----------------------------------------|-------------|
| `SMTP_PASSWORD` | mot de passe SMTP                       | **OUI**     |
| `SMTP_USER`     | `noreply@whitetelecom.fr`               | recommande  |
| `SMTP_HOST`     | `ssl0.ovh.net`                          | optionnel*  |
| `SMTP_PORT`     | `587`                                   | optionnel*  |
| `SMTP_SECURITY` | `starttls`                              | optionnel*  |
| `MAIL_FROM`     | `noreply@whitetelecom.fr`               | optionnel*  |
| `MAIL_TO`       | `Auger939@gmail.com`                    | optionnel*  |

\* Valeurs par defaut deja codees ; ne definir que pour surcharger.

> ⚠️ Ne jamais mettre le mot de passe dans le code ni dans un commit.
> Il est conseille de **changer ce mot de passe** s'il a deja transite en clair.

## Lancer en local (test)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium

cp .env.example .env      # puis renseigne SMTP_PASSWORD
python -m src.main --once               # un passage
python -m src.main --loop --interval 900  # boucle locale, pause 15 min
```

Tester l'envoi de mail seul : mettre `SEND_TEST_EMAIL=1` dans `.env` puis relancer.

## Ajouter un produit

Editer `config.yaml` :

```yaml
  - name: "Mon produit"
    store: leroymerlin   # ou darty | boulanger | generic
    url: "https://..."
    mode: store_pickup   # ou online
    enabled: true
```

## Limites connues

- **Anti-bot** (DataDome/Akamai) : un blocage ponctuel est detecte et **n'envoie pas**
  de fausse alerte (statut "erreur"). Si les blocages sont frequents, on pourra ajouter
  un mode furtif (`playwright-stealth`) ou un proxy.
- **Stock magasin LM** : repose sur l'API interne de Leroy Merlin (susceptible d'evoluer) ;
  un repli sur le texte de la page limite la casse. La logique est isolee dans
  `src/adapters/leroymerlin.py` pour faciliter la maintenance.
- **Cron GitHub** : intervalle reel parfois decale de quelques minutes.
