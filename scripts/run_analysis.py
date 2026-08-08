from pathlib import Path
import argparse
import os
import subprocess
import sys


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

NOTEBOOK = (
    PROJECT_ROOT
    / "notebooks"
    / "01_remal_validation.ipynb"
)

CHECK_SCRIPT = (
    PROJECT_ROOT
    / "scripts"
    / "check_inputs.py"
)


# ============================================================
# AVAILABLE RUNS
# ============================================================

CYCLONES = [
    "remal",
    "sitrang",
    "midhili",
]

LEAD_TIMES = [
    "1dlt",
    "2dlt",
    "3dlt",
]


# ============================================================
# RUN ONE CYCLONE + LEAD TIME
# ============================================================

def run_one(cyclone, lead):

    cyclone = cyclone.lower()
    lead = lead.lower()

    # --------------------------------------------------------
    # Validate arguments
    # --------------------------------------------------------

    if cyclone not in CYCLONES:
        raise ValueError(
            f"Unknown cyclone: {cyclone}\n"
            f"Available cyclones: {', '.join(CYCLONES)}"
        )

    if lead not in LEAD_TIMES:
        raise ValueError(
            f"Unknown lead time: {lead}\n"
            f"Available lead times: {', '.join(LEAD_TIMES)}"
        )

    # --------------------------------------------------------
    # Output directory
    # --------------------------------------------------------

    output_dir = (
        PROJECT_ROOT
        / "outputs"
        / cyclone
        / lead
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Executed notebook name
    # --------------------------------------------------------

    executed_notebook = (
        output_dir
        / f"{cyclone}_{lead}_validation_executed.ipynb"
    )

    # --------------------------------------------------------
    # Run information
    # --------------------------------------------------------

    print()
    print("=" * 78)
    print("IBF ANALYSIS")
    print("=" * 78)

    print(f"Cyclone         : {cyclone.upper()}")
    print(f"Lead time       : {lead}")
    print(f"Repository root : {PROJECT_ROOT}")
    print(f"Notebook        : {NOTEBOOK}")
    print(f"Output folder   : {output_dir}")

    # ========================================================
    # STEP 1 — CHECK INPUTS
    # ========================================================

    print()
    print("=" * 78)
    print("STEP 1/2 — CHECKING INPUTS")
    print("=" * 78)

    subprocess.run(
        [
            sys.executable,
            str(CHECK_SCRIPT),
            "--cyclone",
            cyclone,
            "--lead",
            lead,
        ],
        cwd=PROJECT_ROOT,
        check=True,
    )

    # ========================================================
    # STEP 2 — PASS RUN PARAMETERS TO NOTEBOOK
    # ========================================================

    env = os.environ.copy()

    env["IBF_CYCLONE"] = cyclone
    env["IBF_LEAD"] = lead

    # ========================================================
    # STEP 3 — EXECUTE NOTEBOOK
    # ========================================================

    print()
    print("=" * 78)
    print("STEP 2/2 — RUNNING NOTEBOOK")
    print("=" * 78)

    subprocess.run(
        [
            sys.executable,
            "-m",
            "jupyter",
            "nbconvert",

            "--to",
            "notebook",

            "--execute",
            str(NOTEBOOK),

            "--ExecutePreprocessor.timeout=-1",

            "--output",
            executed_notebook.name,

            "--output-dir",
            str(output_dir),
        ],

        cwd=PROJECT_ROOT,
        env=env,
        check=True,
    )

    # ========================================================
    # COMPLETED
    # ========================================================

    print()
    print("=" * 78)
    print("IBF ANALYSIS COMPLETED SUCCESSFULLY")
    print("=" * 78)

    print(f"Cyclone           : {cyclone.upper()}")
    print(f"Lead time         : {lead}")
    print(f"Results           : {output_dir}")
    print(f"Executed notebook : {executed_notebook}")


# ============================================================
# COMMAND-LINE INTERFACE
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Run Impact-Based Forecast validation "
            "for a cyclone and forecast lead time."
        )
    )

    # --------------------------------------------------------
    # Positional cyclone
    #
    # Example:
    # python scripts/run_analysis.py sitrang 2dlt
    # --------------------------------------------------------

    parser.add_argument(
        "cyclone",
        nargs="?",
        choices=CYCLONES,
        help=(
            "Cyclone name: "
            "remal, sitrang, or midhili"
        ),
    )

    # --------------------------------------------------------
    # Positional lead time
    # --------------------------------------------------------

    parser.add_argument(
        "lead",
        nargs="?",
        choices=LEAD_TIMES,
        help=(
            "Forecast lead time: "
            "1dlt, 2dlt, or 3dlt"
        ),
    )

    # --------------------------------------------------------
    # Run everything
    # --------------------------------------------------------

    parser.add_argument(
        "--all",
        action="store_true",
        help=(
            "Run all cyclones and all "
            "forecast lead times."
        ),
    )

    args = parser.parse_args()

    # ========================================================
    # RUN ALL 9 COMBINATIONS
    # ========================================================

    if args.all:

        total_runs = (
            len(CYCLONES)
            * len(LEAD_TIMES)
        )

        run_number = 0

        print()
        print("=" * 78)
        print("RUNNING COMPLETE IBF VALIDATION")
        print("=" * 78)

        print(
            f"Cyclones   : "
            f"{', '.join(CYCLONES)}"
        )

        print(
            f"Lead times : "
            f"{', '.join(LEAD_TIMES)}"
        )

        print(
            f"Total runs : "
            f"{total_runs}"
        )

        for cyclone in CYCLONES:

            for lead in LEAD_TIMES:

                run_number += 1

                print()
                print("#" * 78)

                print(
                    f"RUN {run_number}/{total_runs}: "
                    f"{cyclone.upper()} — {lead}"
                )

                print("#" * 78)

                run_one(
                    cyclone,
                    lead,
                )

        # ----------------------------------------------------
        # All complete
        # ----------------------------------------------------

        print()
        print("=" * 78)
        print("ALL IBF ANALYSES COMPLETED")
        print("=" * 78)

        print(
            f"Completed {total_runs} "
            f"cyclone/lead-time combinations."
        )

        return

    # ========================================================
    # SINGLE RUN
    # ========================================================

    if args.cyclone is None:

        parser.error(
            "Cyclone is required.\n\n"
            "Example:\n"
            "  python scripts\\run_analysis.py sitrang 2dlt\n\n"
            "Or run everything:\n"
            "  python scripts\\run_analysis.py --all"
        )

    if args.lead is None:

        parser.error(
            "Lead time is required.\n\n"
            "Example:\n"
            "  python scripts\\run_analysis.py sitrang 2dlt"
        )

    run_one(
        args.cyclone,
        args.lead,
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except subprocess.CalledProcessError as exc:

        print()
        print("=" * 78)
        print("IBF ANALYSIS FAILED")
        print("=" * 78)

        print(
            f"A subprocess returned "
            f"exit code {exc.returncode}."
        )

        print(
            "Review the error message above."
        )

        sys.exit(
            exc.returncode
        )

    except Exception as exc:

        print()
        print("=" * 78)
        print("IBF ANALYSIS FAILED")
        print("=" * 78)

        print(exc)

        sys.exit(1)