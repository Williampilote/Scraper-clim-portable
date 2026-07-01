# Guide pas-à-pas — faire tourner le scraper sur ton PC

> Pourquoi sur ton PC ? Les serveurs GitHub ont des adresses IP « datacenter »
> que l'anti-bot de Leroy Merlin (DataDome) bloque (erreur 403). Ton PC, lui, a
> une **IP résidentielle** bien mieux acceptée. C'est donc la méthode gratuite
> la plus fiable pour surveiller le stock.

Le scraper vérifie le produit **toutes les 15 minutes** et t'envoie un **email**
(à `Auger939@gmail.com`) dès qu'il détecte une disponibilité en magasin.

---

## Étape 1 — Installer Python (une seule fois)

### Windows
1. Va sur https://www.python.org/downloads/ et clique sur **Download Python**.
2. Lance l'installateur. **⚠️ Coche « Add Python to PATH »** en bas de la 1ère
   fenêtre, puis clique **Install Now**.
3. À la fin, ferme l'installateur.

### macOS
1. Va sur https://www.python.org/downloads/ et installe la dernière version,
   **ou** ouvre le Terminal et tape `brew install python` (si tu as Homebrew).

---

## Étape 2 — Récupérer le projet

### Le plus simple (sans outils)
1. Ouvre la page du dépôt GitHub `Williampilote/Scraper-clim-portable`,
   branche `claude/portable-ac-tracker-bk5980`.
2. Bouton vert **« Code » → « Download ZIP »**.
3. **Décompresse** le ZIP dans un dossier facile à retrouver
   (ex. `Documents\scraper-clim`).

### Ou avec git (si tu connais)
```
git clone -b claude/portable-ac-tracker-bk5980 <url-du-depot>
```

---

## Étape 3 — Mettre ton mot de passe email

1. Dans le dossier, copie le fichier **`.env.example`** et renomme la copie en
   **`.env`** (juste `.env`, sans `.example`).
   - Windows affiche les extensions ? Sinon : Affichage → coche « Extensions de
     noms de fichiers ».
2. Ouvre `.env` avec le **Bloc-notes** (Windows) ou **TextEdit** (Mac).
3. Complète la ligne du mot de passe SMTP OVH :
   ```
   SMTP_PASSWORD=ton_mot_de_passe_ici
   ```
   Les autres lignes sont déjà bonnes (serveur OVH, expéditeur, destinataire).
4. Enregistre le fichier.

> 🔒 Ce fichier `.env` reste sur ton PC, il n'est jamais envoyé sur internet ni
> sur GitHub. Pense à **changer ce mot de passe chez OVH** puisqu'il a déjà été
> partagé en clair.

---

## Étape 4 — Lancer la surveillance

### Windows
- **Double-clique sur `run.bat`.**
- La première fois, il installe tout (1–2 min) puis démarre.
- Une fenêtre noire s'ouvre et reste ouverte : **laisse-la ouverte**, c'est elle
  qui surveille. Tu verras une ligne toutes les 15 min.

Si Windows affiche un avertissement « Windows a protégé votre PC » :
**Informations complémentaires → Exécuter quand même**.

### macOS / Linux
1. Ouvre le **Terminal** dans le dossier du projet.
2. Rends le script exécutable (une fois) puis lance-le :
   ```
   chmod +x run.sh
   ./run.sh
   ```
3. Laisse le terminal ouvert.

---

## Étape 5 — Vérifier que ça marche

Dans la fenêtre, tu dois voir des lignes comme :
```
Verification [leroymerlin] Climatiseur split mobile ...
  -> indisponible : produit indisponible (texte page)
Passage termine. Alertes envoyees : 0
```
- **« indisponible »** = normal, le produit n'est pas encore en stock. Le scraper
  continue tout seul et t'enverra un mail dès que ça change.
- **« bloque par anti-bot »** = ton IP est challengée par DataDome. Voir dépannage.
- **« DISPONIBLE » + « mail envoye »** = 🎉 tu vas recevoir l'email.

### Tester l'envoi d'email tout de suite
Mets dans `.env` la ligne `SEND_TEST_EMAIL=1`, relance : tu dois recevoir un mail
de test. Remets ensuite `SEND_TEST_EMAIL=0`.

---

## Garder la surveillance active

- Tant que la fenêtre/terminal est **ouvert** et le **PC allumé + connecté**,
  ça tourne.
- Si tu fermes la fenêtre ou éteins le PC, ça s'arrête : il suffira de relancer
  `run.bat` / `./run.sh`.
- Empêche la mise en veille du PC (Paramètres → Alimentation) pour ne rien rater.

---

## Dépannage

**« bloque par anti-bot (DataDome/captcha) »**
Ton IP est temporairement challengée. Solutions :
1. Ouvre `config.yaml`, passe `headless: true` à **`headless: false`** puis
   relance : une fenêtre Chromium visible s'ouvre, résous le captcha une fois ;
   ensuite DataDome te laisse tranquille un moment.
2. Réessaie plus tard, ou depuis une autre connexion.
3. En dernier recours : option proxy résidentiel (voir README, variable `PROXY_URL`).

**« Python n'est pas reconnu »** (Windows)
Python a été installé sans « Add to PATH ». Réinstalle-le en cochant la case.

**Changer la fréquence**
Le `900` dans la commande = 900 secondes = 15 min. Pour 10 min, remplace par
`600` dans `run.bat` / `run.sh`.

**Ajouter d'autres produits à surveiller**
Ouvre `config.yaml` et ajoute un bloc (voir le README, section « Ajouter un
produit »).
