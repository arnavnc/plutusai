import { useState } from 'react';

export function ProjectForm({ onSubmit, disabled }) {
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [results, setResults] = useState([]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    console.log('Submitting description:', description);
    setLoading(true);
    setError('');
    try {
      console.log('Making fetch request...');
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
      console.log('Response received:', response);
      
      if (!response.ok) {
        throw new Error('Failed to fetch results');
      }

      const data = await response.json();
      console.log('Parsed data:', data);
      setResults(data);
      onSubmit(description);
    } catch (err) {
      console.error('Error:', err);
      setError('Failed to generate report. Please try again.');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="w-full bg-[#0A0A0A] border border-gray-800 rounded-lg p-6">
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={6}
          className="w-full bg-transparent text-white placeholder-gray-500 focus:outline-none resize-none"
          placeholder="Describe your research project..."
          disabled={disabled}
        />
      </div>
      <button
        type="submit"
        disabled={disabled || !description.trim()}
        className="w-full py-3 px-4 bg-white text-black rounded-lg font-medium hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Generate Funding Report &rarr;
      </button>
    </form>
  );
}