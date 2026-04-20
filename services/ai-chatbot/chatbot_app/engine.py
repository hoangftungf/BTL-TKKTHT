"""
AI Chatbot Engine with Ollama LLM Integration and RAG Support
"""

import re
import json
import logging
import httpx
import numpy as np
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


# ===================== RAG COMPONENTS =====================

class ProductVectorStore:
    """
    Vector Store for product embeddings using FAISS
    """

    def __init__(self):
        self.index = None
        self.product_ids = []
        self.product_data = {}
        self.embedding_dim = 384
        self._initialized = False

    def _initialize(self):
        """Initialize FAISS index"""
        if self._initialized:
            return

        try:
            import faiss
            self.index = faiss.IndexFlatIP(self.embedding_dim)
            self._initialized = True
            logger.info("FAISS index initialized for chatbot")
        except ImportError:
            logger.warning("FAISS not available, using simple similarity")
            self._embeddings = []
            self._initialized = True

    def add(self, product_id, embedding, product_data=None):
        """Add product to vector store"""
        self._initialize()

        embedding = np.array(embedding).astype('float32')
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        if len(embedding.shape) == 1:
            embedding = embedding.reshape(1, -1)

        if self.index is not None:
            self.index.add(embedding)
        else:
            self._embeddings.append(embedding[0])

        self.product_ids.append(str(product_id))
        if product_data:
            self.product_data[str(product_id)] = product_data

    def search(self, query_embedding, k=5):
        """Search for similar products"""
        self._initialize()

        if len(self.product_ids) == 0:
            return []

        query_embedding = np.array(query_embedding).astype('float32')
        norm = np.linalg.norm(query_embedding)
        if norm > 0:
            query_embedding = query_embedding / norm

        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)

        if self.index is not None:
            import faiss
            distances, indices = self.index.search(query_embedding, min(k, len(self.product_ids)))
            results = []
            for i, idx in enumerate(indices[0]):
                if idx >= 0 and idx < len(self.product_ids):
                    product_id = self.product_ids[idx]
                    results.append({
                        'product_id': product_id,
                        'score': float(distances[0][i]),
                        'data': self.product_data.get(product_id, {})
                    })
            return results
        else:
            if not hasattr(self, '_embeddings') or len(self._embeddings) == 0:
                return []
            embeddings = np.array(self._embeddings)
            scores = np.dot(embeddings, query_embedding.T).flatten()
            top_indices = np.argsort(scores)[::-1][:k]
            results = []
            for idx in top_indices:
                product_id = self.product_ids[idx]
                results.append({
                    'product_id': product_id,
                    'score': float(scores[idx]),
                    'data': self.product_data.get(product_id, {})
                })
            return results


class TextEmbedder:
    """Generate text embeddings"""

    def __init__(self, ollama_host):
        self.ollama_host = ollama_host
        self._tfidf = None

    def embed(self, texts):
        """Generate embeddings for texts"""
        if isinstance(texts, str):
            texts = [texts]

        # Try Ollama embeddings
        try:
            embeddings = []
            for text in texts:
                response = httpx.post(
                    f"{self.ollama_host}/api/embeddings",
                    json={"model": "nomic-embed-text", "prompt": text},
                    timeout=10.0
                )
                if response.status_code == 200:
                    embedding = response.json().get('embedding', [])
                    embeddings.append(embedding)
                else:
                    embeddings.append([0.0] * 384)
            return np.array(embeddings)
        except Exception as e:
            logger.warning(f"Ollama embedding failed: {e}, using TF-IDF")

        # Fallback to TF-IDF
        from sklearn.feature_extraction.text import TfidfVectorizer
        if self._tfidf is None:
            self._tfidf = TfidfVectorizer(max_features=384)
        try:
            if hasattr(self._tfidf, 'vocabulary_') and self._tfidf.vocabulary_:
                return self._tfidf.transform(texts).toarray()
            else:
                return self._tfidf.fit_transform(texts).toarray()
        except:
            return np.zeros((len(texts), 384))


class RAGPipeline:
    """
    RAG Pipeline for product-aware responses
    """

    def __init__(self, ollama_host, ollama_model):
        self.ollama_host = ollama_host
        self.ollama_model = ollama_model
        self.embedder = TextEmbedder(ollama_host)
        self.vector_store = ProductVectorStore()
        self._indexed = False

    def index_products(self):
        """Index products from product service"""
        if self._indexed:
            return

        product_service_url = getattr(settings, 'PRODUCT_SERVICE_URL', 'http://product-service:8000/api/products')

        try:
            response = httpx.get(f"{product_service_url}?page_size=500", timeout=30.0)
            if response.status_code == 200:
                products = response.json().get('results', [])

                texts = []
                for p in products:
                    text = f"{p.get('name', '')} {p.get('description', '')} {p.get('brand', '')}"
                    if p.get('category'):
                        if isinstance(p['category'], dict):
                            text += f" {p['category'].get('name', '')}"
                    texts.append(text)

                if texts:
                    embeddings = self.embedder.embed(texts)
                    for i, (p, emb) in enumerate(zip(products, embeddings)):
                        self.vector_store.add(
                            product_id=p['id'],
                            embedding=emb,
                            product_data={
                                'name': p.get('name', ''),
                                'price': p.get('price'),
                                'category': p.get('category', {}).get('name') if isinstance(p.get('category'), dict) else '',
                                'brand': p.get('brand', '')
                            }
                        )

                self._indexed = True
                logger.info(f"Indexed {len(products)} products for RAG")
        except Exception as e:
            logger.error(f"Failed to index products: {e}")

    def retrieve(self, query, k=5):
        """Retrieve relevant products"""
        self.index_products()

        cache_key = f"rag_chatbot:{hash(query)}:{k}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        query_embedding = self.embedder.embed([query])[0]
        results = self.vector_store.search(query_embedding, k=k)

        cache.set(cache_key, results, timeout=300)
        return results

    def generate_augmented_response(self, query, context_products):
        """Generate response with product context"""
        context = self._build_context(context_products)

        prompt = f"""Bạn là trợ lý AI của cửa hàng thương mại điện tử. Dựa trên thông tin sản phẩm dưới đây, hãy trả lời câu hỏi của khách hàng.

Sản phẩm liên quan:
{context}

Câu hỏi: {query}

Trả lời ngắn gọn, thân thiện, gợi ý sản phẩm phù hợp nếu có:"""

        try:
            response = httpx.post(
                f"{self.ollama_host}/api/generate",
                json={"model": self.ollama_model, "prompt": prompt, "stream": False},
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json().get('response', '')
        except Exception as e:
            logger.error(f"RAG generation error: {e}")

        return self._fallback_response(context_products)

    def _build_context(self, products):
        lines = []
        for i, p in enumerate(products[:5], 1):
            data = p.get('data', {})
            line = f"{i}. {data.get('name', 'Unknown')}"
            if data.get('price'):
                line += f" - {data['price']:,.0f}đ"
            if data.get('category'):
                line += f" ({data['category']})"
            lines.append(line)
        return '\n'.join(lines)

    def _fallback_response(self, products):
        if not products:
            return "Xin lỗi, tôi không tìm thấy sản phẩm phù hợp."
        response = "Gợi ý cho bạn:\n"
        for i, p in enumerate(products[:3], 1):
            data = p.get('data', {})
            response += f"{i}. {data.get('name', 'Unknown')}"
            if data.get('price'):
                response += f" - {data['price']:,.0f}đ"
            response += "\n"
        return response


class IntentClassifier:
    """Phân loại ý định người dùng"""

    INTENT_PATTERNS = {
        'greeting': [
            r'\b(xin chào|chào|hi|hello|hey)\b',
            r'^(chào|hi|hello)',
        ],
        'product_search': [
            r'\b(tìm|tìm kiếm|search|kiếm|mua)\b.*\b(sản phẩm|hàng|đồ)\b',
            r'\b(có|bán)\b.*\b(không|gì)\b',
            r'\b(giá|bao nhiêu)\b',
        ],
        'order_status': [
            r'\b(đơn hàng|order|đơn)\b.*\b(đâu|sao|thế nào|status)\b',
            r'\b(theo dõi|tracking|giao hàng)\b',
            r'\b(khi nào|bao giờ)\b.*\b(nhận|giao)\b',
        ],
        'return_policy': [
            r'\b(đổi|trả|hoàn)\b.*\b(hàng|tiền|sản phẩm)\b',
            r'\b(chính sách|policy)\b.*\b(đổi|trả)\b',
        ],
        'payment': [
            r'\b(thanh toán|payment|trả tiền)\b',
            r'\b(COD|momo|vnpay|thẻ)\b',
        ],
        'shipping': [
            r'\b(ship|giao hàng|vận chuyển|delivery)\b',
            r'\b(phí ship|phí giao|shipping fee)\b',
        ],
        'support': [
            r'\b(hỗ trợ|support|giúp|help)\b',
            r'\b(liên hệ|contact|hotline)\b',
        ],
        'goodbye': [
            r'\b(tạm biệt|bye|goodbye|cảm ơn|thank)\b',
        ],
    }

    @classmethod
    def classify(cls, text):
        """Phân loại intent từ text"""
        text_lower = text.lower()

        for intent, patterns in cls.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return intent

        return 'general'


class ChatbotEngine:
    """
    AI Chatbot Engine với:
    1. Intent Classification
    2. FAQ Matching
    3. RAG (Retrieval-Augmented Generation)
    4. LLM Response Generation (Ollama)
    5. Context Management
    """

    SYSTEM_PROMPT = """Bạn là trợ lý AI của cửa hàng thương mại điện tử.
Nhiệm vụ của bạn là hỗ trợ khách hàng với:
- Tìm kiếm và tư vấn sản phẩm
- Theo dõi đơn hàng
- Giải đáp thắc mắc về chính sách
- Hỗ trợ thanh toán và giao hàng

Hãy trả lời ngắn gọn, thân thiện và hữu ích bằng tiếng Việt.
Khi tư vấn sản phẩm, hãy đưa ra gợi ý cụ thể với giá và lý do phù hợp.
Nếu không biết câu trả lời, hãy hướng dẫn khách hàng liên hệ hotline: 1900-xxxx"""

    INTENT_RESPONSES = {
        'greeting': [
            "Xin chào! Tôi là trợ lý AI của shop. Tôi có thể giúp gì cho bạn?",
            "Chào bạn! Bạn cần tư vấn về sản phẩm hay đơn hàng?",
        ],
        'goodbye': [
            "Cảm ơn bạn đã liên hệ! Chúc bạn một ngày tốt lành!",
            "Tạm biệt! Hẹn gặp lại bạn!",
        ],
        'return_policy': [
            "Chính sách đổi trả của shop:\n- Đổi trả miễn phí trong 7 ngày\n- Sản phẩm còn nguyên tem mác\n- Hoàn tiền trong 3-5 ngày làm việc",
        ],
        'payment': [
            "Shop hỗ trợ các hình thức thanh toán:\n- COD (thanh toán khi nhận hàng)\n- MoMo\n- VNPay\n- Chuyển khoản ngân hàng",
        ],
        'shipping': [
            "Thông tin giao hàng:\n- Nội thành: 1-2 ngày\n- Ngoại thành: 3-5 ngày\n- Miễn phí ship đơn từ 500k",
        ],
        'support': [
            "Bạn có thể liên hệ với chúng tôi qua:\n- Hotline: 1900-xxxx (8h-22h)\n- Email: support@shop.vn\n- Chat trực tiếp tại đây",
        ],
    }

    # Intents that should use RAG for product recommendations
    RAG_INTENTS = ['product_search', 'general']

    def __init__(self):
        self.ollama_host = settings.OLLAMA_HOST
        self.ollama_model = settings.OLLAMA_MODEL
        self.classifier = IntentClassifier()
        self.rag = RAGPipeline(self.ollama_host, self.ollama_model)

    async def chat(self, message, conversation_id=None, session_id=None, user_id=None):
        """
        Xử lý tin nhắn từ người dùng
        """
        from .models import Conversation, Message

        # Get or create conversation
        conversation = self._get_or_create_conversation(
            conversation_id, session_id, user_id
        )

        # Save user message
        user_message = Message.objects.create(
            conversation=conversation,
            role='user',
            content=message
        )

        # Classify intent
        intent = self.classifier.classify(message)

        # Check FAQ first
        faq_answer = self._check_faq(message)
        if faq_answer:
            response = faq_answer
        elif intent in self.INTENT_RESPONSES:
            # Use predefined response
            import random
            response = random.choice(self.INTENT_RESPONSES[intent])
        else:
            # Use LLM for complex queries
            response = await self._generate_llm_response(message, conversation)

        # Save assistant message
        assistant_message = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=response,
            metadata={'intent': intent}
        )

        return {
            'conversation_id': str(conversation.id),
            'response': response,
            'intent': intent,
            'message_id': str(assistant_message.id)
        }

    def chat_sync(self, message, conversation_id=None, session_id=None, user_id=None):
        """Synchronous version of chat with RAG support"""
        from .models import Conversation, Message

        # Get or create conversation
        conversation = self._get_or_create_conversation(
            conversation_id, session_id, user_id
        )

        # Save user message
        user_message = Message.objects.create(
            conversation=conversation,
            role='user',
            content=message
        )

        # Classify intent
        intent = self.classifier.classify(message)

        # Check FAQ first
        faq_answer = self._check_faq(message)
        products = []

        if faq_answer:
            response = faq_answer
        elif intent in self.INTENT_RESPONSES:
            import random
            response = random.choice(self.INTENT_RESPONSES[intent])
        elif intent in self.RAG_INTENTS:
            # Use RAG for product-related queries
            products = self.rag.retrieve(message, k=5)
            if products:
                response = self.rag.generate_augmented_response(message, products)
            else:
                response = self._generate_llm_response_sync(message, conversation)
        else:
            # Use LLM for other queries
            response = self._generate_llm_response_sync(message, conversation)

        # Save assistant message
        assistant_message = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=response,
            metadata={
                'intent': intent,
                'products': [p['product_id'] for p in products] if products else [],
                'used_rag': intent in self.RAG_INTENTS and bool(products)
            }
        )

        # Update conversation
        conversation.save()

        return {
            'conversation_id': str(conversation.id),
            'response': response,
            'intent': intent,
            'message_id': str(assistant_message.id),
            'products': products if products else None,
            'used_rag': intent in self.RAG_INTENTS and bool(products)
        }

    def _get_or_create_conversation(self, conversation_id, session_id, user_id):
        """Get existing or create new conversation"""
        from .models import Conversation
        import uuid as uuid_module

        if conversation_id:
            try:
                return Conversation.objects.get(id=conversation_id)
            except Conversation.DoesNotExist:
                pass

        if not session_id:
            session_id = str(uuid_module.uuid4())

        conversation, created = Conversation.objects.get_or_create(
            session_id=session_id,
            defaults={'user_id': user_id}
        )
        return conversation

    def _check_faq(self, message):
        """Tìm câu trả lời từ FAQ"""
        from .models import FAQ

        cache_key = f"faq:{hash(message.lower())}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # Simple keyword matching
        keywords = message.lower().split()

        faqs = FAQ.objects.filter(is_active=True)
        for faq in faqs:
            faq_keywords = faq.keywords.lower().split()
            matches = sum(1 for k in keywords if k in faq_keywords or k in faq.question.lower())
            if matches >= 2:
                # Update view count
                faq.view_count += 1
                faq.save(update_fields=['view_count'])
                cache.set(cache_key, faq.answer, timeout=300)
                return faq.answer

        return None

    def _generate_llm_response_sync(self, message, conversation):
        """Generate response using Ollama LLM (sync)"""
        try:
            # Build messages context
            messages = self._build_context(conversation, message)

            response = httpx.post(
                f"{self.ollama_host}/api/chat",
                json={
                    "model": self.ollama_model,
                    "messages": messages,
                    "stream": False
                },
                timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()
                return data.get('message', {}).get('content', self._fallback_response())
            else:
                logger.error(f"Ollama error: {response.status_code}")
                return self._fallback_response()

        except Exception as e:
            logger.error(f"LLM error: {e}")
            return self._fallback_response()

    async def _generate_llm_response(self, message, conversation):
        """Generate response using Ollama LLM (async)"""
        try:
            messages = self._build_context(conversation, message)

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_host}/api/chat",
                    json={
                        "model": self.ollama_model,
                        "messages": messages,
                        "stream": False
                    },
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get('message', {}).get('content', self._fallback_response())
                else:
                    return self._fallback_response()

        except Exception as e:
            logger.error(f"LLM error: {e}")
            return self._fallback_response()

    def _build_context(self, conversation, current_message):
        """Build conversation context for LLM"""
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]

        # Get recent messages
        recent_messages = conversation.messages.order_by('-created_at')[:10]
        for msg in reversed(list(recent_messages)):
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # Add current message
        messages.append({"role": "user", "content": current_message})

        return messages

    def _fallback_response(self):
        """Response khi LLM không available"""
        return "Xin lỗi, tôi không thể xử lý yêu cầu lúc này. Vui lòng thử lại sau hoặc liên hệ hotline: 1900-xxxx để được hỗ trợ."

    def search_products(self, query):
        """Search products via AI Search service"""
        try:
            response = httpx.post(
                f"{settings.PRODUCT_SERVICE_URL}/../search/",
                json={"query": query},
                timeout=5.0
            )
            if response.status_code == 200:
                return response.json().get('results', [])
        except Exception as e:
            logger.error(f"Product search error: {e}")
        return []


# Singleton instance
chatbot_engine = ChatbotEngine()
