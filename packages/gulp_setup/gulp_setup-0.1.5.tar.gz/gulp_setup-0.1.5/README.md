# Gulp Input Setter

A simple Python module for creating GULP input files from CIF structures.

## Installation

The installation is very straightforward. Follow the steps below.

### Dependencies

The only dependency is:

- ase (Atomic Simulation Environment)

### Install from PyPI

```bash
pip install gulp_setup
```

### Install from GitHub

Step 1: Clone the repository

```bash
git clone https://github.com/bafgreat/gulp_setup.git
```

Step 2: Move into the folder

```bash
cd gulp_setup
```

Step 3: Install the package

```bash
pip install .
```

This command will install the gulp_setup Python package locally.

## Usage

### Create inputs from a folder of CIF files

Run the command below to create a GULP input file for each CIF file in a folder.
Each file will be placed into a folder named after the prefix of the input file name.

```bash
gulp_setup_folder folder
```

### Create a single input file

If you do not want to create individual folders for each input file, simply run:

```bash
gulp_setup_file input.cif
```

This command will create an input.gin file in the same folder. This is useful when you do not want to create multiple folders for each input file.

### Lattice optimization

By default, GULP input files are created for constant volumes (lattice not optimized).
If you want to optimize the lattices, add the `-op conp` argument after the name of the input file.

Example:

```bash
gulp_setup_file input.cif -op conp
```

This will trigger lattice optimization.

## Running GULP

If you have GULP installed, you can simply run it as follows:

```bash
gulp < input.gin > input.got
```

or

```bash
~/src/gulp-6.0/Src/gulp < input.gin > input.got
```

## Notes

The second example assumes you have compiled GULP into a folder called `$HOME/src`.

For more information about installing GULP, visit:
[Download GULP](https://gulp.curtin.edu.au/download.html)

You can also email me if you have trouble with your installation. I am not an expert but I may have some knowledge to guide you.

## Enjoy gulping