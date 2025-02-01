import { useParams, Navigate } from 'react-router-dom';
import SearchDialog from '../components/SearchDialog';
import { useState } from 'react';

function Demo() {
  const { domain } = useParams<{ domain: string }>();
  const [error, setError] = useState<string>('');

  if (!domain) {
    return <Navigate to="/" replace />;
  }

  const proxyUrl = `/proxy?url=${encodeURIComponent(`https://${domain}`)}`;

  return (
    <div className="h-screen w-screen">
      <iframe
        src={proxyUrl}
        className="w-full h-full border-0"
        title={`Demo of ${domain}`}
        onError={(e) => setError('Failed to load website')}
      />
      <SearchDialog domain={domain ?? 'defaultdomain.com'} />
      {error && (
        <div className="fixed top-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}
    </div>
  );
}

export default Demo;