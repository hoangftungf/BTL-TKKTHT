"""
Model Evaluation Pipeline
=========================
Evaluates multiple LLM models on the AI chatbot system.

Usage:
    # With OpenAI Judge (requires API key)
    python scripts/evaluation/evaluate_models.py \
        --models llama3:8b,qwen2.5:7b,gemma2:9b \
        --datasets synthetic_large \
        --output results/evaluation_results.csv \
        --openai-key $OPENAI_API_KEY

    # With Local LLM Judge (FREE - uses gemma2:9b via Ollama)
    python scripts/evaluation/evaluate_models.py \
        --models gemma2:9b \
        --datasets synthetic_large \
        --output results/evaluation_with_judge.csv \
        --local-judge

Metrics:
    - Latency: Cold-start, warm (cached), P95
    - Faithfulness: Citation presence, no hallucination, price match
    - Relevance: Category match, price filter, LLM-Judge score
"""

import argparse
import asyncio
import csv
import json
import logging
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple

import httpx

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
CHATBOT_URL = os.getenv('CHATBOT_URL', 'http://localhost:8012')
CHAT_ENDPOINT = f'{CHATBOT_URL}/api/chatbot/chat/'
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')


@dataclass
class TestQuery:
    """Single test query for evaluation"""
    id: str
    query: str
    expected_category: Optional[str]
    expected_price_max: Optional[int]
    expected_price_min: Optional[int]
    expected_brand: Optional[str]
    query_type: str  # 'product_search', 'semantic', 'edge_case'


@dataclass
class EvaluationResult:
    """Result of evaluating a single query"""
    query_id: str
    model: str
    dataset: str
    query_text: str
    query_type: str

    # Latency metrics
    latency_ms: float
    is_cached: bool

    # Response data
    response_text: str
    intent: str
    num_products: int
    product_ids: List[str]

    # Faithfulness metrics
    has_citation: bool
    citation_count: int
    has_hallucination: bool
    price_match: bool

    # Relevance metrics
    category_match: bool
    price_filter_ok: bool
    judge_score: Optional[float]  # 1-5 from LLM judge

    # Computed scores
    faithfulness_score: float
    relevance_score: float
    overall_score: float

    timestamp: str


class LLMJudge:
    """Uses GPT-4o-mini to evaluate response quality"""

    JUDGE_PROMPT = """You are evaluating an AI chatbot's response for an e-commerce product search query.

Query: {query}
Response: {response}
Products returned: {products}

Evaluate the response on these criteria (1-5 scale each):

1. RELEVANCE (1-5): Does the response address the user's query? Are the products relevant?
   - 5: Perfectly relevant, all products match the query
   - 3: Partially relevant, some products match
   - 1: Completely irrelevant

2. HELPFULNESS (1-5): Is the response helpful for the user's shopping decision?
   - 5: Very helpful, provides clear recommendations with reasons
   - 3: Somewhat helpful, lists products but no guidance
   - 1: Not helpful at all

3. ACCURACY (1-5): Is the information accurate? No made-up products or prices?
   - 5: All information is accurate and verifiable from the products list
   - 3: Some minor inaccuracies
   - 1: Contains fabricated information

Respond in JSON format only:
{{"relevance": <1-5>, "helpfulness": <1-5>, "accuracy": <1-5>, "reasoning": "<brief explanation>"}}
"""

    def __init__(self, api_key: str, model: str = 'gpt-4o-mini'):
        self.api_key = api_key
        self.model = model
        self.client = None

    async def judge(self, query: str, response: str, products: List[Dict]) -> Tuple[float, str]:
        """
        Judge a response using GPT-4o-mini.
        Returns: (average_score, reasoning)
        """
        if not self.api_key:
            logger.warning("No OpenAI API key - skipping LLM judge")
            return None, "No API key"

        products_summary = "\n".join([
            f"- {p.get('data', {}).get('name', 'Unknown')} ({p.get('data', {}).get('price', 'N/A')}d)"
            for p in products[:5]
        ]) if products else "No products returned"

        prompt = self.JUDGE_PROMPT.format(
            query=query,
            response=response[:500],  # Truncate long responses
            products=products_summary
        )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers={
                        'Authorization': f'Bearer {self.api_key}',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'model': self.model,
                        'messages': [{'role': 'user', 'content': prompt}],
                        'temperature': 0.1,
                        'max_tokens': 200
                    }
                )

                if resp.status_code != 200:
                    logger.warning(f"Judge API error: {resp.status_code}")
                    return None, f"API error: {resp.status_code}"

                result = resp.json()
                content = result['choices'][0]['message']['content']

                # Parse JSON response
                json_match = re.search(r'\{[^}]+\}', content)
                if json_match:
                    scores = json.loads(json_match.group())
                    avg_score = (
                        scores.get('relevance', 3) +
                        scores.get('helpfulness', 3) +
                        scores.get('accuracy', 3)
                    ) / 3
                    return avg_score, scores.get('reasoning', '')

        except Exception as e:
            logger.warning(f"Judge error: {e}")

        return None, "Judge failed"


class LocalLLMJudge:
    """Uses local Ollama model (gemma2:9b) to evaluate response quality - NO API costs!"""

    JUDGE_PROMPT = """You are evaluating an AI chatbot's response for an e-commerce product search query.

Query: {query}
Response: {response}
Products returned: {products}

Evaluate the response on these criteria (1-5 scale each):

1. RELEVANCE (1-5): Does the response address the user's query? Are the products relevant?
   - 5: Perfectly relevant, all products match the query
   - 3: Partially relevant, some products match
   - 1: Completely irrelevant

2. HELPFULNESS (1-5): Is the response helpful for the user's shopping decision?
   - 5: Very helpful, provides clear recommendations with reasons
   - 3: Somewhat helpful, lists products but no guidance
   - 1: Not helpful at all

3. ACCURACY (1-5): Is the information accurate? No made-up products or prices?
   - 5: All information is accurate and verifiable from the products list
   - 3: Some minor inaccuracies
   - 1: Contains fabricated information

Respond in JSON format only:
{{"relevance": <1-5>, "helpfulness": <1-5>, "accuracy": <1-5>, "reasoning": "<brief explanation>"}}
"""

    def __init__(self, model: str = 'qwen2.5:7b', ollama_host: str = None):
        self.model = model
        self.ollama_host = ollama_host or OLLAMA_HOST
        logger.info(f"LocalLLMJudge initialized with model: {model}")

    async def judge(self, query: str, response: str, products: List[Dict]) -> Tuple[float, str]:
        """
        Judge a response using local Ollama model.
        Returns: (average_score, reasoning)
        """
        products_summary = "\n".join([
            f"- {p.get('data', {}).get('name', 'Unknown')} ({p.get('data', {}).get('price', 'N/A')}d)"
            for p in products[:5]
        ]) if products else "No products returned"

        prompt = self.JUDGE_PROMPT.format(
            query=query,
            response=response[:500],
            products=products_summary
        )

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f'{self.ollama_host}/api/generate',
                    json={
                        'model': self.model,
                        'prompt': prompt,
                        'stream': False,
                        'options': {
                            'temperature': 0.1,
                            'num_predict': 300
                        }
                    }
                )

                if resp.status_code != 200:
                    logger.warning(f"Local Judge error: {resp.status_code}")
                    return None, f"Ollama error: {resp.status_code}"

                result = resp.json()
                content = result.get('response', '')

                # Parse JSON response
                json_match = re.search(r'\{[^}]+\}', content)
                if json_match:
                    scores = json.loads(json_match.group())
                    avg_score = (
                        scores.get('relevance', 3) +
                        scores.get('helpfulness', 3) +
                        scores.get('accuracy', 3)
                    ) / 3
                    return avg_score, scores.get('reasoning', '')
                else:
                    logger.warning(f"Could not parse judge response: {content[:100]}")

        except Exception as e:
            logger.warning(f"Local Judge error: {e}")

        return None, "Local Judge failed"


class ModelEvaluator:
    """Main evaluation pipeline"""

    def __init__(
        self,
        models: List[str],
        judge: Optional[LLMJudge] = None
    ):
        self.models = models
        self.judge = judge
        self.results: List[EvaluationResult] = []

    async def switch_model(self, model: str) -> bool:
        """Switch Ollama to use a different model"""
        logger.info(f"Switching to model: {model}")

        # Unload current model
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Generate with empty prompt to load model
                await client.post(
                    f'{OLLAMA_HOST}/api/generate',
                    json={'model': model, 'prompt': 'Hello', 'stream': False}
                )
            logger.info(f"Model {model} loaded")
            return True
        except Exception as e:
            logger.error(f"Failed to load model {model}: {e}")
            return False

    async def run_query(
        self,
        query: TestQuery,
        model: str,
        dataset: str,
        is_warmup: bool = False
    ) -> Optional[EvaluationResult]:
        """Execute a single query and measure metrics"""

        start_time = time.perf_counter()

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    CHAT_ENDPOINT,
                    json={'message': query.query, 'session_id': f'eval-{query.id}'},
                    headers={'X-Trace-Id': f'eval-{model}-{query.id}'}
                )

            latency_ms = (time.perf_counter() - start_time) * 1000

            if resp.status_code != 200:
                logger.warning(f"Query failed: {resp.status_code}")
                return None

            body = resp.json()
            response_text = body.get('response', '')
            intent = body.get('intent', '')
            products = body.get('products') or []

            # Extract metrics
            citations = re.findall(r'\[ID:\s*[^\]]+\]', response_text)
            has_citation = len(citations) > 0

            # Check for hallucination (product mentioned but no citation)
            has_hallucination = self._check_hallucination(response_text, products)

            # Check price match
            price_match = self._check_price_match(response_text, products)

            # Check category match
            category_match = self._check_category_match(products, query.expected_category)

            # Check price filter
            price_filter_ok = self._check_price_filter(products, query.expected_price_max, query.expected_price_min)

            # LLM Judge score
            judge_score = None
            judge_reason = ''
            if self.judge and not is_warmup:
                judge_score, judge_reason = await self.judge.judge(query.query, response_text, products)

            # Compute composite scores
            faithfulness = self._compute_faithfulness(has_citation, not has_hallucination, price_match)
            relevance = self._compute_relevance(category_match, price_filter_ok, judge_score)

            overall = 0.3 * (1 - min(latency_ms / 30000, 1)) + 0.3 * faithfulness + 0.4 * relevance

            return EvaluationResult(
                query_id=query.id,
                model=model,
                dataset=dataset,
                query_text=query.query,
                query_type=query.query_type,
                latency_ms=latency_ms,
                is_cached=is_warmup,
                response_text=response_text[:500],
                intent=intent,
                num_products=len(products),
                product_ids=[p.get('product_id', '') for p in products[:5]],
                has_citation=has_citation,
                citation_count=len(citations),
                has_hallucination=has_hallucination,
                price_match=price_match,
                category_match=category_match,
                price_filter_ok=price_filter_ok,
                judge_score=judge_score,
                faithfulness_score=faithfulness,
                relevance_score=relevance,
                overall_score=overall,
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            logger.error(f"Error running query {query.id}: {e}")
            return None

    def _check_hallucination(self, response: str, products: List[Dict]) -> bool:
        """Check if response mentions products not in the list"""
        # Simple heuristic: if response mentions specific product names not in list
        product_names = [p.get('data', {}).get('name', '').lower() for p in products]

        # Look for "iPhone", "Samsung Galaxy", etc. mentions
        brand_patterns = [
            r'iphone \d+', r'samsung galaxy', r'macbook', r'dell xps',
            r'nike air', r'adidas'
        ]

        for pattern in brand_patterns:
            matches = re.findall(pattern, response.lower())
            for match in matches:
                if not any(match in name for name in product_names):
                    return True

        return False

    def _check_price_match(self, response: str, products: List[Dict]) -> bool:
        """Check if prices in response match products"""
        # Extract prices from response
        price_mentions = re.findall(r'([\d,.]+)\s*(?:d|dong|trieu|tr)', response.lower())
        if not price_mentions or not products:
            return True  # No prices to verify

        product_prices = [p.get('data', {}).get('price') for p in products if p.get('data', {}).get('price')]

        # At least one price should roughly match
        for mention in price_mentions[:3]:
            try:
                mentioned_price = float(mention.replace(',', '').replace('.', ''))
                # Handle "trieu" multiplier
                if mentioned_price < 1000:
                    mentioned_price *= 1_000_000

                for pp in product_prices:
                    if abs(float(pp) - mentioned_price) / float(pp) < 0.1:  # 10% tolerance
                        return True
            except:
                continue

        return False

    def _check_category_match(self, products: List[Dict], expected_category: Optional[str]) -> bool:
        """Check if products match expected category"""
        if not expected_category or not products:
            return True

        expected_lower = expected_category.lower()
        for p in products:
            cat = p.get('data', {}).get('category', '').lower()
            if expected_lower in cat or cat in expected_lower:
                return True

        return False

    def _check_price_filter(
        self,
        products: List[Dict],
        max_price: Optional[int],
        min_price: Optional[int]
    ) -> bool:
        """Check if all products are within price range"""
        if not products:
            return True

        for p in products:
            price = p.get('data', {}).get('price')
            if price is None:
                continue

            try:
                price = float(price)
                if max_price and price > max_price:
                    return False
                if min_price and price < min_price:
                    return False
            except:
                continue

        return True

    def _compute_faithfulness(self, has_citation: bool, no_hallucination: bool, price_match: bool) -> float:
        """Compute faithfulness score (0-1)"""
        score = 0.0
        if has_citation:
            score += 0.4
        if no_hallucination:
            score += 0.4
        if price_match:
            score += 0.2
        return score

    def _compute_relevance(
        self,
        category_match: bool,
        price_filter_ok: bool,
        judge_score: Optional[float]
    ) -> float:
        """Compute relevance score (0-1)"""
        base_score = 0.0
        if category_match:
            base_score += 0.3
        if price_filter_ok:
            base_score += 0.3

        if judge_score is not None:
            # Normalize judge score from 1-5 to 0-0.4
            judge_normalized = (judge_score - 1) / 4 * 0.4
            base_score += judge_normalized
        else:
            base_score += 0.2  # Default if no judge

        return min(base_score, 1.0)

    async def evaluate_model(
        self,
        model: str,
        queries: List[TestQuery],
        dataset: str
    ) -> List[EvaluationResult]:
        """Evaluate a single model on all queries"""
        logger.info(f"\n{'='*60}")
        logger.info(f"Evaluating: {model} on {dataset}")
        logger.info(f"{'='*60}")

        # Switch model
        if not await self.switch_model(model):
            return []

        # Warmup query
        logger.info("Running warmup query...")
        warmup = TestQuery(
            id='warmup',
            query='xin chao',
            expected_category=None,
            expected_price_max=None,
            expected_price_min=None,
            expected_brand=None,
            query_type='warmup'
        )
        await self.run_query(warmup, model, dataset, is_warmup=True)
        await asyncio.sleep(2)

        # Run all queries
        results = []
        for i, query in enumerate(queries):
            logger.info(f"  Query {i+1}/{len(queries)}: {query.query[:50]}...")
            result = await self.run_query(query, model, dataset)
            if result:
                results.append(result)
                self.results.append(result)

            # Small delay between queries
            await asyncio.sleep(1)

        return results

    async def run_evaluation(
        self,
        queries: List[TestQuery],
        datasets: List[str]
    ):
        """Run full evaluation across all models and datasets"""
        for model in self.models:
            for dataset in datasets:
                await self.evaluate_model(model, queries, dataset)

                # Clear cache between models
                logger.info("Clearing cache...")
                await asyncio.sleep(5)

    def save_results(self, filepath: str):
        """Save results to CSV"""
        if not self.results:
            logger.warning("No results to save")
            return

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        fieldnames = [
            'query_id', 'model', 'dataset', 'query_text', 'query_type',
            'latency_ms', 'is_cached', 'intent', 'num_products',
            'has_citation', 'citation_count', 'has_hallucination', 'price_match',
            'category_match', 'price_filter_ok', 'judge_score',
            'faithfulness_score', 'relevance_score', 'overall_score', 'timestamp'
        ]

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for r in self.results:
                row = asdict(r)
                # Remove large text fields for CSV
                del row['response_text']
                del row['product_ids']
                writer.writerow(row)

        logger.info(f"Saved {len(self.results)} results to {filepath}")

        # Also save full results as JSON
        json_path = filepath.replace('.csv', '.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump([asdict(r) for r in self.results], f, ensure_ascii=False, indent=2)

        logger.info(f"Saved full results to {json_path}")

    def print_summary(self):
        """Print evaluation summary"""
        if not self.results:
            return

        print(f"\n{'='*70}")
        print("EVALUATION SUMMARY")
        print(f"{'='*70}")

        # Group by model
        by_model: Dict[str, List[EvaluationResult]] = {}
        for r in self.results:
            by_model.setdefault(r.model, []).append(r)

        print(f"\n{'Model':<20} {'Latency(ms)':<12} {'Faith':<8} {'Relev':<8} {'Overall':<8} {'N':<5}")
        print("-" * 70)

        for model, results in by_model.items():
            avg_latency = sum(r.latency_ms for r in results) / len(results)
            avg_faith = sum(r.faithfulness_score for r in results) / len(results)
            avg_relev = sum(r.relevance_score for r in results) / len(results)
            avg_overall = sum(r.overall_score for r in results) / len(results)

            print(f"{model:<20} {avg_latency:>10.0f}ms {avg_faith:>7.2f} {avg_relev:>7.2f} {avg_overall:>7.2f} {len(results):>4}")

        print("-" * 70)

        # Best model
        model_scores = {
            m: sum(r.overall_score for r in rs) / len(rs)
            for m, rs in by_model.items()
        }
        best_model = max(model_scores, key=model_scores.get)
        print(f"\nBest Model: {best_model} (score: {model_scores[best_model]:.3f})")


def load_test_queries(filepath: Optional[str] = None) -> List[TestQuery]:
    """Load or generate test queries"""
    if filepath and os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return [TestQuery(**q) for q in data['queries']]

    # Default test queries
    return [
        TestQuery('q1', 'Tu van laptop Dell gia duoi 30 trieu', 'laptop', 30000000, None, 'dell', 'product_search'),
        TestQuery('q2', 'Tim dien thoai Samsung gia 15 trieu', 'smartphone', 15000000, None, 'samsung', 'product_search'),
        TestQuery('q3', 'Giay Nike nam size 42 mau trang', 'men_shoes', None, None, 'nike', 'product_search'),
        TestQuery('q4', 'Son moi mau do gia duoi 500k', 'lipstick', 500000, None, None, 'product_search'),
        TestQuery('q5', 'Noi chien khong dau tot nhat', 'kitchen', None, None, None, 'semantic'),
        TestQuery('q6', 'San pham phu hop cho dan van phong', None, None, None, None, 'semantic'),
        TestQuery('q7', 'Ao thun nam basic mau den', 'men_shirts', None, None, None, 'product_search'),
        TestQuery('q8', 'Dam du tiec sang trong', 'dresses', None, None, None, 'semantic'),
        TestQuery('q9', 'Tim iPhone 25 Pro Max', None, None, None, None, 'edge_case'),
        TestQuery('q10', 'Serum vitamin C duong da gia duoi 1 trieu', 'skincare', 1000000, None, None, 'product_search'),
    ]


async def main():
    parser = argparse.ArgumentParser(description='Evaluate AI chatbot models')
    parser.add_argument('--models', '-m', default='llama3:8b,qwen2.5:7b,gemma2:9b',
                        help='Comma-separated model names')
    parser.add_argument('--datasets', '-d', default='default',
                        help='Comma-separated dataset names')
    parser.add_argument('--queries', '-q', type=str, default=None,
                        help='Test queries JSON file')
    parser.add_argument('--output', '-o', default='results/evaluation_results.csv',
                        help='Output CSV file')
    parser.add_argument('--judge-model', default='gpt-4o-mini',
                        help='OpenAI model for LLM judge')
    parser.add_argument('--openai-key', default=None,
                        help='OpenAI API key (or set OPENAI_API_KEY env)')
    parser.add_argument('--local-judge', action='store_true',
                        help='Use local Ollama model (gemma2:9b) as judge instead of OpenAI')
    parser.add_argument('--local-judge-model', default='qwen2.5:7b',
                        help='Local Ollama model for judging (default: qwen2.5:7b)')

    args = parser.parse_args()

    models = args.models.split(',')
    datasets = args.datasets.split(',')
    openai_key = args.openai_key or os.getenv('OPENAI_API_KEY')

    # Initialize judge
    judge = None
    if args.local_judge:
        judge = LocalLLMJudge(model=args.local_judge_model)
        logger.info(f"Using LOCAL LLM Judge with model: {args.local_judge_model}")
    elif openai_key:
        judge = LLMJudge(openai_key, args.judge_model)
        logger.info(f"Using OpenAI LLM Judge with model: {args.judge_model}")
    else:
        logger.warning("No judge configured - LLM judge disabled (use --local-judge or --openai-key)")

    # Load queries
    queries = load_test_queries(args.queries)
    logger.info(f"Loaded {len(queries)} test queries")

    # Initialize evaluator
    evaluator = ModelEvaluator(models, judge)

    # Run evaluation
    await evaluator.run_evaluation(queries, datasets)

    # Save and summarize
    evaluator.save_results(args.output)
    evaluator.print_summary()


if __name__ == '__main__':
    asyncio.run(main())
