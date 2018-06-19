Title: Yield, cédez la priorité
Date: 2018-06-16 20:00
Category: dev
Tags: python, fp
Description: Des exemples de générateurs en Python, pour donner envie de les utiliser plus souvent.
Image: las_vegas_parano.jpg

![Raoul Duke and Dr. Gonzo]({filename}/images/las_vegas_parano.jpg "We can’t stop here. This is bat country.")

`yield` est une instruction bien connue des développeurs Python expérimentés, mais peu utilisée par les plus débutants. Pourtant, le concept est assez simple à appréhender et peut s'avérer pratique dans de nombreux cas.

Yield peut se traduire par retourner / rendre / céder. En Python, il permet à une fonction de rendre la main, avant la fin de son exécution. Ce qui est opportun pour exécuter graduellement du code, via une structure de contrôle nommée "générateur". C’est aussi ce mécanisme qui est à l’œuvre dans les coroutines.

Dans les tutoriels, je vois souvent des exemples de générateurs pour calculer des suites mathématiques (nombres premiers, Fibonacci, etc) ou d'autres cas d'usage que je n'ai jamais eu besoin d'implémenter. J'ai envie de partager des exemples plus "utiles" dans mon quotidien de développeur.

# Paginer des résultats

On veut fournir une API qui pagine les résultats par lots pour économiser de la bande passante.

### Sans générateur (implémentation naive)

```python
def db_execute(query):
    """Return letters of the alphabet."""
    print('Querying DB...')
    return list(string.ascii_lowercase)

def search(query, page):
    data = db_execute(query)
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

La pagination fonctionne comme attendu, mais :

- à chaque page, on fait une nouvelle requête en base, alors qu'on avait déjà récupéré les données ;
- le "client" de notre API doit connaître / gérer la page à charger.

### Sans générateur (implémentation améliorée)

On ajoute un système de cache.

```python
cache = {}

def search(query):
    if query not in cache:
        data = db_execute(query)
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


search('letters')  # client 1
Querying DB...
['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']

search('letters')  # client 2
['k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't']

search('letters')  # client 1
['u', 'v', 'w', 'x', 'y', 'z']

search('letters')  # client 2
StopIteration
```

Plus de requête redondante, ni de page à gérer, mais il y a un risque de collision si deux clients envoient la même requête. On pourrait encore étoffer l'implémentation mais le code devient trop complexe relativement au problème qui est trivial.

### Avec générateur

On utilise un générateur.

```python
def search(query):
    data = db_execute(query)
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

Plus besoin de cache, le code redevient simple. Plus de risque de collision, chaque "client" instanciant son propre générateur.

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

On veut connaître le joueur de la partie, dont c’est le tour de jouer.

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

On veut aussi pouvoir ajouter un joueur, en cours de partie.

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
list(play('anna', 'john'))  # infinite loop
```

Enfin, on peut aussi déclarer le générateur en "intension". On ne peut pas lui envoyer de données via `send`. Par choix, on définit un nombre maximum d'itérations.

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

_Note : la liste contient 5 éléments (sur les 8 initiaux), les 3 premiers ayant déjà été "consommés"._

# Vérifier une condition sur un ensemble

### Sans générateur

Sur un ensemble d'objet `cars`, on veut s'assurer qu'une condition `price_below` est respectée sur :

- au moins un des objets via `any` ;
- l'ensemble des objets via `all`.

```python
cars = [
    {'name': 'Tesla_S', 'price': 70_000},
    {'name': 'Dacia_Sandero', 'price': 11_000},
    {'name': 'Porsche_Cayenne', 'price': 90_000},
    {'name': 'Audi_A4', 'price': 30_000},
]

def price_below(car, max_price):
    is_valid = car['price'] < max_price
    print(f'Checking {car['name']}: {is_valid}')
    return is_valid

any([price_below(car, 20_000) for car in cars])
Checking Tesla_S: False
Checking Dacia_Sandero: True
Checking Porsche_Cayenne: False
Checking Audi_A4: False


all([price_below(car, 80_000) for car in cars])
Checking Tesla_S: True
Checking Dacia_Sandero: True
Checking Porsche_Cayenne: False
Checking Audi_A4: True
```

On vérifie bien les conditions mais on parcourt systématiquement l'ensemble des valeurs alors que ce n'est pas nécessaire.

### Avec générateur

On veut stopper l'itération dès lors que l'on a :

- un resultat positif qui valide notre `any` ;
- un resultat négatif qui invalide notre `all`.

```python
any((price_below(car, 20_000) for car in cars))
Checking Tesla_S: False
Checking Dacia_Sandero: True


all((price_below(car, 80_000) for car in cars))
Checking Tesla_S: True
Checking Dacia_Sandero: True
Checking Porsche_Cayenne: False
```

# Surveiller des entrées / sorties

On veut contrôler en continu les entrées ajoutées à un fichier de log.

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

On veut aussi pouvoir écrire dans ce même fichier.

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

# Orchestrer des opérations

On veut récupérer des données depuis un fichier CSV en y appliquant diverses opérations de filtrage et de formatage, tout en évitant de :

- charger en mémoire l'ensemble des données en même temps ;
- parcourir plusieurs fois la liste des données.

### Sans générateur (implémentation naive)

```python
def filter_price(car, max_price):
    return int(car['price']) < max_price

def format_price(car, currency):
    car['price'] = '%s %.2f' % (currency, int(car['price']))

def read_cars(country, max_price, currency):
    if country not in ('fr', 'us'):
        raise ValueError('Invalid country.')
    with open('%s_cars.csv' % country) as f:
        reader = csv.DictReader(f, delimiter=';')
        assert reader.fieldnames == ['name', 'price', 'color']
        cars = []
        for car in reader:
            if filter_price(car, max_price=max_price):
                format_price(car, currency=currency)
                cars.append(car)
        return cars

us_cars = read_cars('us', max_price=80_000, currency='$')
fr_cars = read_cars('fr', max_price=90_000, currency='€')
```

On repond au besoin mais :

- la complexité de la fonction `read_cars` croît en fonction du nombre d'opérations ;
- on ne sait pas faire varier les opérations exécutées selon le contexte.

### Sans générateur (implémentation améliorée)

```python
def filter_color(car, only_colors):
    return car['color'] in only_colors

def format_name(car, tag):
    car['name'] += f' #{tag}'

def read_cars(country, filters, formatters):
    if country not in ('fr', 'us'):
        raise ValueError('Invalid country.')
    with open('%s_cars.csv' % country) as f:
        reader = csv.DictReader(f, delimiter=';')
        assert reader.fieldnames == ['name', 'price', 'color']
        cars = []
        for car in reader:
            if all((func(car, **kwargs) for func, kwargs in filters)):
                for func, kwargs in iter(formatters):
                    func(car, **kwargs)
                cars.append(car)
        return cars

def get_us_cars():
    filters = [(filter_price, {'max_price': 80_000})]
    formatters = [(format_price, {'currency': '$'})]
    return read_cars('us', filters, formatters)

def get_fr_cars():
    filters = [
        (filter_price, {'max_price': 90_000}),
        (filter_color, {'only_colors': ['yellow']}),
    ]
    formatters = [
        (format_price, {'currency': '€'}),
        (format_name, {'tag': 'rare'}),
    ]
    return read_cars('fr', filters, formatters)
```

Le code est d'avantage extensible, mais on ne peut toujours pas :

- gérer un autre type d'opération (autre que filtrage ou formatage) ;
- conditionner l'exécution d'une opération en fonction du résultat d'une précédente.

_Note : on pourrait faire d'autres tentatives avec des structures plus sophistiquées. Mais le code serait trop complexe en comparaison du problème qui est trivial._

### Avec générateur

```python
def read_cars(country):
    if country not in ('fr', 'us'):
        raise ValueError('Invalid country.')
    with open('%s_cars.csv' % country) as f:
        reader = csv.DictReader(f, delimiter=';')
        assert reader.fieldnames == ['name', 'price', 'color']
        for car in reader:
            yield car

def get_us_cars():
    for car in read_cars('us'):
        if filter_price(car, max_price=80_000):
            format_price(car, '$')
            yield car

def get_fr_cars():
    for car in read_cars('fr'):
        if filter_color(car, only_colors=['yellow']:
            format_name(car, tag='rare')
        elif filter_price(car, max_price=20_000):
            format_name(car, tag='cheap')
        elif not filter_price(car, max_price=90_000):
            continue
        format_price(car, '€')
        yield car

us_cars = list(get_us_cars())
fr_cars = list(get_fr_cars())
```

On obtient enfin toute la souplesse désirée dans la combinaison des opérations. Cela, sans "polluer" la fonction de lecture des données `read_cars`.

---

Grâce aux générateurs :

- on économise la mémoire en ne chargeant pas l'ensemble des données d'un coup ;
- on économise le processeur en n'exécutant pas plus d'instructions que nécessaire ;
- on segmente mieux le code, en donnant le contrôle de l'exécution des couches inférieures aux couches supérieures.

J'espère que ces exemples donneront un peu d'inspiration à ceux qui voudraient exploiter d'avantage le potentiel de `yield` et des générateurs. Je n'ai volontairement pas donné d'exemple de coroutines, parce que je souhaiterais écrire un billet spécifiquement sur ce sujet.
