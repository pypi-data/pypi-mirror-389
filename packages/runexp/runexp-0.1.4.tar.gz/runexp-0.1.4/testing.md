# How to "test"

- argparse vs config_file [Ap] [Cf]
- no_sweep vs sweep [Ns] [Sp]
- slurm+template vs slurm vs local [ST] [Sm] [Lc]

('Ap', 'Ns', 'ST')
python examples/argparse/main.py target --string 'a bc' --float 0.1 --no-option --sc --runexp-slurm-template examples/job.sh.template

('Ap', 'Ns', 'Sm')  env:OK, absent from dry-run
python examples/argparse/main.py target --string 'a bc' --float 0.1 --no-option --sc --runexp-slurm

('Ap', 'Ns', 'Lc')  env:OK, absent from dry-run
python examples/argparse/main.py target --string 'a bc' --float 0.1 --no-option --sc --runexp-max-concurrent-sweep 1

('Ap', 'Sp', 'ST')  env:OK, seen in the template
python examples/argparse/main.py target --string 'a bc' --sweep-float 0.1,0.2 --no-option --sc --runexp-slurm-template examples/job.sh.template

('Ap', 'Sp', 'Sm') -> not supported (slurm requires a template for a job array)

('Ap', 'Sp', 'Lc') env:OK, absent from dry-run
python examples/argparse/main.py target --string 'a bc' --sweep-float 0.1,0.2 --no-option --sc --runexp-max-concurrent-sweep 1

('Cf', 'Ns', 'ST')  env:OK, seen in the template
python examples/config_file/main.py examples/config_file/config.yml --runexp-slurm-template examples/job.sh.template

('Cf', 'Ns', 'Sm')  env:OK, absent from dry-run
python examples/config_file/main.py examples/config_file/config.yml --runexp-slurm

('Cf', 'Ns', 'Lc')  env:OK, absent from dry-run
python examples/config_file/main.py examples/config_file/config.yml

('Cf', 'Sp', 'ST')  env:OK, seen in the template
python examples/config_file/main.py examples/config_file/config_sweep.yml --runexp-slurm-template examples/job.sh.template

('Cf', 'Sp', 'Sm') -> not supported (slurm requires a template for a job array)

('Cf', 'Sp', 'Lc')  env:OK, absent from-dru-run
python examples/config_file/main.py examples/config_file/config_sweep.yml
