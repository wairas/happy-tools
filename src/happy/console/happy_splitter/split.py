import argparse
import traceback

from happy.base.app import init_app
from happy.splitters import CrossValidationSplitter, TrainTestSplitter

            
def main():
    init_app()
    parser = argparse.ArgumentParser(
        description='Generate train/validation/test splits for Happy data.',
        prog="happy-splitter",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d', '--happy_base_folder', type=str, help='Path to the Happy base folder', required=True)
    parser.add_argument('-r', '--num_repeats', type=int, default=1, help='Number of repeats')
    parser.add_argument('-f', '--num_folds', type=int, default=1, help='Number of folds')
    parser.add_argument('-t', '--train_percent', type=float, default=70.0, help='Percentage of data in the training set')
    parser.add_argument('-v', '--validation_percent', type=float, default=10.0, help='Percentage of data in the validation set')
    parser.add_argument('-R', '--use_regions', action='store_true', help='Use regions in generating splits')
    parser.add_argument('-H', '--holdout_percent', type=float, default=None, help='Percentage of data to hold out as a holdout set')
    parser.add_argument('-o', '--output_file', type=str, default='output_split.json', help='Path to the output split file', required=True)
    parser.add_argument("-S", "--seed", type=int, help="The seed to use for reproducible results", required=False, default=None)
    args = parser.parse_args()

    if args.num_folds == 1:
        splitter = TrainTestSplitter(args.happy_base_folder, args.use_regions, args.train_percent, args.validation_percent, holdout_percent=args.holdout_percent, seed=args.seed)
    else:
        splitter = CrossValidationSplitter(args.happy_base_folder, args.use_regions, args.num_repeats, args.num_folds, args.train_percent, args.validation_percent, holdout_percent=args.holdout_percent, seed=args.seed)
    splits = splitter.generate_splits()
    splits.save(args.output_file)


def sys_main() -> int:
    """
    Runs the main function using the system cli arguments, and
    returns a system error code.

    :return: 0 for success, 1 for failure.
    """
    try:
        main()
        return 0
    except Exception:
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    main()
