function Home() {
  return (
    <div className="min-h-screen bg-gray-100">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-4">
          Interactive Search Demo
        </h1>
        <p className="text-gray-600">
          Type in <code className="bg-gray-200 px-2 py-1 rounded">/demo/example.com</code> to try it out.
        </p>
      </div>
    </div>
  );
}

export default Home;