"""
Chart Generator for Model Evaluation Results
=============================================
Generates comparison charts from evaluation results.

Usage:
    python scripts/evaluation/generate_charts.py \
        --input results/evaluation_results.csv \
        --output results/charts/

Output:
    - latency_comparison.png
    - faithfulness_comparison.png
    - relevance_comparison.png
    - overall_radar.png
    - query_type_breakdown.png
"""

import argparse
import os
import pandas as pd
import numpy as np

# Use Agg backend for non-interactive environments
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# Try to use a font that supports Vietnamese (optional)
try:
    plt.rcParams['font.family'] = 'DejaVu Sans'
except:
    pass

plt.style.use('seaborn-v0_8-whitegrid')


def load_results(filepath: str) -> pd.DataFrame:
    """Load evaluation results from CSV"""
    df = pd.read_csv(filepath)
    return df


def plot_latency_comparison(df: pd.DataFrame, output_dir: str):
    """Generate latency comparison bar chart"""
    # Group by model and calculate stats
    latency_stats = df.groupby('model')['latency_ms'].agg(['mean', 'std', 'median']).reset_index()

    fig, ax = plt.subplots(figsize=(10, 6))

    models = latency_stats['model']
    x = np.arange(len(models))
    width = 0.35

    # Mean with std error bars
    bars = ax.bar(x, latency_stats['mean'], width, yerr=latency_stats['std'],
                  capsize=5, color=['#3498db', '#e74c3c', '#2ecc71'][:len(models)],
                  alpha=0.8, label='Mean')

    # Add median line
    ax.scatter(x, latency_stats['median'], color='black', marker='_', s=200,
               linewidths=3, zorder=5, label='Median')

    ax.set_xlabel('Model', fontsize=12)
    ax.set_ylabel('Latency (ms)', fontsize=12)
    ax.set_title('Response Latency Comparison', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(models, fontsize=10)
    ax.legend()

    # Add value labels on bars
    for bar, val in zip(bars, latency_stats['mean']):
        ax.annotate(f'{val:.0f}ms',
                    xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    xytext=(0, 5), textcoords='offset points',
                    ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'latency_comparison.png'), dpi=150)
    plt.close()
    print(f"  Generated: latency_comparison.png")


def plot_faithfulness_comparison(df: pd.DataFrame, output_dir: str):
    """Generate faithfulness metrics comparison"""
    # Calculate faithfulness components
    faith_data = df.groupby('model').agg({
        'has_citation': 'mean',
        'has_hallucination': lambda x: 1 - x.mean(),  # Invert: higher is better
        'price_match': 'mean',
        'faithfulness_score': 'mean'
    }).reset_index()

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Left: Component breakdown
    ax1 = axes[0]
    models = faith_data['model']
    x = np.arange(len(models))
    width = 0.25

    ax1.bar(x - width, faith_data['has_citation'], width, label='Has Citation', color='#3498db')
    ax1.bar(x, faith_data['has_hallucination'], width, label='No Hallucination', color='#2ecc71')
    ax1.bar(x + width, faith_data['price_match'], width, label='Price Match', color='#9b59b6')

    ax1.set_xlabel('Model')
    ax1.set_ylabel('Score (0-1)')
    ax1.set_title('Faithfulness Components')
    ax1.set_xticks(x)
    ax1.set_xticklabels(models)
    ax1.legend()
    ax1.set_ylim(0, 1.1)

    # Right: Overall faithfulness
    ax2 = axes[1]
    colors = ['#3498db', '#e74c3c', '#2ecc71'][:len(models)]
    bars = ax2.bar(models, faith_data['faithfulness_score'], color=colors, alpha=0.8)

    ax2.set_xlabel('Model')
    ax2.set_ylabel('Faithfulness Score')
    ax2.set_title('Overall Faithfulness Score')
    ax2.set_ylim(0, 1.1)

    # Add value labels
    for bar, val in zip(bars, faith_data['faithfulness_score']):
        ax2.annotate(f'{val:.2f}',
                    xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    xytext=(0, 5), textcoords='offset points',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'faithfulness_comparison.png'), dpi=150)
    plt.close()
    print(f"  Generated: faithfulness_comparison.png")


def plot_relevance_comparison(df: pd.DataFrame, output_dir: str):
    """Generate relevance metrics comparison"""
    # Calculate relevance components
    relev_data = df.groupby('model').agg({
        'category_match': 'mean',
        'price_filter_ok': 'mean',
        'judge_score': 'mean',
        'relevance_score': 'mean'
    }).reset_index()

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Left: Component breakdown
    ax1 = axes[0]
    models = relev_data['model']
    x = np.arange(len(models))
    width = 0.25

    ax1.bar(x - width, relev_data['category_match'], width, label='Category Match', color='#e74c3c')
    ax1.bar(x, relev_data['price_filter_ok'], width, label='Price Filter OK', color='#f39c12')

    # Normalize judge_score from 1-5 to 0-1
    if not relev_data['judge_score'].isna().all():
        judge_norm = (relev_data['judge_score'] - 1) / 4
        ax1.bar(x + width, judge_norm, width, label='LLM Judge (norm)', color='#1abc9c')

    ax1.set_xlabel('Model')
    ax1.set_ylabel('Score (0-1)')
    ax1.set_title('Relevance Components')
    ax1.set_xticks(x)
    ax1.set_xticklabels(models)
    ax1.legend()
    ax1.set_ylim(0, 1.1)

    # Right: Overall relevance
    ax2 = axes[1]
    colors = ['#3498db', '#e74c3c', '#2ecc71'][:len(models)]
    bars = ax2.bar(models, relev_data['relevance_score'], color=colors, alpha=0.8)

    ax2.set_xlabel('Model')
    ax2.set_ylabel('Relevance Score')
    ax2.set_title('Overall Relevance Score')
    ax2.set_ylim(0, 1.1)

    for bar, val in zip(bars, relev_data['relevance_score']):
        ax2.annotate(f'{val:.2f}',
                    xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    xytext=(0, 5), textcoords='offset points',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'relevance_comparison.png'), dpi=150)
    plt.close()
    print(f"  Generated: relevance_comparison.png")


def plot_radar_chart(df: pd.DataFrame, output_dir: str):
    """Generate radar chart for overall comparison"""
    # Prepare data
    metrics = df.groupby('model').agg({
        'latency_ms': lambda x: 1 - min(x.mean() / 30000, 1),  # Normalize & invert
        'faithfulness_score': 'mean',
        'relevance_score': 'mean',
        'has_citation': 'mean',
        'num_products': lambda x: min(x.mean() / 5, 1)  # Normalize
    }).reset_index()

    categories = ['Speed', 'Faithfulness', 'Relevance', 'Citations', 'Products']
    models = metrics['model'].tolist()

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]  # Complete the loop

    colors = ['#3498db', '#e74c3c', '#2ecc71', '#9b59b6', '#f39c12']

    for i, model in enumerate(models):
        values = [
            metrics.loc[metrics['model'] == model, 'latency_ms'].values[0],
            metrics.loc[metrics['model'] == model, 'faithfulness_score'].values[0],
            metrics.loc[metrics['model'] == model, 'relevance_score'].values[0],
            metrics.loc[metrics['model'] == model, 'has_citation'].values[0],
            metrics.loc[metrics['model'] == model, 'num_products'].values[0]
        ]
        values += values[:1]

        ax.plot(angles, values, 'o-', linewidth=2, label=model, color=colors[i % len(colors)])
        ax.fill(angles, values, alpha=0.15, color=colors[i % len(colors)])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=11)
    ax.set_ylim(0, 1)
    ax.set_title('Model Comparison Radar Chart', fontsize=14, fontweight='bold', y=1.08)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'overall_radar.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Generated: overall_radar.png")


def plot_query_type_breakdown(df: pd.DataFrame, output_dir: str):
    """Generate breakdown by query type"""
    # Group by model and query_type
    breakdown = df.groupby(['model', 'query_type'])['overall_score'].mean().unstack(fill_value=0)

    fig, ax = plt.subplots(figsize=(12, 6))

    breakdown.plot(kind='bar', ax=ax, width=0.8, alpha=0.8)

    ax.set_xlabel('Model', fontsize=12)
    ax.set_ylabel('Overall Score', fontsize=12)
    ax.set_title('Performance by Query Type', fontsize=14, fontweight='bold')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    ax.legend(title='Query Type')
    ax.set_ylim(0, 1.1)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'query_type_breakdown.png'), dpi=150)
    plt.close()
    print(f"  Generated: query_type_breakdown.png")


def plot_dataset_comparison(df: pd.DataFrame, output_dir: str):
    """Generate comparison across datasets"""
    if 'dataset' not in df.columns or df['dataset'].nunique() <= 1:
        print("  Skipped: dataset_comparison.png (single dataset)")
        return

    # Group by model and dataset
    ds_data = df.groupby(['model', 'dataset'])['overall_score'].mean().unstack(fill_value=0)

    fig, ax = plt.subplots(figsize=(12, 6))

    ds_data.plot(kind='bar', ax=ax, width=0.8, alpha=0.8)

    ax.set_xlabel('Model', fontsize=12)
    ax.set_ylabel('Overall Score', fontsize=12)
    ax.set_title('Performance Across Datasets', fontsize=14, fontweight='bold')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    ax.legend(title='Dataset')
    ax.set_ylim(0, 1.1)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'dataset_comparison.png'), dpi=150)
    plt.close()
    print(f"  Generated: dataset_comparison.png")


def generate_summary_table(df: pd.DataFrame, output_dir: str):
    """Generate summary table as image"""
    summary = df.groupby('model').agg({
        'latency_ms': ['mean', 'std'],
        'faithfulness_score': 'mean',
        'relevance_score': 'mean',
        'overall_score': 'mean',
        'query_id': 'count'
    }).round(3)

    summary.columns = ['Latency (mean)', 'Latency (std)', 'Faithfulness', 'Relevance', 'Overall', 'N']

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.axis('off')

    table = ax.table(
        cellText=summary.values,
        colLabels=summary.columns,
        rowLabels=summary.index,
        cellLoc='center',
        loc='center'
    )

    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1.2, 1.8)

    # Style header
    for key, cell in table.get_celld().items():
        if key[0] == 0:
            cell.set_text_props(fontweight='bold')
            cell.set_facecolor('#3498db')
            cell.set_text_props(color='white')
        elif key[1] == -1:
            cell.set_text_props(fontweight='bold')
            cell.set_facecolor('#ecf0f1')

    plt.title('Model Evaluation Summary', fontsize=14, fontweight='bold', y=0.95)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'summary_table.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Generated: summary_table.png")


def main():
    parser = argparse.ArgumentParser(description='Generate evaluation charts')
    parser.add_argument('--input', '-i', required=True, help='Input CSV file')
    parser.add_argument('--output', '-o', default='results/charts/', help='Output directory')

    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    print(f"\nLoading results from {args.input}...")
    df = load_results(args.input)
    print(f"  Loaded {len(df)} records for {df['model'].nunique()} models")

    print(f"\nGenerating charts in {args.output}...")

    plot_latency_comparison(df, args.output)
    plot_faithfulness_comparison(df, args.output)
    plot_relevance_comparison(df, args.output)
    plot_radar_chart(df, args.output)
    plot_query_type_breakdown(df, args.output)
    plot_dataset_comparison(df, args.output)
    generate_summary_table(df, args.output)

    print(f"\nDone! Charts saved to {args.output}")


if __name__ == '__main__':
    main()
