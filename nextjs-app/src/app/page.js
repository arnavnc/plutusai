'use client';

import { useState, useEffect } from 'react';
import { ProjectForm } from './components/ProjectForm';
import { ResultsDisplay } from './components/ResultsDisplay';
import { LoadingStates } from './components/LoadingStates';
import { FaDiscord, FaSlack } from 'react-icons/fa';
import Typewriter from 'typewriter-effect';
import { features } from './data/features';

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [loadingStates, setLoadingStates] = useState({
    searchTerms: false,
    paperSearch: {},
    fundingData: false,
    summary: false
  });
  const [searchTerms, setSearchTerms] = useState([]);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');

  const handleSubmit = async (description) => {
    setLoading(true);
    setError('');
    setResults(null);
    setLoadingStates({
      searchTerms: false,
      paperSearch: {},
      fundingData: false,
      summary: false
    });
    
    try {
      const eventSource = new EventSource(
        `http://localhost:8000/generate_funding_report?description=${encodeURIComponent(description)}`,
        {
          withCredentials: true,
        }
      );

      eventSource.addEventListener('open', (event) => {
        console.log('Connection opened');
      });

      eventSource.addEventListener('message', (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log("Received SSE data:", data);
          
          if (data.error) {
            console.error("SSE error:", data.error);
            setError(data.error);
            eventSource.close();
            setLoading(false);
            return;
          }
          
          if (data.stage) {
            switch (data.stage) {
              case 'searchTerms':
                if (data.status === 'completed') {
                  setSearchTerms(data.data);
                  setLoadingStates(prev => ({
                    ...prev,
                    searchTerms: true
                  }));
                }
                break;
                
              case 'paperSearch':
                if (data.status === 'completed') {
                  setLoadingStates(prev => ({
                    ...prev,
                    paperSearch: {
                      ...prev.paperSearch,
                      [data.term]: true
                    }
                  }));
                }
                break;
                
              case 'fundingData':
                if (data.status === 'completed') {
                  setLoadingStates(prev => ({
                    ...prev,
                    fundingData: true
                  }));
                }
                break;
                
              case 'summary':
                if (data.status === 'completed') {
                  setLoadingStates(prev => ({
                    ...prev,
                    summary: true
                  }));
                }
                break;
            }
          } else {
            setResults(data);
            eventSource.close();
            setLoading(false);
          }
        } catch (e) {
          console.error('Error parsing SSE data:', e);
          setError('Error processing server response');
          eventSource.close();
          setLoading(false);
        }
      });

      eventSource.addEventListener('error', (event) => {
        console.error('EventSource error:', event);
        if (event.target.readyState === EventSource.CLOSED) {
          console.log('Connection was closed');
        }
        eventSource.close();
        setError('Failed to generate report. Please try again.');
        setLoading(false);
      });

      // Add cleanup on component unmount
      return () => {
        if (eventSource) {
          console.log('Closing connection');
          eventSource.close();
        }
      };
    } catch (error) {
      console.error('Error setting up EventSource:', error);
      setError('Failed to connect to server');
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
              <button disabled={true} className="disabled:cursor-not-allowed bg-opacity-40 bg-slate-900 w-full py-3 border border-gray-800 rounded-lg hover:border-gray-700 transition-all">
                <FaSlack size={20} className="inline-block mr-2 mb-0.5" /> Download Slack App (Coming Soon)
              </button>
            </div>
          </div>
        </div>

        {loading && (
          <LoadingStates 
            states={loadingStates}
            searchTerms={searchTerms}
          />
        )}
        
        {results && <ResultsDisplay results={results} />}
        {error && <div className="text-red-600 text-center mt-8">{error}</div>}

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