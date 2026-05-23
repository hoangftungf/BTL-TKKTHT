"""
Full Pipeline Runner
====================
Orchestrates the complete data preparation and evaluation pipeline.

Usage:
    # Run full pipeline
    python scripts/run_pipeline.py --all

    # Run specific phases
    python scripts/run_pipeline.py --phase data      # Scrape & normalize
    python scripts/run_pipeline.py --phase import    # Import to Django
    python scripts/run_pipeline.py --phase index     # Build FAISS & Neo4j
    python scripts/run_pipeline.py --phase evaluate  # Run model evaluation
    python scripts/run_pipeline.py --phase charts    # Generate charts
"""

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}  {text}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}\n")


def print_step(text: str):
    print(f"{Colors.BLUE}[STEP]{Colors.END} {text}")


def print_success(text: str):
    print(f"{Colors.GREEN}[OK]{Colors.END} {text}")


def print_warning(text: str):
    print(f"{Colors.YELLOW}[WARN]{Colors.END} {text}")


def print_error(text: str):
    print(f"{Colors.RED}[ERROR]{Colors.END} {text}")


def run_command(cmd: list, cwd: str = None, env: dict = None) -> bool:
    """Run a command and return success status"""
    print_step(f"Running: {' '.join(cmd[:5])}...")

    full_env = os.environ.copy()
    if env:
        full_env.update(env)

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=full_env,
            capture_output=False,
            text=True
        )
        if result.returncode == 0:
            print_success("Command completed successfully")
            return True
        else:
            print_error(f"Command failed with code {result.returncode}")
            return False
    except Exception as e:
        print_error(f"Command error: {e}")
        return False


def phase_data(args):
    """Phase 1: Data collection and normalization"""
    print_header("PHASE 1: DATA COLLECTION & NORMALIZATION")

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    # Step 1: Generate synthetic large dataset
    print_step("Generating synthetic large dataset (500 products)...")
    if not run_command([
        sys.executable, 'scripts/data/generate_synthetic_large.py',
        '--output', 'data/processed/synthetic_large.json',
        '--count', '500',
        '--category-map', 'scripts/data/category_mapping.json'
    ]):
        return False

    # Step 2: Scrape Tiki (if requested)
    if args.scrape_tiki:
        print_step("Scraping Tiki products...")
        if not run_command([
            sys.executable, 'scripts/scrapers/tiki_scraper.py',
            '--output', 'data/raw/tiki_products.json',
            '--limit', str(args.tiki_limit),
            '--categories', args.tiki_categories
        ]):
            print_warning("Tiki scraping failed, continuing with synthetic data only")

        # Normalize Tiki data
        if os.path.exists('data/raw/tiki_products.json'):
            print_step("Normalizing Tiki data...")
            run_command([
                sys.executable, 'scripts/data/normalize_scraped_data.py',
                '--tiki', 'data/raw/tiki_products.json',
                '--category-map', 'scripts/data/category_mapping.json',
                '--output', 'data/processed/'
            ])

    print_success("Phase 1 completed!")
    return True


def phase_import(args):
    """Phase 2: Import data to Django"""
    print_header("PHASE 2: IMPORT TO DJANGO")

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    product_service = os.path.join(project_root, 'services', 'product-service')

    # Check if product-service exists
    if not os.path.exists(product_service):
        print_error(f"Product service not found at {product_service}")
        return False

    os.chdir(product_service)

    # Clear existing data if requested
    if args.clear_db:
        print_step("Clearing existing data...")
        run_command([sys.executable, 'manage.py', 'flush', '--no-input'])

    # Import categories first
    print_step("Creating categories from mapping...")

    # Import synthetic large
    synthetic_large = os.path.join(project_root, 'data', 'processed', 'synthetic_large.json')
    if os.path.exists(synthetic_large):
        print_step("Importing synthetic_large dataset...")
        run_command([
            sys.executable, os.path.join(project_root, 'scripts', 'data', 'import_to_django.py'),
            '--source', synthetic_large,
            '--category-map', os.path.join(project_root, 'scripts', 'data', 'category_mapping.json'),
            '--dataset-tag', 'synthetic_large'
        ])

    # Import Tiki data
    tiki_norm = os.path.join(project_root, 'data', 'processed', 'tiki_normalized.json')
    if os.path.exists(tiki_norm):
        print_step("Importing real_tiki dataset...")
        run_command([
            sys.executable, os.path.join(project_root, 'scripts', 'data', 'import_to_django.py'),
            '--source', tiki_norm,
            '--category-map', os.path.join(project_root, 'scripts', 'data', 'category_mapping.json'),
            '--dataset-tag', 'real_tiki'
        ])

    print_success("Phase 2 completed!")
    return True


def phase_index(args):
    """Phase 3: Build FAISS and Neo4j indexes"""
    print_header("PHASE 3: BUILD INDEXES (FAISS & NEO4J)")

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Build FAISS index
    chatbot_service = os.path.join(project_root, 'services', 'ai-chatbot')
    if os.path.exists(chatbot_service):
        print_step("Building FAISS index...")
        os.chdir(chatbot_service)
        run_command([
            sys.executable, 'manage.py', 'build_ai_index',
            '--index-dir', '/app/ai_index' if args.docker else os.path.join(project_root, 'ai_index')
        ])

    # Push to Neo4j
    recommendation_service = os.path.join(project_root, 'services', 'ai-recommendation')
    if os.path.exists(recommendation_service):
        print_step("Pushing data to Neo4j...")
        os.chdir(recommendation_service)
        run_command([sys.executable, 'manage.py', 'push_to_neo4j', '--rebuild'])

        print_step("Enhancing Neo4j graph...")
        run_command([sys.executable, 'manage.py', 'enhance_graph'])

        print_step("Validating pipeline...")
        run_command([sys.executable, 'manage.py', 'validate_pipeline'])

    print_success("Phase 3 completed!")
    return True


def phase_evaluate(args):
    """Phase 4: Run model evaluation"""
    print_header("PHASE 4: MODEL EVALUATION")

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    models = args.models or 'llama3:8b,qwen2.5:7b,gemma2:9b'
    datasets = args.datasets or 'synthetic_large'

    cmd = [
        sys.executable, 'scripts/evaluation/evaluate_models.py',
        '--models', models,
        '--datasets', datasets,
        '--queries', 'scripts/evaluation/test_queries.json',
        '--output', 'results/evaluation_results.csv'
    ]

    if args.openai_key:
        cmd.extend(['--openai-key', args.openai_key])

    print_step(f"Evaluating models: {models}")
    print_step(f"Datasets: {datasets}")

    if not run_command(cmd):
        return False

    print_success("Phase 4 completed!")
    return True


def phase_charts(args):
    """Phase 5: Generate charts"""
    print_header("PHASE 5: GENERATE CHARTS")

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    results_file = 'results/evaluation_results.csv'
    if not os.path.exists(results_file):
        print_error(f"Results file not found: {results_file}")
        print_warning("Run evaluation phase first: python scripts/run_pipeline.py --phase evaluate")
        return False

    print_step("Generating comparison charts...")
    if not run_command([
        sys.executable, 'scripts/evaluation/generate_charts.py',
        '--input', results_file,
        '--output', 'results/charts/'
    ]):
        return False

    print_success("Phase 5 completed!")
    print(f"\nCharts saved to: results/charts/")
    return True


def main():
    parser = argparse.ArgumentParser(description='Run AI evaluation pipeline')
    parser.add_argument('--all', action='store_true', help='Run all phases')
    parser.add_argument('--phase', choices=['data', 'import', 'index', 'evaluate', 'charts'],
                        help='Run specific phase')

    # Data phase options
    parser.add_argument('--scrape-tiki', action='store_true', help='Scrape data from Tiki')
    parser.add_argument('--tiki-limit', type=int, default=500, help='Tiki scrape limit')
    parser.add_argument('--tiki-categories', default='laptop,smartphone,men_shirts,skincare',
                        help='Tiki categories to scrape')

    # Import phase options
    parser.add_argument('--clear-db', action='store_true', help='Clear existing database')
    parser.add_argument('--docker', action='store_true', help='Running in Docker environment')

    # Evaluate phase options
    parser.add_argument('--models', type=str, help='Comma-separated model names')
    parser.add_argument('--datasets', type=str, help='Comma-separated dataset names')
    parser.add_argument('--openai-key', type=str, help='OpenAI API key for LLM judge')

    args = parser.parse_args()

    start_time = time.time()

    print_header("AI E-COMMERCE EVALUATION PIPELINE")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    success = True

    if args.all:
        phases = ['data', 'import', 'index', 'evaluate', 'charts']
    elif args.phase:
        phases = [args.phase]
    else:
        parser.print_help()
        return

    phase_funcs = {
        'data': phase_data,
        'import': phase_import,
        'index': phase_index,
        'evaluate': phase_evaluate,
        'charts': phase_charts
    }

    for phase in phases:
        if not phase_funcs[phase](args):
            print_error(f"Phase '{phase}' failed!")
            success = False
            if args.all:
                print_warning("Continuing with next phase...")

    elapsed = time.time() - start_time
    print_header("PIPELINE COMPLETE")
    print(f"Total time: {elapsed/60:.1f} minutes")

    if success:
        print_success("All phases completed successfully!")
    else:
        print_warning("Some phases had errors - check output above")


if __name__ == '__main__':
    main()
