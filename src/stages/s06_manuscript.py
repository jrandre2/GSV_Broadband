"""
Stage 06: Manuscript Validation
===============================

Validate manuscript against journal requirements.

Input: manuscript_quarto/
Output: data_work/diagnostics/submission_validation.md
"""

import pandas as pd
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import MANUSCRIPT_DIR, DIAGNOSTICS_DIR
from src.utils.helpers import ensure_dir


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def validate_manuscript(manuscript_dir: Path) -> dict:
    """Validate manuscript files."""
    results = {
        'files_found': [],
        'files_missing': [],
        'word_counts': {},
        'issues': [],
    }

    # Check for required files
    required_files = [
        '_quarto.yml',
        'index.qmd',
        'references.bib',
    ]

    for filename in required_files:
        path = manuscript_dir / filename
        if path.exists():
            results['files_found'].append(filename)
        else:
            results['files_missing'].append(filename)
            results['issues'].append(f"Missing required file: {filename}")

    # Count words in main manuscript
    index_path = manuscript_dir / 'index.qmd'
    if index_path.exists():
        with open(index_path, 'r') as f:
            content = f.read()
        results['word_counts']['index.qmd'] = count_words(content)

    # Check figures directory
    figures_dir = manuscript_dir / 'figures'
    if figures_dir.exists():
        figures = list(figures_dir.glob('*.png')) + list(figures_dir.glob('*.pdf'))
        results['n_figures'] = len(figures)
    else:
        results['n_figures'] = 0
        results['issues'].append("Figures directory not found")

    return results


def generate_validation_report(results: dict) -> str:
    """Generate markdown validation report."""
    lines = [
        "# Manuscript Validation Report",
        "",
        "## File Status",
        "",
    ]

    if results['files_found']:
        lines.append("### Found")
        for f in results['files_found']:
            lines.append(f"- [x] {f}")
        lines.append("")

    if results['files_missing']:
        lines.append("### Missing")
        for f in results['files_missing']:
            lines.append(f"- [ ] {f}")
        lines.append("")

    lines.extend([
        "## Statistics",
        "",
        f"- Figures: {results.get('n_figures', 0)}",
    ])

    for file, count in results.get('word_counts', {}).items():
        lines.append(f"- Word count ({file}): {count}")

    if results.get('issues'):
        lines.extend([
            "",
            "## Issues",
            "",
        ])
        for issue in results['issues']:
            lines.append(f"- {issue}")

    return "\n".join(lines)


def main(journal: str = 'default') -> int:
    """Run Stage 06: Manuscript Validation."""
    print("=" * 70)
    print("STAGE 06: MANUSCRIPT VALIDATION")
    print("=" * 70)

    try:
        print(f"\n📂 Validating manuscript in: {MANUSCRIPT_DIR}")

        if not MANUSCRIPT_DIR.exists():
            print("   Manuscript directory not found - creating placeholder")
            ensure_dir(MANUSCRIPT_DIR)

        results = validate_manuscript(MANUSCRIPT_DIR)

        # Generate report
        report = generate_validation_report(results)

        # Save report
        ensure_dir(DIAGNOSTICS_DIR)
        report_path = DIAGNOSTICS_DIR / 'submission_validation.md'
        with open(report_path, 'w') as f:
            f.write(report)

        print(f"\n📄 Validation report saved: {report_path}")

        # Print summary
        print("\n📊 Summary:")
        print(f"   Files found: {len(results['files_found'])}")
        print(f"   Files missing: {len(results['files_missing'])}")
        print(f"   Figures: {results.get('n_figures', 0)}")
        print(f"   Issues: {len(results.get('issues', []))}")

        if results.get('issues'):
            print("\n⚠️  Issues found:")
            for issue in results['issues']:
                print(f"   - {issue}")

        print("\n✅ Stage 06 complete!")
        return 0

    except Exception as e:
        print(f"\n❌ Stage 06 failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--journal', default='default')
    args = parser.parse_args()
    sys.exit(main(journal=args.journal))
