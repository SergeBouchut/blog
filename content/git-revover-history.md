Title: Retrouver son historique Git
Date: 2018-06-15 20:00
Category: dev
Tags: git
Description: Mieux comprendre Git pour se sortir de situations épineuses.
Image: sherlock.jpg


![Sherlock Holmes]({filename}/images/sherlock.jpg "Because you're an idiot. No, no, no. Don't look like that. Practically everyone is.")

En discutant avec un collègue, je me suis rendu compte que j’avais une compréhension erronée, de la "véritable nature" des branches et des tags dans Git.

En effet, je me les représentais comme des "ensembles de commits". C’est peut-être la manière usuelle de les décrire qui m'a induit en erreur.

_Cette branche "contient" ces commits._

_Ce commit "provient de" cette branche._

En réalité, les tags et les branches sont simplement des pointeurs vers des commits.

- Le tag est supposé être fixe (toujours pointer sur le même commit).
- La branche est conçue pour être "itinérante" (pointer sur le dernier commit).

Chaque commit connaissant son parent, n’importe quel commit est indirectement auto-porteur de son historique.

On peut donc utiliser les commandes usuelles directement avec les hash des commits.

_Note : pour le confort de la lecture, je remplace les hashs de commit par des numéros._

```bash
git checkout #1

git diff #2 #3

git rebase #4
```

On peut légitiment se questionner sur l'intérêt de manipuler directement des commits via leur hash, alors qu'on dispose d'outils plus "amicaux", à savoir les branches et les tags. Au quotidien, cela ne s'impose pas. Mais occasionnelement, cela peut permettre de récuperer de l'historique que l'on croyait perdu.

# Restaurer une branche / un tag supprimé

Prenons en exemple, un dépôt avec deux branches : `master` qui pointe sur le commit `#1` et `feature` qui pointe sur le commit `3`.

```
(master)$ git log --oneline --all
#3 (feature) update feature
#2 add feature
#1 (HEAD -> master) init readme
```

_Note : l’option `all` permet d'afficher tous les commits "attachés", pas uniquement à la branche `master` où l'on se trouve ; `HEAD` indique notre position._

En supprimant la branche `feature`, les commits `#2` et `#3` deviennent orphelins ; ils n’apparaissent plus dans `git log`.

```
git branch -D feature

(master)$ git log --oneline --all
#1 (HEAD -> master) init readme
```

Orphelins certe, mais pas perdus. En se positionnant directement sur le commit `#3`, on retrouve son historique.

```
(master)$ git checkout #3

(#3)$ git log --online
#3 (HEAD) update feature
#2 add feature
#1 (master) init readme
```

Libre à nous de re-créer la branche `feature` dans le même état qu'avant sa suppression.

```
(#3)$ git branch feature

(#3)$ git checkout master

(master)$ git log --oneline --all
#3 (feature) update feature
#2 add feature
#1 (HEAD -> master) init readme
```

Bien sûr, après avoir supprimé la branche `feature`, on peut ne pas connaître le hash du dernier commit. Dans ce cas, on consulte l'historique des déplacement de `HEAD` via `git reflog`.

```
(master)$ git reflog | grep 'update feature'
#3 HEAD@{1}: commit: update feature
```

La démarche est exactement la même pour restaurer un tag supprimé.

# Restaurer un commit écrasé

Reprenons l'exemple de notre branche `feature`, qui pointe sur le commit `#3`.

```
(feature)$ git log --oneline
#3 (HEAD -> feature) update feature
#2 add feature
```

En éditant le dernier commit `#3`, celui-ci est en réalité remplacé par un nouveau `#4`.

Au passage, il n'est pas recommandé de modifier son historique. Il est toujours sécuritaire d'empiler un autre commit pour éditer / compléter des modifications.

```
(feature)$ git commit --amend

(feature)$ git log --oneline
#4 (HEAD -> feature) update feature edited
#2 add feature
```

Le commit `#3` a disparu des radars, mais n'est pas perdu, seulement orphelin. En se positionner directement dessus, puis en forçant la création de la branche `feature` (qui existe déjà), on peut le restaurer.

```
(feature)$ git checkout #3

(#3)$ git log --online --all
#4 (feature) update feature edited
#3 (HEAD) update feature
#2 add feature


(#3)$ git branch feature --force

(#3)$ git checkout feature

(feature)$ git log --oneline
#3 (HEAD -> feature_branch) update feature
#2 add feature
```

La documentation officielle de Git pour ~démolir~ modifier puis récupérer son historique.

- <https://git-scm.com/book/fr/v1/Utilitaires-Git-R%C3%A9%C3%A9crire-l-historique>
- <https://git-scm.com/book/fr/v1/Les-tripes-de-Git-Maintenance-et-r%C3%A9cup%C3%A9ration-de-donn%C3%A9es>

Finalement, ils ne sont pas si antipathiques ces commits. :)
