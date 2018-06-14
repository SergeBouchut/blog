Title: Le polymorphisme en Python
Date: 2018-06-14 21:40
Category: python


Le polymorphisme dit "paramétrique" est un des concepts clés de la programmation orientée objet. Il permet de définir plusieurs fonctions de même nom mais avec des signatures différentes (variant sur le nombre et le type d'argument). C'est aussi un bon moyen de segmenter le code par logique "métier".

Python répond nativement à ces besoins, grâce au typage dynamique (duck typing) des variables et à la séparation (unpacking) des arguments. Toutefois, c'est un bon exercice que d'en chercher une implémentation.

Pour l’exemple, je souhaite obtenir une fonction `add` qui :

- somme les arguments si ce sont des entiers ;
- les concatène, avec des espaces, si ce sont chaînes ;
- lever une exception sinon.ValueError.

Par soucis de simplification, on admet que tous les arguments sont de même type.

# Implémentation naive

```python
def add(*args):
    arg_type = type(args[0])
    if arg_type is int:
        return add_int(*args)
    elif arg_type is str:
        return add_str(*args)
    else:
        raise ValueError

def add_int(*numbers):
    return sum(numbers)

def add_str(*words):
    return ' '.join(words)

assert add(1, 2, 3) == 6
assert add('hello', 'world') == 'hello world'
assert add(True, False) raises ValueError
```

_Note : par commodité, j'écris `assert ... raises ...`, bien que l'instruction n’existe pas. A l'occasion, j'en proposerai aussi une implémentation._

On a une fonction "technique" qui analyse le type d'argument et redirige vers les fonctions "métier" attendues.

L’implémentation fonctionne, mais elle est perfectible. En effet, à chaque ajout/retrait de fonction métier on doit aussi modifier la fonction générique. On souhaiterait d'avantage découpler la logique "technique" de la logique "métier".

# Avec un décorateur

```python
mapping = {}
def register_add(arg_type):
    def register(func):
        mapping[arg_type] = func
        def run(*args):
            arg_type = type(args[0])
            if arg_type not in mapping:
                raise ValueError
            return mapping[arg_type](*args)
        return run
    return register

@register_add(NoneType)
def add(*args):
    pass

@register_add(int)
def add_int(*numbers):
    return sum(numbers)

@register_add(str)
def add_str(*words):
    return ' '.join(words)
```

Cette fois-ci, c'est bon, on peut ajouter de nouvelles fonctions métiers sans toucher au noyau technique, grâce à l'usage du décorateur.

Cette implémentation requiert qu’au moins une des fonctions décorées soit nommée `add`, pour servir de point d’entrée. Ce ne sera pas forcément cette foncion qui sera réellement executée. Ce qui peut porter à confusion.

```python
assert add_int(1, 2, 3) == 6  # no surprise
assert add(1, 2, 3) == 6  # cool
assert add_str(1, 2, 3) == 6  # ouch
```

D’autre part, on aimerait regrouper le dictionnaire de "mapping" et la fonction de "dispatch", dans une même structure de données, leurs fonctionnements étant liés. Cela va nous amener à implémenter le code sous forme de classe.

# Avec une classe

```python
class Add(object):
    _mapping = {}

    @classmethod
    def register(cls, arg_type):
        def wrapper(func):
            cls._mapping[arg_type] = func
        return wrapper

    @classmethod
    def run(cls, *args):
        arg_type = type(args[0])
        if arg_type not in cls._mapping:
            raise ValueError
        return cls._mapping[arg_type](*args)

@Add.register(int)
def _(*numbers):
    return sum(numbers)

@Add.register(str)
def _(*words):
    return ' '.join(words)

add = Add.run
assert add(1, 2, 3) == 6
assert add('hello', 'world') == 'hello world'
```

_Note: Nul, besoin d’instancier la classe. Heureusement d'ailleurs car on a utiliser une valeur par défaut "muable" pour l'attribut de classe. C'est un piège en Python._

Contrairement à d’autres langages, Python n’encourage pas à systématiquement utiliser des classes, si cela n’est pas nécessaire. Mais dans notre cas, j’y vois un gain notable dans la construction et la lisibilité du code.

Ce motif "dispatcher" peut permettre d’implémenter de nombreux cas d’usage autres que le polymorphisme. J'en propose quelques exemples.

# Avec les libs standards

```python
from functools import singledispatch

@singledispatch
def add(*args):
    raise ValueError

@add.register(int)
def _(*numbers):
    return sum(numbers)

@add.register(str)
def _(*words):
    return ' '.join(words)
```

En fait, il existe un décorateur pré-conçu à cet usage, disponible dans `functools` à partir de Python 3.4. Faut toujours penser à regarder dans les libs standards, on gagne du temps !
