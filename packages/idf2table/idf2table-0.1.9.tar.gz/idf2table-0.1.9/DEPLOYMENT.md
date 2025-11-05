# Guide de déploiement sur PyPI

Ce guide explique comment publier le package `idf2table` sur PyPI (Python Package Index).

## Prérequis

1. **Compte PyPI** : Créez un compte sur [PyPI](https://pypi.org/account/register/)
2. **Token API PyPI** : Générez un token d'API pour la publication
3. **Outils de build** : `build` et `twine` doivent être installés

## Étape 1 : Préparer le projet

### Vérifier les métadonnées

Vérifiez que le fichier `pyproject.toml` contient toutes les métadonnées nécessaires :

- ✅ Nom du package unique
- ✅ Version (utilisez [semantic versioning](https://semver.org/))
- ✅ Description
- ✅ Auteurs
- ✅ Licence
- ✅ URLs du projet

### Vérifier que tout fonctionne localement

```bash
# Installer les outils de build
uv add --dev build twine

# Tester la construction du package
uv run python -m build

# Vérifier le contenu des distributions
ls -la dist/
```

## Étape 2 : Créer un token PyPI

1. Allez sur [https://pypi.org/manage/account/](https://pypi.org/manage/account/)
2. Dans la section "API tokens", cliquez sur "Add API token"
3. Donnez un nom au token (ex: "idf2table-publish")
4. Sélectionnez le scope (entire account ou juste le projet)
5. Copiez le token (format : `pypi-...`)

⚠️ **Important** : Le token ne s'affichera qu'une seule fois. Sauvegardez-le dans un gestionnaire de mots de passe.

## Étape 2b : Créer un compte et token TestPyPI (optionnel mais recommandé)

⚠️ **TestPyPI nécessite un compte et un token séparés !**

1. Créez un compte sur [TestPyPI](https://test.pypi.org/account/register/)
2. Allez sur [https://test.pypi.org/manage/account/](https://test.pypi.org/manage/account/)
3. Générez un token API séparé pour TestPyPI
4. Le token TestPyPI commence aussi par `pypi-` mais est différent de celui de PyPI principal

## Étape 3 : Tester sur TestPyPI (optionnel mais recommandé)

Avant de publier sur PyPI, testez sur TestPyPI :

```bash
# Créer un compte sur TestPyPI : https://test.pypi.org/account/register/

# Construire le package
uv run python -m build

# Publier sur TestPyPI
uv run twine upload --repository testpypi dist/*

# Tester l'installation depuis TestPyPI
uv pip install --index-url https://test.pypi.org/simple/ idf2table
```

## Étape 4 : Publier sur PyPI

### Méthode 1 : Avec twine (recommandé)

```bash
# 1. Construire les distributions
uv run python -m build

# 2. Publier sur PyPI
# Le token sera demandé interactivement ou peut être fourni via variable d'environnement
uv run twine upload dist/*

# 3. Si vous avez configuré un token dans ~/.pypirc, twine l'utilisera automatiquement
```

### Méthode 2 : Avec variable d'environnement

```bash
# Définir les credentials
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-<votre-token>

# Construire et publier
uv run python -m build
uv run twine upload dist/*
```

### Méthode 3 : Avec fichier de configuration ~/.pypirc

Créez ou mettez à jour le fichier `~/.pypirc` :

```ini
[pypi]
username = __token__
password = pypi-<votre-token-pypi-principal>

[testpypi]
username = __token__
password = pypi-<votre-token-testpypi-separe>
```

⚠️ **Important** : 
- TestPyPI nécessite un **compte séparé** et un **token séparé**
- Votre token PyPI principal ne fonctionne **pas** sur TestPyPI
- Vous devez créer un compte sur [TestPyPI](https://test.pypi.org/account/register/) et générer un token spécifique

Ensuite :

```bash
uv run python -m build
uv run twine upload dist/*
```

## Étape 5 : Vérifier la publication

1. Allez sur [https://pypi.org/project/idf2table/](https://pypi.org/project/idf2table/)
2. Vérifiez que votre package apparaît
3. Testez l'installation :

```bash
pip install idf2table
```

## Mettre à jour une version existante

1. **Incrémentez la version** dans `pyproject.toml` :

```toml
version = "0.1.1"  # ou "0.2.0" pour une nouvelle fonctionnalité, "1.0.0" pour stable
```

2. **Créez un tag git** (optionnel mais recommandé) :

```bash
git tag v0.1.1
git push origin v0.1.1
```

3. **Reconstruisez et republiez** :

```bash
# Nettoyer les anciennes distributions
rm -rf dist/ build/ *.egg-info

# Reconstruire
uv run python -m build

# Publier
uv run twine upload dist/*
```

## Automatisation avec CI/CD (GitLab CI)

Vous pouvez créer un fichier `.gitlab-ci.yml` pour automatiser la publication :

```yaml
stages:
  - build
  - publish

build-package:
  stage: build
  image: python:3.12
  before_script:
    - pip install build twine
  script:
    - python -m build
  artifacts:
    paths:
      - dist/
    expire_in: 1 hour

publish-pypi:
  stage: publish
  image: python:3.12
  dependencies:
    - build-package
  before_script:
    - pip install twine
  script:
    - twine upload dist/* --username __token__ --password $PYPI_API_TOKEN
  only:
    - tags
  when: manual
```

Ajoutez la variable `PYPI_API_TOKEN` dans les variables CI/CD de GitLab.

## Commandes utiles

```bash
# Vérifier le package avant publication
uv run twine check dist/*

# Voir ce qui sera publié
tar -tzf dist/idf2table-*.tar.gz | head -20

# Nettoyer les fichiers de build
rm -rf dist/ build/ *.egg-info __pycache__ .eggs/
```

## Checklist avant publication

- [ ] Version incrémentée dans `pyproject.toml`
- [ ] README.md à jour et correct
- [ ] Tests passent (si vous en avez)
- [ ] Toutes les dépendances listées dans `pyproject.toml`
- [ ] Le package fonctionne après `python -m build`
- [ ] `twine check dist/*` ne signale pas d'erreurs
- [ ] Test sur TestPyPI réussi (optionnel)

## Notes importantes

- ⚠️ **PyPI ne permet pas de supprimer une version publiée**, seulement d'ajouter de nouvelles versions
- ✅ Utilisez [semantic versioning](https://semver.org/) : MAJOR.MINOR.PATCH
- 📝 Testez toujours sur TestPyPI avant de publier sur PyPI
- 🔒 Ne partagez jamais votre token API publiquement
- 📦 Le nom du package `idf2table` doit être unique sur PyPI

## Ressources

- [Guide officiel PyPI](https://packaging.python.org/en/latest/guides/publishing-package-distribution-using-twine/)
- [Documentation twine](https://twine.readthedocs.io/)
- [Semantic Versioning](https://semver.org/)

