'use client';

import { useState } from 'react';
import { ProjectForm } from './components/ProjectForm';
import { ResultsDisplay } from './components/ResultsDisplay';
import { FaDiscord, FaSlack } from 'react-icons/fa';
import Typewriter from 'typewriter-effect';
import { features } from './data/features';

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
    <div className="min-h-screen bg-black text-white">
      {/* Hero Section */}
      <div className="container mx-auto px-4 pt-20 pb-12">
        <div className="px-10 py-10 border border-gray-800 bg-[#0A0A0A] hover:border-gray-700 transition-all cursor-pointer">
          <div className="text-center mb-10">
            <h1 className="text-5xl font-bold my-4 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 inline-block text-transparent bg-clip-text">
              Plutus AI
            </h1>
            <div className="text-xl text-gray-400 flex mr-1 justify-center items-center gap-2">
              {/* <span>With Plutus AI, you can</span> */}
              <Typewriter
                options={{
                  strings: [
                    'Discover untapped funding opportunities',
                    'Match your research with ideal grants',
                    'Accelerate your funding success rate',
                    'Streamline your grant discovery process',
                    'Identify strategic funding partners'
                  ],
                  autoStart: true,
                  loop: true,
                }}
              />
            </div>
          </div>

          {/* Main Form */}
          <div className="max-w-4xl mx-auto mb-10">
            <ProjectForm onSubmit={handleSubmit} disabled={loading} />
            <div className="flex justify-center gap-4 mt-4">
              <button className="bg-opacity-40 bg-slate-900 w-full py-3 border border-gray-800 rounded-lg hover:border-gray-700 transition-all">
                <FaDiscord size={20} className="inline-block mr-2 mb-0.5" /> Download Discord App
              </button>
              <button className="bg-opacity-40 bg-slate-900 w-full py-3 border border-gray-800 rounded-lg hover:border-gray-700 transition-all">
                <FaSlack size={20} className="inline-block mr-2 mb-0.5" /> Download Slack App
              </button>
            </div>
          </div>
        </div>

        {/* Feature Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 mx-auto">
          {features.map((feature, index) => (
            <FeatureCard
              key={index}
              title={feature.title}
              description={feature.description}
              icon={feature.icon}
            />
          ))}
        </div>

        {loading && <div className="text-center mt-8">Loading...</div>}
        {error && <div className="text-red-600 text-center mt-8">{error}</div>}
        {results && <ResultsDisplay results={results} />}
      </div>
    </div>
  );
}

function FeatureCard({ title, description, icon: Icon }) {
  return (
    <div className="p-6 border border-gray-800 bg-[#0A0A0A] hover:border-gray-700 transition-all cursor-pointer">
      <div className="text-4xl mb-4 text-indigo-500 mx-auto">
        <Icon size={32} />
      </div>
      <h3 className="text-xl font-bold mb-2">{title}</h3>
      <p className="text-gray-400">{description}</p>
    </div>
  );
}