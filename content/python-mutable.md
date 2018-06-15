Title: Faire la paix avec les mutables
Date: 2018-06-17 20:00
Category: dev
Tags: python

![Magneto]({filename}/images/xmen.jpg "Peace was never an option.")

En python, certaines structures de données sont dites "mutables" : on peut en modifier les valeurs en conservant la même instance. Cela offre quelques propriétés intéressantes mais parfois dangereuses.

Parmi les structures de données les plus courantes :

- ne sont pas mutables : les tuples, les chaines et autres types de base ;
- sont mutables : les listes, les dictionnaires, les objets.

Pour s'en convaincre, on peut comparer les `id` avant et après modification.

Par exemple, dans le cas d'une chaine, l'instance change.

```python
xmens = 'tornade,cyclope,'
id(xmens)
139893527618544

xmens += 'phoenix,'
id(xmens)
139893504693696  # other id
```

En revanche, dans le cas d'une liste, l'instance demeure (sauf si on ré-instancie explicitement la liste).

```python
xmens = ['tornade', 'cyclope']
id(xmens)
140229166148488

xmens += ['phoenix']  # or xmens.append('phoenix')
id(xmens)
140229166148488  # same id

xmens = [*xmens, 'malicia']  # this is a new list
140229204490952  # other id
```

Au passage, on note la distinction entre égalité (des valeurs) et identité (des instances).

```python
['tornade', 'cyclope'] == ['tornade', 'cyclope']
True  # same values

['tornade', 'cyclope'] is ['tornade', 'cyclope']
False  # not the same instances
```

# Bénéfices

En découle qu'il n'est pas nécessaire de retourner les arguments mutables modifiés dans une fonction.

```python
def hire(mutant, team):
    team.append(mutant)

xmens = ['tornade', 'cyclope']
hire('wolverine', xmens)

print(xmens)
['tornade', 'cyclope', 'wolverine']
```

C'est pratique car cela :

- évite de ré-instancier la liste `xmens` avec le résultat de la fonction `hire` ;
- procure une syntaxe plus légère (surtout quand le nombre d'arguments augmente) ;
- facilite l'écriture des fonctions récursives.

# Premier danger : la copie

En résulte un premier comportement qui peut surprendre : copier un mutable ne créer pas de nouvelle instance.

```python
xmens = ['charles-xavier']
villains = xmens
villains[0] = 'magneto'

print(villains)
['magneto']  # good

print(xmens)
['magneto']  # not good
```

Il faut explicitement ré-instancier une nouvelle liste, à partir des éléments de la liste que l'on veut copier.

```python
villains = [mutant for mutant in xmens]
villains = [*xmens]  # from python 3

from copy import copy
villains = copy(xmens)
```

Mais ce n'est toujours pas suffisant, si la liste contient elle-même des mutables, ceux-ci seront "partagés" entre les instances. Dans ce cas, il faut faire une copie récursive.

```python
from copy import deepcopy
villains = deepcopy(xmens)
```

# Second danger : les valeurs par défaut

Autre comportements surprenant, si on définis un mutable comme valeur par défaut d'un argument d'une fonction. Dans l’exemple, on créer et retourne une nouvelle liste si aucune n’est fournie.

```python
def hire(mutant, team=[]):
    """Create a new team, if no team provided."""
    team.append(mutant)
    return team

xmens = hire('charles-xavier')
['charles-xavier']  # good

villains = hire('magneto')
['charles-xavier', 'magneto']  # not good
```

Non, non, il semblerait que ce ne soit pas un anomalie, mais bien un "choix d'implémentation".

La raison est que, en Python, les fonctions (tout comme les classes) sont des objets de première classe.

Voir: <https://fr.wikipedia.org/wiki/Objet_de_premi%C3%A8re_classe>

On peut donc, accéder à leur propriétés, les assigner, etc.

```python
hire.__name__
hire

x = hire
x.__name__
hire

x('wolverine')
['wolverine']
```

Les valeurs par défauts des arguments font aussi partis des propriétés de la fonction.

```python
hire.__defaults__
([],)

hire('charles-xavier')
hire.__defaults__
(['charles-xavier'],)

hire('magneto')
hire.__defaults__
(['charles-xavier', 'magneto'],)
```

Dans notre exemple, la valeur par défaut étant une propriété mutable, elle n'est pas à l'abris d'être modifiée lors de l'exécution de la fonction.

Faut reconnaître que c’est un peu traître d'utiliser une valeur par défaut mutable et donc pas considéré comme une bonne pratique. Pylint, par exemple, affiche un message d’avertissement.

_W0102: Dangerous default value [] as argument._

Voir: <http://pylint-messages.wikidot.com/messages:w0102>

La parade la plus connue est de définir `None` comme valeur par défaut, puis de créer, si besoin, la liste à l’intérieur de la fonction. Ainsi, la liste ne sera pas liée aux propriétés de la fonction.

```python
def hire(mutant, team=None):
    """Create a new team, if no team provided."""
    if team is None:
         team = []
    team.append(mutant)
    return team

hire.__defaults__
(None,)

hire('charles-xavier')
hire.__defaults__
(None,)

hire('magneto')
hire.__defaults__
(None,)
```

Même problématique avec les valeurs par défaut des attributs de classe, qui eux non plus, ne sont pas à l'abris d'être modifiés entre les instances.

```python
class Team:
    mutants = []
    def hire(self, mutant):
        self.mutants.append(mutant)

xmens = Team()
xmens.hire('charles-xavier')
xmens.mutants == ['charles-xavier']

villains = Team()
villains.hire('magneto')
villains.mutants == ['charles-xavier', 'magneto']

Team.mutants == ['charles-xavier', 'magneto']
```

Même problème, même solution.

```python
class Team:
    mutants = None
    def hire(self, mutant):
        if self.mutant is None:
            self.mutant = []
        self.mutants.append(mutant)

xmens = Team()
xmens.hire('charles-xavier')
xmens.mutants == ['charles-xavier']

villains = Team()
villains.hire('magneto')
villains.mutants == ['magneto']

Team.mutants == None
```

Personnellement, même si je comprends les raisons techniques d'un tel comportement, je ne suis pas convaincu de son intérêt sur un plan pratique.

Il y a bien d’autres manières, plus simples et plus explicites, de rendre des données persistantes entre des objets ou des appels de fonctions. Celle-ci étant, à mon goût, trop implicite et trop peu intuitive, se heurte aux dogmes fondamentaux du langages.

- _Explicit is better than implicit._
- _Simple is better than complex._
- _Practicality beats purity._
- _There should be one — and preferably only one — obvious way to do it._

J'imagine, qu'il existe une bonne raison d'avoir conserver un tel comportement mais je n'en ai pas trouvé d'explication.

_Note : les mutables ne seront pas acceptés en valeur par défaut des attributs des `Data Classes`, qui arrivent avec Python 3.7._

- <https://www.python.org/dev/peps/pep-0557/#mutable-default-values>
- <https://github.com/ericvsmith/dataclasses/issues/3>
