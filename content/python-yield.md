Title: Yield : cédez la priorité
Date: 2018-06-16 20:00
Category: dev
Tags: python, fp

![Johnny Depp / Benicio del Toro]({filename}/images/las_vegas_parano.jpg "We can’t stop here. This is bat country.")

`yield` est une instruction bien connue des développeurs Python expérimentés, mais peu utilisée par les plus débutants. Pourtant, le concept est assez simple à appréhender et peut s'avérer pratique dans de nombreux cas.

Yield peut se traduire par retourner / rendre / céder. En Python, il permet à une fonction de rendre la main, avant la fin de son exécution. Ce qui est opportun pour exécuter graduellement du code (via un "générateur"). C’est aussi ce mécanisme qui est à l’œuvre dans les coroutines.

Dans les tutoriels, je vois souvent des exemples de générateurs pour calculer des suites de nombres (suite de Fibonacci, nombres premiers, etc). J'ai envie de partager des exemples plus "utiles" dans mon quotidien de développeur.

_Note : pour le premier exemple, je compare des implémentations sans et avec générateur, pour en faire apprécier la valeur ajoutée. Pour les autres exemples, je vais droit au but._

# La pagination

Imaginons vouloir fournir un "endpoint" qui pagine les résultats par lot de 10 pour économiser de la bande passante. Pour l'exemple, la base de données, retourne simplement les lettres de l'alphabet, via `db.execute`.

### 1- implémentation naive

```python
def search(query, page):
    data = db.execute(query)
    count = ceil(len(data) / 10)

    if page not in range(1, count+1):
        raise ValueError

    return data[(page-1)*10 : page*10]


search('letters', page=1)
Querying DB...
['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']

search('letters', page=2)
Querying DB...
['k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't']

search('letters', page=3)
Querying DB...
['u', 'v', 'w', 'x', 'y', 'z']

search('letters', page=4)
Querying DB...
ValueError
```

Le code fonctionne mais pose quelques problèmes :

- à chaque page, on fait une nouvelle requête en base, alors qu'on avait déjà récupéré les données,
- le "consommateur" de notre endpoint doit connaître / gérer la page à charger.

### 2- utilisation d'un cache

```python
cache = {}

def search(query):
    if query not in cache:
        data = db.execute(query)
        count = ceil(len(data) / 10)
        cache[query] = {
            'data': data,
            'count': count,
            'page': 1,
        }

    data, count, page = cache[query].values()

    if page > count:
        del cache[query]  # clean the cache
        raise StopIteration

    cache[query]['page'] += 1  # prepare next iteration
    return data[(page-1)*10 : page*10]


search('letters')
Querying DB...
['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']

search('letters')
['k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't']

search('letters')
['u', 'v', 'w', 'x', 'y', 'z']

search('letters')
StopIteration
```

On a résolus nos précédents problèmes, mais :

- il y a collision si deux "consommateurs" envois la même requête,
- le code commence à se complexifier alors que le problème est trivial.

### 3- utilisation d'un générateur

```python
def search(query):
    data = db.execute(query)
    count = ceil(len(data) / 10)

    for page in range(1, count+1):
        yield data[(page-1)*10 : page*10]


letters = search('letters')

next(letters)
Querying DB...
['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']

next(letters)
['k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't']

next(letters)
['u', 'v', 'w', 'x', 'y', 'z']

next(letters)
StopIteration
```

Plus besoin de cache, le code redevient simple. Plus de risque de collision, chaque "consommateur" instanciant son propre générateur.

On peut aussi générer toutes les valeurs d'un coup.

```python
list(search('letters'))
Querying DB...
[['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'],
 ['k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't'],
 ['u', 'v', 'w', 'x', 'y', 'z']]
```

# Génération cyclique

On peut sans risque, utiliser des boucles infinies dans le générateurs, à condition de rendre à la main à chaque tour. C’est idéal pour générer des valeurs cycliques.

Imaginons vouloir connaître le joueur de la partie, dont c’est le tour de jouer.

```python
def play(*players):
    while True:
        for player in players:
            yield player


game = play('anna', 'john')

next(game)
'anna'

next(game)
'john'

next(game)
'anna'

...
```

On peut même envoyer des données dans le générateur.

Imaginons que l’on veuille ajouter un joueur, en cours de partie.

```python
def play(*players):
    new = None
    while True:
        for player in players:
            new = yield player
            if new is not None:
                players = new, *players


game = play('anna', 'john')

next(game)
'anna'

game.send('dave')

next(game)
'john'

next(game)
'dave'
```

Attention, si on essaie de générer toutes les valeurs d’un coup, on tombe dans la boucle infinie !

```python
list(play('anna', 'john'))
# infinite loop
```

Enfin, on peut aussi déclarer le générateur "en intension". On ne peut pas lui envoyer de données via `send` et on définit une limite d'itérattion (ici un nombre de tour maximum).

```python
game = (name for turn in range(4) for name in ('anna', 'john'))

next(game)
'anna'

next(game)
'john'

next(game)
'anna'

list(game)
['john, 'anna', 'john, 'anna', 'john]
```

_Note : la liste contient 5 éléments (au lieu des 8 qu'on pourrait attendre), les 3 premiers ayant déjà été "consommés"._

# Parcourir / rechercher des données

La grande force des générateurs, c'est aussi d'économiser de la RAM en ne chargeant qu'une partie des données en mémoire. C'est vite significatif sur des volumes de données importants. On peut convertir n'importe quel itérable en générateur via `iter`.

```python
def search_error(logs):
    for log in iter(logs):
        if log.startwith('ERROR'):
            return log
```

`yield` nous offre toute la flexibilité de décider de continuer la recherche, si on souhaite d'avantage de résultats.

```python
def search_error(logs):
    for log in iter(logs):
        if log.startwith('ERROR'):
            yield log

log = search_error(logs)
error = next(log)
if 'HTTP_401_UNAUTHORIZED' in error:
    # generate new token and retry
elif 'HTTP_403_FORBIDDEN' in error:
    # get more details in logs
    details = next(log)
```

Le point fort est que l'on n'a pas besoin de définir les critères pour continuer ou non la recherche dans la méthode du générateur qui peut rester générique.

# Surveiller des entrées / sorties

Imaginons vouloir lire en continue un fichier de log, alimenté par une source extérieur.

```python
def reader(path):
    with open(path, 'a+') as f:
        while True:
            yield f.readline()


log = reader('service.log')

next(log)
''

# echo 'foo' >> service.log
next(log)
'foo\n'
```

On pourrait aussi se passer de générateur, à chaque fois : ouvrir, déplacer le pointeur, lire, fermer le fichier. Mais ce ne serait pas optimal.

Et si par la même occasion on souhaite écrire dans le fichier.

```python
def reader_writer(path):
    with open(path, 'a+') as f:
        while True:
            text = yield f.readline()
            if text is not None:
                f.writelines(f'{text}\n')
                f.flush()

log = reader_writer('service.log')

next(log)
''

log.send('bar')
# cat service.log | tail -n 1
# bar
```

J'espère qu'avec ces exemples donneront un peu d'inspiration à ceux qui voudraient exploiter d'avantage le potentiel de `yield` et des générateurs. Je n'ai volontairement pas donner d'exemple de coroutines, parce que je souhaiterais écrire un billet spécifiquement sur ce sujet.
