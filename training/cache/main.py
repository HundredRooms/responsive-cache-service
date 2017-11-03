import os
from argparse import ArgumentParser
from json import load as json_load, loads as json_loads
from tensorflow.contrib.learn.python.learn import learn_runner

from cache.models.experiment import generate_experiment_fn
from cache.utils import check_path, full_path, FileNotFoundError

eget = os.environ.get


HYPERPARAMETERS = {
        'hidden1': {
            'type': int,
            'description': 'First hidden layer size',
            'default': 20,
        },
        'hidden2': {
            'type': int,
            'description': 'Second hidden layer size',
            'default': 100,
        },
        'ones_bias': {
            'type': int,
            'description': 'Bias to outweight 1vs0 over 0vs1',
            'default': 15,
        },
        'bool_th': {
            'type': float,
            'description': 'Threshold to decide wether a label is set or not',
            'default': 0.6,
        },
}


if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument('-o', '--out_dir', help='Experiment output directory')
    parser.add_argument('-j', '--job-dir', dest='job_dir',
                        help='Experiment output directory')
    parser.add_argument('-t', '--train_file', help='Input train file')
    parser.add_argument('-e', '--test_file', help='Input test file')
    parser.add_argument('-c', '--config_file',
                        help='JSON file defining experiment setup')
    parser.add_argument('-n', '--train_steps', type=int,
                        help='Number of train steps')

    for name, info in HYPERPARAMETERS.items():
        parser.add_argument('--{}'.format(name),
                            type=info['type'],
                            help=info['description'])

    args = parser.parse_args()

    env = json_loads(eget('TF_CONFIG', '{}'))
    task_trial = env.get('task', {}).get('trial', '')

    job_dir = args.job_dir
    output_dir = os.path.join(args.out_dir or job_dir, task_trial)
    train_file = full_path(args.train_file)
    test_file = full_path(args.test_file)
    train_steps = args.train_steps

    try:
        config_file = check_path(args.config_file)

        with open(config_file, 'r') as f_conf:
            estimator_config = json_load(f_conf)

    except FileNotFoundError:
        estimator_config = {}

    for name, info in HYPERPARAMETERS.items():
        param = getattr(args, name) or info['default']
        estimator_config[name] = param

    exp_fn = generate_experiment_fn(train_steps=train_steps, eval_steps=1,
                                    train_file=train_file, test_file=test_file,
                                    estimator_config=estimator_config)
    learn_runner.run(exp_fn, output_dir)
