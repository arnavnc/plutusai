import ReactMarkdown from 'react-markdown';

export function ResultsDisplay({ results }) {
  return (
    <div className="space-y-6 border border-gray-800 bg-[#0A0A0A] p-6">
      <div className="flex flex-col gap-4 border-b border-gray-800 pb-4">
        <h2 className="text-xl font-semibold mb-2 text-white">Your Results</h2>
      </div>
      <div>
        <h2 className="text-xl font-semibold mb-2 text-white">Search Terms Used</h2>
        <div className="flex flex-wrap gap-2">
          {results.search_terms.map((term, index) => (
            <span key={index} className="px-3 py-1 bg-opacity-40 bg-slate-900 border border-gray-800 rounded-full text-gray-300 text-sm">
              {term}
            </span>
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-xl font-semibold mb-2 text-white">Funding Summary</h2>
        <div className="prose prose-invert max-w-none text-gray-300">
          <ReactMarkdown>{results.summary}</ReactMarkdown>
        </div>
      </div>

      <div>
        <h2 className="text-xl font-semibold mb-4 text-white">Funding Opportunities</h2>
        <div className="grid lg:grid-cols-2">
          {results.funders_data.map((funder, index) => (
            <div key={index} className="max-h-48 overflow-clip overflow-y-scroll scroll-y-auto border border-gray-800 bg-opacity-40 bg-slate-900 p-4 hover:border-gray-700 transition-all">
              <h3 className="font-medium text-white text-lg mb-2">{funder.title}</h3>
              <div className="grid grid-cols-2 gap-4 mb-3">
                <div className="flex items-center space-x-2">
                  <span className="text-gray-500">Year:</span>
                  <span className="text-gray-300">{funder.publication_year}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-gray-500">Citations:</span>
                  <span className="text-gray-300">{funder.cited_by_count}</span>
                </div>
              </div>
              <div className="mt-3">
                <p className="text-gray-300 font-medium mb-2">Grants:</p>
                <div className="space-y-2">
                  {funder.grants.map((grant, gIndex) => (
                    <div key={gIndex} className="flex flex-col space-y-1 p-2 bg-black bg-opacity-50 rounded">
                      <span className="text-indigo-400 font-medium">
                        {grant.funder_display_name}
                      </span>
                      {grant.award_id && (
                        <span className="text-gray-400 text-sm">
                          Grant ID: {grant.award_id}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
              {funder.doi && (
                <a 
                  href={funder.doi}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block mt-3 text-sm text-indigo-400 hover:text-indigo-300 transition-colors"
                >
                  View Publication →
                </a>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}