import ReactMarkdown from 'react-markdown';
import { FaUniversity, FaChartLine, FaClipboardList, FaRegLightbulb } from 'react-icons/fa';

export function ResultsDisplay({ results }) {
  return (
    <div className="space-y-8 border border-gray-800 bg-[#0A0A0A] p-6">
      {/* Search Terms Section */}
      <div className="pb-6 border-b border-gray-800">
        <h2 className="text-xl font-semibold mb-3 text-white flex items-center gap-2">
          <FaRegLightbulb className="text-indigo-400" />
          Search Terms
        </h2>
        <div className="flex flex-wrap gap-2">
          {results.search_terms.map((term, index) => (
            <span key={index} className="px-3 py-1 bg-opacity-40 bg-indigo-900 border border-indigo-800 rounded-full text-indigo-200 text-sm">
              {term}
            </span>
          ))}
        </div>
      </div>

      {/* Key Findings Section */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Top Funders Section */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <FaUniversity className="text-indigo-400" />
            Top Funding Organizations
          </h3>
          <div className="space-y-3">
            {extractTopFunders(results.summary).map((funder, index) => (
              <div key={index} className="p-3 border border-gray-800 rounded-lg hover:border-gray-700 transition-all">
                <h4 className="font-medium text-white">{funder.name}</h4>
                <p className="text-sm text-gray-400">{funder.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Grant Patterns Section */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <FaChartLine className="text-indigo-400" />
            Typical Grant Patterns
          </h3>
          <div className="space-y-3">
            {extractGrantPatterns(results.summary).map((pattern, index) => (
              <div key={index} className="p-3 border border-gray-800 rounded-lg hover:border-gray-700 transition-all">
                <span className="text-white">{pattern}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Strategic Recommendations */}
      <div className="pt-6 border-t border-gray-800">
        <h3 className="text-lg font-semibold mb-4 text-white flex items-center gap-2">
          <FaClipboardList className="text-indigo-400" />
          Strategic Recommendations
        </h3>
        <div className="grid md:grid-cols-2 gap-4">
          {extractRecommendations(results.summary).map((rec, index) => (
            <div key={index} className="p-4 bg-opacity-40 bg-slate-900 rounded-lg border border-gray-800">
              <p className="text-gray-300">{rec}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Funding Examples */}
      <div className="pt-6 border-t border-gray-800">
        <h3 className="text-lg font-semibold mb-4 text-white">Recent Funding Examples</h3>
        <div className="grid md:grid-cols-2 gap-4">
          {results.funders_data.map((funder, index) => (
            <div key={index} className="p-4 border border-gray-800 rounded-lg hover:border-gray-700 transition-all">
              <h4 className="font-medium text-white text-lg mb-2">{funder.title}</h4>
              <div className="flex items-center gap-4 mb-3 text-sm">
                <span className="text-gray-400">Year: {funder.publication_year}</span>
                <span className="text-gray-400">Citations: {funder.cited_by_count}</span>
              </div>
              <div className="space-y-2">
                {funder.grants.map((grant, gIndex) => (
                  <div key={gIndex} className="p-2 bg-black bg-opacity-50 rounded">
                    <span className="text-indigo-400 font-medium block">
                      {grant.funder_display_name}
                    </span>
                    {grant.award_id && (
                      <span className="text-gray-500 text-sm">
                        Grant ID: {grant.award_id}
                      </span>
                    )}
                  </div>
                ))}
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

// Helper functions to parse the summary text
function cleanMarkdown(text) {
  return text
    .replace(/\*\*/g, '')  // Remove bold markdown
    .replace(/\*/g, '')    // Remove italic markdown
    .replace(/`/g, '')     // Remove code markdown
    .replace(/^-\s*/g, '') // Remove leading dash and space
    .trim();
}

function extractTopFunders(summary) {
  const funders = [];
  const lines = summary.split('\n');
  let inFundersSection = false;

  for (const line of lines) {
    if (line.includes('Top Funding Organizations')) {
      inFundersSection = true;
      continue;
    }
    if (inFundersSection && line.startsWith('2.')) {
      break;
    }
    if (inFundersSection && line.trim().startsWith('-')) {
      const [name, ...descParts] = cleanMarkdown(line).split(':');
      funders.push({
        name: name.trim(),
        description: descParts.join(':').trim()
      });
    }
  }
  return funders;
}

function extractGrantPatterns(summary) {
  const patterns = [];
  const lines = summary.split('\n');
  let inPatternSection = false;

  for (const line of lines) {
    if (line.includes('Typical Grant Sizes')) {
      inPatternSection = true;
      continue;
    }
    if (inPatternSection && line.startsWith('3.')) {
      break;
    }
    if (inPatternSection && line.trim().startsWith('-')) {
      patterns.push(cleanMarkdown(line));
    }
  }
  return patterns;
}

function extractRecommendations(summary) {
  const recommendations = [];
  const lines = summary.split('\n');
  let inRecommendationsSection = false;

  for (const line of lines) {
    if (line.includes('Specific Recommendations')) {
      inRecommendationsSection = true;
      continue;
    }
    if (inRecommendationsSection && line.trim().startsWith('-')) {
      recommendations.push(cleanMarkdown(line));
    }
  }
  return recommendations;
}