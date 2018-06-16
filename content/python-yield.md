Title: Yield : cédez le passage
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

### Implémentation naive

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

### Utilisation d'un cache

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

### Utilisation d'un générateur

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

### Générateur en intension

Pour finir en beauté, on reprend l'exemple du générateur cyclique en une seule ligne (remplaçant la boucle infinie par un nombre de tour max).

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

_Note : la liste contient 5 éléments (au lieu de 8), les 3 premiers ayant déjà été "consommés"._

# Parser des données

Lorque l'on "parse" des données, il est courant de ne pas vouloir systématiquement récupérer toutes les occurences. `yield` nous offre toute la flexibilité de décider de continuer le "parsing" des données en dehors du code du "parser", selon le contexte.

```python
def parser(path, word):
    with open(path) as f:
        for line in f:
            if word in line.split():
                yield line

find_error = parser('service.log', 'ERROR')
while not_found:
    error_line = next(find_error)
    ...
```

# Chainer des traitements

<https://zestedesavoir.com/articles/152/la-puissance-cachee-des-coroutines/#2-ya-du-monde-dans-le-pipe>
```python
def grepper(data, word):
    yield
```

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

Bien sûr, la grande force des générateurs, c'est aussi d'économiser de la RAM en ne chargeant pas d'un coup toutes les itérations. C'est vite significatif sur des volumes de données importants.

J'espère qu'avec ces exemples, vous serez plus inspiré par `yield` à l'avenir. :)
