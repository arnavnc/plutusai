import ReactMarkdown from 'react-markdown';

export function ResultsDisplay({ results }) {
  return (
    <div className="mt-8 space-y-6 bg-white shadow rounded-lg p-6">
      <div>
        <h2 className="text-xl font-semibold mb-2">Search Terms Used</h2>
        <div className="flex flex-wrap gap-2">
          {results.search_terms.map((term, index) => (
            <span key={index} className="px-2 py-1 bg-gray-100 rounded-full text-sm">
              {term}
            </span>
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-xl font-semibold mb-2">Funding Summary</h2>
        <div className="prose max-w-none">
          <ReactMarkdown>{results.summary}</ReactMarkdown>
        </div>
      </div>

      <div>
        <h2 className="text-xl font-semibold mb-2 text-black">Detailed Results</h2>
        <div className="space-y-4 text-black">
          {results.funders_data.map((funder, index) => (
            <div key={index} className="border rounded p-4">
              <h3 className="font-medium">{funder.title}</h3>
              <div className="mt-2 text-sm text-black">
                <p>Publication Year: {funder.publication_year}</p>
                <p>Citations: {funder.cited_by_count}</p>
                <div className="mt-2">
                  <p className="font-medium">Grants:</p>
                  <ul className="list-disc pl-5">
                    {funder.grants.map((grant, gIndex) => (
                      <li key={gIndex}>
                        {grant.funder_display_name}
                        {grant.award_id && ` (Grant ID: ${grant.award_id})`}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}