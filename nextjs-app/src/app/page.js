'use client';

import { useState } from 'react';
import { ProjectForm } from './components/ProjectForm';
import { ResultsDisplay } from './components/ResultsDisplay';

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');

  const handleSubmit = async (description) => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch('http://localhost:8000/generate_funding_report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          description,
          max_results: 50
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch results');
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError('Failed to generate report. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 py-12 px-4 sm:px-6 lg:px-8 text-black">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-8">
          Research Funding Assistant
        </h1>
        <ProjectForm onSubmit={handleSubmit} disabled={loading} />
        
        {loading && <div>Loading...</div>}
        {error && <div className="text-red-600 text-center mt-4">{error}</div>}
        {results && <ResultsDisplay results={results} />}
      </div>
    </div>
  );
}