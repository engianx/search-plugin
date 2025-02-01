import React, { useState, useRef, useEffect } from 'react';
import { Search, Send, Loader2, ChevronLeft, ChevronRight, X } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { SearchInput } from './SearchInput';
import { SearchResults, SearchResult } from './SearchResults';

interface Product {
  url: string;
  images: string[];
  highlights: string[];
  title: string;
  price: number;
}

const MOCK_RESULTS: Record<string, SearchResult> = {
  gadgets: {
    products: [
      {
        url: '/products/premium-headphones',
        title: 'Premium Headphones',
        price: 299.99,
        images: [
          'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&q=80',
        ],
        highlights: ['Noise cancelling', 'Wireless', '30h battery life']
      },
      {
        url: '/products/smart-watch',
        title: 'Smart Watch',
        price: 199.99,
        images: [
          'https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=400&q=80'
        ],
        highlights: ['Fitness tracking', 'Heart rate monitor', 'Water resistant']
      },
      {
        url: '/products/wireless-earbuds',
        title: 'Wireless Earbuds',
        price: 149.99,
        images: [
          'https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=400&q=80'
        ],
        highlights: ['Active noise cancelling', 'Touch controls', '24h playtime']
      },
      {
        url: '/products/smart-speaker',
        title: 'Smart Speaker',
        price: 199.99,
        images: [
          'https://images.unsplash.com/photo-1589492477829-5e65395b66cc?w=400&q=80'
        ],
        highlights: ['360° sound', 'Voice control', 'Multi-room sync']
      }
    ],
    answer: {
      url: "https://example.com/gadgets-guide",
      content: "Here are the latest smart gadgets that match your search criteria..."
    }
  },
  dresses: {
    products: [
      {
        url: '/products/summer-floral-dress',
        title: 'Summer Floral Dress',
        price: 59.99,
        images: [
          'https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=400&q=80'
        ],
        highlights: ['100% Cotton', 'Floral pattern', 'Midi length']
      },
      {
        url: '/products/evening-cocktail-dress',
        title: 'Evening Cocktail Dress',
        price: 79.99,
        images: [
          'https://images.unsplash.com/photo-1566174053879-31528523f8ae?w=400&q=80'
        ],
        highlights: ['Elegant design', 'Perfect for parties', 'Available in multiple colors']
      },
      {
        url: '/products/casual-maxi-dress',
        title: 'Casual Maxi Dress',
        price: 39.99,
        images: [
          'https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=400&q=80'
        ],
        highlights: ['Comfortable fit', 'Breathable fabric', 'Perfect for summer']
      }
    ],
    answer: {
      url: "https://example.com/dress-guide",
      content: "Discover our collection of stylish dresses perfect for any occasion..."
    }
  },
  books: {
    products: [
      {
        url: '/products/art-of-programming',
        title: 'The Art of Programming',
        price: 29.99,
        images: [
          'https://images.unsplash.com/photo-1532012197267-da84d127e765?w=400&q=80'
        ],
        highlights: ['Bestseller', 'Comprehensive guide', 'Perfect for beginners']
      },
      {
        url: '/products/modern-cooking',
        title: 'Modern Cooking',
        price: 39.99,
        images: [
          'https://images.unsplash.com/photo-1589998059171-988d887df646?w=400&q=80'
        ],
        highlights: ['100+ recipes', 'Step-by-step guides', 'Beautiful photography']
      }
    ],
    answer: {
      url: "https://example.com/book-guide",
      content: "Explore our curated selection of books that will expand your knowledge..."
    }
  },
  "guide": {
    products: [],
    answer: {
      url: "https://example.com/general-guide",
      content: "Here are some popular items from different categories that might interest you..."
    }
  }
};

interface SearchDialogProps {
  domain: string;
}

function SearchDialog({ domain }: SearchDialogProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<SearchResult | null>(null);
  const [currentSlide, setCurrentSlide] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const [hoveredProduct, setHoveredProduct] = useState<string | null>(null);
  const [imageIndices, setImageIndices] = useState<Record<string, number>>({});

  useEffect(() => {
    if (isExpanded && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isExpanded]);

  // Image rotation effect based on hovered product
  useEffect(() => {
    if (!hoveredProduct) return;
    const product = result?.products.find(p => p.url === hoveredProduct);
    if (!product || product.images.length <= 1) return;
    const timer = setInterval(() => {
      setImageIndices(prev => ({
        ...prev,
        [hoveredProduct]: ((prev[hoveredProduct] || 0) + 1) % product.images.length
      }));
    }, 1000);
    return () => clearInterval(timer);
  }, [hoveredProduct, result?.products]);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setIsLoading(true);
    setIsDialogOpen(true);
    setCurrentSlide(0);

    try {
      const searchUrl = `http://localhost:8080/search/${domain}?query=${encodeURIComponent(query)}`;
      const response = await fetch(searchUrl);
      if (!response.ok) {
        throw new Error('Search request failed');
      }
      const searchResult: SearchResult = await response.json();
      setResult(searchResult);
    } catch (error) {
      console.error('Search failed:', error);
      // Fallback to mock data
      setResult({
        products: [
          MOCK_RESULTS.gadgets.products[0],
          MOCK_RESULTS.dresses.products[0],
          MOCK_RESULTS.books.products[0]
        ],
        answer: {
          url: "https://example.com/error-recommendations",
          content: "We encountered an error, but here are some popular items you might like..."
        }
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const slideNext = () => {
    if (result && currentSlide < result.products.length - 3) {
      setCurrentSlide(prev => prev + 1);
    }
  };

  const slidePrev = () => {
    if (currentSlide > 0) {
      setCurrentSlide(prev => prev - 1);
    }
  };

  const showNavigation = result && result.products.length > 3;

  return (
    <div className="fixed bottom-8 right-8 z-50">
      {!isDialogOpen ? (
        <div className="flex items-center">
          <div
            className={`relative bg-white rounded-full shadow-lg transition-all duration-300 ease-in-out flex items-center ${
              isExpanded ? 'w-64 px-4 py-2' : 'w-12 h-12 justify-center cursor-pointer'
            }`}
            onClick={() => {
              if (!isExpanded) setIsExpanded(true);
            }}
          >
            {isExpanded ? (
              <>
                <input
                  ref={inputRef}
                  type="text"
                  className="flex-1 outline-none px-2 py-2"
                  placeholder="How can I help you?"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyPress={handleKeyPress}
                />
                <button onClick={handleSearch} className="p-2 hover:text-blue-600 transition-colors">
                  <Send size={20} />
                </button>
                <button
                  onClick={() => {
                    setQuery('');
                    setIsExpanded(false);
                  }}
                  className="absolute -top-3 -right-3 p-2 bg-white shadow-md hover:bg-gray-200 rounded-full"
                >
                  <X size={20} />
                </button>
              </>
            ) : (
              <Search size={20} />
            )}
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-xl w-[800px] h-[600px] p-6 flex flex-col relative">
          {/* [X] Close button half-overlapping the top-right corner */}
          <button
            onClick={() => {
              setIsDialogOpen(false);
              setQuery('');
            }}
            className="absolute -top-3 -right-3 p-2 bg-white shadow-md hover:bg-gray-200 rounded-full"
          >
            <X size={20} />
          </button>
          <SearchInput
            query={query}
            isLoading={isLoading}
            onQueryChange={setQuery}
            onSearch={handleSearch}
            onClose={() => {
              setIsDialogOpen(false);
              setQuery('');
            }}
            onKeyPress={handleKeyPress}
          />

          {/* Results area wrapped in a scrollable container */}
          {result && (
            <div className="flex-1 overflow-y-auto mt-4">
              {result.products && result.products.length > 0 ? (
                <SearchResults
                  result={result}
                  currentSlide={currentSlide}
                  slideNext={slideNext}
                  slidePrev={slidePrev}
                  showNavigation={!!showNavigation}
                  imageIndices={imageIndices}
                  setHoveredProduct={setHoveredProduct}
                  setImageIndices={setImageIndices}
                />
              ) : (
                // Render answer-only content when there are no products.
                <div className="p-4">
                  <ReactMarkdown>{result.answer.content}</ReactMarkdown>
                  <a href={result.answer.url} className="text-blue-600 mt-2 inline-block">
                    Learn more
                  </a>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default SearchDialog;