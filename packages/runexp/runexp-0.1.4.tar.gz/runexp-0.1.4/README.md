# runexp

Library to run experiment from argparse or config file with slurm

## Examples

### `argparse`

To work with the builtin `argparse` library, have a look at the file `examples/argparse/main.py`. The only change required is the line to parse the arguments :

```diff
import argparse
from runexp import parse

parser = argparse.ArgumentParser(...)

parser.add_argument(...)

- args = parser.parse_args()
+ args = parse(parser)

# rest of the program, using `args`
time.sleep(5.0)
pprint.pprint(vars(args))
```

If you don't specify any special options, it's like `runexp` was never there in the first place.

```sh
python examples/argparse/main.py target --string 'a bc' --float 0.1 --no-option --sc
```

To perform a parameter sweep, you can prefix key-value arguments with `sweep-` and write all values as a coma separated list. Because dry-run is the default, it will print the command to execute the script and show a description equivalent to what the run would be :

```sh
$ python examples/argparse/main.py target --string 'a bc' --sweep-float 0.1,0.2,0.3 --no-option --sc
=== DRY RUN ===
run the command below for an actual execution
python examples/argparse/main.py target --string 'a bc' --sweep-float 0.1,0.2,0.3 --no-option --sc --runexp-no-dry-run
===============
/home/maxime/repos/runexp/.venv/bin/python examples/argparse/main.py target --float 0.1 --no-option --sc --string 'a bc'
/home/maxime/repos/runexp/.venv/bin/python examples/argparse/main.py target --float 0.2 --no-option --sc --string 'a bc'
/home/maxime/repos/runexp/.venv/bin/python examples/argparse/main.py target --float 0.3 --no-option --sc --string 'a bc'
```

If you want to run this code on a SLURM cluster, you can do it as follows :

```sh
$ python examples/argparse/main.py target --string 'a bc' --float 0.1 --no-option --sc --runexp-slurm
=== DRY RUN ===
run the command below for an actual execution
python examples/argparse/main.py target --string 'a bc' --float 0.1 --no-option --sc --runexp-slurm --runexp-no-dry-run
===============
```

## Behavior inconsistance

What should happen if no runexp option is given ?

For the ArgParse case, it makes sense that if no RunExp option is found, nothing happens : RunExp should be minimally intrusive and avoid breaking everything, so args are returned as if RunExp did nothing.

For the ConfigFile case, it is not possible to run the program without RunExp as this is the way to parse the config. If it makes sense to re-use the function, it should be defined elsewhere and the decorator should be used as a function.

Moreover, because the ArgParse function needs to return the namespace, it should exit the process on a dry run, while the ConfigFile currently doesn't.
