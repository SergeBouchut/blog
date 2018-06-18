Title: Yield : cédez la priorité
Date: 2018-06-16 20:00
Category: dev
Tags: python, fp

![Johnny Depp / Benicio del Toro]({filename}/images/las_vegas_parano.jpg "We can’t stop here. This is bat country.")

`yield` est une instruction bien connue des développeurs Python expérimentés, mais peu utilisée par les plus débutants. Pourtant, le concept est assez simple à appréhender et peut s'avérer pratique dans de nombreux cas.

Yield peut se traduire par retourner / rendre / céder. En Python, il permet à une fonction de rendre la main, avant la fin de son exécution. Ce qui est opportun pour exécuter graduellement du code (via un "générateur"). C’est aussi ce mécanisme qui est à l’œuvre dans les coroutines.

Dans les tutoriels, je vois souvent des exemples de générateurs pour calculer des suites mathématiques (nombres premiers, Fibonacci, etc) ou d'autres opérations que je n'ai jamais eu besoin d'implémenter. J'ai envie de partager des exemples plus "utiles" dans mon quotidien de développeur.

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

- à chaque page, on fait une nouvelle requête en base, alors qu'on avait déjà récupéré les données ;
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

On a résolu nos précédents problèmes, mais :

- il y a collision si deux "consommateurs" envoient la même requête ;
- le code commence à se complexifier inutilement pour un problème trivial.

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

On peut sans risque, utiliser des boucles infinies dans le générateur, à condition de rendre la main à chaque tour. C’est idéal pour générer des valeurs cycliques.

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

Enfin, on peut aussi déclarer le générateur en "intension". On ne peut pas lui envoyer de données via `send` et on définit une limite d'itération (ici un nombre maximum de tours).

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

_Note : la liste contient 5 éléments (au lieu des 8 que l'on pourrait attendre), les 3 premiers ayant déjà été "consommés"._

# Surveiller des entrées / sorties

Imaginons vouloir lire en continu un fichier de log, alimenté par une source extérieure.

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

Sans `yield`, on devrait, à chaque fois, ouvrir puis refermer le fichier. Ce qui ne serait vraiment pas optimal.

On voudrait aussi pouvoir écrire dans le même fichier.

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

# Parcourir / rechercher des données

La grande force des générateurs, c'est aussi d'économiser de la RAM en ne chargeant qu'une partie des données en mémoire. Cela devient vite significatif sur des volumes de données importants. On peut convertir n'importe quel itérable en générateur via `iter`.

```python
def search_error(logs):
    for log in iter(logs):
        if log.startwith('ERROR'):
            return log
```

`yield` nous offre toute la flexibilité de décider de continuer la recherche, si l'on souhaite d'avantage de résultats.

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

Le point fort est que l'on gère la poursuite de l'exécution de la recherche hors de la méthode `search_error`, qui peut rester agnostique au contexte.

# Chaîner des traitements

Imaginons vouloir récupérer des données depuis un fichier CSV en y appliquant diverses opérations de filtrage et de formatage, tout en évitant de :

- charger en mémoire l'ensemble des données en même temps ;
- parcourir plusieurs fois la liste des données.

Ces critères sont plutôt simples à respecter, même sans utiliser `yield`.

### 1- implémentation naive

```python
def filter_price(car, max_price):
    return int(car['price']) < max_price

def format_price(car, currency):
    car['price'] = '%s %.2f' % (currency, int(car['price']))

def read_cars(path, delimiter):
    with open(path) as f:
        columns = f.readline().rstrip('\n').split(delimiter)
        cars = []
        for line in f:
            car = dict(zip(columns, line.rstrip('\n').rstrip('\n').split(delimiter)))
            if filter_price(car, max_price=1000):
                format_price(car, currency='$')
                cars.append(car)
        return cars

def get_cars():
    return read_cars('cars.csv', delimiter=';')
```

On complexifie le problème en faisant varier les paramètres des fonctions de filtrage et de formatage selon le contexte métier. Cela nous contraint à remonter ces paramètres dans la fonction parente `read_cars`.

```python
def get_us_cars():
    return read_cars('us_cars.csv', delimiter=';',
                     max_price='1000', currency='$')

def get_en_cars():
    return read_cars('eu_cars.csv', delimiter=';',
                     max_price='1200', currency='€')
```

Cette fois, on ne veut plus seulement faire varier les valeurs, mais aussi faire varier les opérations exécutées selon le contexte métier.

On pourrait faire le choix, d'ajouter des paramètres indiquant :

- les opérations à exécuter, selon le contexte ;
- les valeurs associées à ces opérations.

Mais cela polluerait progressivement la fonction, à mesure, que le nombre d'opérations augmenterait. Il devient donc préférable de rassembler les opérations, en fonction de leur nature, avec leurs paramètres dans des structures de données.

### 2- regroupement des opérations

```python
def read_cars(path, delimiter, filters, formatters):
    with open(path) as f:
        columns = f.readline().rstrip('\n').split(delimiter)
        cars = []
        for line in f:
            car = dict(zip(columns, line.rstrip('\n').split(delimiter)))
            if all((func(car, **kwargs) for func, kwargs in iter(filters))):
                for func, kwargs in iter(formatters):
                    func(car, **kwargs)
                cars.append(car)
        return cars

def get_us_cars():
    filters = [(filter_price, {'max_price': 1000})]
    formatters = [(format_price, {'currency': '$'})]
    return read_cars('us_cars.csv', ';', filters, formatters)

def get_eu_cars():
    filters = [
        (filter_price, {'max_price': 1200}),
        (filter_color, {'exclude': ['blue']}),
        (filter_price, {'max_price': 900}),  # make the first filter useless
    ]
    formatters = [
        (format_price, {'currency': '€'}),
        (format_name, {}),
    ]
    return read_cars('en_cars.csv', ';', filters, formatters)
```

Note code est d'avantage extensible, on peut désormais :

- exécuter plusieurs fois la même opération avec des valeurs différentes ;
- définir des ordres d'éxecutions.

En revanche, on ne peut toujours pas :

- gérer un autre type d'opération (autre que filtrage ou formatage) ;
- conditionner l'exécution d'une opération en fonction du résultat d'une précédente.

On pourrait faire d'autres tentatives avec des structures de données et de contrôle plus sophistiquées. Mais cela introduirait trop de complexité pour un problème qui, au final, demeure trivial.

### 3- utilisation d'un générateur

```python
def read(path, delimiter):
    with open(path) as f:
        columns = f.readline().rstrip('\n').split(delimiter)
        for line in f:
            yield dict(zip(columns, line.rstrip('\n').split(delimiter)))

def get_us_cars():
    reader = read('us_cars.csv', delimiter=';')
    cars = []
    while True:
        try:
            car = next(reader)
        except StopIteration:
            return cars

        if filter_price(car, max_price=1000):
            format_price(car, '$')
            cars.append(car)

def get_eu_cars():
    reader = read('eu_cars.csv', delimiter=';')
    cars = []
    while True:
        try:
            car = next(reader)
        except StopIteration:
            return cars

        if (
            filter_price(car, max_price=1200) and
            filter_color(car, exclude=['blue']
        ):
            format_price(car, '€')
            cars.append(car)
        elif filter_price(car, max_price=900):
            format_price(car, '€')
            format_name(car)
            cars.append(car)
```

On obtient enfin toute la souplesse désirée dans la combinaison des opérations. Cela, sans polluer la fonction de lecture des données `read` qui devient minimaliste (et même indépendante du type d'objet lu).

---

J'espère que ces exemples donneront un peu d'inspiration à ceux qui voudraient exploiter d'avantage le potentiel de `yield` et des générateurs. Je n'ai volontairement pas donné d'exemple de coroutines, parce que je souhaiterais écrire un billet spécifiquement sur ce sujet.
