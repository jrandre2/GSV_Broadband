#!/usr/bin/env python3
"""
ML Vision Broadband Pipeline CLI
=================================

CENTAUR-style command-line interface for running the analysis pipeline.

Usage:
    python src/pipeline.py <command> [options]

Commands:
    ingest_data         Load and validate raw data (s00)
    link_records        Link images to ZIP codes and labels (s01)
    build_panel         Extract features and build analysis panel (s02)
    run_estimation      Train ML models (s03)
    estimate_robustness Run robustness checks (s04)
    make_figures        Generate publication figures (s05)
    validate_manuscript Validate manuscript (s06)
    run_all             Run complete pipeline
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main():
    parser = argparse.ArgumentParser(
        description="ML Vision Broadband CENTAUR Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    subparsers = parser.add_subparsers(dest='command', help='Pipeline commands')

    # Stage 00: Ingest Data
    p_ingest = subparsers.add_parser(
        'ingest_data',
        help='Load and validate raw data (manifest, labels, RUCA codes)'
    )
    p_ingest.add_argument('--use-demo', action='store_true',
                          help='Use demo/sample data')

    # Stage 01: Link Records
    p_link = subparsers.add_parser(
        'link_records',
        help='Link images to ZIP codes and broadband labels'
    )

    # Stage 02: Build Panel
    p_panel = subparsers.add_parser(
        'build_panel',
        help='Extract CV features and build analysis panel'
    )
    p_panel.add_argument('--recompute', action='store_true',
                         help='Force recomputation of features')
    p_panel.add_argument('--max-images', type=int, default=10,
                         help='Max images per ZIP for feature extraction')

    # Stage 03: Run Estimation
    p_est = subparsers.add_parser(
        'run_estimation',
        help='Train ML models (Ridge, RF, ExtraTrees)'
    )
    p_est.add_argument('--models', nargs='+',
                       default=['ruca_baseline', 'visual_only', 'combined'],
                       help='Models to train')
    p_est.add_argument('--all', action='store_true',
                       help='Run all model specifications')
    p_est.add_argument('--profile', default='default',
                       help='Estimation profile (default, conference)')

    # Stage 04: Robustness
    p_robust = subparsers.add_parser(
        'estimate_robustness',
        help='Run robustness checks (spatial CV, RUCA encoding, ablation)'
    )
    p_robust.add_argument('--compare-cv', action='store_true',
                          help='Compare spatial vs random CV')
    p_robust.add_argument('--spatial-sensitivity', action='store_true',
                          help='Run sensitivity across spatial grouping methods')

    # Stage 05: Figures
    p_figs = subparsers.add_parser(
        'make_figures',
        help='Generate publication-quality figures'
    )
    p_figs.add_argument('--figures', nargs='+',
                        help='Specific figures to generate')

    # Stage 06: Manuscript
    p_ms = subparsers.add_parser(
        'validate_manuscript',
        help='Validate manuscript against journal requirements'
    )
    p_ms.add_argument('--journal', default='default',
                      help='Journal configuration to use')

    # Run All
    p_all = subparsers.add_parser(
        'run_all',
        help='Run complete pipeline from ingestion to figures'
    )
    p_all.add_argument('--skip', nargs='+', default=[],
                       help='Stages to skip')

    # Parse arguments
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 1

    # Route to appropriate stage
    try:
        if args.command == 'ingest_data':
            from src.stages import s00_ingest
            return s00_ingest.main(use_demo=args.use_demo)

        elif args.command == 'link_records':
            from src.stages import s01_link
            return s01_link.main()

        elif args.command == 'build_panel':
            from src.stages import s02_panel
            return s02_panel.main(
                recompute=args.recompute,
                max_images=args.max_images,
            )

        elif args.command == 'run_estimation':
            from src.stages import s03_estimation
            return s03_estimation.main(
                models=args.models if not args.all else None,
                run_all=args.all,
                profile=args.profile,
            )

        elif args.command == 'estimate_robustness':
            from src.stages import s04_robustness
            return s04_robustness.main(
                compare_cv=args.compare_cv,
                spatial_sensitivity=args.spatial_sensitivity,
            )

        elif args.command == 'make_figures':
            from src.stages import s05_figures
            return s05_figures.main(figures=args.figures)

        elif args.command == 'validate_manuscript':
            from src.stages import s06_manuscript
            return s06_manuscript.main(journal=args.journal)

        elif args.command == 'run_all':
            return run_full_pipeline(skip=args.skip)

        else:
            print(f"Unknown command: {args.command}")
            return 1

    except Exception as e:
        print(f"Error in {args.command}: {e}")
        import traceback
        traceback.print_exc()
        return 1


def run_full_pipeline(skip: list = None):
    """Run the complete pipeline."""
    skip = skip or []
    stages = [
        ('ingest_data', 's00_ingest'),
        ('link_records', 's01_link'),
        ('build_panel', 's02_panel'),
        ('run_estimation', 's03_estimation'),
        ('estimate_robustness', 's04_robustness'),
        ('make_figures', 's05_figures'),
    ]

    print("=" * 70)
    print("ML VISION BROADBAND - FULL PIPELINE")
    print("=" * 70)

    for stage_name, module_name in stages:
        if stage_name in skip:
            print(f"\n⏭️  Skipping {stage_name}...")
            continue

        print(f"\n{'=' * 70}")
        print(f"RUNNING: {stage_name}")
        print("=" * 70)

        try:
            module = __import__(f'src.stages.{module_name}', fromlist=['main'])
            result = module.main()
            if result != 0:
                print(f"❌ Stage {stage_name} failed with code {result}")
                return result
        except Exception as e:
            print(f"❌ Stage {stage_name} failed: {e}")
            import traceback
            traceback.print_exc()
            return 1

    print("\n" + "=" * 70)
    print("✅ PIPELINE COMPLETE")
    print("=" * 70)
    return 0


if __name__ == '__main__':
    sys.exit(main())
