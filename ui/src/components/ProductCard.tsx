import React from 'react';

export interface Product {
  url: string;
  images: string[];
  highlights: string[];
  title: string;
  price: number;
}

export interface ProductCardProps {
  product: Product;
  imageIndex: number;
  onMouseEnter: () => void;
  onMouseLeave: () => void;
  onCardClick: () => void;
}

export function ProductCard({
  product,
  imageIndex,
  onMouseEnter,
  onMouseLeave,
  onCardClick,
}: ProductCardProps) {
  return (
    <div
      className="w-1/3 bg-gray-50 rounded-lg p-4 flex flex-col cursor-pointer hover:shadow-lg transition-shadow"
      onClick={onCardClick}
    >
      <div
        className="relative pb-[100%] mb-4"
        onMouseEnter={onMouseEnter}
        onMouseLeave={onMouseLeave}
      >
        <img
          src={product.images[imageIndex] || product.images[0]}
          alt={product.title}
          className="absolute inset-0 w-full h-full object-cover rounded-lg transition-opacity duration-500"
        />
      </div>
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-lg font-semibold">{product.title}</h3>
        <span className="text-sm text-blue-600">
          ${product.price?.toFixed(2)}
        </span>
      </div>
      <ul className="space-y-1">
        {product.highlights.map((highlight, idx) => (
          <li key={idx} className="flex items-start gap-2 text-sm">
            <div className="w-1.5 h-1.5 bg-blue-500 rounded-full flex-shrink-0 mt-1.5" />
            <span className="text-gray-700">{highlight}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}