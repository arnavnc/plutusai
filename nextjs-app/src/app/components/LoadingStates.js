import { FaCheck } from 'react-icons/fa';

export function LoadingStates({ states, searchTerms = [] }) {
  return (
    <div className="mt-8 space-y-3 border border-gray-800 bg-[#0A0A0A] p-6 rounded-lg">
      <div className="flex items-center space-x-2">
        {states.searchTerms ? (
          <FaCheck className="text-green-500" />
        ) : (
          <div className="animate-spin h-4 w-4 border-2 border-gray-500 rounded-full border-t-transparent" />
        )}
        <span className="text-gray-300">Generating search terms</span>
      </div>
      
      {searchTerms.map((term, index) => (
        <div key={term} className="flex items-center space-x-2 ml-4">
          {states.paperSearch[term] ? (
            <FaCheck className="text-green-500" />
          ) : (
            <div className="animate-spin h-4 w-4 border-2 border-gray-500 rounded-full border-t-transparent" />
          )}
          <span className="text-gray-300">Finding papers for "{term}"</span>
        </div>
      ))}

      {searchTerms.length > 0 && (
        <>
          <div className="flex items-center space-x-2">
            {states.fundingData ? (
              <FaCheck className="text-green-500" />
            ) : (
              <div className="animate-spin h-4 w-4 border-2 border-gray-500 rounded-full border-t-transparent" />
            )}
            <span className="text-gray-300">Compiling funding data</span>
          </div>

          <div className="flex items-center space-x-2">
            {states.summary ? (
              <FaCheck className="text-green-500" />
            ) : (
              <div className="animate-spin h-4 w-4 border-2 border-gray-500 rounded-full border-t-transparent" />
            )}
            <span className="text-gray-300">Generating summary...</span>
          </div>
        </>
      )}
    </div>
  );
} 