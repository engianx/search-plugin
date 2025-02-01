import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Product, ProductCard } from './ProductCard';

export interface SearchResult {
  products: Product[];
  answer: {
    url: string;
    content: string;
  };
}

export interface SearchResultsProps {
  result: SearchResult;
  currentSlide: number;
  slideNext: () => void;
  slidePrev: () => void;
  showNavigation: boolean;
  imageIndices: Record<string, number>;
  setHoveredProduct: (url: string | null) => void;
  setImageIndices: React.Dispatch<React.SetStateAction<Record<string, number>>>;
}

export function SearchResults({
  result,
  currentSlide,
  slideNext,
  slidePrev,
  showNavigation,
  imageIndices,
  setHoveredProduct,
  setImageIndices,
}: SearchResultsProps) {
  return (
    <>
      <div className="h-[400px]">
        <div className="relative h-full">
          {showNavigation && (
            <div className="absolute inset-y-0 left-0 flex items-center z-10">
              <button
                onClick={slidePrev}
                disabled={currentSlide === 0}
                className="p-2 rounded-full bg-white shadow-lg disabled:opacity-50"
              >
                <ChevronLeft size={24} />
              </button>
            </div>
          )}
          <div className="h-full">
            <div className="w-full px-12">
              <div className="flex gap-6">
                {result.products
                  .slice(currentSlide, currentSlide + 3)
                  .map((product) => (
                    <ProductCard
                      key={product.url}
                      product={product}
                      imageIndex={imageIndices[product.url] || 0}
                      onMouseEnter={() => setHoveredProduct(product.url)}
                      onMouseLeave={() =>
                        setImageIndices((prev) => ({ ...prev, [product.url]: 0 })) ||
                        setHoveredProduct(null)
                      }
                      onCardClick={() => window.open(product.url, '_blank')}
                    />
                  ))}
              </div>
            </div>
          </div>
          {showNavigation && (
            <div className="absolute inset-y-0 right-0 flex items-center z-10">
              <button
                onClick={slideNext}
                disabled={currentSlide >= result.products.length - 3}
                className="p-2 rounded-full bg-white shadow-lg disabled:opacity-50"
              >
                <ChevronRight size={24} />
              </button>
            </div>
          )}
        </div>
      </div>
      {result.answer && (
        <div className="bg-gray-50 rounded-lg p-4 mb-4">
          <ReactMarkdown
            className="text-gray-700 prose prose-sm max-w-none"
            components={{
              a: ({ node, ...props }) => (
                <a
                  {...props}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline"
                  onClick={(e) => e.stopPropagation()}
                />
              ),
            }}
          >
            {result.answer.content}
          </ReactMarkdown>
          <a
            href={result.answer.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline mt-2 inline-block"
            onClick={(e) => e.stopPropagation()}
          >
            [Learn more]
          </a>
        </div>
      )}
    </>
  );
}