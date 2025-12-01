"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();
  const [query, setQuery] = useState("Compare Notion vs Coda vs ClickUp for project management");
  const [companies, setCompanies] = useState("Notion, Coda, ClickUp");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const companiesList = companies.split(",").map((c) => c.trim()).filter(Boolean);

      if (companiesList.length === 0) {
        setError("Please enter at least one company");
        setLoading(false);
        return;
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/research`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query,
          companies: companiesList,
          analysis_depth: "standard",
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Navigate to research page with session ID
      router.push(`/research/${data.session_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start research");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 text-white">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-5xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
              Multi-Agent Market Research
            </h1>
            <p className="text-xl text-gray-300">
              7 AI agents working together to deliver comprehensive competitive intelligence
            </p>
          </div>

          {/* Features */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-12">
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-lg p-4 border border-gray-700">
              <div className="text-blue-400 font-semibold mb-2">🔍 Deep Research</div>
              <div className="text-sm text-gray-400">Web search, financial data, and market analysis</div>
            </div>
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-lg p-4 border border-gray-700">
              <div className="text-purple-400 font-semibold mb-2">⚡ Real-Time</div>
              <div className="text-sm text-gray-400">Watch agents execute live with progress updates</div>
            </div>
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-lg p-4 border border-gray-700">
              <div className="text-green-400 font-semibold mb-2">📊 Comprehensive</div>
              <div className="text-sm text-gray-400">SWOT, comparisons, fact-checking, and visualizations</div>
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-8 border border-gray-700 shadow-2xl">
            <div className="mb-6">
              <label htmlFor="query" className="block text-sm font-medium mb-2 text-gray-300">
                Research Query
              </label>
              <input
                id="query"
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full px-4 py-3 bg-gray-900 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-white placeholder-gray-500"
                placeholder="What would you like to research?"
                required
              />
            </div>

            <div className="mb-6">
              <label htmlFor="companies" className="block text-sm font-medium mb-2 text-gray-300">
                Companies (comma-separated)
              </label>
              <input
                id="companies"
                type="text"
                value={companies}
                onChange={(e) => setCompanies(e.target.value)}
                className="w-full px-4 py-3 bg-gray-900 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-white placeholder-gray-500"
                placeholder="e.g., Notion, Coda, ClickUp"
                required
              />
            </div>

            {error && (
              <div className="mb-6 p-4 bg-red-900/50 border border-red-700 rounded-lg text-red-200">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:from-gray-600 disabled:to-gray-600 text-white font-semibold py-4 px-6 rounded-lg transition-all transform hover:scale-105 disabled:scale-100 disabled:cursor-not-allowed shadow-lg"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Starting Research...
                </span>
              ) : (
                "Start Research"
              )}
            </button>
          </form>

          {/* Info */}
          <div className="mt-8 text-center text-sm text-gray-400">
            <p>Powered by 7 specialized AI agents using LangGraph orchestration</p>
          </div>
        </div>
      </div>
    </div>
  );
}
