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
      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700">
          Project Description
        </label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={6}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
          placeholder="Describe your research project..."
          disabled={disabled}
        />
      </div>
      <button
        type="submit"
        disabled={disabled || !description.trim()}
        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
      >
        Generate Funding Report
      </button>
    </form>
  );
}