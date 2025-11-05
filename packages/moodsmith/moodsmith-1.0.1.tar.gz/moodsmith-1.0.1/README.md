[![Pylint](https://github.com/swe-students-fall2025/3-python-package-team_harbor/actions/workflows/pylint.yml/badge.svg)](https://github.com/swe-students-fall2025/3-python-packagepackage-team_harbor/actions/workflows/pylint.yml)
[![CI / CD](https://github.com/swe-students-fall2025/3-python-package-team_harbor/actions/workflows/tests.yml/badge.svg)](https://github.com/swe-students-fall2025/3-python-package-team_harbor/actions/workflows/tests.yml)

# Moodsmith

Pypi link: https://pypi.org/project/moodsmith

## Setting Up a Virtual Environment and Installing Moodsmith

### 1. Install pipenv

If you don’t already have `pipenv` installed, run:

```bash
pip install pipenv
```
### 2. Activate the virtual environment
```bash
pipenv shell
```

### 3. Install Moodsmith
```bash
pipenv install moodsmith
```
To verify the installation, run
```bash
moodsmith --version
```

## Moodsmith in the command line

For a list of all commands and available flags, type
```bash
moodsmith --help
```
### Example Usage
---
### Funny message
- For a funny message:
```bash
moodsmith -c funny
```
Available flags:
- --name (-n) : Name
- --enthusiasm (-e) : Enthusiasm (number of exclamation points after the message)
- --language (-l) : Language (en/fr/es)
### Negative motivational message
- For a sarcastic message:
```bash
moodsmith -c negative 
```
Available flags:
- --name (-n) : Name
- --enthusiasm (-e) : Enthusiasm (number of exclamation points after the message)
- --intensity (-i) : Intensity (soft/medum/hard) (How sarcastic should the message be)
- --language (-l) : Language (en/fr/es)
### Motivational message
- For a motivational message:
```bash
moodsmith -c motivational
```
Available flags:
- --name (-n) : Name
- --intensity (-i) : Intensity (soft, medium, hard) (How motivational should the message be)
- --language (-l) : Language (en/fr/es)
### Positive message:
- For a positive message:
```bash
moodsmith -c positive
```
Available flags:
- --name (-n) : Name
- --enthusiasm (-e) : Enthusiasm (number of exclamation points after the message)
- --language (-l) : Language (en/fr/es)
---
### Within a python program 
- Import moodsmith using:
```python
import moodsmith
```
- Alternatively, import specifically the needed functions from moodsmith. The below code imports all available functions. 
```python
from moodsmith import positive, negative, motivational, funny
```
### Usage of moodsmith functions:
- Funny:
```python
funny(name="name", enthusiasm=2, language="en", seed=22)
```
- Negative motivational:
```python
negative(name="name", enthusiasm=0, intensity="hard", language="fr", seed=22)
```
- Motivational:
```python
motivational(name="name", intensity="soft", language="es", seed=22)
```
- Positive:
```python
positive(name="name", enthusiasm=5, language="en", seed=22)
```

Note that all arguments have defaults and none are required.

For an example python project using moodsmith, click here: [example moodsmith program](examples/demo.py)

# Contributors
- Samuel Yang (https://github.com/SamuelYang24)
- Conor Tiernan (https://github.com/ct-04)
- Ganling Zhou (https://github.com/GanlingZ)
- Eason Huang (https://github.com/GILGAMESH605)
- Harrison Coon (https://github.com/hoc2006-code)