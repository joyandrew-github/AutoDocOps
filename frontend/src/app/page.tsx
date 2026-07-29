export default function Home() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-4xl mx-auto px-4 py-16">
        <div className="text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            AutoDocOps
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Production-grade AI platform for automated documentation operations
          </p>
          <div className="flex gap-4 justify-center">
            <button className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
              Get Started
            </button>
            <button className="px-6 py-3 bg-white text-gray-700 rounded-lg hover:bg-gray-50 transition-colors border border-gray-300">
              Learn More
            </button>
          </div>
        </div>
        
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">Fast & Scalable</h3>
            <p className="text-gray-600">Built with modern technologies for optimal performance</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">AI-Powered</h3>
            <p className="text-gray-600">Leverage cutting-edge AI for intelligent documentation</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">Production Ready</h3>
            <p className="text-gray-600">Enterprise-grade architecture with comprehensive tooling</p>
          </div>
        </div>
      </div>
    </main>
  )
}
