"""Entry point for `python -m quarry`."""

from quarry.cli import parse_args
from quarry.pipeline import run_pipeline


def main() -> None:
    args = parse_args()
    run_pipeline(
        game_path=args.game_path,
        language=args.language,
        output_dir=args.output_dir,
        game_version=args.version,
        categories=args.categories,
    )


if __name__ == "__main__":
    main()
