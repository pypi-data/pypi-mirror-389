# skelgen

A simple Python CLI tool that generates project skeletons from text-based structure files.

## Installation

```bash
pip install git+https://github.com/y1cho-HIU/ez-skelgen.git
```

## Usage
```bash
skelgen <structure.txt>
```

### Input file example:
```css
project/
    include/
        header.h
    src/
        main.c
    data/
    makefile
```

### This creates:
```css
project/
├── include/
│   └── header1.h
├── src/
│   └── main.c
├── data/
└── makefile
```