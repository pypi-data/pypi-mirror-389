import argparse
import numpy as np
import pandas as pd
from .core import cronbachs_alpha
from .sample import load_sample_matrix


def main() -> None:
    import argparse
    import numpy as np
    import pandas as pd
    from .core import cronbachs_alpha
    from .sample import load_sample_matrix

    parser = argparse.ArgumentParser(prog="missalpha", description="Cronbach's alpha bounds with missing data")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # existing "csv" subcommand ...
    p_csv = sub.add_parser("csv", help="Read a CSV file and compute bounds")
    p_csv.add_argument("--path", required=True, help="Path to CSV file")
    p_csv.add_argument("--score-max", type=int, required=True, help="Maximum possible item score")
    p_csv.add_argument("--num-random", type=int, default=1000)
    p_csv.add_argument("--enum-all", action="store_true")
    p_csv.add_argument("--num-opt", type=int, default=1)
    p_csv.add_argument("--debug", action="store_true")

    # NEW: "demo" runs the embedded sample.csv
    p_demo = sub.add_parser("demo", help="Run on the embedded sample.csv packaged with missalpha")
    p_demo.add_argument("--score-max", type=int, default=None, help="If omitted, infer from the sample data")
    p_demo.add_argument("--num-random", type=int, default=1000)
    p_demo.add_argument("--enum-all", action="store_true")
    p_demo.add_argument("--num-opt", type=int, default=1)
    p_demo.add_argument("--debug", action="store_true")

    args = parser.parse_args()

    if args.cmd == "csv":
        df = pd.read_csv(args.path)
        X = df.to_numpy(dtype=float)
        a_min, a_max = cronbachs_alpha(
            X,
            score_max=args.score_max,
            num_random=args.num_random,
            enum_all=args.enum_all,
            num_opt=args.num_opt,
            debug=args.debug,
        )
        print(f"alpha_min={a_min:.6f}, alpha_max={a_max:.6f}")

    elif args.cmd == "demo":
        X = load_sample_matrix()
        # If score_max not provided, infer from data (ignoring NaNs)
        sm = int(np.nanmax(X)) if args.score_max is None else args.score_max
        a_min, a_max = cronbachs_alpha(
            X,
            score_max=sm,
            num_random=args.num_random,
            enum_all=args.enum_all,
            num_opt=args.num_opt,
            debug=args.debug,
        )
        print(f"[demo] score_max={sm} -> alpha_min={a_min:.6f}, alpha_max={a_max:.6f}")

