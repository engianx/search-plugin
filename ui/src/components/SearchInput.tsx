import React from 'react';
import { Send, Loader2 } from 'lucide-react';

export interface SearchInputProps {
  query: string;
  isLoading: boolean;
  onQueryChange: (value: string) => void;
  onSearch: () => void;
  onKeyPress: (e: React.KeyboardEvent<HTMLInputElement>) => void;
}

export function SearchInput({
  query,
  isLoading,
  onQueryChange,
  onSearch,
  onKeyPress,
}: SearchInputProps) {
  return (
    <div className="flex items-center gap-4 mb-6">
      <input
        type="text"
        className="flex-1 px-4 py-2 border rounded-lg outline-none focus:border-blue-500"
        placeholder="Search..."
        value={query}
        onChange={(e) => onQueryChange(e.target.value)}
        onKeyPress={onKeyPress}
      />
      <button
        onClick={onSearch}
        className="p-2 rounded-full hover:bg-gray-100 transition-colors"
        disabled={isLoading}
      >
        {isLoading ? <Loader2 className="animate-spin" size={20} /> : <Send size={20} />}
      </button>
    </div>
  );
}