# Pito

Dynamic PDF document generator using Python + XeLaTeX.

## Install

```bash
pip install pito
````

## Usage

```bash
pito init my_project
cd my_project
pito build
```

## Concept

`.pto` file can call python functions inline:

```pito
{{myFunc()}}
```

Pito lets you create programmable documents,
not static templates.

## Config

Edit `config.yaml` for metadata / title / author / etc.
