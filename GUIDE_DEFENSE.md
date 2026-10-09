# Guide de défense — Learn2Slither

Ce guide est pour toi, pas pour le dépôt (ne le commite pas, ou garde-le hors du dossier du projet).
Objectif : pouvoir répondre à « que fait cette ligne ? », « où est-ce dans le code ? », « pourquoi ce choix ? ».

---

## 0. Comment l'étudier (4 séances de 30-45 min)

1. **Séance 1 : la boucle globale** (section 1) et `environment.py` (section 2). Lance le jeu en visuel, regarde le terminal.
2. **Séance 2 : `interpreter.py`** (section 3). C'est le cœur : vision, état, récompenses.
3. **Séance 3 : `agent.py`** (section 4). Apprends la formule de Q-learning par cœur et sache la dérouler sur un exemple.
4. **Séance 4 : `main.py` + `display.py`** (sections 5 et 6), puis la section 8 (démos) et la section 9 (questions).

Règle d'or : **ferme le guide, ouvre le code, et explique à voix haute**. Si tu bloques sur une ligne, c'est qu'il faut la relire ici.

---

## 1. La boucle globale (à savoir dessiner au tableau)

```
          ┌────────────── Environment (Board) ◄──────────────┐
          │ (le jeu complet : serpent, pommes, murs)         │
          ▼                                                  │ action (0-3)
   Interpreter                                               │
   look() → encode()   ──── state (un entier) ──►  Agent ────┘
   reward(event)       ──── reward (un nombre) ──►  (Q-table)
```

À chaque pas de temps (`run_session` dans `main.py`) :
1. L'**interpréteur** regarde le plateau depuis la tête (`look`), en fait un entier (`encode`) : **l'état**.
2. L'**agent** reçoit cet entier et choisit une action (`choose`).
3. Le **plateau** applique l'action (`step`) et renvoie un événement : `EMPTY`, `GREEN`, `RED` ou `DEAD`.
4. L'**interpréteur** transforme l'événement en **récompense** (`reward`).
5. L'**agent** met à jour sa Q-table avec (état, action, récompense, nouvel état) (`learn`).
6. On recommence avec le nouvel état, jusqu'à la mort.

**Phrase clé de défense :** « L'agent ne voit jamais le plateau. Il reçoit un entier calculé par l'interpréteur à partir de la vision de la tête, et un nombre pour la récompense. »
Preuve dans le code : `agent.py` n'importe **rien** de `environment.py` ni de `interpreter.py`.

---

## 2. `environment.py` — le jeu

### Constantes (haut du fichier)
- `UP, LEFT, DOWN, RIGHT = 0, 1, 2, 3` : les 4 actions sont des numéros. Elles sont **absolues** (HAUT veut toujours dire vers le haut de l'écran, quel que soit le sens du serpent).
- `ACTION_NAMES` : sert à afficher `UP`, `LEFT`... dans le terminal.
- `MOVES` : pour chaque action, le déplacement `(delta_ligne, delta_colonne)`. Exemple : `UP = (-1, 0)` car la ligne 0 est en haut, monter diminue le numéro de ligne.
- `EMPTY, GREEN, RED, DEAD` : ce qui s'est passé après un coup.
- `START_LENGTH = 3` : longueur de départ imposée par le sujet.
- `MIN_SIZE = 5` : en dessous, pas la place pour un serpent de 3 et 3 pommes.

Coordonnées : toujours `(ligne, colonne)`, ligne 0 en haut.

### `Board.__init__(size, seed)`
1. Vérifie que `size` est un entier ≥ 5, sinon `ValueError` (c'est ce qui permet un message propre si on tape `-size 3`).
2. `self.rng = random.Random(seed)` : **un générateur aléatoire propre au plateau**. Avec la même `seed`, la partie est reproductible (utile pour une démo : « je relance et tu verras exactement la même partie »).
3. Appelle `reset()`.

### `reset()` — nouvelle partie (= nouvelle session)
- Serpent : `_random_snake()`.
- Deux listes `greens` et `reds`, puis `_place` : 2 pommes vertes et 1 rouge.
- `steps = 0` (durée de la session), `max_length = 3` (longueur max atteinte).

### `_random_snake()`
Boucle : tire une **tête** au hasard et une **direction** au hasard, construit les 3 cases `tête - i × direction` (i = 0, 1, 2), c'est-à-dire la tête puis 2 cases derrière elle. Si une case sort du plateau, on recommence. Résultat : serpent **aléatoire** et **contiguë** par construction.

### `_place(apples)`
Calcule les cases occupées (serpent + pommes), liste les cases libres, en choisit une au hasard. S'il n'y a plus de case libre (plateau rempli par le serpent), **on ne fait rien** au lieu de planter.

### `step(action)` — LA fonction à maîtriser
```
self.steps += 1
nouvelle tête = tête actuelle + MOVES[action]
si hors plateau ou sur une case du serpent → return DEAD
insérer la nouvelle tête au début de la liste
si pomme verte : retirer la pomme, en replacer une, event = GREEN       (on garde la queue → +1)
sinon si rouge : retirer la pomme, pop() deux fois, replacer, event = RED  (→ −1)
sinon : pop() une fois, event = EMPTY                                  (même longueur)
si le serpent est vide → DEAD
mettre à jour max_length, return event
```
L'astuce à expliquer : **on ajoute toujours la tête, puis on enlève 0, 1 ou 2 segments de queue**. Un seul mécanisme pour les trois cas.

- Le serpent est une **liste** `[tête, ..., queue]`.
- Mur : `not self._inside(head)`. Corps : `head in self.snake`.
- **Choix à défendre :** la queue est mortelle aussi. Dans les jeux classiques on peut aller sur la case que la queue vient de quitter ; ici on a simplifié car la vision affiche `S` pour tout segment et l'agent traite `S` comme un danger. Simple et cohérent.
- Cas limite : longueur 1 + pomme rouge → tête ajoutée (2), deux `pop` (0) → serpent vide → `DEAD`. C'est la règle « longueur 0 = game over ».

### `symbol_at(cell)`
Renvoie `W` (hors plateau), `H`, `S`, `G`, `R` ou `0`. **L'ordre des tests compte** : on teste mur, tête, corps, pommes, puis vide. C'est la seule porte d'entrée de l'interpréteur vers le plateau.

---

## 3. `interpreter.py` — vision, état, récompenses

### `REWARDS` et `reward(event)`
| Événement | Récompense | Pourquoi |
|---|---|---|
| `GREEN` | +30 | Le but : grandir. |
| `RED` | −15 | Mauvais, mais moins grave que mourir (on peut survivre avec 3 → 2). |
| `EMPTY` | −1 | Petit coût par coup : sans lui, tourner en rond ne coûte rien. |
| `DEAD` | −100 | Le pire : mur, corps ou longueur 0. |

**Justification des ordres de grandeur :** mort ≪ rouge < vide < vert. La mort doit coûter bien plus que 30 pas à vide, sinon l'agent préférerait mourir vite plutôt que chercher une pomme. Le sujet laisse le choix des valeurs, il impose juste l'ordre logique.

### `look(board)` — la vision
- Pour chaque direction, on part de la tête et on avance case par case.
- `ray += board.symbol_at(...)` : on accumule les symboles, **du plus proche au plus lointain**.
- La boucle s'arrête quand le dernier symbole est `W` (le mur est atteint, `symbol_at` ne renvoie `W` que hors plateau).
- Résultat : `{UP: "000RG00W", LEFT: "0000W", ...}`.
- Le corps **ne bloque pas** la vue (comme sur la figure du sujet où on voit `S 0 W`), seul le mur termine le rayon.

### `render(seen)` — l'affichage en croix
- `left = seen[LEFT][::-1]` : on inverse (`[::-1]`) pour que le mur lointain soit à gauche.
- `pad` : espaces égaux à la longueur de la partie gauche, pour que les lignes du haut et du bas soient alignées sur la colonne de la tête.
- Lignes du haut : `seen[UP][::-1]` inversé (le mur en haut). Ligne du milieu : `left + "H" + seen[RIGHT]`. Lignes du bas : `seen[DOWN]` tel quel.
- Résultat identique à la figure du sujet (vérifié par un test).

### `_describe(ray)` — résumer UNE direction en un nombre de 0 à 11
1. `stops` : positions des symboles `W` ou `S` dans le rayon (les obstacles).
2. `first_obstacle = stops[0]` : le **premier** obstacle. Il existe toujours car un rayon finit par `W`.
3. `free = ray[:first_obstacle]` : les cases libres avant l'obstacle.
4. `distance = min(first_obstacle, 2)` : 0 = obstacle collé à la tête, 1 = une case libre puis obstacle, 2 = loin. **On plafonne à 2** : c'est ce qui rend l'état **indépendant de la taille du plateau** (bonus).
5. `green = "G" in free`, `red = "R" in free` : y a-t-il une pomme verte / rouge **avant** l'obstacle ?
6. Retour : `(distance * 2 + green) * 2 + red` : 3 distances × 2 × 2 = **12 valeurs** (0 à 11). Les booléens valent 0 ou 1 en Python.

Pourquoi ne pas voir une pomme derrière un obstacle ? Parce qu'en ligne droite elle est inatteignable ; ça réduit le nombre d'états sans perdre d'information utile.

### `encode(seen)` — 4 nombres en un seul entier
```python
state = 0
for direction in (UP, LEFT, DOWN, RIGHT):
    state = state * 12 + _describe(seen[direction])
```
C'est une **écriture en base 12** à 4 chiffres : UP est le chiffre de gauche, RIGHT celui de droite. Il y a donc 12⁴ = **20 736 états possibles**. On l'utilise comme clé du dictionnaire Q-table.

### Défense « tu ne donnes que la vision ? »
- Tout part de `look()`, qui n'appelle que `symbol_at` en s'éloignant de la tête dans 4 directions.
- `encode()` ne reçoit que `seen`, jamais le plateau.
- La distance (0, 1, 2+) se déduit de la **position** des symboles dans le rayon, donc c'est bien de l'information visible.

---

## 4. `agent.py` — Q-table et apprentissage

### Vocabulaire à maîtriser
- **Q-table** : un dictionnaire `self.q` qui associe à chaque état une liste de 4 nombres `[Q(UP), Q(LEFT), Q(DOWN), Q(RIGHT)]`. **Q(s, a)** = « combien de récompense future totale j'espère en faisant l'action a dans l'état s ».
- **α (alpha) = 0,1** : vitesse d'apprentissage. Petit = on change d'avis lentement, stable.
- **γ (gamma) = 0,9** : importance du futur. Proche de 1 = on pense long terme. 0,9 signifie qu'une récompense dans 10 coups compte environ 35 % de sa valeur (0,9¹⁰ ≈ 0,35).
- **ε (epsilon)** : probabilité de jouer **au hasard** (exploration).

### `__init__`
Stocke les hyperparamètres, `sessions = 0` (nombre de sessions apprises), `q = {}` (vide au début), `rng` (aléatoire de l'agent, reproductible avec `-seed`), et `learn_enabled` (l'interrupteur de `-dontlearn`).

### `choose(state)` — epsilon-greedy
```
si on apprend ET tirage < epsilon : action au hasard           ← exploration
sinon : prendre l'action de plus grande valeur Q de cet état    ← exploitation
        (si égalité, ou état inconnu : au hasard parmi les ex æquo)
```
- État inconnu → `self.q.get(state, [0.0]*4)` : on ne crée **pas** la ligne dans la table (important en `-dontlearn` : la table ne bouge pas du tout).
- En `-dontlearn`, `epsilon` est ignoré : pas d'exploration pendant l'évaluation. C'est ce qui donne les meilleures performances. Le hasard restant vient des égalités.

### `learn(state, action, reward, next_state, done)` — la formule
```
Q(s,a) ← Q(s,a) + α × ( reward + γ × max Q(s', ·) − Q(s,a) )
```
Lecture :
- `reward + γ × max Q(s',·)` est la **cible** : ce que je viens de gagner + la meilleure valeur future que je connais depuis l'état suivant.
- `cible − Q(s,a)` est l'**erreur** : de combien je m'étais trompé.
- On corrige Q(s,a) d'une fraction α de cette erreur.
- Si `done` (le serpent est mort), il n'y a **pas de futur** : cible = `reward`.
- `if not self.learn_enabled: return` : c'est `-dontlearn`, la récompense est ignorée et la table ne change pas.
- `setdefault(state, [0.0]*4)` : crée la ligne à zéro la première fois qu'on rencontre un état.

**Exemple chiffré à savoir faire de tête.** Q = 0 partout, α = 0,5, le serpent mange une pomme verte (+30) et l'état suivant a Q max = 10 :
cible = 30 + 0,9 × 10 = 39 ; Q ← 0 + 0,5 × (39 − 0) = **19,5**.

### `end_session()`
Après chaque session d'apprentissage : `sessions += 1` et `epsilon = max(epsilon_min, epsilon × 0,995)`.
- Départ : ε = 1 (**100 % de hasard**), puis il diminue de 0,5 % par session.
- Après 10 sessions : ≈ 0,95. Après 100 : ≈ 0,61. Après environ 920 : il atteint le plancher 0,01 (1 % de hasard).
- **C'est pourquoi les modèles à 1, 10 et 100 sessions sont faibles** : l'agent a surtout joué au hasard et connaît peu d'états (1, 23 et 96 états connus pour les modèles fournis, contre 894 à 10 000 sessions). Les modèles à 1000+ sessions montrent l'apprentissage.
- Pourquoi un plancher à 0,01 ? Pour ne jamais arrêter totalement d'explorer pendant l'entraînement.

### `save(path)` / `load(path)`
- Format **JSON** : lisible à l'œil, facile à montrer à l'évaluateur. Il contient `format`, `sessions`, `epsilon` et `q`.
- Les clés JSON doivent être des chaînes : on écrit `str(state)` et on relit `int(key)`.
- On sauvegarde `epsilon` et `sessions` pour pouvoir **reprendre un entraînement** là où on l'avait laissé.
- `save` écrit dans un fichier `.tmp` puis `os.replace` : jamais de modèle à moitié écrit si on coupe en plein milieu.
- `load` valide tout (`_check`) : format, types, 4 valeurs finies par ligne, `epsilon` entre 0 et 1. Un fichier invalide lève `ModelError` avec un message clair, jamais un plantage.

---

## 5. `main.py` — la boucle et les options

### `bounded(kind, low, high, label)`
Fabrique une fonction de validation pour `argparse` : convertit en `int` ou `float`, refuse le texte, `nan` et les valeurs hors bornes, avec un message clair (`ArgumentTypeError`).

### `parse_args`
- Options à **un seul tiret** comme dans le sujet (`-sessions`, `-dontlearn`, `-step-by-step`...). `argparse` le permet.
- `allow_abbrev=False` : pas d'abréviation implicite.
- Valeurs par défaut : 1 session, visuel activé, vitesse 10 coups/s, taille 10.

### `check_save_path`
Vérifie **avant l'entraînement** qu'on pourra sauver (pas un nom vide, pas un dossier, dossier créable et accessible en écriture). Évite de perdre une heure d'entraînement pour une faute de frappe dans `-save`.

### `run_session(board, agent, view, args, verbose, caption)` — À SAVOIR PAR CŒUR
1. `board.reset()` : nouvelle partie.
2. `idle_limit = size² × 2` (200 sur 10×10) et `idle = 0` : compteur de coups sans pomme.
3. Première observation : `seen = look(board)` puis `state = encode(seen)`.
4. **Boucle :**
   - dessine la fenêtre ; si `-step-by-step`, attend une touche (ou Entrée dans le terminal si pas de fenêtre) ;
   - si `verbose` : affiche la vision (`render`) ;
   - `action = agent.choose(state)` et affiche son nom ;
   - `event = board.step(action)` ;
   - `done = (event == DEAD)` ;
   - si pas mort : nouvelle observation → `next_state` ; sinon `next_state = None` (on **ne lit pas** un plateau de serpent mort, pas de crash sur un serpent vide) ;
   - `agent.learn(state, action, reward(event), next_state, done)` ;
   - si mort, `break` ;
   - `state = next_state` ; compteur : remis à 0 si pomme mangée, +1 sinon ; si `idle ≥ idle_limit`, `break`.
5. `agent.end_session()` (décroissance d'epsilon) et retour de `(max_length, steps)`.

**La limite de 200 coups sans pomme :** choix à assumer clairement. Sans elle, un modèle déterministe peut tourner en boucle indéfiniment, ce qui ressemble à un plantage. Elle ne s'applique que dans ce cas pathologique (le serpent entraîné mange des pommes bien avant).

### `open_display(args)`
Si `-visual off` : rien. Sinon crée la fenêtre. Si pygame ou l'écran manquent (`ImportError`, `RuntimeError`), **avertit et continue sans fenêtre** au lieu de planter.

### `summary(results)`
Affiche `Game over, max length = X, max duration = Y` (format du sujet) puis la moyenne et le **pourcentage de sessions ≥ 10**, très utile pour répondre au critère « plus de 50 % ».

### `run(args)` — le chef d'orchestre
1. `Agent(learn=not args.dontlearn)` : c'est ici que `-dontlearn` est branché.
2. `-load` : charge ; erreur → message, code de sortie 1.
3. `-save` : vérifie le chemin tout de suite.
4. Crée le plateau (`-size`) et la fenêtre.
5. Boucle sur les sessions. `verbose` est vrai si fenêtre ou pas-à-pas : la vision est affichée à chaque coup. En mode silencieux, une ligne de progression tous les 10 %.
6. `except KeyboardInterrupt` : Ctrl+C, fermeture de fenêtre ou Échap : arrêt propre.
7. `finally` : ferme la fenêtre. Puis résumé, et **sauvegarde même si on a interrompu**.

### `main()` et `snake`
`snake` est un mini-script qui appelle `main()` (il n'a pas d'extension `.py`, donc `flake8 .` ne le lit pas, mais il passe quand même flake8). `main()` convertit aussi l'erreur « tube fermé » (`./snake ... | head`) en sortie silencieuse.

---

## 6. `display.py` — la fenêtre

- `pygame.display.init()` : on n'initialise **que la vidéo** (pas l'audio).
- `cell` : taille d'une case en pixels, adaptée à la taille du plateau.
- `draw()` : traite les événements (fermer = `KeyboardInterrupt`), remplit le fond, dessine pommes, serpent (tête plus foncée) et grille, `flip()` affiche, `clock.tick(speed)` impose la **vitesse** (coups par seconde).
- `wait_key()` : bloque jusqu'à Espace, Entrée ou Flèche droite (**pas-à-pas**) ; Échap quitte.
- C'est une **vue pure** : elle lit le plateau, ne le modifie jamais, et n'est même pas importée en mode `-visual off`.
- Couleurs du sujet : pomme verte, pomme rouge, serpent bleu.

---

## 7. Où trouver quoi (grille de correction → code → démo)

| Critère de la grille | Où dans le code | Démo |
|---|---|---|
| Règles du plateau | `environment.py` : `reset`, `step` | `./snake -sessions 1 -seed 3` |
| Vitesse lisible | `Display.draw` (`clock.tick`), option `-speed` | `./snake -speed 5` |
| Vision affichée dans le terminal | `main.run_session` (`print(render(seen))`), `interpreter.render` | idem, regarder le terminal |
| **Seule la vision est donnée à l'agent** | `interpreter.look/encode` ; `agent.choose(state)` ne reçoit qu'un entier ; `agent.py` n'importe rien du jeu | ouvrir `agent.py`, montrer les imports |
| Action affichée + serpent bouge | `ACTION_NAMES` + `board.step` | terminal : `UP`, `LEFT`... |
| Récompenses | `interpreter.REWARDS` | montrer le tableau |
| Q-value et son calcul | `agent.learn` | dérouler l'exemple chiffré |
| Hasard de temps en temps | `agent.choose` (epsilon) | `./snake -sessions 3` : parties différentes |
| Entraîner N sessions | option `-sessions` | `./snake -sessions 10 -save models/x.json -visual off` |
| Export / import de modèles | `agent.save` / `load`, options `-save` / `-load` | ouvrir `models/100sess.json` |
| Utiliser sans apprendre | `-dontlearn` → `learn_enabled` | `./snake -load models/100sess.json -dontlearn -sessions 10` |
| Pas-à-pas | `-step-by-step` → `wait_key` | `... -step-by-step`, touche Espace |
| Architecture | 3 modules : `environment`, `interpreter`, `agent` | montrer le schéma section 1 |
| ≥ 10 dans plus de 50 % des sessions | `summary` affiche le pourcentage | `./snake -visual off -load models/10000sess.json -dontlearn -sessions 100` |
| Bonus : taille variable | `-size` → `Board(size)` ; état plafonné à 2 (`_describe`) | `./snake -load models/10000sess.json -dontlearn -size 12` |
| Norme | `flake8 .` | taper la commande devant lui |
| Aucun crash | `test_robustness.py` | `python -m unittest -v test_robustness` |

### Démo « je lis la Q-table »
```bash
python3 - <<'EOF'
from agent import Agent
a = Agent(); a.load("models/10000sess.json")
print(len(a.q), "états connus sur", 12 ** 4)
# serpent collé au mur du haut, pomme verte visible à gauche, le reste libre
state = ((0 * 12 + 10) * 12 + 8) * 12 + 8
print("Q [UP, LEFT, DOWN, RIGHT] =", [round(x, 1) for x in a.q[state]])
EOF
```
Résultat sur le modèle fourni : environ `[-83.3, 28.7, 4.7, 4.4]`.
Lecture : **UP vaut −83 (mur collé = mort), LEFT vaut +29 (pomme verte visible de ce côté)**. L'agent a donc appris tout seul « fuis le mur, va vers la pomme verte ». Le modèle ne connaît que 894 états sur 20 736 : seuls les états réellement rencontrés sont stockés (d'où le dictionnaire et non un tableau complet).

Décoder un état (écriture base 12, chiffres lus de droite à gauche : RIGHT, DOWN, LEFT, UP) :
chiffre = `(distance × 2 + vert) × 2 + rouge`. Exemple : 10 = (2 × 2 + 1) × 2 + 0 → loin, pomme verte, pas de rouge.

---

## 8. Défendre les choix (réponses prêtes)

**Pourquoi une Q-table et pas un réseau de neurones ?**
Le sujet autorise les deux. L'espace d'états est petit (20 736 états, environ 900 réellement visités), donc une table exacte suffit : plus simple, entièrement explicable, entraînement rapide, aucune dépendance (pas de numpy ni de PyTorch).

**Pourquoi un dictionnaire plutôt qu'un tableau ?**
Seuls ~900 états sur 20 736 apparaissent vraiment. Le dictionnaire ne stocke que ceux-là et la sauvegarde reste petite.

**Que contient ton état ? Est-ce que tu triches ?**
Pour chaque direction : distance au premier obstacle (0, 1, ou 2+), pomme verte avant l'obstacle, pomme rouge avant l'obstacle. Tout vient de `look()`, donc de la vision de la tête. L'agent ne reçoit que cet entier.

**Pourquoi plafonner la distance à 2 ?**
Moins d'états donc apprentissage plus rapide, et l'état ne dépend plus de la taille du plateau : le même modèle joue sur du 8×8 comme du 15×15 (bonus).

**Pourquoi −1 à chaque coup ?**
Pour décourager de tourner en rond ou d'errer : chaque coup inutile coûte, donc l'agent cherche les pommes.

**Pourquoi −100 pour la mort ?**
La mort doit être bien pire que n'importe quel détour. Elle fait aussi perdre toutes les récompenses futures.

**Pourquoi γ = 0,9 ?**
Pour que l'agent voie un peu plus loin que le prochain coup (se diriger vers une pomme visible), sans que les valeurs divergent.

**Pourquoi α = 0,1 ?**
Compromis : assez rapide pour apprendre, assez lent pour ne pas osciller à cause de la part de hasard du jeu (position des nouvelles pommes).

**Pourquoi epsilon part de 1 et décroît ?**
Au début, la table est vide : mieux vaut explorer. Plus tard, on exploite ce qui a été appris. Le plancher à 0,01 garde un peu d'exploration.

**Pourquoi le serpent meurt-il encore parfois avec le meilleur modèle (~4 % sous 10) ?**
L'état est une **observation partielle** : il ne voit que 4 lignes, pas tout le corps. Il peut s'enfermer dans une spirale sans le voir venir. C'est une limite de la consigne (vision limitée), pas un bug.

**Que se passe-t-il en `-dontlearn` ?**
`learn_enabled = False` : `learn()` ne fait rien, `choose()` n'explore plus, `end_session()` ne change rien. Le fichier modèle reste identique (testé).

**Pourquoi la limite de 200 coups sans pomme ?**
Pour qu'aucun modèle ne puisse bloquer le programme dans une boucle infinie. Elle n'est pas dans le sujet, c'est une protection que j'assume.

**Pourquoi JSON ?**
Lisible, vérifiable par l'évaluateur, validation stricte à la lecture.

**Pourquoi des actions absolues ?**
Le sujet définit 4 actions UP, LEFT, DOWN, RIGHT. Elles s'alignent avec la vision en croix : chaque direction de la vision correspond directement à une action.

**Pourquoi la queue est-elle mortelle ?**
Simplification cohérente avec la vision : tout `S` est un danger.

**Si on met epsilon à 0, l'agent apprend-il encore ?**
Oui, ici, un peu moins bien sur le long terme : voir l'expérience 2 (section 9). Les Q partent de 0 et les récompenses sont surtout négatives, donc les actions déjà essayées perdent face aux actions inconnues. Epsilon reste utile : il garantit l'exploration et le sujet le demande.

**Que fait `max Q(s', ·)` ?**
Il prend la meilleure valeur connue de l'état suivant, comme si on jouait ensuite au mieux. C'est ce qui fait de Q-learning un algorithme *off-policy*.

---

## 9. Expériences en direct (pour prouver que tu maîtrises)

1. **Changer une récompense (résultats mesurés, 1000 sessions, 300 parties de test).**
   Référence : longueur moyenne 14,9 et 69 % des sessions à 10 ou plus. Puis, une seule valeur modifiée dans `REWARDS` (`interpreter.py`) à la fois :
   - `DEAD: 0` (la mort ne coûte rien) : longueur moyenne 3,0, 0 % : le serpent ne cherche plus à survivre.
   - `GREEN: -5` (manger du vert est puni) : 3,6 et 1 %.
   - `GREEN: 0` : 5,5 et 9 %.
   - `EMPTY: 0` (aucun coût par coup) : 6,5 et 18 %.
   Cela démontre que **les récompenses pilotent le comportement**. Réentraîne avec `./snake -sessions 1000 -save /tmp/x.json -visual off`, puis évalue avec `-dontlearn`.
   Attention : mettre `RED: +15` ne casse presque rien (13,7 et 68 %) car le vert rapporte toujours plus ; ne montre pas celle-là.
2. **Exploration : une surprise à connaître.** En mettant `epsilon=0` (aucun coup aléatoire par epsilon), l'agent apprend quand même (15,8 et 78 % sur 1000 sessions). Pourquoi : les valeurs Q partent de 0 et presque toutes les récompenses sont négatives, donc une action essayée devient moins bonne que celles pas encore essayées, et le départage aléatoire des égalités pousse à essayer les autres. Si on te pose la question « à quoi sert epsilon alors ? » : il **garantit** l'exploration quel que soit le réglage des récompenses, et le sujet l'exige (« l'agent prend parfois des actions aléatoires »). Sur ce problème précis, il n'est pas la seule source d'exploration.
3. **Comparer les modèles.** Lance `-dontlearn -sessions 100 -visual off` sur 1, 10, 100, 1000, 10000 : montre la progression des pourcentages.
4. **Même graine, même partie.** `./snake -sessions 1 -seed 3` deux fois : même partie. Preuve de la reproductibilité.
5. **Autre taille.** `-size 8`, `-size 15` avec le même modèle : bonus.

(Après chaque expérience : `git checkout interpreter.py agent.py` pour revenir à l'état d'origine.)

---

## 10. Auto-test : réponds sans regarder

1. Dessine le schéma environnement / interpréteur / agent avec ce qui circule.
2. Que contient exactement l'état ? Combien d'états possibles ? Pourquoi 12 ?
3. Dans `step`, comment le serpent grandit-il, rétrécit-il, reste-t-il identique ?
4. Écris la formule de mise à jour de Q et explique chaque terme.
5. Que vaut Q après un coup : Q = 0, α = 0,5, récompense +30, Q max suivant = 10 ?
6. Qu'est-ce qui change entre `-dontlearn` et le mode normal, ligne par ligne ?
7. Pourquoi les modèles 1, 10, 100 sont-ils faibles ?
8. Où prouves-tu que l'agent ne voit que la vision ?
9. Comment `-size` fonctionne-t-il avec le même modèle ?
10. Que se passe-t-il si on passe `-sessions abc`, `-load` sur un fichier cassé, ou si on ferme la fenêtre ?
11. Pourquoi `next_state = None` quand le serpent meurt ?
12. À quoi sert `end_session` ?
13. Que contient un fichier modèle ? Pourquoi sauver `epsilon` ?
14. Pourquoi aucun import de `environment` dans `agent.py` ?
15. Quelles sont les limites de ton agent, honnêtement ?

Si tu hésites sur une réponse, retourne à la section correspondante, puis refais la question.
