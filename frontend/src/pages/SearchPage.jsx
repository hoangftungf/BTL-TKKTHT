import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { searchService } from '../services/aiService';
import ProductGrid from '../components/product/ProductGrid';

const SearchPage = () => {
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q') || '';

  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [suggestions, setSuggestions] = useState([]);

  useEffect(() => {
    const searchWithAI = async () => {
      if (!query) return;

      setLoading(true);
      try {
        const response = await searchService.search(query);
        const results = response.data.results || [];

        // Map results to product format
        const mappedProducts = results.map((r) => ({
          id: r.product_id,
          name: r.name,
          price: r.price,
          category: r.category,
          brand: r.brand,
          ...r.product,
        }));

        setProducts(mappedProducts);
        setTotal(response.data.total || 0);
      } catch (error) {
        console.error('Search error:', error);
        setProducts([]);
      } finally {
        setLoading(false);
      }
    };

    searchWithAI();
  }, [query]);

  useEffect(() => {
    const fetchSuggestions = async () => {
      if (query.length >= 2) {
        try {
          const response = await searchService.autocomplete(query, 5);
          setSuggestions(response.data.suggestions || []);
        } catch (error) {
          setSuggestions([]);
        }
      }
    };

    fetchSuggestions();
  }, [query]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">
        Kết quả tìm kiếm
      </h1>
      <p className="text-gray-500 mb-4">
        {total} kết quả cho "{query}"
      </p>

      {suggestions.length > 0 && (
        <div className="mb-6">
          <p className="text-sm text-gray-500 mb-2">Gợi ý tìm kiếm:</p>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((s, index) => (
              <a
                key={index}
                href={`/search?q=${encodeURIComponent(s.text)}`}
                className="px-3 py-1 bg-gray-100 rounded-full text-sm text-gray-700 hover:bg-gray-200"
              >
                {s.text}
              </a>
            ))}
          </div>
        </div>
      )}

      <ProductGrid
        products={products}
        loading={loading}
        emptyMessage={`Không tìm thấy sản phẩm cho "${query}"`}
      />
    </div>
  );
};

export default SearchPage;
