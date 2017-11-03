from tensorflow.contrib.learn import (Experiment, utils as learn_utils)
from cache.models.responsive import (train_input as responsive_train_fn,
                                     eval_input as responsive_eval_fn,
                                     serving_input as responsive_serving_fn,
                                     DEFAULT_ESTIMATOR as responsive_default)


def generate_experiment(estimator, model_type, train_file, test_file,
                        **experiment_args):
    """
        Generate a tf.contrib.learn.Experiment object for the
        guien estimator

        :param estimator: tf.contrib.learn.Estimator to use
        :param model_type: str. model type. Currently supported types are:
            - responsive: For a guiven search suggests a set of searches
        :param experiment_args: dict. Arguments piped to Experiment constructor

        :return: tf.contrib.learn.Experiment wraping the estimator
    """

    if model_type == 'responsive':
        train_input = responsive_train_fn(train_file)
        eval_input = responsive_eval_fn(test_file)
        serving_input = responsive_serving_fn()
    else:
        error_msg = "Model type {} is not supported".format(model_type)
        raise ValueError(error_msg)

    serving = learn_utils.saved_model_export_utils.make_export_strategy(
            serving_input,
            default_output_alternative_key=None,
            exports_to_keep=1
    )

    experiment = Experiment(estimator,
                            train_input_fn=train_input,
                            eval_input_fn=eval_input,
                            export_strategies=[serving],
                            **experiment_args)
    return experiment


def generate_experiment_fn(train_file, test_file,
                           model_type='responsive', estimator_fn=None,
                           estimator_config={}, **experiment_args):
    if model_type == 'responsive':
        estimator_fn = estimator_fn or responsive_default
    else:
        error_msg = "Model type {} is not supported".format(model_type)
        raise ValueError(error_msg)

    def _experiment_fn(output_dir):
        estimator = estimator_fn(output_dir, **estimator_config)
        experiment = generate_experiment(estimator, model_type, train_file,
                                         test_file, **experiment_args)
        return experiment

    return _experiment_fn
